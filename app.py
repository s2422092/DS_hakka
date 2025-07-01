from __init__ import create_app
from flask_cors import CORS  # ← 追加

app = create_app()

# 🔒 セッションなどに必要なシークレットキーを設定
app.secret_key = 'your_secret_key_here'  # ← 好きなランダムな文字列でOK

CORS(app)  # ← 追加: 全ルートでCORSを許可

if __name__ == '__main__':
    print("アクセスURL: http://localhost:5003/general/explamation")
    app.run(debug=True, port=5003)
