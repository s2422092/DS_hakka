from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
import sqlite3
import os
import logging

users_login_bp = Blueprint(
    'users_login', __name__,
    template_folder='../../templates/users_login',
    url_prefix='/users_login'
)

# --- データベース接続ヘルパー ---
def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'app.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# --- ログインページ ---
@users_login_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['u_name']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users_table WHERE u_name = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        # パスワードは平文で比較
        if user and user['password'] == password:
            session['id'] = user['id']
            session['u_name'] = user['u_name']
            flash("ログインに成功しました", "success")
            return redirect(url_for('users_home.home'))
        else:
            flash("ユーザー名またはパスワードが正しくありません", "error")
            return render_template('login.html')

    return render_template('login.html')


# --- 新規登録ページ ---
@users_login_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        u_name = request.form.get('u_name')
        email = request.form.get('email')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        if not all([u_name, email, password1, password2]):
            flash("すべての項目を入力してください", "error")
            return render_template('signup.html')

        if password1 != password2:
            flash("パスワードが一致しません", "error")
            return render_template('signup.html')

        # パスワードは平文のまま保存
        password = password1

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users_table (u_name, email, password) VALUES (?, ?, ?)",
                (u_name, email, password)
            )
            conn.commit()
            conn.close()

            flash("登録が完了しました。ログインしてください。", "success")
            return redirect(url_for('users_login.login'))

        except sqlite3.IntegrityError:
            flash("このメールアドレスはすでに使用されています", "error")
            return render_template('signup.html')
        except Exception as e:
            logging.error(f"サインアップエラー: {e}")
            flash("予期せぬエラーが発生しました。管理者にお問い合わせください。", "error")
            return render_template('signup.html')

    return render_template('signup.html')

# --- パスワード再設定: メールアドレス入力ページ ---
@users_login_bp.route('/re_enrollment', methods=['GET', 'POST'])
def re_enrollment():
    if request.method == 'POST':
        email = request.form.get('email')

        if not email:
            flash("メールアドレスを入力してください", "error")
            return render_template('re_enrollment.html')

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users_table WHERE email = ?", (email,))
            user = cursor.fetchone()
            conn.close()

            if user:
                session['reset_email'] = email
                flash("メールアドレスが確認できました。新しいパスワードを設定してください。", "info")
                return redirect(url_for('users_login.password_input'))
            else:
                flash("このメールアドレスは登録されていません", "error")
                return render_template('re_enrollment.html')

        except Exception as e:
            logging.error(f"メールアドレス確認エラー: {e}")
            flash("システムエラーが発生しました。後ほどお試しください。", "error")
            return render_template('re_enrollment.html')

    return render_template('re_enrollment.html')

# --- パスワード再設定: 新パスワード入力ページ ---
@users_login_bp.route('/password_input', methods=['GET', 'POST'])
def password_input():
    if 'reset_email' not in session:
        flash("有効なセッションがありません。もう一度メールアドレスを入力してください。", "error")
        return redirect(url_for('users_login.re_enrollment'))

    if request.method == 'POST':
        email = session.get('reset_email')
        password_one = request.form.get('password_one')
        password_two = request.form.get('password_two')

        if not all([password_one, password_two]):
            flash("すべての項目を入力してください。", "error")
            return render_template('password_input.html')

        if password_one != password_two:
            flash("入力されたパスワードが一致しません。", "error")
            return render_template('password_input.html')

        # 平文で保存
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users_table SET password = ? WHERE email = ?",
                (password_one, email)
            )
            conn.commit()

            if cursor.rowcount > 0:
                flash("パスワードが正常に変更されました。ログインしてください。", "success")
                session.pop('reset_email', None)
                conn.close()
                return redirect(url_for('users_login.login'))
            else:
                conn.close()
                flash("パスワードの更新に失敗しました。再度お試しください。", "error")
                return render_template('password_input.html')

        except sqlite3.Error as e:
            logging.error(f"パスワード更新DBエラー: {e}")
            flash("データベースエラーが発生しました。", "error")
            return render_template('password_input.html')

    return render_template('password_input.html')
