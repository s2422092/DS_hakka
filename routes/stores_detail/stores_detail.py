# routes/general/explamation.py
from flask import Blueprint, render_template

stores_detail_bp = Blueprint('stores_detail', __name__, url_prefix='/stores_detail')

@stores_detail_bp.route('/menu_check')
def menu_check():
    return render_template('stores_detail/menu_check.html')

@stores_detail_bp.route('/menu_registration')
def menu_registration():
    return render_template('stores_detail/menu_registration.html')

@stores_detail_bp.route('/order_list')
def order_list():
    return render_template('stores_detail/order_list.html')

@stores_detail_bp.route('/procedure')
def procedure():
    return render_template('stores_detail/procedure.html')

@stores_detail_bp.route('/store_home')
def store_home():
    return render_template('stores_detail/store_home.html')