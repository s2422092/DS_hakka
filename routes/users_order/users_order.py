# routes/users_order/users_order.py

# 標準ライブラリ
import sqlite3
import datetime
from functools import wraps
import os
import json
import logging
import time
import uuid

# サードパーティライブラリ
from dotenv import load_dotenv
import paypayopa # ★★★ これが重要！PayPay OPA SDKのインポート ★★★

# Flask関連のインポート
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify
)

# .envファイルの読み込み
load_dotenv()

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 環境変数の取得と検証
_DEBUG = os.environ.get("_DEBUG", "False").lower() == "true"
API_KEY = os.environ.get("API_KEY")
API_SECRET = os.environ.get("API_SECRET")
MERCHANT_ID = os.environ.get("MERCHANT_ID")
# FRONTEND_BASE_URL (旧 FRONTEND_PATH) を使用します。
# これがPayPayがリダイレクトする際のベースURLになります。
# 5003はモバイルオーダーアプリのポートであると仮定します。
FRONTEND_BASE_URL = os.environ.get("FRONTEND_BASE_URL", default="http://127.0.0.1:5003") # ★ポートを5003に合わせる

# 必須環境変数のチェック (これはapp.pyから移植)
if not API_KEY:
    logger.error("環境変数 'API_KEY' が設定されていません。")
    raise ValueError("環境変数 'API_KEY' が設定されていません。")
if not API_SECRET:
    logger.error("環境変数 'API_SECRET' が設定されていません。")
    raise ValueError("環境変数 'API_SECRET' が設定されていません。")
if not MERCHANT_ID:
    logger.error("環境変数 'MERCHANT_ID' が設定されていません。")
    raise ValueError("環境変数 'MERCHANT_ID' が設定されていません。")

# PayPay OPA クライアントの初期化
client = paypayopa.Client(
    auth=(API_KEY, API_SECRET),
    production_mode=False)
client.set_assume_merchant(MERCHANT_ID)

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

# (menu, add_to_cart, cart_confirmation, payment_selection は変更なし)
# payment_selection ルートはそのままにして、JavaScriptでPayPay処理をトリガーします。
@users_order_bp.route('/menu/<int:store_id>')
@login_required
def menu(store_id):
    """選択された店舗のメニューページを表示する"""
    session['current_store_id'] = store_id
    
    conn = get_db_connection()
    store = conn.execute("SELECT * FROM store WHERE store_id = ?", (store_id,)).fetchone()
    if store is None:
        flash("指定された店舗は存在しません。")
        conn.close()
        return redirect(url_for('users_home.home'))
    
    menu_items = conn.execute("SELECT menu_id, menu_name, category, price FROM menus WHERE store_id = ? AND soldout = 0", (store_id,)).fetchall()
    categories = conn.execute("""SELECT DISTINCT category FROM menus WHERE store_id = ? AND soldout = 0""", (store_id,)).fetchall()
    categories = [row['category'] for row in categories if row['category']]

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
        cart=current_cart,
        total_quantity=total_quantity,
        total_price=total_price,
        store_name=store['store_name'],
        store_id=store_id,
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

    # ★★★ ここを修正 ★★★
    # current_cartは辞書形式なので、values()でイテレータを取得し、
    # list()でリストに変換することで、JavaScriptの配列として適切に扱えるようにします。
    # また、Rowオブジェクトの場合は、dict()に変換することでtojsonが安全に処理できます。
    cart_for_js = []
    for item_key, item_value in current_cart.items():
        # item_valueがsqlite3.Rowオブジェクトの場合は、dict()で通常の辞書に変換する
        if isinstance(item_value, sqlite3.Row):
            cart_for_js.append(dict(item_value))
        else:
            cart_for_js.append(item_value) # 既に辞書形式ならそのまま

    return render_template(
        'users_order/payment_selection.html',
        cart=cart_for_js, # ★ 修正後のリストを渡す ★
        total_price=total_price,
        store_name=store['store_name'],
        u_name=session.get('u_name', 'ゲスト')
    )

