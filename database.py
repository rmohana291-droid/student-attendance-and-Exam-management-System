from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    roll_no = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    register_no = db.Column(db.String(20), unique=True, nullable=False)
    attendance = db.relationship('Attendance', backref='student', lazy=True)
    marks = db.relationship('Mark', backref='student', lazy=True)

class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    attendance = db.relationship('Attendance', backref='subject', lazy=True)
    marks = db.relationship('Mark', backref='subject', lazy=True)

class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(10), nullable=False)  # Present/Absent
    total_classes = db.Column(db.Integer, default=1)

class Mark(db.Model):
    __tablename__ = 'marks'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    marks_obtained = db.Column(db.Float, nullable=False)
    total_marks = db.Column(db.Float, nullable=False)
    exam_type = db.Column(db.String(50), nullable=False)  # Internal/External