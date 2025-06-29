from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sqlite3



users_order_bp = Blueprint('users_order', __name__)

@users_order_bp.route('/home_clear_cart')
def home_clear_cart():
    session.pop('cart', None)  # カート情報を消す
    return redirect(url_for('users_home.home'))

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

from flask import request, session, jsonify

@users_order_bp.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    try:
        menu_id = int(data.get('menu_id'))
        name = data.get('name')
        category = data.get('category')
        price = int(data.get('price'))
        quantity = int(data.get('quantity', 1))
    except (TypeError, ValueError):
        return jsonify({'error': '不正なデータです'}), 400

    if not all([menu_id, name, category, price]):
        return jsonify({'error': '必要なデータがありません'}), 400

    cart = session.get('cart', [])

    for item in cart:
        if item['menu_id'] == menu_id:
            item['quantity'] += quantity
            break
    else:
        cart.append({
            'menu_id': menu_id,
            'name': name,
            'category': category,
            'price': price,
            'quantity': quantity
        })

    session['cart'] = cart
    session.modified = True
    return jsonify({'message': 'カートに追加しました', 'cart_count': sum(i['quantity'] for i in cart)})


@users_order_bp.route('/cart_confirmation/<int:store_id>')
def cart_confirmation(store_id):
    # セッションからカート情報を取得（なければ空リスト）
    cart = session.get('cart', [])

    # 合計数量と合計金額を計算
    total_quantity = sum(item['quantity'] for item in cart)
    total_price = sum(item['quantity'] * item['price'] for item in cart)

    # 店舗名をセッションから取得、なければDBから取得しセッションに保存
    store_name = session.get('store_name', '')
    if not store_name:
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute("SELECT store_name FROM store WHERE store_id = ?", (store_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            store_name = row[0]
            session['store_name'] = store_name
        else:
            flash("店舗情報が取得できませんでした。")
            return redirect(url_for('users_home.home'))

    # テンプレートに渡す
    return render_template(
        'users_order/cart_confirmation.html',
        cart=cart,
        total_quantity=total_quantity,
        total_price=total_price,
        store_name=store_name,
        store_id=store_id,
        u_name=session.get('u_name', 'ゲスト')
    )

@users_order_bp.route('/payment_selection')
def payment_selection():
    
    return render_template('users_order/payment_selection.html')


@users_order_bp.route('/pay_payment')





def pay_payment():
    return render_template('users_order/pay_payment.html')



@users_order_bp.route('/reservation_number')
def reservation_number():
    return render_template('users_order/reservation_number.html')

