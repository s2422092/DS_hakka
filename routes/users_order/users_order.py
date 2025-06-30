# routes/users_order/users_order.py

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import datetime
from functools import wraps

# ★ここから追加・変更
import os
import json
import logging
import time
import uuid # uuidをインポート

# PayPay OPA SDKのインポート
# おそらくあなたのプロジェクトのルート直下、または何らかのlibs/paypay_opaのような場所にある想定
# もしapp.pyで直接インストールしたなら、ここでもインストールされているはず
import paypayopa

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 環境変数の設定 (app.pyから持ってくるか、.envから読み込む)
# users_order.pyが直接.envを読み込む場合はdotenvもインポート
from dotenv import load_dotenv
load_dotenv() # .envファイルを読み込む

_DEBUG = os.environ.get("_DEBUG", "False").lower() == "true"
API_KEY = os.environ.get("API_KEY")
API_SECRET = os.environ.get("API_SECRET")
MERCHANT_ID = os.environ.get("MERCHANT_ID")
# フロントエンドのURLを正しく設定（ポート番号など注意）
# users_order.pyで直接使うので、users_orderブループリントのURLプレフィックスは含まない
FRONTEND_BASE_URL = os.environ.get("FRONTEND_BASE_URL", default="http://127.0.0.1:5000") # あなたのフロントエンドURLに合わせて変更

# PayPay OPA クライアントの初期化
client = paypayopa.Client(
    auth=(API_KEY, API_SECRET),
    production_mode=False) # production_modeをFalseに設定し、サンドボックス環境を使用
client.set_assume_merchant(MERCHANT_ID)

