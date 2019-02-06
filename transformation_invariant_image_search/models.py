from flask import Flask
from flask_sqlalchemy import SQLAlchemy

DB = SQLAlchemy()

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
