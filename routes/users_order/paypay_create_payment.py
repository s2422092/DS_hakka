from flask import Blueprint, request, redirect, url_for, flash, render_template
import time
import requests
import json

# --- PayPay API クライアントクラス ---
class PayPayClient:
    def __init__(self, api_key, api_secret, merchant_id):
        self.api_key = api_key
        self.api_secret = api_secret
        self.merchant_id = merchant_id
        self.base_url = "https://stg-api.sandbox.paypay.ne.jp/v2"  # サンドボックス環境

    def create_payment_url(self, amount, order_id, redirect_url):
        url = f"{self.base_url}/payments"
        headers = {
            "Content-Type": "application/json",
            "X-Api-Key": self.api_key
        }
        payload = {
            "merchantPaymentId": order_id,
            "amount": {
                "amount": int(amount),
                "currency": "JPY"
            },
            "codeType": "ORDER_QR",
            "redirectUrl": redirect_url,
            "orderDescription": "モバイルオーダーの支払い",
            "isAuthorization": False
        }

        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            return response.json()
        except Exception as e:
            print("API通信エラー:", e)
            return None

# --- Flask Blueprint の設定 ---
paypay_bp = Blueprint('users_order_paypay', __name__, url_prefix='/users_order/paypay')

# --- PayPay APIキー（テスト用） ---
TEST_API_KEY = "a_Al3djIsQo4_fd3q"
TEST_API_SECRET = "iAclVPnwJm1W9ZNVnqycTXtJzcqStIew9P1g0RW508c="
TEST_MERCHANT_ID = "933772843478294528"

paypay_client = PayPayClient(TEST_API_KEY, TEST_API_SECRET, TEST_MERCHANT_ID)

# --- 決済作成処理 ---
@paypay_bp.route('/create-payment', methods=['POST'])
def paypay_create_payment():
    amount = request.form.get('amount')
    if not amount:
        flash("金額が指定されていません。", "error")
        return redirect(url_for('users_order.order_confirm'))  # 実際のルートに応じて修正

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

# --- 決済完了画面 ---
@paypay_bp.route('/complete')
def paypay_complete():
    flash("PayPayでの支払いが正常に完了しました！", "success")
    return render_template('users_order/paypay_complete.html')
