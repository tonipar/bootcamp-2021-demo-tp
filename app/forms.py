from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, IntegerField, SelectField
from wtforms.validators import ValidationError, DataRequired, Optional, Email, EqualTo, Length
from app.models import User, Course, Hole

# Contains forms that app uses

# Form for login page
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

# Form for registering new user
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Submit')

    def __init__(self, original_username, original_email, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')
    
    def validate_email(self, email):
        if email.data != self.original_email:
            email = User.query.filter_by(email=self.email.data).first()
            if email is not None:
                raise ValidationError('Email is already in use.')

class CreateCourseForm(FlaskForm):
    coursename = StringField('Name', validators=[DataRequired()])
    courseholes = IntegerField('Number of holes', validators=[DataRequired()])
    courselocation = StringField('Location (city)', validators=[DataRequired()])
    submit = SubmitField('Submit')
    
    def validate_coursename(self, coursename):
        user = Course.query.filter_by(coursename=coursename.data).first()
        if user is not None:
            raise ValidationError('Course already registered.')


class AddCourseHoleForm(FlaskForm):
    holenum = IntegerField('Holenum', validators=[DataRequired()])
    holepar = IntegerField('Holepar', validators=[DataRequired()])
    holelength = IntegerField('Holelegth')
    submit = SubmitField('Submit')

class EditHoleForm(FlaskForm):
    holepar = IntegerField('Par', validators=[DataRequired()])
    holelength = IntegerField('Lenght', validators=[Optional()])
    submit = SubmitField('Submit')

class CreateRoundForm(FlaskForm):
   courses = Course.query.all()
   choices = []
   for c in courses:
       choices.append(c.coursename)

   course = SelectField(choices=choices)
   submit = SubmitField('Submit')

class ScoreForm(FlaskForm):
    score = IntegerField('Score', validators=[DataRequired()])
    ob = BooleanField('Ob')
    submit = SubmitField('Next')