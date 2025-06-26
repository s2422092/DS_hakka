# routes/general/explamation.py
from flask import Blueprint, render_template

users_order_bp = Blueprint('users_order', __name__, url_prefix='/users_order')

@users_order_bp.route('/users_order')
def users_order():
    return render_template('users_order/cart_confirmation.html')