# ★★★ ここからPayPay決済ロジックを統合 ★★★

@users_order_bp.route('/paypay/create-qr', methods=['POST'])
@login_required
def paypay_create_qr():
    req = request.json
    logger.info(f"Received create-qr request: {req}")

    store_id = session.get('current_store_id')
    if not store_id:
        return jsonify({"error": "店舗情報がセッションにありません"}), 400

    user_id = session.get('id')
    if not user_id:
        return jsonify({"error": "ユーザー情報がセッションにありません"}), 400

    # MerchantPaymentId を最低50文字にするように修正 (uuidを連結)
    merchant_payment_id = uuid.uuid4().hex + uuid.uuid4().hex
    logger.info(f"Generated merchantPaymentId: {merchant_payment_id} (Length: {len(merchant_payment_id)})")

    conn = get_db_connection()
    cursor = conn.cursor()
    order_id = None

    try:
        current_time = datetime.datetime.now()
        cursor.execute("""
            INSERT INTO orders (user_id, store_id, status, datetime, payment_method, total_amount, merchant_payment_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, store_id, 'pending', current_time, 'PayPay', req["amount"]["amount"], merchant_payment_id))

        order_id = cursor.lastrowid

        order_items_data = [
            (order_id, item['menu_id'], item['quantity'], item['unitPrice']['amount'])
            for item in req["orderItems"]
        ]
        
        cursor.executemany("""
            INSERT INTO order_items (order_id, menu_id, quantity, price_at_order)
            VALUES (?, ?, ?, ?)
        """, order_items_data)

        conn.commit()
        session['current_paypay_order'] = {
            'order_id': order_id,
            'merchant_payment_id': merchant_payment_id,
            'total_amount': req["amount"]["amount"]
        }
        session.modified = True

    except sqlite3.Error as e:
        conn.rollback()
        logger.exception(f"Error saving pending order to DB: {e}")
        return jsonify({"error": "Failed to save pending order", "details": str(e)}), 500
    finally:
        conn.close()

    payment_details = {
        "merchantPaymentId": merchant_payment_id,
        "codeType": "ORDER_QR",
        "orderItems": req["orderItems"],
        "amount": req["amount"],
        # ここをFRONTEND_BASE_URLに合わせる
        "redirectUrl": "{}/users_order/paypay/callback/{}".format(FRONTEND_BASE_URL, merchant_payment_id),
        "redirectType": "WEB_LINK",
        "userAgent": request.headers.get('User-Agent')
    }

    try:
        resp = client.Code.create_qr_code(data=payment_details)
        logger.info(f"QR code creation response: {resp}")

        if resp.get('resultInfo', {}).get('code') == 'SUCCESS' and resp.get('data'):
            response_data = resp['data']
            response_data['orderId'] = order_id
            return jsonify(resp)
        else:
            if order_id:
                conn = get_db_connection()
                conn.execute("UPDATE orders SET status = 'canceled' WHERE order_id = ?", (order_id,))
                conn.commit()
                conn.close()
            logger.error(f"PayPay QR code creation failed. Response: {json.dumps(resp, indent=2)}")
            return jsonify({"error": "Failed to create QR code", "details": resp.get('resultInfo', {}).get('message', 'Unknown error')}), 500

    except Exception as e:
        if order_id:
            conn = get_db_connection()
            conn.execute("UPDATE orders SET status = 'canceled' WHERE order_id = ?", (order_id,))
            conn.commit()
            conn.close()
        logger.exception(f"Error calling PayPay API for QR code: {e}")
        return jsonify({"error": "Failed to communicate with PayPay API", "details": str(e)}), 500

@users_order_bp.route('/paypay/order-status/<string:merchant_payment_id>')
@login_required
def paypay_order_status(merchant_payment_id):
    logger.info(f"Checking order status for merchant ID: {merchant_payment_id}")

    conn = get_db_connection()
    order = conn.execute("SELECT order_id, status FROM orders WHERE merchant_payment_id = ?", (merchant_payment_id,)).fetchone()
    conn.close()

    if order and order['status'] == 'completed':
        logger.info(f"Order {order['order_id']} with merchant ID {merchant_payment_id} already completed in DB.")
        return jsonify({"data": {"status": "COMPLETED", "db_status": "COMPLETED"}}), 200

    try:
        resp = client.Payment.get_payment_details(merchant_payment_id)
        logger.info(f"PayPay order status response: {resp}")

        if resp.get('resultInfo', {}).get('code') == 'RATE_LIMIT':
            logger.warning(f"RATE_LIMIT error for {merchant_payment_id}.")
            return jsonify({"error": "RATE_LIMIT", "message": "Too many requests, please retry later."}), 429

        if resp.get('resultInfo', {}).get('code') == 'SUCCESS' and resp.get('data'):
            paypay_status = resp['data'].get('status')
            
            if paypay_status == 'COMPLETED':
                if order and order['status'] != 'completed':
                    conn = get_db_connection()
                    conn.execute("UPDATE orders SET status = 'completed' WHERE order_id = ?", (order['order_id'],))
                    store_id = session.get('current_store_id')
                    if store_id and str(store_id) in session.get('carts', {}):
                        del session['carts'][str(store_id)]
                        session.modified = True
                    conn.commit()
                    conn.close()
                    logger.info(f"Order {order['order_id']} updated to COMPLETED in DB.")
                session['last_order_id'] = order['order_id'] if order else None
                session.modified = True
                return jsonify(resp), 200
            elif paypay_status == 'CANCELED' or paypay_status == 'FAILED':
                 if order and order['status'] != 'canceled':
                    conn = get_db_connection()
                    conn.execute("UPDATE orders SET status = 'canceled' WHERE order_id = ?", (order['order_id'],))
                    conn.commit()
                    conn.close()
                    logger.info(f"Order {order['order_id']} updated to CANCELED/FAILED in DB.")
                 return jsonify(resp), 200 # 失敗ステータスも正常応答として返す
            else:
                return jsonify(resp), 200 # pendingなども含む

        else:
            logger.error(f"PayPay status check failed. Response: {json.dumps(resp, indent=2)}")
            return jsonify({"error": "PayPay API Error", "message": resp.get('resultInfo', {}).get('message', 'Unknown error')}), 500

    except Exception as e:
        logger.exception(f"Error checking PayPay order status: {e}")
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500

@users_order_bp.route('/paypay/callback/<string:merchant_payment_id>')
def paypay_callback(merchant_payment_id):
    logger.info(f"Received PayPay callback for merchantPaymentId: {merchant_payment_id}")
    session['paypay_callback_merchant_id'] = merchant_payment_id
    session.modified = True
    return redirect(url_for('users_order.payment_selection'))

# (既存の create_order ルートは今回は直接使わないため、PayPay決済フローとは切り離して考える)
@users_order_bp.route('/create_order', methods=['POST'])
@login_required
def create_order():
    """注文をデータベースに保存する (PayPay決済なしの注文確定用、または従来のロジック)"""
    # このルートは、PayPay決済フローを介さずに直接DBに注文を保存したい場合に利用します。
    # PayPay決済と連携する場合は、payment_selection.htmlのJSからこのルートを呼ばないように変更してください。

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
        # PayPay決済フローと区別するため、payment_methodを別の値にしたり、
        # あるいはこのルートを削除してPayPay決済に一本化することも検討
        cursor.execute("""
            INSERT INTO orders (user_id, store_id, status, datetime, payment_method, total_amount)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, store_id, 'completed', current_time, 'Cash' if request.form.get('payment_method') == 'cash' else 'Other', total_price))
        
        order_id = cursor.lastrowid

        order_items_data = [
            (order_id, item['menu_id'], item['quantity'], item['price'])
            for item in current_cart.values()
        ]
        
        cursor.executemany("""
            INSERT INTO order_items (order_id, menu_id, quantity, price_at_order)
            VALUES (?, ?, ?, ?)
        """, order_items_data)

        conn.commit()

        if str(store_id) in session['carts']:
            del session['carts'][str(store_id)]
            session.modified = True
            
        session['last_order_id'] = order_id
        
        flash("注文が完了しました。")
        return redirect(url_for('users_order.reservation_number'))

    except sqlite3.Error as e:
        conn.rollback()
        flash(f"注文処理中にエラーが発生しました: {e}")
        return redirect(url_for('users_order.cart_confirmation'))
    finally:
        conn.close()


