# __init__.py （DS_HAKKAの直下にある前提）
from flask import Flask

def create_app():
    app = Flask(__name__)
    
    # ルートの登録
    from routes.general.explamation import general_bp
    app.register_blueprint(general_bp)

    return app
