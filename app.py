from flask import Flask, session
from datetime import timedelta
from flask_socketio import SocketIO, emit, join_room
from models import db, Users, Messages

app = Flask(__name__)
app.secret_key = "hello"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.permanent_session_lifetime = timedelta(days=5)

# Initialize db with app
db.init_app(app)

socketio = SocketIO(app, cors_allowed_origins="*")

# Register blueprints
from auth import auth
from chat import chat

app.register_blueprint(auth)
app.register_blueprint(chat)


# Socket events
@socketio.on('connect')
def handle_connect():
    if "user" in session:
        user_id = session.get("user_id")
        user = Users.query.get(user_id)
        if user:
            user.is_online = True
            db.session.commit()
            emit('user_status', {'user_id': user_id, 'is_online': True}, broadcast=True)
        print(f'{session["user"]} connected')


@socketio.on('disconnect')
def handle_disconnect():
    if "user" in session:
        user_id = session.get("user_id")
        user = Users.query.get(user_id)
        if user:
            user.is_online = False
            db.session.commit()
            emit('user_status', {'user_id': user_id, 'is_online': False}, broadcast=True)
        print(f'{session["user"]} disconnected')


@socketio.on('join')
def handle_join(data):
    join_room(str(session['user_id']))
    print(f'User {session["user"]} joined room {session["user_id"]}')


@socketio.on('message')
def handle_message(data):
    userid = str(session.get("user_id"))
    receiver = str(data['reciever'])
    message_text = data['message']
    
    new_message = Messages(userid, receiver, message_text)
    db.session.add(new_message)
    db.session.commit()
    
    # Send to sender's room
    socketio.send({
        'sender': userid,
        'message': message_text,
        'reciever': receiver,
        'timestamp': new_message.timestamp.strftime('%H:%M')
    }, to=userid)
    
    # Send to receiver's room
    socketio.send({
        'sender': userid,
        'message': message_text,
        'reciever': receiver,
        'timestamp': new_message.timestamp.strftime('%H:%M')
    }, to=receiver)
    
    # Notify receiver about unread message
    socketio.emit('unread_update', {
        'sender_id': userid,
        'receiver_id': receiver
    }, to=receiver)


@socketio.on('mark_read')
def handle_mark_read(data):
    user_id = session.get("user_id")
    sender_id = data.get('sender_id')
    
    Messages.query.filter_by(
        sender=str(sender_id),
        receiver=str(user_id),
        is_read=False
    ).update({'is_read': True})
    db.session.commit()


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)