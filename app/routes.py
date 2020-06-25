import os
import base64
import secrets
from flask import render_template, request, session, redirect, url_for, jsonify
from app import app, db, bcrypt
from app.models import User, Event
from flask_login import login_user, current_user, logout_user

@app.route('/', methods=["GET", "POST"])
@app.route('/index', methods=["GET", "POST"])
def index():
    if current_user.is_authenticated:
        userEvents = User.query.order_by(Event.date).get(current_user.get_id()).events

        image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
        return render_template('index.html', events=userEvents, user=current_user, image=image_file)
    else:
        return redirect(url_for('login'))


#validation of login credentials
@app.route('/validate', methods=['POST'])
def validate():

    data = request.get_json()
    senha = data['pass'] #senha
    user = User.query.filter_by(email=data['mail']).first()

    if (user != None and bcrypt.check_password_hash(user.password, senha)):
        login_user(user)
        return jsonify({"redirect": "/index"})
    else:
        return jsonify({"err": 'user not found'})


@app.route('/register')
def register():
    return (render_template('register.html'))


@app.route('/account_reg', methods=['POST'])
def accountReg():

    data = request.get_json()

    user = User(
        username=data['username'],
        email=data['email'],
        password=bcrypt.generate_password_hash(password=data['pass']).decode('utf-8')
        )
    
    if(user != None):
        db.session.add(user)
        db.session.commit()
        return jsonify({"done": 'user created'})
    else:
        return jsonify({"err": 'invalid user'})


@app.route('/new_event')
def newEvent():
    if current_user.is_authenticated:
        image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
        return (render_template('new_event.html', user=current_user, image=image_file))
    else:
        return redirect(url_for('login'))

@app.route('/create_event', methods=['POST'])
def createEvent():
    if current_user.is_authenticated:
        data = request.get_json()

        event = Event(
                title=data['title'],
                description=data['description'],
                date=data['date'],
                user_id=current_user.get_id()
            )
        
        if(event != None):
            db.session.add(event)
            db.session.commit()
            return jsonify({"done": 'event created'})
        else:
            return jsonify({"err": 'invalid event'})
    else:
        return redirect(url_for('login'))

@app.route('/redirect_update', methods=['GET'])
def redirectUpdate():
    if current_user.is_authenticated:
        id = request.args.get('id')
        image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
        event = Event.query.filter_by(user_id=current_user.get_id()).filter_by(id=id).first()

        if (event != None):
            return (render_template('update_event.html', user=current_user, image=image_file, event=event))
        return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))


@app.route('/update_event', methods=['POST'])
def UpdateEvent():
    if current_user.is_authenticated:
        data = request.get_json()
        event = Event.query.filter_by(user_id=current_user.get_id()).filter_by(id=data['id']).first()

        event.title = data['title']
        event.description = data['description']
        event.date = data['date']
        event.user_id = current_user.get_id()
        
        if(event != None):
            db.session.commit()
            return jsonify({"redirect": "/index"})
        else:
            return jsonify({"err": 'invalid event'})
    else:
        return redirect(url_for('login'))


@app.route('/delete_event', methods=['GET'])
def deleteEvent():
    if current_user.is_authenticated:
        id = request.args.get('id')
        event = Event.query.filter_by(user_id=current_user.get_id()).filter_by(id=id).first()

        if (event != None):
            db.session.delete(event)
            db.session.commit()
            return redirect(url_for('index'))

        return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))
    
@app.route('/user_page')
def userPage():
    if current_user.is_authenticated:
        image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
        return (render_template('user_page.html', user=current_user, image=image_file))
    else:
        return redirect(url_for('login'))

def savePicture(picture):
    random_hex = secrets.token_hex(5)

    encoded_data = picture.split(',')[1]
    imgdata = base64.b64decode(encoded_data)

    f_ext = '.' + picture.split(',')[0].split(';')[0].split('/')[1]

    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
    
    with open(picture_path, 'wb') as f:
        f.write(imgdata)

    return picture_fn

@app.route('/update_user', methods=["GET", "POST"])
def updateUser():
    if current_user.is_authenticated:
        data = request.get_json()
        old_pic = None

        if (data['image']):
            old_pic = current_user.image_file
            picture_file = savePicture(data['image'])
            current_user.image_file = picture_file

        current_user.username = data['username']
        current_user.email = data['email']

        db.session.commit()

        if old_pic != None and old_pic != 'default.jpg':
            path = os.path.join(app.root_path, 'static\\profile_pics',old_pic)
            os.remove(path)

        return jsonify({"redirect": "/user_page"})
    else:
        return jsonify({"err": 'user not found'})

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/login')
def login():
    return (render_template('login.html'))