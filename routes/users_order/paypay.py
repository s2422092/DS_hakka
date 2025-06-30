from flask import Blueprint, request, redirect, url_for, flash, session, render_template
import time
from lib.paypay_client import PayPayClient

paypay_bp = Blueprint('users_order_paypay', __name__, url_prefix='/users_order/paypay')

# ここは実際にPayPayから取得したサンドボックスキーに差し替えてください
TEST_API_KEY = "a_Al3djIsQo4_fd3q"
TEST_API_SECRET = "iAclVPnwJm1W9ZNVnqycTXtJzcqStIew9P1g0RW508c="
TEST_MERCHANT_ID = "933772843478294528"

paypay_client = PayPayClient(TEST_API_KEY, TEST_API_SECRET, TEST_MERCHANT_ID)

@paypay_bp.route('/create-payment', methods=['POST'])
def paypay_create_payment():
    amount = request.form.get('amount')
    if not amount:
        flash("金額が指定されていません。", "error")
        return redirect(url_for('users_order.order_confirm'))  # 適宜リダイレクト先を調整

    order_id = "ORDER_" + str(int(time.time()))

    completion_url = url_for('users_order_paypay.paypay_complete', _external=True)

    response = paypay_client.create_payment_url(amount, order_id, completion_url)

    if response and response.get('resultInfo', {}).get('code') == 'SUCCESS':
        payment_url = response['data']['url']
        return redirect(payment_url)
    else:
        error_message = response.get('resultInfo', {}).get('message', '不明なエラー') if response else "API接続エラー"
        flash(f"決済の作成に失敗しました: {error_message}", "error")
        return redirect(url_for('users_order.order_confirm'))


@paypay_bp.route('/complete')
def paypay_complete():
    flash("PayPayでの支払いが正常に完了しました！", "success")
    return render_template('users_order/paypay_complete.html')
