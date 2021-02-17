from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login



# Contains models for database tables. SQLAlchemy will convert these to proper tables for database.

# Loads given users Id for Flask-Login to keep track logged users.
@login.user_loader
def load_user(id):
    return User.query.get(int(id))

# Model for User table. Usermixin will add is_authenticated, is_active, is_anonymous, get_id() properties 
# for the user model.
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    rounds = db.relationship('Round', backref='user', lazy='dynamic')

    # creates hashed password
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # check if password is correct
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_rounds(self):
        playedrounds = Round.query.filter_by(rounduser_id=self.id)
        return playedrounds.order_by(Round.rounddate.desc())

    def __repr__(self):
        return '<User {}>'.format(self.username)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    coursename = db.Column(db.String(64), index=True, unique=True)
    courseholes = db.Column(db.Integer)
    courselocation = db.Column(db.String(64))
    rounds = db.relationship('Round', backref='course', lazy='dynamic')
    holes = db.relationship('Hole', backref='course', lazy='dynamic')
    
    def __repr__(self):
        return '<Course {}>'.format(self.coursename)

    def get_holes(self):
        holes = Hole.query.filter_by(holecourse_id=self.id)
        return holes

    def get_coursepar(self):
        holes = Hole.query.filter_by(holecourse_id=self.id)
        par = 0
        for hole in holes:
            par = par + hole.holepar
        return par

    def get_rounds(self, userid):
        rounds = Round.query.filter_by(roundcourse_id=self.id, rounduser_id=userid)
        return rounds

    def get_holemean(self, userid, holenum):
        rounds = Round.query.filter_by(roundcourse_id=self.id, rounduser_id=userid)
        holetotal = 0
        for round in rounds:
            holetotal = holetotal + round.get_holescore(holenum)
        holemean = holetotal / rounds.count()
        return holemean

    def get_roundmean(self, userid):
        rounds = Round.query.filter_by(roundcourse_id=self.id, rounduser_id=userid)
        roundtotal = 0
        for round in rounds:
            roundtotal = roundtotal + round.get_totalscore()
        roundmean = roundtotal / rounds.count()
        return roundmean

class Hole(db.Model):
    __tablename__ = 'course_hole'
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

class Round(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rounddate = db.Column(db.DateTime, default=datetime.utcnow)
    roundweather = db.Column(db.String(16))
    rounduser_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    roundcourse_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    roundscores = db.relationship('Roundscore', backref='round', lazy='dynamic')

    def __repr__(self):
        return '<Round {}>'.format(self.id)

    def get_coursename(self):
        course = Course.query.filter_by(id=self.roundcourse_id).first()
        return course.coursename
    
    def get_date(self):
        date = self.rounddate.strftime('%d/%m/%Y')
        return date
    
    def get_scores(self):
        scores = Roundscore.query.filter_by(round_id=self.id)
        return scores
    
    def get_totalscore(self):
        scores = Roundscore.query.filter_by(round_id=self.id)
        totalscore = 0
        for score in scores:
            totalscore = totalscore + score.score
        return totalscore
    
    def get_totalscorepar(self):
        scores = Roundscore.query.filter_by(round_id=self.id)
        totalscore = 0
        for score in scores:
            totalscore = totalscore + score.score
        course = Course.query.filter_by(id=self.roundcourse_id).first_or_404()
        par = course.get_coursepar()
        return totalscore - par

    def get_holescore(self, holenum):
        score = Roundscore.query.filter_by(round_id=self.id, hole=holenum).first_or_404()
        return score.score

    def get_weatherurl(self):
        url = "http://openweathermap.org/img/wn/" + self.roundweather + ".png"
        return url


class Roundscore(db.Model):
    __tablename__ = 'round_hole'
    __table_args__ = (
        db.UniqueConstraint('hole', 'round_id'),
    )
    id = db.Column(db.Integer, primary_key=True)
    hole = db.Column(db.Integer)
    score = db.Column(db.Integer)
    ob = db.Column(db.Boolean)
    round_id = db.Column(db.Integer, db.ForeignKey('round.id'))
    
    def __repr__(self):
        return '<Roundscore {}>'.format(self.id)
    
    def get_par(self, courseid):
        hole = Hole.query.filter_by(holecourse_id=courseid, holenum=self.hole).first_or_404()
        return hole.holepar
