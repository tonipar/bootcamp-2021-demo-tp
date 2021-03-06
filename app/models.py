from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login




@login.user_loader
def load_user(id):
    """
    Loads given users Id for Flask-Login to keep track logged users
    """
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    """
    Model for User table
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    rounds = db.relationship('Round', backref='user', lazy='dynamic')
  
    def set_password(self, password):
        """
        set_password creates hashed password for the user
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        check_password check user password when user try log in
        """
        return check_password_hash(self.password_hash, password)

    def get_rounds(self):
        """
        get_rounds will retrieve all rounds user has been played from database and return them in descending order
        """
        playedrounds = Round.query.filter_by(rounduser_id=self.id)
        return playedrounds.order_by(Round.id.desc())

    def __repr__(self):
        """
        ___repr__ method tells python how to print objects of user
        """
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
    
    def __repr__(self):
        """
        ___repr__ method tells python how to print objects of user
        """
        return '<Course {}>'.format(self.coursename)

    def get_holes(self):
        """
        get_holes will retrieve all holes associated with course object and returns them
        """
        holes = Hole.query.filter_by(holecourse_id=self.id)
        return holes

    def get_coursepar(self):
        """
        get_coursepar will calculate sum of every par value from holes associated with course and return it
        """
        holes = Hole.query.filter_by(holecourse_id=self.id)
        par = 0
        for hole in holes:
            par = par + hole.holepar
        return par

    def get_rounds(self, userid):
        """
        get_rounds will retrieve every round user has created for this course object and return them
        """
        rounds = Round.query.filter_by(roundcourse_id=self.id, rounduser_id=userid)
        return rounds.order_by(Round.id.desc())

    def get_holemean(self, userid, holenum):
        """
        get_holemean will calculate a mean for scores in particular hole of course, from all rounds user has created for this course object and return it
        """
        rounds = Round.query.filter_by(roundcourse_id=self.id, rounduser_id=userid)
        holetotal = 0
        for round in rounds:
            holetotal = holetotal + round.get_holescore(holenum)
        holemean = holetotal / rounds.count()
        return holemean

    def get_roundmean(self, userid):
        """
        get_roundmean will calculate a mean for final result of rounds user has created for this course object 
        """
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

    def __repr__(self):
        """
        ___repr__ method tells python how to print objects of Hole
        """
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
        """
        ___repr__ method tells python how to print objects of Round
        """
        return '<Round {}>'.format(self.id)

    def get_coursename(self):
        """
        get_coursename retrieves name of the Course this Round has been played on.
        """
        course = Course.query.filter_by(id=self.roundcourse_id).first()
        return course.coursename
    
    def get_date(self):
        """
        get_date retrieves date when this Round was played. Return converted datetime object as string.
        """
        date = self.rounddate.strftime('%d/%m/%Y')
        return date
    
    def get_scores(self):
        """
        get_scores retrieves scores of all holes played this Round and returns them
        """
        scores = Roundscore.query.filter_by(round_id=self.id)
        return scores
    
    def get_totalscore(self):
        """
        get_totalscore calculates the sum of all scores from Holes played this Round and returns it
        """
        scores = Roundscore.query.filter_by(round_id=self.id)
        totalscore = 0
        for score in scores:
            totalscore = totalscore + score.score
        return totalscore
    
    def get_totalscorepar(self):
        """
        get_totalscorepar calculates the sum of all scores from Holes played this Round and then substracts it from sum of all par values of Holes played this Round
        """
        scores = Roundscore.query.filter_by(round_id=self.id)
        totalscore = 0
        for score in scores:
            totalscore = totalscore + score.score
        course = Course.query.filter_by(id=self.roundcourse_id).first_or_404()
        par = course.get_coursepar()
        return totalscore - par

    def get_holescore(self, holenum):
        """
        get holescore retrieves score of one hole and returns it
        """
        score = Roundscore.query.filter_by(round_id=self.id, hole=holenum).first_or_404()
        return score.score

    def get_weatherurl(self):
        """
        get_weatherurl returns a url for weather icon 
        """
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
    
    def __repr__(self):
        """
        ___repr__ method tells python how to print objects of round_hole
        """
        return '<Roundscore {}>'.format(self.id)
    
    
    def get_par(self, courseid):
        """
        get_par retrieves par value of corresponding Hole
        """
        hole = Hole.query.filter_by(holecourse_id=courseid, holenum=self.hole).first_or_404()
        return hole.holepar
