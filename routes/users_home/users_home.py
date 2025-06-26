from flask import Blueprint, render_template, session, redirect, url_for, flash

# Blueprint作成
users_home_bp = Blueprint('users_home', __name__, url_prefix='/users_home')

@users_home_bp.route('/home')
def home():
    # ✅ ログインしているか確認（sessionにuser_idがあるか）
    if 'user_id' not in session:
        flash("ログインしてください")
        return redirect(url_for('users_login.login'))  # ログインページにリダイレクト

    username = session.get('username', 'ゲスト')  # セッションからユーザー名取得（任意）
    return render_template('users_home/home.html', username=username)
