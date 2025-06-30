from flask import Blueprint, render_template, request, redirect, url_for, flash
from .paypay_client import PayPayClient
import time
# --- ▼▼▼ あなたが取得したサンドボックスのキーに書き換えてください ▼▼▼ ---
TEST_API_KEY = "a_Al3djIsQo4_fd3q"
TEST_API_SECRET = "iAclVPnwJm1W9ZNVnqycTXtJzcqStIew9P1g0RW508c="
TEST_MERCHANT_ID = "933772843478294528"
# --- ▲▲▲ -------------------------------------------------- ▲▲▲ ---
# PayPayクライアントを初期化
paypay_client = PayPayClient(TEST_API_KEY, TEST_API_SECRET, TEST_MERCHANT_ID)
# Blueprintを定義
stores_bp = Blueprint('stores', __name__, url_prefix='/stores')
# 注文ページ表示
@stores_bp.route('/order')
def order_page():
    return render_template('order_page.html')
# 決済作成のルート
@stores_bp.route('/create-payment', methods=['POST'])
def create_payment():
    amount = request.form.get('amount')
    order_id = "MY_ORDER_" + str(int(time.time()))
    # 決済完了後に戻ってくる、自分のサイトのURLを組み立てる
    completion_url = url_for('stores.order_complete', _external=True)
    # PayPayクライアントを使い、本物の決済用URLを生成してもらう
    response = paypay_client.create_payment_url(amount, order_id, completion_url)
    # PayPayからの応答をチェック
    if response and response.get('resultInfo', {}).get('code') == 'SUCCESS':
        # 成功したら、PayPayが発行した本物の決済URLにユーザーを移動させる
        payment_url = response['data']['url']
        return redirect(payment_url)

    else:
        # 失敗したら、エラーメッセージを表示して注文ページに戻る
        error_message = response.get('resultInfo', {}).get('message', '不明なエラー') if response else "API接続エラー"
        flash(f'決済の作成に失敗しました: {error_message}'
        , 'error')
        return redirect(url_for('stores.order_page'))


# 決済完了ページ
@stores_bp.route('/complete')
def order_complete():
    # PayPayの画面から戻ってきたときにメッセージを表示
    flash('PayPayでの支払いが正常に完了しました！', 'success')
    return render_template('order_complete.html')