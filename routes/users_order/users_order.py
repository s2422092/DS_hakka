# routes/general/explamation.py
from flask import Blueprint, render_template
import sqlite3


users_order_bp = Blueprint('users_order', __name__, url_prefix='/users_order')

@users_order_bp.route('/cart_confirmation')
def cart_confirmation():
    return render_template('users_order/cart_confirmation.html')

@users_order_bp.route('/menu/<int:store_id>')
def menu(store_id):
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()

    # 店舗名取得
    cursor.execute("SELECT store_name FROM store WHERE store_id = ?", (store_id,))
    row = cursor.fetchone()
    if row is None:
        cursor.close()
        conn.close()
        return "店舗が見つかりません", 404
    store_name = row[0]

    # メニュー取得（例）
    cursor.execute("SELECT menu_id, menu_name, category, price FROM menus WHERE store_id = ?", (store_id,))
    menu_items = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('users_order/menu.html', store_name=store_name, menu_items=menu_items)


@users_order_bp.route('/pay_payment')
def pay_payment():
    return render_template('users_order/pay_payment.html')

@users_order_bp.route('/payment_selection')
def payment_selection():
    return render_template('users_order/payment_selection.html')

@users_order_bp.route('/reservation_number')
def reservation_number():
    return render_template('users_order/reservation_number.html')

