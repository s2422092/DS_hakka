# routes/users_order/users_order.py

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import datetime
from functools import wraps

# (Blueprint定義、get_db_connection, login_requiredデコレータは変更なし)
users_order_bp = Blueprint('users_order', __name__, url_prefix='/users_order')

def get_db_connection():
    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'id' not in session:
            flash("この操作にはログインが必要です。")
            return redirect(url_for('users_login.login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Routes ---

@users_order_bp.route('/menu/<int:store_id>')
@login_required
def menu(store_id):
    """選択された店舗のメニューページを表示する"""
    session['current_store_id'] = store_id
    
    conn = get_db_connection()
    # storeオブジェクト全体を取得するよう修正
    store = conn.execute("SELECT * FROM store WHERE store_id = ?", (store_id,)).fetchone()
    if store is None:
        flash("指定された店舗は存在しません。")
        conn.close()
        return redirect(url_for('users_home.home'))
    
    menu_items = conn.execute("SELECT menu_id, menu_name, category, price FROM menus WHERE store_id = ? AND soldout = 0", (store_id,)).fetchall()
    categories = conn.execute("""SELECT DISTINCT category FROM menus WHERE store_id = ? AND soldout = 0""", (store_id,)).fetchall()
    categories = [row['category'] for row in categories if row['category']]  # Noneを除外

    conn.close()

    carts = session.get('carts', {})
    current_cart = carts.get(str(store_id), {})

    return render_template(
        'users_order/menu.html',
        store=store,
        menu_items=menu_items,
        cart=current_cart,
        u_name=session.get('u_name', 'ゲスト'),
        categories=categories
    )


# add_to_cartから下の関数は、前回提示した完成版のままでOKです。
# 念のため、以下に全コードを記載しておきます。
@users_order_bp.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    if 'current_store_id' not in session:
        return jsonify({'error': '店舗を選択してください'}), 400
    data = request.get_json()
    try:
        menu_id = int(data['menu_id'])
        quantity = int(data['quantity'])
    except (TypeError, ValueError, KeyError):
        return jsonify({'error': '不正なデータ形式です'}), 400
    store_id = session['current_store_id']
    conn = get_db_connection()
    menu_item = conn.execute("SELECT menu_name, price, store_id FROM menus WHERE menu_id = ?", (menu_id,)).fetchone()
    conn.close()
    if not menu_item or menu_item['store_id'] != store_id:
        return jsonify({'error': '無効な商品です'}), 400
    carts = session.get('carts', {})
    store_id_str, menu_id_str = str(store_id), str(menu_id)
    current_cart = carts.get(store_id_str, {})
    if menu_id_str in current_cart:
        current_cart[menu_id_str]['quantity'] += quantity
    else:
        current_cart[menu_id_str] = {
            'menu_id': menu_id, 'name': menu_item['menu_name'],
            'price': menu_item['price'], 'quantity': quantity
        }
    carts[store_id_str] = current_cart
    session['carts'] = carts
    session.modified = True
    total_items = sum(item['quantity'] for item in current_cart.values())
    return jsonify({'message': 'カートに追加しました', 'cart_count': total_items})

@users_order_bp.route('/cart_confirmation')
@login_required
def cart_confirmation():
    if 'current_store_id' not in session:
        return redirect(url_for('users_home.home'))
    store_id = session['current_store_id']
    carts = session.get('carts', {})
    current_cart = carts.get(str(store_id), {})
    total_quantity = sum(item['quantity'] for item in current_cart.values())
    total_price = sum(item['quantity'] * item['price'] for item in current_cart.values())
    conn = get_db_connection()
    store = conn.execute("SELECT store_name FROM store WHERE store_id = ?", (store_id,)).fetchone()
    conn.close()
    if not store:
        return redirect(url_for('users_home.home'))
    return render_template(
        'users_order/cart_confirmation.html',
        cart=list(current_cart.values()),
        total_quantity=total_quantity,
        total_price=total_price,
        store_name=store['store_name'],
        store_id=store_id, # ★★★ この一行を追加してください ★★★
        u_name=session.get('u_name', 'ゲスト')
    )


@users_order_bp.route('/payment_selection')
@login_required
def payment_selection():
    """決済方法選択と最終確認ページ"""
    if 'current_store_id' not in session:
        flash("店舗が選択されていません。")
        return redirect(url_for('users_home.home'))

    store_id = session['current_store_id']
    carts = session.get('carts', {})
    current_cart = carts.get(str(store_id), {})

    if not current_cart:
        flash("カートが空です。")
        return redirect(url_for('users_order.menu', store_id=store_id))

    total_price = sum(item['quantity'] * item['price'] for item in current_cart.values())
    
    conn = get_db_connection()
    store = conn.execute("SELECT store_name FROM store WHERE store_id = ?", (store_id,)).fetchone()
    conn.close()

    return render_template(
        'users_order/payment_selection.html',
        cart=list(current_cart.values()),
        total_price=total_price,
        store_name=store['store_name'],
        u_name=session.get('u_name', 'ゲスト')
    )

@users_order_bp.route('/create_order', methods=['POST'])
@login_required
def create_order():
    """注文をデータベースに保存する"""
    if 'current_store_id' not in session:
        return redirect(url_for('users_home.home'))

    user_id = session['id']
    store_id = session['current_store_id']
    carts = session.get('carts', {})
    current_cart = carts.get(str(store_id), {})

    if not current_cart:
        return redirect(url_for('users_order.menu', store_id=store_id))

    total_price = sum(item['quantity'] * item['price'] for item in current_cart.values())

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        current_time = datetime.datetime.now()
        cursor.execute("""
            INSERT INTO orders (user_id, store_id, status, datetime, payment_method, total_amount)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, store_id, 'completed', current_time, 'PayPay', total_price))
        
        order_id = cursor.lastrowid

        order_items_data = [
            (order_id, item['menu_id'], item['quantity'], item['price'])
            for item in current_cart.values()
        ]
        
        # order_itemsテーブルのprice_at_orderカラムに合わせて修正
        cursor.executemany("""
            INSERT INTO order_items (order_id, menu_id, quantity, price_at_order)
            VALUES (?, ?, ?, ?)
        """, order_items_data)

        conn.commit()

        if str(store_id) in session['carts']:
            del session['carts'][str(store_id)]
            session.modified = True
            
        session['last_order_id'] = order_id
        
        # ここで実際にPayPay APIを呼び出す処理が入ります
        # 今回は成功したと仮定して、予約番号表示ページへリダイレクト
        flash("注文が完了しました。")
        return redirect(url_for('users_order.reservation_number'))

    except sqlite3.Error as e:
        conn.rollback()
        flash(f"注文処理中にエラーが発生しました: {e}")
        return redirect(url_for('users_order.cart_confirmation'))
    finally:
        conn.close()

@users_order_bp.route('/reservation_number')
@login_required
def reservation_number():
    """予約（注文）番号表示ページ"""
    order_id = session.pop('last_order_id', 'N/A') # 一度表示したらセッションから消す
    if order_id == 'N/A':
        flash("不正なアクセスです。")
        return redirect(url_for('users_home.home'))
    return render_template('users_order/reservation_number.html', order_id=order_id)

@users_order_bp.route('/clear_cart')
@login_required
def clear_cart():
    """現在選択中の店舗のカートを空にする"""
    # セッションに店舗IDとカート情報があるか確認
    if 'current_store_id' in session and 'carts' in session:
        store_id_str = str(session['current_store_id'])
        
        # 現在の店舗のカートが存在すれば削除
        if store_id_str in session['carts']:
            del session['carts'][store_id_str]
            session.modified = True # セッションの変更をFlaskに通知
            flash('現在のカートを空にしました。')
    
    # 処理が終わったら、今いるお店のメニューページにリダイレクトして戻る
    # もしカート確認ページから呼ばれた場合も、一旦メニューに戻すのがシンプル
    if 'current_store_id' in session:
        return redirect(url_for('users_order.menu', store_id=session['current_store_id']))
    else:
        # 万が一店舗IDがセッションになければホームへ
        return redirect(url_for('users_home.home'))
    
@users_order_bp.route('/back_to_home')
@login_required
def back_to_home_and_clear_cart():
    """
    現在の店舗のカート情報をクリアし、ホーム画面に戻るためのルート
    """
    # セッションに現在見ている店舗IDがあるか確認
    if 'current_store_id' in session:
        store_id_str = str(session['current_store_id'])
        
        # 全体のカート情報（carts）があるか確認
        if 'carts' in session and store_id_str in session['carts']:
            # 現在の店舗のカート情報だけを削除
            del session['carts'][store_id_str]
            session.modified = True # セッションの変更をFlaskに通知
    
    # current_store_idもセッションから削除して、完全に店舗選択から抜ける
    session.pop('current_store_id', None)
    
    # ユーザーのホーム画面にリダイレクト
    return redirect(url_for('users_home.home'))