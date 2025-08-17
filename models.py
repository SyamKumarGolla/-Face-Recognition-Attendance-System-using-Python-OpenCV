from flask_sqlalchemy import SQLAlchemy
import datetime
db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(15), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(20))  # Admin, Teacher, Student, Employee

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    date = db.Column(db.DateTime, default=datetime.datetime.now)

class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    type = db.Column(db.String(50))  # Room, Lab, Equipment, Staff
    status = db.Column(db.String(20), default='available')  # available, occupied