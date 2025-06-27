from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sqlite3

users_order_bp = Blueprint('users_order', __name__)

@users_order_bp.route('/menu/<int:store_id>', methods=['GET'])
def menu(store_id):
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    cursor.execute("SELECT store_name FROM store WHERE store_id = ?", (store_id,))
    store_name = cursor.fetchone()[0]

    cursor.execute("""
        SELECT menu_id, menu_name, category, price 
        FROM menus 
        WHERE store_id = ?
    """, (store_id,))
    menu_items = cursor.fetchall()
    conn.close()

    return render_template(
        'users_order/menu.html',
        store_id=store_id,
        store_name=store_name,
        menu_items=menu_items,
        u_name=session.get('u_name', 'ゲスト')
    )

# 🔽 商品追加用のルート（JavaScriptからPOSTされる）
@users_order_bp.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    item = request.json
    cart = session.get('cart', [])
    
    # 同じ商品があるか確認して数量加算
    for cart_item in cart:
        if cart_item['menu_id'] == item['menu_id']:
            cart_item['quantity'] += 1
            break
    else:
        item['quantity'] = 1
        cart.append(item)
    
    session['cart'] = cart
    return {'message': 'カートに追加しました'}


@users_order_bp.route('/cart_confirmation')
def cart_confirmation():
    cart = session.get('cart', [])
    total_quantity = sum(item['quantity'] for item in cart)
    total_price = sum(item['quantity'] * item['price'] for item in cart)

    return render_template(
        'users_order/cart_confirmation.html',
        cart=cart,
        total_quantity=total_quantity,
        total_price=total_price,
        store_name=session.get('store_name', ''),
        store_id=session.get('store_id', 0),  # ← ここで明示的に store_id を渡す
        u_name=session.get('u_name', 'ゲスト')
    )




@users_order_bp.route('/pay_payment')





def pay_payment():
    return render_template('users_order/pay_payment.html')

@users_order_bp.route('/payment_selection')
def payment_selection():
    return render_template('users_order/payment_selection.html')

@users_order_bp.route('/reservation_number')
def reservation_number():
    return render_template('users_order/reservation_number.html')

