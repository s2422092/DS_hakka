# paypay/__init__.py

from flask import Flask

def create_app():
    app = Flask(__name__)
    
    # 各 Blueprint をインポート
    from routes.general.explamation import general_bp

    # Blueprint を登録
    app.register_blueprint(general_bp)

    return app