# ★ここまで追加・変更

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
# payment_selection ルートの cart=list(current_cart.values()) はそのままにしておきます。
# JavaScript側でこのリスト構造を利用します。

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
    current_cart = carts.get(str(store_id), {}) # ★★★ 変更点：辞書のまま保持 ★★★

    total_quantity = sum(item['quantity'] for item in current_cart.values())
    total_price = sum(item['quantity'] * item['price'] for item in current_cart.values())
    
    conn = get_db_connection()
    store = conn.execute("SELECT store_name FROM store WHERE store_id = ?", (store_id,)).fetchone()
    conn.close()
    if not store:
        return redirect(url_for('users_home.home'))
        
    return render_template(
        'users_order/cart_confirmation.html',
        cart=current_cart, # ★★★ 変更点：辞書のままテンプレートに渡す ★★★
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

    return render_template(
        'users_order/payment_selection.html',
        # JavaScript側で扱いやすいように、dict_valuesオブジェクトではなくlistに変換して渡す
        cart=list(current_cart.values()), # ★ここも変更済みと認識
        total_price=total_price,
        store_name=store['store_name'],
        u_name=session.get('u_name', 'ゲスト')
    )

# ★ここからPayPay API関連の新しいエンドポイントを追加
@users_order_bp.route('/paypay/create-qr', methods=['POST'])
@login_required
def paypay_create_qr():
    """PayPayのQRコード支払いを生成するエンドポイント"""
    req = request.json
    logger.info(f"Received create-qr request: {req}")

    store_id = session.get('current_store_id')
    if not store_id:
        return jsonify({"error": "店舗情報がセッションにありません"}), 400

    user_id = session.get('id')
    if not user_id:
        return jsonify({"error": "ユーザー情報がセッションにありません"}), 400

    # 支払いと注文の紐付けのためのユニークなIDを生成
    # MerchantPaymentId を最低50文字にするように修正
    # uuid.uuid4().hex は32文字なので、もう一つUUIDを連結して64文字にする
    merchant_payment_id = uuid.uuid4().hex + uuid.uuid4().hex
    logger.info(f"Generated merchantPaymentId: {merchant_payment_id} (Length: {len(merchant_payment_id)})")

    # 注文データを一時的にDBに保存（ここでは'pending'状態）
    # この merchant_payment_id を orders テーブルのどこかに保存して、後で更新できるようにする
    # 例: orders テーブルに merchant_payment_id カラムを追加するか、
    # 別の payment_transactions テーブルを作成して紐付ける
    # 今回はシンプルに orders テーブルに 'pending' 状態でmerchant_payment_idを紐付け、後で更新する
    conn = get_db_connection()
    cursor = conn.cursor()
    order_id = None # order_idを事前に定義

    try:
        current_time = datetime.datetime.now()
        cursor.execute("""
            INSERT INTO orders (user_id, store_id, status, datetime, payment_method, total_amount, merchant_payment_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, store_id, 'pending', current_time, 'PayPay', req["amount"]["amount"], merchant_payment_id)) # statusをpendingに

        order_id = cursor.lastrowid

        order_items_data = [
            (order_id, item['menu_id'], item['quantity'], item['unitPrice']['amount']) # unitPrice.amountをprice_at_orderに
            for item in req["orderItems"]
        ]
        
        cursor.executemany("""
            INSERT INTO order_items (order_id, menu_id, quantity, price_at_order)
            VALUES (?, ?, ?, ?)
        """, order_items_data)

        conn.commit()
        # ここで order_id と merchant_payment_id をセッションに保存しておくと、
        # 後続のポーリングや、エラー時の対応がしやすくなる
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

    # PayPay APIへのリクエストデータ準備
    payment_details = {
        "merchantPaymentId": merchant_payment_id,
        "codeType": "ORDER_QR",
        "orderItems": req["orderItems"], # フロントエンドから来た形式をそのまま使用
        "amount": req["amount"],
        # redirectUrlは、このFlaskアプリのパスにmerchantPaymentIdを含める
        "redirectUrl": "{}/users_order/paypay/callback/{}".format(FRONTEND_BASE_URL, merchant_payment_id),
        "redirectType": "WEB_LINK",
        "userAgent": request.headers.get('User-Agent') # UserAgentを付与するとより良い
    }

    try:
        resp = client.Code.create_qr_code(data=payment_details)
        logger.info(f"QR code creation response: {resp}")

        if resp.get('resultInfo', {}).get('code') == 'SUCCESS' and resp.get('data'):
            # ここで、QRコード生成が成功したら、order_idを紐付けたmerchant_payment_idを返す
            # Frontend JSでpollingするためにmerchantPaymentIdが必要
            response_data = resp['data']
            response_data['orderId'] = order_id # 生成したDBのorder_idもフロントエンドに返す
            return jsonify(resp)
        else:
            # QRコード生成失敗時、DBの仮注文をキャンセルなど考慮
            if order_id:
                conn = get_db_connection()
                conn.execute("UPDATE orders SET status = 'canceled' WHERE order_id = ?", (order_id,))
                conn.commit()
                conn.close()
            logger.error(f"PayPay QR code creation failed. Response: {json.dumps(resp, indent=2)}")
            return jsonify({"error": "Failed to create QR code", "details": resp.get('resultInfo', {}).get('message', 'Unknown error')}), 500

    except Exception as e:
        # API呼び出し中の例外発生時、DBの仮注文をキャンセルなど考慮
        if order_id:
            conn = get_db_connection()
            conn.execute("UPDATE orders SET status = 'canceled' WHERE order_id = ?", (order_id,))
            conn.commit()
            conn.close()
        logger.exception(f"Error calling PayPay API for QR code: {e}")
        return jsonify({"error": "Failed to communicate with PayPay API", "details": str(e)}), 500


@users_order_bp.route('/paypay/order-status/<string:merchant_payment_id>')
@login_required # ログイン必須であれば追加
def paypay_order_status(merchant_payment_id):
    """PayPayの支払いステータスをポーリングするエンドポイント"""
    logger.info(f"Checking order status for merchant ID: {merchant_payment_id}")

    # このmerchant_payment_idに対応する仮注文があるか確認（オプション）
    conn = get_db_connection()
    order = conn.execute("SELECT order_id, status FROM orders WHERE merchant_payment_id = ?", (merchant_payment_id,)).fetchone()
    conn.close()

    if order and order['status'] == 'completed':
        # 既に完了している場合はPayPayに問い合わせずそのまま返す
        logger.info(f"Order {order['order_id']} with merchant ID {merchant_payment_id} already completed in DB.")
        return jsonify({"data": {"status": "COMPLETED", "db_status": "COMPLETED"}}), 200

    try:
        resp = client.Payment.get_payment_details(merchant_payment_id)
        logger.info(f"PayPay order status response: {resp}")

        # レート制限エラーハンドリング
        if resp.get('resultInfo', {}).get('code') == 'RATE_LIMIT':
            logger.warning(f"RATE_LIMIT error for {merchant_payment_id}. Will retry. Link: https://developer.paypay.ne.jp/develop/resolve?api_name=v2_getQRPaymentDetails&code=RATE_LIMIT&code_id=08100998")
            # レート制限の場合は、フロントエンドにポーリングを継続させるためのエラーを返す
            return jsonify({"error": "RATE_LIMIT", "message": "Too many requests, please retry later."}), 429 # HTTP 429 Too Many Requests

        # 成功レスポンスの場合
        if resp.get('resultInfo', {}).get('code') == 'SUCCESS' and resp.get('data'):
            paypay_status = resp['data'].get('status')
            
            # DBの注文ステータスを更新するロジック
            if paypay_status == 'COMPLETED':
                if order and order['status'] != 'completed':
                    conn = get_db_connection()
                    conn.execute("UPDATE orders SET status = 'completed' WHERE order_id = ?", (order['order_id'],))
                    # 決済が完了したらカートをクリア
                    store_id = session.get('current_store_id')
                    if store_id and str(store_id) in session.get('carts', {}):
                        del session['carts'][str(store_id)]
                        session.modified = True
                    conn.commit()
                    conn.close()
                    logger.info(f"Order {order['order_id']} updated to COMPLETED in DB.")
                # 最終的な予約番号（order_id）をフロントエンドに返す
                session['last_order_id'] = order['order_id'] if order else None
                session.modified = True

            elif paypay_status == 'CANCELED' or paypay_status == 'FAILED': # 必要に応じて他の失敗ステータスも追加
                 if order and order['status'] != 'canceled':
                    conn = get_db_connection()
                    conn.execute("UPDATE orders SET status = 'canceled' WHERE order_id = ?", (order['order_id'],))
                    conn.commit()
                    conn.close()
                    logger.info(f"Order {order['order_id']} updated to CANCELED/FAILED in DB.")
            
            return jsonify(resp), 200
        else:
            # PayPayからの応答がSUCCESSでない場合、エラーとして扱う
            logger.error(f"PayPay status check failed. Response: {json.dumps(resp, indent=2)}")
            return jsonify({"error": "PayPay API Error", "message": resp.get('resultInfo', {}).get('message', 'Unknown error')}), 500

    except Exception as e:
        logger.exception(f"Error checking PayPay order status: {e}")
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500

# ★ここからPayPayのリダイレクト後のコールバック処理
@users_order_bp.route('/paypay/callback/<string:merchant_payment_id>')
def paypay_callback(merchant_payment_id):
    """
    PayPay決済が完了または失敗した後にPayPayからリダイレクトされるURL。
    ここでは、単にフロントエンドのステータス確認画面にリダイレクトし、
    JavaScriptがポーリングを続けるようにします。
    """
    logger.info(f"Received PayPay callback for merchantPaymentId: {merchant_payment_id}")
    # フロントエンドの支払い完了・確認画面にリダイレクト
    # 例えば、payment_selection.htmlに戻り、モーダルを再表示させるようなロジックが必要
    # または、専用の支払い結果表示ページにリダイレクトする
    # ここでは、簡素化のため、payment_selectionページに戻り、JSがポーリングで状態を拾うのを想定
    
    # セッションに merchant_payment_id を渡すことで、フロントエンドがそのIDでポーリングを再開できるようにする
    session['paypay_callback_merchant_id'] = merchant_payment_id
    session.modified = True
    
    # ★重要: このリダイレクト先は、payment_selection.html にモーダルを表示するためのJSがあるページのURLにしてください
    # そのページに、クエリパラメータでmerchant_payment_idを渡すのが一般的です。
    # 例: return redirect(url_for('users_order.payment_selection', merchantId=merchant_payment_id))
    # 今回は、セッションを利用して、payment_selection() が読み込まれた際にJSが自動でポーリング開始するよう調整します。
    return redirect(url_for('users_order.payment_selection'))

# ★★★ 既存の create_order ルートの変更 ★★★
# このルートはPayPay決済が完了した後に呼ばれるべきです。
# フロントエンドからPayPay決済が成功したことを通知するAPIを新設し、
# そこでこのロジックを呼び出す形が良いですが、
# 今回は既存の create_order を使わず、PayPay決済の成功時にDBのstatusを'completed'に更新する形で対応します。
# したがって、HTMLのフォームからこのcreate_orderを直接呼び出すことはなくします。
# もし`この内容で注文を確定する`ボタンで注文をDBに確定させたい場合は、`users_order.create_order`の呼び出し方を変更します。
# いったん、このルートはコメントアウトまたは削除せず、別の利用方法を想定しておきます。
# `paypay_create_qr`で注文は'pending'状態でDBに保存され、`paypay_order_status`で'completed'に更新されます。
# したがって、`payment_selection.html`の「この内容で注文を確定する」ボタンは、PayPayの決済フローを開始するためのボタンに一本化します。

# @users_order_bp.route('/create_order', methods=['POST'])
# @login_required
# def create_order():
#     # ... (上記に移動した注文保存ロジックは削除または変更) ...
#     pass # このルートは使わないか、別の用途にする

# ★ここまでPayPay API関連の新しいエンドポイントを追加


# (reservation_number, clear_cart, back_to_home_and_clear_cart, update_cart_item, delete_cart_item は変更なし)

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

@users_order_bp.route('/update_cart_item', methods=['POST'])
@login_required
def update_cart_item():
    """カート内の商品の数量を更新する"""
    if 'current_store_id' not in session:
        return redirect(url_for('users_home.home'))

    try:
        menu_id_str = request.form['menu_id']
        # 数量が1未満の場合は削除として扱う
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
            # 数量が0以下の場合は商品を削除
            del carts[store_id_str][menu_id_str]
            flash("商品をカートから削除しました。")
        
        session['carts'] = carts
        session.modified = True
    
    return redirect(url_for('users_order.cart_confirmation'))


@users_order_bp.route('/delete_cart_item', methods=['POST'])
@login_required
def delete_cart_item():
    """カートから商品を削除する"""
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