"""
Usage: main.py lookup <image>...
       main.py insert <image>...
"""
from collections import Counter
from os import cpu_count
import hashlib
import multiprocessing
import os
import platform
import shutil
import sys
import tempfile
import pathlib

from appdirs import user_data_dir
from flask.cli import FlaskGroup
from flask_admin import Admin, AdminIndexView
from flask_sqlalchemy import SQLAlchemy
from PIL import Image
from sqlalchemy_utils import database_exists, create_database
import click
import cv2
import flask
import numpy as np
import redis
import tqdm
from flask import (
    current_app,
    Flask,
    jsonify,
    request,
    send_from_directory,
    url_for,
)

from . import models
from .keypoints import compute_keypoints
from .models import (
    DB,
    Checksum,
    DATA_DIR,
    DEFAULT_IMAGE_DIR
)
from .phash import (
    triangles_from_keypoints,
    hash_triangles,
    TRIANGLE_LOWER,
    TRIANGLE_UPPER,
)


__version__ = '0.0.1'
DEFAULT_DB_URI = 'sqlite:///{}'.format(os.path.join(DATA_DIR, 'tiis.db'))


def phash_triangles(img, triangles, batch_size=None):
    """Get phash from triangles.

    >>> filename = 'fullEndToEndDemo/inputImages/cat_original.png'
    >>> img = cv2.imread(filename)
    >>> keypoints = compute_keypoints(img)
    >>> triangles = triangles_from_keypoints(keypoints)
    >>> res = phash_triangles(img, triangles)
    >>> len(res)
    34770
    >>> sorted(res)[0]
    '0000563b8d730d07'
    """
    n = len(triangles)

    if batch_size is None:
        batch_size = n // cpu_count()

    array = np.asarray(triangles, dtype='d')
    tasks = [(img, array[i:i + batch_size]) for i in range(0, n, batch_size)]
    results = []

    with multiprocessing.Pool(processes=cpu_count()) as p:
        for result in p.starmap(hash_triangles, tasks):
            results += result

    return results


def get_duplicate(
        session, filename=None, csm_m=None, img_dir=DEFAULT_IMAGE_DIR,
        triangle_lower=TRIANGLE_LOWER, triangle_upper=TRIANGLE_UPPER):
    """Get duplicate data.
    >>> import tempfile
    >>> from . import main
    >>> filename1 = 'fullEndToEndDemo/inputImages/cat_original.png'
    >>> filename2 = 'fullEndToEndDemo/inputImages/cat1.png'
    >>> filename3 = 'fullEndToEndDemo/inputImages/mona.jpg'
    >>> image_fd = tempfile.mkdtemp()
    >>> app = main.create_app(db_uri='sqlite://')
    >>> app.app_context().push()
    >>> DB.create_all()
    >>> triangle_lower = 100
    >>> triangle_upper = 300
    >>> # Get duplicate from image filename
    >>> get_duplicate(
    ...     DB.session, filename1,
    ...     triangle_lower=triangle_lower, triangle_upper=triangle_upper)
    []
    >>> # Get duplicate from checksum model
    >>> m = DB.session.query(Checksum).filter_by(id=1).first()
    >>> get_duplicate(
    ...     DB.session, csm_m=m,
    ...     triangle_lower=triangle_lower, triangle_upper=triangle_upper)
    []
    >>> len(m.phashes) > 0
    True
    >>> get_duplicate(
    ...     DB.session, filename2,
    ...     triangle_lower=triangle_lower, triangle_upper=triangle_upper)
    [<Checksum(v=54abb6e, ext=png, trash=False)>]
    >>> get_duplicate(DB.session, csm_m=m, triangle_lower=triangle_lower)
    [<Checksum(v=4aba099, ext=png, trash=False)>]
    >>> get_duplicate(
    ...     DB.session, filename3,
    ...     triangle_lower=triangle_lower, triangle_upper=triangle_upper)
    []
    """
    if csm_m is not None and filename is not None:
        raise ValueError('Only either checksum model or filename is required')
    if csm_m:
        m, created = csm_m, False
    else:
        m, created = models.get_or_create_checksum_model(
            session, filename, img_dir=img_dir)
    res = []
    if created:
        session.add(m)
        session.commit()
    hash_list = None
    if not m.phashes:
        if filename:
            img = cv2.imread(filename)
        else:
            img = cv2.imread(get_image_path(m.value, m.ext, img_dir))
        keypoints = compute_keypoints(img)
        triangles = triangles_from_keypoints(
            keypoints, lower=triangle_lower, upper=triangle_upper)
        hash_list = []
        for triangle in tqdm.tqdm(triangles):
            hashes = hash_triangles(img, [triangle])
            hash_list.extend(hashes)
        hash_list = set(hash_list)  # deduplicate hash_list
        hash_list_ms = session.query(models.Phash) \
            .filter(models.Phash.value.in_(hash_list)).all()
        hash_list_ms_values = [x.value for x in hash_list_ms]
        not_in_db_hash_list = \
            [x for x in hash_list if x not in hash_list_ms_values]
        if not_in_db_hash_list:
            for hash_group in tqdm.tqdm(
                    list(models.grouper(not_in_db_hash_list, 1000))):
                session.add_all(
                    [models.Phash(value=i) for i in hash_group if i])
                session.flush
                session.commit()
        hash_list_ms = session.query(models.Phash) \
            .filter(models.Phash.value.in_(hash_list)).all()
        m.phashes = hash_list_ms
        session.add(m)
        session.commit()
    if session.query(Checksum).count() > 1:
        res = session.query(Checksum).join(models.Phash.checksums) \
            .distinct(Checksum.id) \
            .filter(models.Phash.checksums.any(Checksum.value == m.value)) \
            .filter(Checksum.id != m.id).all()
    return res


