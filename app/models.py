from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login

@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def __repr__(self):
        return '<User {}>'.format(self.username)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    coursename = db.Column(db.String(64), index=True, unique=True)
    courseholes = db.Column(db.Integer)
    courselocation = db.Column(db.String(64))
    #rounds = db.relationship('Round', backref='course', lazy='dynamic')
    holes = db.relationship('Hole', backref='course', lazy='dynamic')
    
    def __repr__(self):
        return '<Course {}>'.format(self.coursename)

class Hole(db.Model):
    __table_args__ = (
        db.UniqueConstraint('holenum', 'holecourse_id'),
    )
    id = db.Column(db.Integer, primary_key=True)
    holenum = db.Column(db.Integer, index=True)
    holepar = db.Column(db.Integer)
    holelength = db.Column(db.Integer)
    holecourse_id = db.Column(db.Integer, db.ForeignKey('course.id'))

    def __repr__(self):
        return '<Hole {}>'.format(self.holenum)