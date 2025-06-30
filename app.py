# app.py

# dotenvをインポートし、環境変数を読み込む
from dotenv import load_dotenv
load_dotenv() # ★これが必要★

from __init__ import create_app
import os # 環境変数を取得するためにosモジュールもインポート

app = create_app()

# SECRET_KEYは、環境変数から取得するのがベストプラクティスです。
# ただし、今回は直接書き込む例を示します。
# 開発環境であれば直接記述でも構いませんが、本番環境では環境変数から取得することを強く推奨します。
# 例: app.secret_key = os.environ.get('SECRET_KEY', 'your_fallback_secret_key_if_env_not_set')
app.secret_key = 'your_secret_key_here'  # ← 好きなランダムな文字列でOK

# ここにCORSの設定を追加する場合もありますが、
# もし__init__.pyのcreate_app関数内でCORSが初期化されているなら不要です。
# 例: from flask_cors import CORS; CORS(app)

if __name__ == '__main__':
    # FRONTEND_BASE_URLの環境変数とポートが一致していることを確認
    # ここで表示するURLは、.envで設定したFRONTEND_BASE_URLと同じであるべきです。
    frontend_base_url = os.environ.get("FRONTEND_BASE_URL", "http://127.0.0.1:5003")
    print(f"アクセスURL: {frontend_base_url}/general/explanation")
    # debugモードは、.envの_DEBUG設定から取得するのが望ましい
    _DEBUG = os.environ.get("_DEBUG", "False").lower() == "true"
    app.run(debug=_DEBUG, port=5003) # portは.envのFRONTEND_BASE_URLと一致させる