# (reservation_number, clear_cart, back_to_home_and_clear_cart, update_cart_item, delete_cart_item は変更なし)
@users_order_bp.route('/reservation_number')
@login_required
def reservation_number():
    """予約（注文）番号表示ページ"""
    order_id = session.pop('last_order_id', 'N/A')
    if order_id == 'N/A':
        flash("不正なアクセスです。")
        return redirect(url_for('users_home.home'))
    return render_template('users_order/reservation_number.html', order_id=order_id)

@users_order_bp.route('/clear_cart')
@login_required
def clear_cart():
    if 'current_store_id' in session and 'carts' in session:
        store_id_str = str(session['current_store_id'])
        if store_id_str in session['carts']:
            del session['carts'][store_id_str]
            session.modified = True
            flash('現在のカートを空にしました。')
    if 'current_store_id' in session:
        return redirect(url_for('users_order.menu', store_id=session['current_store_id']))
    else:
        return redirect(url_for('users_home.home'))
    
@users_order_bp.route('/back_to_home')
@login_required
def back_to_home_and_clear_cart():
    if 'current_store_id' in session:
        store_id_str = str(session['current_store_id'])
        if 'carts' in session and store_id_str in session['carts']:
            del session['carts'][store_id_str]
            session.modified = True
    session.pop('current_store_id', None)
    return redirect(url_for('users_home.home'))

