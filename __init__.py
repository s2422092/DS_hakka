from flask import Flask

def create_app():
    app = Flask(__name__)
    
    # Blueprintのインポート
    from routes.general.explamation import general_bp
    from routes.stores.store import store_bp 
    from routes.stores_detail.stores_detail import stores_detail_bp
    from routes.users_home.users_home import users_home_bp
    from routes.users_login.users_login import users_login_bp
    from routes.users_order.users_order import users_order_bp
    from routes.users_order.paypay_create_payment import paypay_bp

    # Blueprintの登録
    app.register_blueprint(general_bp)
    app.register_blueprint(store_bp)
    app.register_blueprint(stores_detail_bp)
    app.register_blueprint(users_home_bp)
    app.register_blueprint(users_login_bp)
    app.register_blueprint(users_order_bp)
    app.register_blueprint(paypay_bp)

    return app
