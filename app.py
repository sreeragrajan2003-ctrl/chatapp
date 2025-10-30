from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import timedelta,datetime
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, send, join_room
from werkzeug.security import generate_password_hash,check_password_hash


app = Flask(__name__)
app.secret_key = "hello"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.permanent_session_lifetime = timedelta(days=5)

db = SQLAlchemy(app)
socketio = SocketIO(app)


# -------------------- MODELS --------------------

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = password


class Messages(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(100))
    receiver = db.Column(db.String(100))
    message = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now())

    def __init__(self, sender, receiver, message):
        self.sender = sender
        self.receiver = receiver
        self.message = message


# -------------------- ROUTES --------------------


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["nm"]
        email = request.form["email"]
        password = request.form["password"]
        repeat_password = request.form["repeat_password"]

        if password != repeat_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('register'))

        existing_user = Users.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered!", "warning")
            return redirect(url_for('register'))
        hash=generate_password_hash(password)
        new_user = Users(name, email, hash)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please login.", "success")
        return redirect(url_for('login'))

    return render_template("register.html")

@app.route('/', methods=["GET", "POST"])
@app.route('/login', methods=['POST', 'GET'])
def login():
    
    if request.method == 'POST':
        email = request.form["email"]
        password = request.form["password"]
    
        existing_user = Users.query.filter_by(email=email).first()

        if not existing_user:
            flash("Mail ID wrong!", "warning")
            return redirect(url_for('login'))
        else:
            if check_password_hash(existing_user.password,password):
                session["user"] = existing_user.name
                session["user_id"]=existing_user.id
                flash("Login successful!", "success")
                return redirect(url_for('home'))
            else:
                flash("Incorrect password!", "danger")

    return render_template('login.html')


@app.route('/home')
def home():
    if "user" not in session:
        flash("Please login first!", "danger")
        return redirect(url_for('login'))

    existing_user = session.get("user")
    users = Users.query.filter(Users.name != existing_user).all()
    return render_template('home.html', users=users)


@app.route('/logout')
def logout():
    session.pop("user", None)
    session.pop("user_id", None)
    flash("Logged out successfully!", "success")
    return redirect(url_for('login'))

@app.route('/delete_user')
def delete_user():
    username = session.get("user")
    if not username:
        flash("You must be logged in to delete your account.", "danger")
        return redirect(url_for('login'))

    # Find the user by username
    user = Users.query.filter_by(name=username).first()

    if user:
        
        # Delete all messages sent or received by this user
        Messages.query.filter(
            (Messages.sender == user.id)|(Messages.receiver == user.id)
        ).delete()

        # Delete the user account
        db.session.delete(user)
        db.session.commit()

        # Clear session
        session.pop("user", None)
        flash("Your account and all your messages have been deleted.", "info")
        return redirect(url_for('register'))
    else:
        flash("User not found!", "warning")
        return redirect(url_for('login'))


@app.route('/get_messages/<int:receiver_id>')
def get_messages(receiver_id):
    user_id = session.get("user_id")
    
    messages = Messages.query.filter(
        ((Messages.sender == str(user_id)) & (Messages.receiver == str(receiver_id))) |
        ((Messages.sender == str(receiver_id)) & (Messages.receiver == str(user_id)))
    ).order_by(Messages.timestamp.asc()).all()
    
    return {
        "messages": [{'sender': m.sender, 'message': m.message, 'timestamp': m.timestamp.strftime('%H:%M')} for m in messages],
        "current_user": str(user_id)
    }

# -------------------- SOCKET EVENTS --------------------

@socketio.on('connect')
def handle_connect():
    if "user" in session:
        print(f'{session["user"]} connected')

@socketio.on('join')
def handle_join(data):
    join_room(str(session['user_id']))

    

@socketio.on('message')
def handle_message(data):
    userid = session.get("user_id")
    print(userid)
    reciever = data['reciever']
    
    message_text = data['message']
    

    new_message = Messages(userid, reciever, message_text)
    db.session.add(new_message)
    db.session.commit()
    room = str(session['user_id'])
    
    socketio.send({
        'sender': userid,
        'message': message_text,
        'reciever': reciever,
        'timestamp': new_message.timestamp.strftime('%H:%M')
    }, to=room
    )
    socketio.send({
        'sender': userid,
        'message': message_text,
        'reciever': reciever,
        'timestamp': new_message.timestamp.strftime('%H:%M')
    }, to=str(reciever)
    )


# -------------------- MAIN --------------------

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)