from flask import Flask
from paypay.routes.general.explamation import explamation_bp  # ← パス修正に注意

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'your_secret_key'

# Blueprint登録
app.register_blueprint(explamation_bp)

if __name__ == '__main__':
    app.run(debug=True, port=5003)
