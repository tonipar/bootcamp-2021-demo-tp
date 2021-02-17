from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, CreateCourseForm, AddCourseHoleForm, EditHoleForm, CreateRoundForm, ScoreForm
from app.models import User, Course, Hole, Round, Roundscore
from datetime import datetime, date
from pyowm.owm import OWM

# Contains different URLs that app has

# Main page
@app.route('/')
@app.route('/index')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    rounds = current_user.get_rounds().paginate(page,3,False)
    next_url = url_for('index', page=rounds.next_num) \
        if rounds.has_next else None
    prev_url = url_for('index', page=rounds.prev_num) \
        if rounds.has_prev else None
    return render_template('index.html', title='Home', rounds=rounds.items, next_url=next_url,
                           prev_url=prev_url)

# Login Page. If user is already logged in redirect user to the main page.
# If password or username is wrong user will get error message.
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

# Log out user from app
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

# User registration page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        flash('curretn user authenticated')
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    flash('test message')
    return render_template('register.html', title='Register', form=form)

# User profile page
@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user.html', user=user)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username, current_user.email)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    return render_template('edit_profile.html', title='Edit Profile', form=form)
    
@app.route('/createcourse', methods=['GET', 'POST'])
@login_required
def createcourse():

    form = CreateCourseForm()
    if form.validate_on_submit():
        course = Course(coursename=form.coursename.data, courseholes=form.courseholes.data, courselocation=form.courselocation.data)
        db.session.add(course)
        db.session.commit()

        for holenum in range(form.courseholes.data):
            holenum = holenum+1
            hole = Hole(holenum=holenum, holepar=3, holecourse_id=course.id)
            db.session.add(hole)
            db.session.commit()
        
        flash('New course has been created!')

        return redirect(url_for('course', coursename=course.coursename))
    return render_template('createcourse.html', title='Register', form=form)

@app.route('/courses')
@login_required
def courses():
    page = request.args.get('page', 1, type=int)
    courses = Course.query.order_by(Course.coursename.desc()).paginate(page,5,False)
    next_url = url_for('courses', page=courses.next_num) \
        if courses.has_next else None
    prev_url = url_for('courses', page=courses.prev_num) \
        if courses.has_prev else None
    return render_template('courses.html', courses = courses.items, next_url=next_url,
                           prev_url=prev_url)

@app.route('/course/<coursename>')
@login_required
def course(coursename):
    course = Course.query.filter_by(coursename=coursename).first_or_404()
    holes = Hole.query.filter_by(holecourse_id=course.id)
    return render_template('course.html', course=course, holes=holes)

@app.route('/edithole/<coursename>/<holenum>', methods=['GET', 'POST'])
@login_required
def edithole(coursename, holenum):
    course = Course.query.filter_by(coursename=coursename).first_or_404()
    hole = Hole.query.filter_by(holenum = holenum, holecourse_id = course.id).first_or_404()
    form = EditHoleForm()
    if form.validate_on_submit():
        hole.holepar = form.holepar.data
        hole.holelength = form.holelength.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('course', coursename=coursename ))
    elif request.method == 'GET':
        form.holepar.data = hole.holepar
        form.holelength.data = hole.holelength
    return render_template('edithole.html', title='Edit Hole', form=form)

@app.route('/createround', methods=['GET', 'POST'])
@login_required
def createround():

    courses = Course.query.all()
    form = CreateRoundForm()
    if form.validate_on_submit():
        course = Course.query.filter_by(coursename=form.course.data).first_or_404()
        today = datetime.today()
        
        owm = OWM('309d1acf125bea57bb26866e210087ca')
        mgr = owm.weather_manager()
        observation = mgr.weather_at_place("Kuopio")
        weather = observation.weather
        icon = weather.weather_icon_name
        
        round = Round(rounddate=today, roundweather=icon, rounduser_id= current_user.id ,roundcourse_id= course.id)
        db.session.add(round)
        db.session.commit()

        holes = course.get_holes()
        holenum = 1
        for hole in holes:
            roundscore = Roundscore(hole=holenum, score=hole.holepar, ob=False, round_id=round.id)
            db.session.add(roundscore)
            db.session.commit()
            holenum = holenum+1
        
        flash('New round has been started!')
        holenum = 1
        return redirect(url_for('roundscores', roundid = round.id, holenum = holenum))
    return render_template('createround.html', title='Start new round', courses = courses, form=form)

@app.route('/roundscores/<roundid>/<holenum>', methods=['GET', 'POST'])
@login_required
def roundscores(roundid, holenum):
    round = Round.query.filter_by(id=roundid).first_or_404()
    course = Course.query.filter_by(id=round.roundcourse_id).first_or_404()
    if not isinstance(holenum, int):
        holenum = int(holenum)

    if holenum > course.courseholes:
        return redirect(url_for('roundview', roundid=round.id))

    score = Roundscore.query.filter_by(hole=holenum, round_id=roundid).first()
    form = ScoreForm()
    if score is None:
        if form.validate_on_submit():
            roundscore = Roundscore(hole=holenum, score=form.score.data, ob=form.ob.data, round_id = roundid)
            db.session.add(roundscore)
            db.session.commit()
            flash('Score for hole' + str(holenum) + ' has been updated!')
            holenum = holenum+1
            return redirect(url_for('roundscores', roundid=roundid, holenum=holenum))
        return render_template('roundscores.html', title='Round', coursename= course.coursename, holenum=holenum, roundid=roundid, form=form)
    else:
        if form.validate_on_submit():
            score.score = form.score.data
            score.ob = form.ob.data
            db.session.commit()
            flash('Score for hole' + str(holenum) + ' has been updated!')
            holenum = holenum+1
            return redirect(url_for('roundscores', roundid=roundid, holenum=holenum))
        elif request.method == 'GET':
            form.score.data = score.score
            form.ob.data = score.ob
        return render_template('roundscores.html', title='Round', coursename= course.coursename, holenum=holenum, roundid=roundid, form=form)


@app.route('/roundview/<roundid>')
@login_required
def roundview(roundid):
    round = Round.query.filter_by(id=roundid).first_or_404()
    scores = round.get_scores()
    course = Course.query.filter_by(id=round.roundcourse_id).first_or_404()
    return render_template('roundview.html', title='Roundview', scores=scores, course=course, round = round)
    
@app.route('/analyzecourse/<coursename>')
@login_required
def analyzecourse(coursename):
    course = Course.query.filter_by(coursename=coursename).first_or_404()
    page = request.args.get('page', 1, type=int)
    rounds = course.get_rounds(current_user.id).paginate(page,3,False)
    next_url = url_for('analyzecourse', coursename = coursename, page=rounds.next_num) \
        if rounds.has_next else None
    prev_url = url_for('analyzecourse', coursename = coursename, page=rounds.prev_num) \
        if rounds.has_prev else None
    return render_template('analyzecourse.html', title='Analyze Course', course=course, rounds=rounds.items, next_url=next_url,
                           prev_url=prev_url)