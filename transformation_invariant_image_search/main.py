"""
Usage: main.py lookup <image>...
       main.py insert <image>...
"""
from collections import Counter
from os import cpu_count
import multiprocessing
import sys
import os

from flask import Flask
from flask.cli import FlaskGroup
from flask_admin import Admin, AdminIndexView
import click
import cv2
import numpy as np
import redis

from .keypoints import compute_keypoints
from .phash import triangles_from_keypoints, hash_triangles
from .models import DB


__version__ = '0.0.1'
DEFAULT_DB_URI = None


def phash_triangles(img, triangles, batch_size=None):
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


def create_app(script_info=None, db_uri=DEFAULT_DB_URI):
    """create app."""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri # NOQA
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('TIIS_SECRET_KEY') or os.urandom(24)
    app.config['WTF_CSRF_ENABLED'] = False
    # app and db
    #  DB.init_app(app)
    #  app.app_context().push()
    #  db.create_all()

    @app.shell_context_processor
    def shell_context():
        return {'app': app, 'db': DB, 'models': models, 'session': DB.session}

    #  Migrate(app, DB)
    # flask-admin
    app_admin = Admin(
        app, name='Transformation Image Search', template_mode='bootstrap3',
        index_view=AdminIndexView(
            #  name='Home',
            #  template='admin/myhome.html',
            url='/'
        )
    )
    #  index_view=views.HomeView(name='Home', template='transformation_invariant_image_search/index.html', url='/'))  # NOQA
    return app


def get_custom_version(ctx, param, value):
    #  if not value or ctx.resilient_parsing:
        #  return
    message = '{app_name} {app_version}\nFlask {version}\nPython {python_version}'
    click.echo(message.format(**{
        'app_name': 'Transformation Invariant Image Search',
        'app_version': __version__,
        'version': flask_version,
        'python_version': sys.version,
    }), color=ctx.color)
    ctx.exit()


class CustomFlaskGroup(FlaskGroup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.params[0].help = 'Show the program version'
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
