import requests
import json
import uuid

class PayPayClient:
    def __init__(self, api_key, api_secret, merchant_id):
        self.api_key = api_key
        self.api_secret = api_secret
        self.merchant_id = merchant_id
        self.base_url = "https://stg-api.sandbox.paypay.ne.jp/v2"  # サンドボックス用URL

    def create_payment_url(self, amount, order_id, redirect_url):
        url = f"{self.base_url}/payments"

        headers = {
            "Content-Type": "application/json",
            "X-Api-Key": self.api_key
        }

        payload = {
            "merchantPaymentId": order_id,
            "amount": {
                "amount": int(amount),  # 円単位（例：100 = ¥100）
                "currency": "JPY"
            },
            "codeType": "ORDER_QR",  # 固定でOK
            "redirectUrl": redirect_url,
            "orderDescription": "モバイルオーダーの支払い",
            "isAuthorization": False  # 即時支払い（オーソリでない）
        }

        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            return response.json()
        except Exception as e:
            print("API通信エラー:", e)
            return None
