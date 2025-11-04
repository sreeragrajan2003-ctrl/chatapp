from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from models import db, Users, Messages

chat = Blueprint('chat', __name__)


@chat.route('/home')
def home():
    if "user" not in session:
        flash("Please login first!", "danger")
        return redirect(url_for('auth.login'))

    existing_user = session.get("user")
    user_id = session.get("user_id")
    users = Users.query.filter(Users.name != existing_user).all()
    
    users_with_unread = []
    for user in users:
        unread_count = Messages.query.filter_by(
            sender=str(user.id),
            receiver=str(user_id),
            is_read=False
        ).count()
        users_with_unread.append({
            'id': user.id,
            'name': user.name,
            'is_online': user.is_online,
            'unread_count': unread_count
        })
    
    return render_template('home.html', users=users_with_unread)


@chat.route('/get_messages/<int:receiver_id>')
def get_messages(receiver_id):
    user_id = session.get("user_id")
    
    messages = Messages.query.filter(
        ((Messages.sender == str(user_id)) & (Messages.receiver == str(receiver_id))) |
        ((Messages.sender == str(receiver_id)) & (Messages.receiver == str(user_id)))
    ).order_by(Messages.timestamp.asc()).all()
    
    # Mark messages as read
    Messages.query.filter_by(
        sender=str(receiver_id),
        receiver=str(user_id),
        is_read=False
    ).update({'is_read': True})
    db.session.commit()
    
    return jsonify({
        "messages": [{'sender': m.sender, 'message': m.message, 'timestamp': m.timestamp.strftime('%H:%M')} for m in messages],
        "current_user": str(user_id)
    })


@chat.route('/check_status/<int:user_id>')
def check_status(user_id):
    user = Users.query.get(user_id)
    if user:
        return jsonify({"is_online": user.is_online})
    return jsonify({"is_online": False})


@chat.route('/get_unread_count/<int:sender_id>')
def get_unread_count(sender_id):
    user_id = session.get("user_id")
    count = Messages.query.filter_by(
        sender=str(sender_id),
        receiver=str(user_id),
        is_read=False
    ).count()
    return jsonify({"unread_count": count})


@chat.route('/delete_user')
def delete_user():
    username = session.get("user")
    user_id = session.get("user_id")
    
    if not username:
        flash("You must be logged in to delete your account.", "danger")
        return redirect(url_for('auth.login'))

    user = Users.query.get(user_id)

    if user:
        # Delete all messages where user is sender or receiver
        Messages.query.filter(
            (Messages.sender == str(user.id)) | (Messages.receiver == str(user.id))
        ).delete()

        db.session.delete(user)
        db.session.commit()

        session.pop("user", None)
        session.pop("user_id", None)
        flash("Your account and all your messages have been deleted.", "info")
        return redirect(url_for('auth.register'))
    else:
        flash("User not found!", "warning")
        return redirect(url_for('auth.login'))