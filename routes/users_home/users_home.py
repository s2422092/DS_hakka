from flask import Blueprint, render_template, session, redirect, url_for, flash

# Blueprint作成
users_home_bp = Blueprint('users_home', __name__, url_prefix='/users_home')

@users_home_bp.route('/logout')
def logout():
    # セッションをクリアしてログアウト
    session.clear()
    flash("ログアウトしました")
    return redirect(url_for('users_login.login'))

@users_home_bp.route('/home')
def home():
    # ✅ ログインしているか確認（sessionにuser_idがあるか）
    if 'user_id' not in session:
        flash("ログインしてください")
        return redirect(url_for('users_login.login'))  # ログインページにリダイレクト

    u_name = session.get('u_name', 'ゲスト')  # セッションからユーザー名取得（任意）
    return render_template('users_home/home.html', u_name=u_name)

@users_home_bp.route('/map_shop')
def map_shop():
    # ✅ ログインしているか確認（sessionにuser_idがあるか）
    if 'user_id' not in session:
        flash("ログインしてください")
        return redirect(url_for('users_login.login'))
    u_name = session.get('u_name', 'ゲスト')
    return render_template('users_home/map_shop.html', u_name=u_name)

@users_home_bp.route('/payment_history')
def payment_history():
    # ✅ ログインしているか確認（sessionにuser_idがあるか）
    if 'user_id' not in session:
        flash("ログインしてください")
        return redirect(url_for('users_login.login'))
    u_name = session.get('u_name', 'ゲスト')
    return render_template('users_home/payment_history.html', u_name=u_name)