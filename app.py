from flask import Flask
from .routes.general.explamation import explamation_bp

app = Flask(__name__, template_folder='template')  # ← ここがポイント

app.secret_key = 'your_secret_key'

# Blueprintの登録

app.register_blueprint(explamation_bp)

if __name__ == '__main__':
    app.run(debug=True, port=5004)  # デバッグモードでポート5000で実
