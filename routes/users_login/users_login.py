# routes/general/explamation.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
import sqlite3
from werkzeug.security import generate_password_hash
import os

users_login_bp = Blueprint('users_login', __name__, url_prefix='/users_login')

@users_login_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash("ユーザー名とパスワードを入力してください")
            return render_template('users_login/login.html')

        # データベースからユーザー情報を取得
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users_table WHERE u_name = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user:
            db_username = user[1]  # u_name
            db_password_hash = user[3]  # password_hash（列順はテーブルにより異なる）

            if check_password_hash(db_password_hash, password):
                # ログイン成功：セッションに記録してリダイレクト
                session['username'] = db_username
                flash("ログインに成功しました")
                return render_template('users_home/home.html')

        flash("ユーザー名またはパスワードが間違っています")
        return render_template('users_login/login.html')

    # GETリクエスト時
    return render_template('users_login/login.html')


@users_login_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # フォームからデータ取得
        username = request.form.get('u_name')
        email = request.form.get('email')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        # 入力チェック
        if not username or not email or not password1 or not password2:
            flash("すべての項目を入力してください")
            return render_template('registration.html')

        if password1 != password2:
            flash("パスワードが一致しません")
            return render_template('registration.html')

        # パスワードをハッシュ化
        password_hash = generate_password_hash(password1)

        try:
            # データベース接続
            db_path = os.path.join(os.path.dirname(__file__), '..', 'app.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # データ挿入
            cursor.execute("""
                INSERT INTO users_table (u_name, email, password_hash)
                VALUES (?, ?, ?)
            """, (username, email, password_hash))

            conn.commit()
            conn.close()

            flash("登録が完了しました")
            return render_template('users_login/login.html')

        except sqlite3.IntegrityError:
            flash("このメールアドレスはすでに使用されています")
            return render_template('users_login/signup.html')

        except Exception as e:
            flash(f"エラーが発生しました: {e}")
            return render_template('users_login/signup.html')

    # GETリクエスト時
    return render_template('users_login/signup.html')


