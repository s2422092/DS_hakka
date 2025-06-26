from flask import Blueprint, render_template, session, redirect, url_for, flash

# Blueprint作成
users_home_bp = Blueprint('users_home', __name__, url_prefix='/users_home')

@users_home_bp.route('/home')
def home():
    return render_template('users_home/home.html')
