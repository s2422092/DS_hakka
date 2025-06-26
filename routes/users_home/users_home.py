# routes/general/explamation.py
from flask import Blueprint, render_template

users_home_bp = Blueprint('users_home', __name__, url_prefix='/users_home')

@users_home_bp.route('/users_home')
def users_home():
    return render_template('users_home/home.html')