@users_order_bp.route('/update_cart_item', methods=['POST'])
@login_required
def update_cart_item():
    if 'current_store_id' not in session:
        return redirect(url_for('users_home.home'))
    try:
        menu_id_str = request.form['menu_id']
        new_quantity = int(request.form['quantity'])
    except (KeyError, ValueError):
        flash("不正なリクエストです。")
        return redirect(url_for('users_order.cart_confirmation'))

    store_id_str = str(session['current_store_id'])
    carts = session.get('carts', {})

    if store_id_str in carts and menu_id_str in carts[store_id_str]:
        if new_quantity > 0:
            carts[store_id_str][menu_id_str]['quantity'] = new_quantity
            flash("数量を更新しました。")
        else:
            del carts[store_id_str][menu_id_str]
            flash("商品をカートから削除しました。")
        session['carts'] = carts
        session.modified = True
    return redirect(url_for('users_order.cart_confirmation'))

@users_order_bp.route('/delete_cart_item', methods=['POST'])
@login_required
def delete_cart_item():
    if 'current_store_id' not in session:
        return redirect(url_for('users_home.home'))
    try:
        menu_id_str = request.form['menu_id']
    except KeyError:
        flash("不正なリクエストです。")
        return redirect(url_for('users_order.cart_confirmation'))

    store_id_str = str(session['current_store_id'])
    carts = session.get('carts', {})

    if store_id_str in carts and menu_id_str in carts[store_id_str]:
        del carts[store_id_str][menu_id_str]
        session['carts'] = carts
        session.modified = True
        flash("商品をカートから削除しました。")
    return redirect(url_for('users_order.cart_confirmation'))