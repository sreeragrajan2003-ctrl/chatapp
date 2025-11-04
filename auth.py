from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Users

auth = Blueprint('auth', __name__)


@auth.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["nm"]
        email = request.form["email"]
        password = request.form["password"]
        repeat_password = request.form["repeat_password"]

        if password != repeat_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('auth.register'))

        existing_user = Users.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered!", "warning")
            return redirect(url_for('auth.register'))
        
        hash_pwd = generate_password_hash(password)
        new_user = Users(name, email, hash_pwd)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please login.", "success")
        return redirect(url_for('auth.login'))

    return render_template("register.html")


@auth.route('/login', methods=['POST', 'GET'])
@auth.route('/', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form["email"]
        password = request.form["password"]
    
        existing_user = Users.query.filter_by(email=email).first()

        if not existing_user:
            flash("Email not found!", "warning")
            return redirect(url_for('auth.login'))
        else:
            if check_password_hash(existing_user.password, password):
                existing_user.is_online = True
                db.session.commit()
                
                session["user"] = existing_user.name
                session["user_id"] = existing_user.id
                flash("Login successful!", "success")
                return redirect(url_for('chat.home'))
            else:
                flash("Incorrect password!", "danger")

    return render_template('login.html')


@auth.route('/logout')
def logout():
    user_id = session.get("user_id")
    if user_id:
        user = Users.query.get(user_id)
        if user:
            user.is_online = False
            db.session.commit()
    
    session.pop("user", None)
    session.pop("user_id", None)
    flash("Logged out successfully!", "success")
    return redirect(url_for('auth.login'))