def pipeline(r, data, chunk_size):
    npartitions = len(data) // chunk_size
    pipe = r.pipeline()

    for chunk in np.array_split(data, npartitions or 1):
        yield pipe, chunk


def insert(chunks, filename):
    n = 0

    for pipe, keys in chunks:
        for key in keys:
            pipe.sadd(key, filename)

        n += sum(pipe.execute())

    print(f'added {n} fragments for {filename}')


def lookup(chunks, filename):
    count = Counter()

    for pipe, keys in chunks:
        for key in keys:
            pipe.smembers(key)

        for result in pipe.execute():
            count.update(result)

    print(f'matches for {filename}:')

    for key, num in count.most_common():
        print(f'{num:<10d} {key.decode("utf-8")}')


def create_app(script_info=None, db_uri=DEFAULT_DB_URI, image_dir=DEFAULT_IMAGE_DIR):
    """create app."""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri # NOQA
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('TIIS_SECRET_KEY') or os.urandom(24)
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['IMAGE_DIR'] = image_dir
    DB.init_app(app)
    if not database_exists(db_uri):
        create_database(db_uri)
        with app.app_context():
            DB.create_all()

    @app.shell_context_processor
    def shell_context():
        return {'app': app, 'db': DB, 'models': models, 'session': DB.session}

    #  Migrate(app, DB)
    # flask-admin
    app_admin = Admin(
        app, name='Transformation Invariant Image Search', template_mode='bootstrap3',
        index_view=AdminIndexView(
            name='Home',
            template='tiis/index.html',
            url='/'
        )
    )
    #  index_view=views.HomeView(name='Home', template='transformation_invariant_image_search/index.html', url='/'))  # NOQA
    app.add_url_rule('/api/checksum', 'checksum_list', checksum_list, methods=['GET', 'POST'])
    app.add_url_rule('/api/checksum/<int:cid>/duplicate', 'checksum_duplicate', checksum_duplicate)
    app.add_url_rule('/api/image', 'image_list', image_list, methods=['GET', 'POST'])
    app.add_url_rule('/i/<path:filename>', 'image_url', image_url)
    return app


def image_url(filename):
    img_dir = current_app.config.get('IMAGE_DIR')
    return send_from_directory(
        img_dir, os.path.join(filename[:2], filename))


def checksum_duplicate(cid):
    m = DB.session.query(Checksum).filter_by(id=cid).first_or_404()
    res = models.get_duplicate(
        DB.session, csm_m=m, triangle_lower=100, triangle_upper=300
    )
    dict_list = [x.to_dict() for x in res]
    list(map(
        lambda x: x.update({'url': url_for(
            '.image_url', _external=True,
            filename='{}.{}'.format(x['value'], x['ext']))}),
        dict_list
    ))
    return jsonify(dict_list)


