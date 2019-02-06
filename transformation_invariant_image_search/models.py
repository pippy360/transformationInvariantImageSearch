import hashlib
import os
import pathlib
import shutil

from appdirs import user_data_dir
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from PIL import Image

DB = SQLAlchemy()
DATA_DIR = user_data_dir('transformation_invariant_image_search', 'Tom Murphy')
pathlib.Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
DEFAULT_IMAGE_DIR = os.path.join(DATA_DIR, 'image')

triangle_points = DB.Table(
    'triangle_points',
    DB.Column('triangle_phash_id', DB.Integer, DB.ForeignKey('triangle_phash.id'), primary_key=True),
    DB.Column('point_id', DB.Integer, DB.ForeignKey('point.id'), primary_key=True))
triangle_phashes = DB.Table(
    'triangle_phashes',
    DB.Column('triangle_phash_id', DB.Integer, DB.ForeignKey('triangle_phash.id'), primary_key=True),
    DB.Column('phash_id', DB.Integer, DB.ForeignKey('phash.id'), primary_key=True))


class Base(DB.Model):
    __abstract__ = True
    id = DB.Column(DB.Integer, primary_key=True)


class Checksum(Base):
    value = DB.Column(DB.String(), unique=True, nullable=False)
    trash = DB.Column(DB.Boolean(), default=False)
    ext = DB.Column(DB.String(), nullable=False)

    def __repr__(self):
        templ = '<Checksum(v={1}, ext={0.ext}, trash={0.trash})>'
        return templ.format(self, self.value[:7])

    def to_dict(self):
        keys = ['value', 'trash', 'ext', 'id']
        return {k: getattr(self, k) for k in keys}


class Point(Base):
    x = DB.Column(DB.Integer(), nullable=False)
    y = DB.Column(DB.Integer(), nullable=False)

    def __repr__(self):
        templ = '<Point(x,y={0.x},{0.y}})>'
        return templ.format(self)


class Phash(Base):
    value = DB.Column(DB.String(), unique=True, nullable=False)

    def __repr__(self):
        templ = '<Phash(v={0.value}})>'
        return templ.format(self)


class TrianglePhash(Base):
    checksum_id = DB.Column(DB.Integer, DB.ForeignKey('checksum.id'), nullable=False)
    checksum = DB.relationship('Checksum', backref='triangle_phashes', lazy=True)
    points = DB.relationship('Point', secondary=triangle_points, lazy='subquery',
        backref=DB.backref('triangle_phashes', lazy=True))
    phashes =  DB.relationship('Phash', secondary=triangle_phashes, lazy='subquery',
        backref=DB.backref('triangle_phashes', lazy=True))

    def __repr__(self):
        templ = '<TrianglePhash(checksum={0.checksum.value[:7]}, points=[{1}], phashes=[{2}])>'
        return templ.format(
            self,
            ','.join(['({0.x, 0.y})'.format(x) for x in Point]),
            ','.join(['{0.value}'.format(x) for x in Point]),
        )


def get_or_create(session, model, **kwargs):
    """Creates an object or returns the object if exists."""
    instance = session.query(model).filter_by(**kwargs).first()
    created = False
    if not instance:
        instance = model(**kwargs)
        session.add(instance)
        created = True
    return instance, created


def get_image_path(checksum_value, ext, img_dir=DEFAULT_IMAGE_DIR):
    """Get image path.
    >>> import tempfile
    >>> image_fd = tempfile.mkdtemp()
    >>> get_image_path(
    ...     '54abb6e1eb59cccf61ae356aff7e491894c5ca606dfda4240d86743424c65faf',
    ...     'png', image_fd)
    '.../54/54abb6e1eb59cccf61ae356aff7e491894c5ca606dfda4240d86743424c65faf.png'
    """
    return os.path.join(img_dir, checksum_value[:2], '{}.{}'.format(checksum_value, ext))


def get_or_create_checksum_model(session, filename, img_dir=DEFAULT_IMAGE_DIR):
    """Get or create checksum model.
    >>> import tempfile
    >>> from . import main
    >>> filename = 'fullEndToEndDemo/inputImages/cat_original.png'
    >>> image_fd = tempfile.mkdtemp()
    >>> app = main.create_app(db_uri='sqlite://')
    >>> app.app_context().push()
    >>> DB.create_all()
    >>> get_or_create_checksum_model(DB.session, filename, image_fd)
    (<Checksum(v=54abb6e, ext=png, trash=False)>, ...)
    >>> res = get_or_create_checksum_model(DB.session, filename, image_fd)
    >>> res
    (<Checksum(v=54abb6e, ext=png, trash=False)>, False)
    >>> m = res[0]
    >>> os.path.isfile(get_image_path(m.value, m.ext, image_fd))
    True
    """
    pil_img = Image.open(filename)
    sha256 = hashlib.sha256()
    with open(filename, 'rb') as f:
        for block in iter(lambda: f.read(128*1024), b''):
            sha256.update(block)
    sha256_csum = sha256.hexdigest()
    m, created = get_or_create(session, Checksum, value=sha256_csum)
    m.ext = pil_img.format.lower()
    m.trash = False
    dst_file = get_image_path(m.value, m.ext, img_dir)
    pathlib.Path(os.path.dirname(dst_file)).mkdir(parents=True, exist_ok=True)
    shutil.copy(filename, dst_file)
    return m, created


def get_duplicate(session, filename=None, csm_m=None, img_dir=DEFAULT_IMAGE_DIR):
    """Get duplicate data.
    >>> import tempfile
    >>> from . import main
    >>> filename1 = 'fullEndToEndDemo/inputImages/cat_original.png'
    >>> filename2 = 'fullEndToEndDemo/inputImages/cat1.png'
    >>> image_fd = tempfile.mkdtemp()
    >>> app = main.create_app(db_uri='sqlite://')
    >>> app.app_context().push()
    >>> DB.create_all()
    >>> get_duplicate(DB.session, filename1)
    []
    >>> m = DB.session.query(Checksum).filter_by(id=1).first()
    >>> len(m.triangle_phashes)
    0
    """
    if filename is None and csm_m is not None:
        # TODO
        raise NotImplementedError
    m = get_or_create_checksum_model(session, filename, img_dir=img_dir)[0]
    if m.triangle_phashes == 0:
        img = cv2.imread(filename)
        keypoints = compute_keypoints(img)
        triangles = triangles_from_keypoints(keypoints, lower=50, upper=400)
        hashes = phash_triangles(img, triangles)
    return []
