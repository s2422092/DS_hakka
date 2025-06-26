from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

users_login_bp = Blueprint('users_login', __name__, url_prefix='/users_login')


# ログインページ
@users_login_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['u_name']
        password = request.form['password']

    # DB接続してユーザー確認
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, u_name, password_hash FROM users_table WHERE u_name = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['u_name'] = user[1]
            flash("ログインに成功しました")
            return redirect(url_for('users_home.home'))  # ✅ ユーザーホームにリダイレクト
        else:
            flash("ユーザー名またはパスワードが正しくありません")
            return render_template('users_login/login.html')

    return render_template('users_login/login.html')


# 新規登録ページ
@users_login_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        u_name = request.form.get('u_name')
        email = request.form.get('email')
        password1 = request.form.get('password')
        password2 = request.form.get('confirm_password')

        # 入力チェック
        if not u_name or not email or not password1 or not password2:
            flash("すべての項目を入力してください")
            return render_template('users_login/signup.html')

        if password1 != password2:
            flash("パスワードが一致しません")
            return render_template('users_login/signup.html')

        password_hash = generate_password_hash(password1)

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users_table (u_name, email, password_hash)
                VALUES (?, ?, ?)
            """, (u_name, email, password_hash))
            conn.commit()
            conn.close()

            flash("登録が完了しました。ログインしてください。")
            return redirect(url_for('users_login.login'))

        except sqlite3.IntegrityError:
            flash("このメールアドレスはすでに使用されています")
            return render_template('users_login/signup.html')

        except Exception as e:
            flash(f"予期せぬエラーが発生しました: {e}")
            return render_template('users_login/signup.html')

    return render_template('users_login/signup.html')