def checksum_list():
    if request.method == 'POST':
        csm_value = request.form.get('value', None)
        if not csm_value:
            return jsonify({})
        m = DB.session.query(Checksum).filter_by(value=csm_value).first()
        if m is None:
            kwargs = dict(value=csm_value)
            ext = request.form.get('ext', None)
            if ext is not None:
                kwargs['ext'] = ext
            trash = request.form.get('trash', None)
            if trash is not None:
                kwargs['trash'] = trash
            m = Checksum(**kwargs)
            DB.session.add(m)
            DB.session.commit()
        return jsonify(m.to_dict())
    ms = DB.session.query(Checksum).paginate(1, 10).items
    return jsonify([x.to_dict() for x in ms])


def image_list():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'})
        file_ = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file_.filename == '':
            return jsonify({'error': 'No selected file'})
        with tempfile.NamedTemporaryFile(delete=False) as f:
            file_.save(f.name)
            pil_img = Image.open(f.name)
            sha256 = hashlib.sha256()
            with open(f.name, 'rb') as f:
                for block in iter(lambda: f.read(128*1024), b''):
                    sha256.update(block)
            sha256_csum = sha256.hexdigest()
            image_dir = current_app.config.get('IMAGE_DIR', None)
            if image_dir is None:
                return jsonify({'error': 'Image dir is not specified'})
            ext = pil_img.format.lower()
            dst_file = os.path.join(
                image_dir, sha256_csum[:2], '{}.{}'.format(sha256_csum, ext))
            m = models.get_or_create(DB.session, Checksum, value=sha256_csum)[0]
            m.ext = ext
            m.trash = False
            pathlib.Path(os.path.dirname(dst_file)).mkdir(parents=True, exist_ok=True)
            shutil.move(f.name, dst_file)
            DB.session.add(m)
            DB.session.commit()
            dict_res = m.to_dict()
            dict_res['url'] = url_for(
                '.image_url', _external=True,
            filename='{}.{}'.format(m.value, m.ext)),
            return jsonify(dict_res)
    ms = DB.session.query(Checksum).filter_by(trash=False).paginate(1, 10).items
    return jsonify([x.to_dict() for x in ms])


def get_custom_version(ctx, param, value):
    """Output modified --version flag result.

    Modified from:
    https://github.com/pallets/flask/blob/master/flask/cli.py
    """
    if not value or ctx.resilient_parsing:
        return
    import werkzeug
    message = (
        '%(app_name)s %(app_version)s\n'
        'Python %(python)s\n'
        'Flask %(flask)s\n'
        'Werkzeug %(werkzeug)s'
    )
    click.echo(message % {
        'app_name': 'Transformation Invariant Image Search',
        'app_version': __version__,
        'python': platform.python_version(),
        'flask': flask.__version__,
        'werkzeug': werkzeug.__version__,
    }, color=ctx.color)
    ctx.exit()


class CustomFlaskGroup(FlaskGroup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.params[0].help = 'Show the program version.'
        self.params[0].callback = get_custom_version


@click.group(cls=CustomFlaskGroup, create_app=create_app)
def cli():
    """CLI interface for Transformation Invariant Image Search."""
    pass


@cli.command()
@click.argument('image', nargs=-1)
def insert(image):
    """Insert image's triangle phashes to database."""
    main('insert', image)


@cli.command()
@click.argument('image', nargs=-1)
def lookup(image):
    """Lookup image's triangle phashes in database."""
    main('lookup', image)


def main(command, filenames):
    command = insert if command == 'insert' else lookup

    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    try:
        r.ping
    except redis.ConnectionError:
        print('You need to install redis.')
        return

    for filename in filenames:
        print('loading', filename)
        img = cv2.imread(filename)

        keypoints = compute_keypoints(img)
        triangles = triangles_from_keypoints(keypoints, lower=50, upper=400)
        hashes = phash_triangles(img, triangles)
        chunks = pipeline(r, hashes, chunk_size=1e5)

        print()
        command(chunks, filename)


if __name__ == '__main__':
    cli()
