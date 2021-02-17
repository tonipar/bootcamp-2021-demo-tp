from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login



# Contains models for database tables. SQLAlchemy will convert these to proper tables for database.

# Loads given users Id for Flask-Login to keep track logged users.
@login.user_loader
def load_user(id):
    """
    Loads given users Id for Flask-Login to keep track logged users
    
    """
    return User.query.get(int(id))

# Model for User table. Usermixin will add is_authenticated, is_active, is_anonymous, get_id() properties 
# for the user model.
class User(UserMixin, db.Model):
    """
    Model for User table

    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    rounds = db.relationship('Round', backref='user', lazy='dynamic')

    """
    set_password creates hashed password for the user

    """
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    """
    check_password check user password when user try log in

    """
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    """
    get_rounds will retrieve all rounds user has been played from database and return them in descending order

    """
    def get_rounds(self):
        playedrounds = Round.query.filter_by(rounduser_id=self.id)
        return playedrounds.order_by(Round.rounddate.desc())

    """
    ___repr__ method tells python how to print objects of user

    """
    def __repr__(self):
        return '<User {}>'.format(self.username)

class Course(db.Model):
    """
    Model for Course Table

    """
    id = db.Column(db.Integer, primary_key=True)
    coursename = db.Column(db.String(64), index=True, unique=True)
    courseholes = db.Column(db.Integer)
    courselocation = db.Column(db.String(64))
    rounds = db.relationship('Round', backref='course', lazy='dynamic')
    holes = db.relationship('Hole', backref='course', lazy='dynamic')
    
    """
    ___repr__ method tells python how to print objects of user

    """
    def __repr__(self):
        return '<Course {}>'.format(self.coursename)

    """
    get_holes will retrieve all holes associated with course object and returns them

    """
    def get_holes(self):
        holes = Hole.query.filter_by(holecourse_id=self.id)
        return holes

    """
    get_coursepar will calculate sum of every par value from holes associated with course and return it

    """
    def get_coursepar(self):
        holes = Hole.query.filter_by(holecourse_id=self.id)
        par = 0
        for hole in holes:
            par = par + hole.holepar
        return par

    """
    get_rounds will retrieve every round user has created for this course object and return them

    """
    def get_rounds(self, userid):
        rounds = Round.query.filter_by(roundcourse_id=self.id, rounduser_id=userid)
        return rounds


    """
    get_holemean will calculate a mean for scores in particular hole of course, from all rounds user has created for this course object and return it

    """
    def get_holemean(self, userid, holenum):
        rounds = Round.query.filter_by(roundcourse_id=self.id, rounduser_id=userid)
        holetotal = 0
        for round in rounds:
            holetotal = holetotal + round.get_holescore(holenum)
        holemean = holetotal / rounds.count()
        return holemean

    """
    get_roundmean will calculate a mean for final result of rounds user has created for this course object 

    """
    def get_roundmean(self, userid):
        rounds = Round.query.filter_by(roundcourse_id=self.id, rounduser_id=userid)
        roundtotal = 0
        for round in rounds:
            roundtotal = roundtotal + round.get_totalscore()
        roundmean = roundtotal / rounds.count()
        return roundmean

class Hole(db.Model):
    """
    Model for Hole table. Each Course has multiple holes.

    """
    __tablename__ = 'course_hole'
    __table_args__ = (
        db.UniqueConstraint('holenum', 'holecourse_id'),
    )
    id = db.Column(db.Integer, primary_key=True)
    holenum = db.Column(db.Integer, index=True)
    holepar = db.Column(db.Integer)
    holelength = db.Column(db.Integer)
    holecourse_id = db.Column(db.Integer, db.ForeignKey('course.id'))

    """
    ___repr__ method tells python how to print objects of Hole

    """
    def __repr__(self):
        return '<Hole {}>'.format(self.holenum)

class Round(db.Model):
    """
    Model for Round Table. User can create multiple Rounds for one Course.

    """
    id = db.Column(db.Integer, primary_key=True)
    rounddate = db.Column(db.DateTime, default=datetime.utcnow)
    roundweather = db.Column(db.String(16))
    rounduser_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    roundcourse_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    roundscores = db.relationship('Roundscore', backref='round', lazy='dynamic')

    def __repr__(self):
        return '<Round {}>'.format(self.id)

    """
    get_coursename retrieves name of the Course this Round has been played on.

    """
    def get_coursename(self):
        course = Course.query.filter_by(id=self.roundcourse_id).first()
        return course.coursename
    
    """
    get_date retrieves date when this Round was played. Return converted datetime object as string.

    """
    def get_date(self):
        date = self.rounddate.strftime('%d/%m/%Y')
        return date
    
    """
    get_scores retrieves scores of all holes played this Round and returns them

    """
    def get_scores(self):
        scores = Roundscore.query.filter_by(round_id=self.id)
        return scores
    
    """
    get_totalscore calculates the sum of all scores from Holes played this Round and returns it

    """
    def get_totalscore(self):
        scores = Roundscore.query.filter_by(round_id=self.id)
        totalscore = 0
        for score in scores:
            totalscore = totalscore + score.score
        return totalscore
    
    """
    get_totalscorepar calculates the sum of all scores from Holes played this Round and then substracts it from sum of all par values of Holes played this Round

    """
    def get_totalscorepar(self):
        scores = Roundscore.query.filter_by(round_id=self.id)
        totalscore = 0
        for score in scores:
            totalscore = totalscore + score.score
        course = Course.query.filter_by(id=self.roundcourse_id).first_or_404()
        par = course.get_coursepar()
        return totalscore - par

    """
    get holescore retrieves score of one hole and returns it

    """
    def get_holescore(self, holenum):
        score = Roundscore.query.filter_by(round_id=self.id, hole=holenum).first_or_404()
        return score.score

    """
    get_weatherurl returns a url for weather icon 

    """
    def get_weatherurl(self):
        url = "http://openweathermap.org/img/wn/" + self.roundweather + ".png"
        return url


class Roundscore(db.Model):
    """
    Model for round_hole table. Round has multiple round_hole objects. a Round is played on a Course and every Hole a Course has, there must be corresponding round_hole

    """
    __tablename__ = 'round_hole'
    __table_args__ = (
        db.UniqueConstraint('hole', 'round_id'),
    )
    id = db.Column(db.Integer, primary_key=True)
    hole = db.Column(db.Integer)
    score = db.Column(db.Integer)
    ob = db.Column(db.Boolean)
    round_id = db.Column(db.Integer, db.ForeignKey('round.id'))
    
    """
    ___repr__ method tells python how to print objects of round_hole
    """
    def __repr__(self):
        return '<Roundscore {}>'.format(self.id)
    
    """
    get_par retrieves par value of corresponding Hole

    """
    def get_par(self, courseid):
        hole = Hole.query.filter_by(holecourse_id=courseid, holenum=self.hole).first_or_404()
        return hole.holepar
