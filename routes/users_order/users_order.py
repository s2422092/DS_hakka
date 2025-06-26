# routes/general/explamation.py
from flask import Blueprint, render_template

users_order_bp = Blueprint('users_order', __name__, url_prefix='/users_order')

@users_order_bp.route('/cart_confirmation')
def cart_confirmation():
    return render_template('users_order/cart_confirmation.html')

@users_order_bp.route('/menu')
def menu():
    return render_template('users_order/menu.html')

@users_order_bp.route('/pay_payment')
def pay_payment():
    return render_template('users_order/pay_payment.html')

@users_order_bp.route('/payment_selection')
def payment_selection():
    return render_template('users_order/payment_selection.html')

@users_order_bp.route('/reservation_number')
def reservation_number():
    return render_template('users_order/reservation_number.html')

