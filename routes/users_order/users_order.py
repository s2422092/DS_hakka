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

@users_order_bp.route('/cart_confirmation/<int:store_id>')
def cart_confirmation(store_id):
    # この関数は変更ありません
    cart = session.get('cart', [])
    total_quantity = sum(item['quantity'] for item in cart)
    total_price = sum(item['quantity'] * item['price'] for item in cart)
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
    return render_template(
        'users_order/cart_confirmation.html',
        cart=cart,
        total_quantity=total_quantity,
        total_price=total_price,
        store_name=store_name,
        store_id=store_id,
        u_name=session.get('u_name', 'ゲスト')
    )

@users_order_bp.route('/payment_selection/<int:store_id>') # store_idを受け取るように変更
def payment_selection(store_id):
    # ▼▼▼▼▼ ここを修正 ▼▼▼▼▼
    # cart_confirmationとほぼ同じ処理を行い、セッションからカート情報を取得
    cart = session.get('cart', [])

    # カートが空なら、メニューページに戻す（親切設計）
    if not cart:
        flash("カートが空です。")
        return redirect(url_for('users_order.menu', store_id=store_id))

    # 合計数量と合計金額を計算
    total_quantity = sum(item['quantity'] for item in cart)
    total_price = sum(item['quantity'] * item['price'] for item in cart)

    # テンプレートにカート情報や合計金額を渡す
    return render_template(
        'users_order/payment_selection.html',
        cart=cart,
        total_quantity=total_quantity,
        total_price=total_price,
        store_name=session.get('store_name', ''),
        store_id=store_id,
        u_name=session.get('u_name', 'ゲスト')
    )
    # ▲▲▲▲▲ ここまで修正 ▲▲▲▲▲


@users_order_bp.route('/pay_payment')
def pay_payment():
    # ▼▼▼▼▼ ここを修正 ▼▼▼▼▼
    # ここでPayPayのAPIを叩くなどの実際の支払い処理を将来的に実装する

    # 注文が完了したとみなし、カートのセッションを削除
    session.pop('cart', None)
    
    flash("お支払いが完了しました。")
    # 予約番号ページへリダイレクト
    return redirect(url_for('users_order.reservation_number'))
    # ▲▲▲▲▲ ここまで修正 ▲▲▲▲▲


@users_order_bp.route('/reservation_number')
def reservation_number():
    # この関数は変更ありません
    return render_template('users_order/reservation_number.html')