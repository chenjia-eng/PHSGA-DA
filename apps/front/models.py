from exts import db
from datetime import datetime


class SampleModel(db.Model):
    __tablename__ = 'sample'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    sample_name = db.Column(db.String(255), nullable=False)
    sample_path = db.Column(db.String(255), nullable=False)
    reverse_state = db.Column(db.Integer, default=0, nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.now)
    state = db.Column(db.Integer, default=0, nullable=False)


class CacheModel(db.Model):
    __tablename__ = 'cache'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    hash = db.Column(db.String(255), nullable=False)
    sample_name = db.Column(db.String(255), nullable=False)