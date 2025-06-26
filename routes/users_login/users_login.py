# routes/general/explamation.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
import os
import sqlite3
from werkzeug.security import generate_password_hash

users_login_bp = Blueprint('users_login', __name__, url_prefix='/users_login')

@users_login_bp.route('/login')
def login():
    return render_template('users_login/login.html')


@users_login_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # フォームからデータ取得
        username = request.form.get('username')
        email = request.form.get('email')
        password1 = request.form.get('password')
        password2 = request.form.get('confirm_password')

        # 入力チェック
        if not username or not email or not password1 or not password2:
            flash("すべての項目を入力してください")
            return render_template('users_login/signup.html')

        if password1 != password2:
            flash("パスワードが一致しません")
            return render_template('users_login/signup.html')

        # パスワードをハッシュ化
        password_hash = generate_password_hash(password1)

        try:
            # データベース接続
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            # データ挿入
            cursor.execute("""
                INSERT INTO users_table (u_name, email, password_hash)
                VALUES (?, ?, ?)
            """, (username, email, password_hash))

            conn.commit()
            conn.close()

            flash("登録が完了しました。ログインしてください。")
            return redirect(url_for('users_login.login'))

        except sqlite3.IntegrityError:
            flash("このメールアドレスはすでに使用されています")
            return render_template('users_login/signup.html')

        except Exception as e:
            flash(f"エラーが発生しました: {e}")
            return render_template('users_login/signup.html')

    # GETリクエスト時
    return render_template('users_login/signup.html')


