# routes/general/explamation.py
from flask import Blueprint, render_template

users_login_bp = Blueprint('users_login', __name__, url_prefix='/users_login')

@users_login_bp.route('/users_login')
def users_login():
    return render_template('users_login/login.html')
