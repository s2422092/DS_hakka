# routes/general/explamation.py
from flask import Blueprint, render_template

users_login_bp = Blueprint('users_login', __name__, url_prefix='/users_login')

@users_login_bp.route('/login')
def login():
    return render_template('users_login/login.html')


@users_login_bp.route('/signup')
def signup():
    return render_template('users_login/signup.html')

