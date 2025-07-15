from . import db
from datetime import datetime

class Project(db.Model):
    __tablename__ = 'project'
    id = db.Column(db.Integer, primary_key=True)
    case_number = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(32), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    files = db.relationship(
        'File', back_populates='project',
        cascade='all, delete-orphan'
    )

class File(db.Model):
    __tablename__ = 'file'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    filename = db.Column(db.String(256), nullable=False)
    status = db.Column(db.String(32), default='pending')

    project = db.relationship('Project', back_populates='files')
    detections = db.relationship(
        'Detection', back_populates='file',
        cascade='all, delete-orphan'
    )

class Detection(db.Model):
    __tablename__ = 'detection'

    id         = db.Column(db.Integer, primary_key=True)
    file_id    = db.Column(db.Integer, db.ForeignKey('file.id'), nullable=False)
    frame      = db.Column(db.Integer, nullable=False)
    label      = db.Column(db.String(64), nullable=False)
    probability= db.Column(db.Float,   nullable=False)
    details    = db.Column(db.Text,    nullable=True)  # renamed from metadata

    file = db.relationship('File', back_populates='detections')
