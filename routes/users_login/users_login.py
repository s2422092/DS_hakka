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
            session['id'] = user[0]
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
        password1 = request.form.get('password1')  # ✅ HTMLと一致
        password2 = request.form.get('password2')  # ✅ HTMLと一致



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
# メールアドレス入力ページ
import logging  # ログを記録するためのモジュール

@users_login_bp.route('/re_enrollment', methods=['GET', 'POST'])
def re_enrollment():
    if request.method == 'POST':
        email = request.form.get('email')

        # 入力チェック
        if not email:
            flash("メールアドレスを入力してください", "error")
            return render_template('users_login/re_enrollment.html')

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            # メールアドレスに基づくデータを取得
            cursor.execute("SELECT u_name FROM users_table WHERE email = ?", (email,))
            user = cursor.fetchone()
            conn.close()

            if user:
                # メールアドレスが存在する場合、セッションに保存してパスワード変更ページへリダイレクト
                session['email'] = email  # セッションに登録したメールアドレスを保存
                flash("メールアドレスが認証されました。パスワード変更画面へ移動します。", "success")
                return redirect(url_for('users_login.password_input'))  # パスワード変更ページに移動
                
            else:
                # メールアドレスが存在しない場合
                flash("このメールアドレスは登録されていません", "error")
                return render_template('users_login/re_enrollment.html')

        except Exception as ex:
            logging.error(f"エラー発生: {ex}")  # ログにエラーを記録
            flash("システムエラーが発生しました。後ほどお試しください。", "error")
            return render_template('users_login/re_enrollment.html')

    return render_template('users_login/re_enrollment.html')
#登録されたメールアドレスならパスワード変更画面へ移動させる
@users_login_bp.route('/password_input', methods=['GET', 'POST'])
def password_input():
    if request.method == 'POST':
        # セッションからメールアドレスを取得
        email = session.get('email')

        # セッションが無効な場合の処理
        if not email:
            flash("セッションが切れています。最初からやり直してください。", "error")
            return redirect(url_for('users_login.re_enrollment'))

        # フォームからパスワードの入力を取得
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        # 入力チェック
        if not password1 or not password2:
            flash("すべての項目を入力してください。", "error")
            return render_template('users_login/password_input.html')

        if password1 != password2:
            flash("入力されたパスワードが一致しません。", "error")
            return render_template('users_login/password_input.html')

        # パスワードをハッシュ化
        password_hash = generate_password_hash(password1)

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            # DEBUG: 確認のため SELECT を実行
            cursor.execute("SELECT email FROM users_table WHERE email = ?", (email,))
            existing_user = cursor.fetchone()
            if not existing_user:
                flash("指定されたメールアドレスのユーザーが見つかりません。", "error")
                logging.warning(f"パスワード変更に失敗しました。該当するメールアドレスが存在しません: {email}")
                return render_template('users_login/password_input.html')
            else:
                logging.info(f"メールアドレスがデータベースで確認されました: {email}")

            # パスワードを更新
            cursor.execute("""
                UPDATE users_table
                SET password_hash = ?
                WHERE email = ?
            """, (password_hash, email))

            # 更新処理が成功したか確認
            if cursor.rowcount > 0:  # `rowcount` は更新された行数を返します
                conn.commit()
                flash("パスワードが正常に変更されました。ログインしてください。", "success")
                logging.info(f"ユーザー {email} のパスワードが正常に変更されました。")
                return redirect(url_for('users_login.login'))
            else:
                flash("パスワードの変更に失敗しました。もう一度お試しください。", "error")
                logging.warning(f"ユーザー {email} のパスワード変更がデータベースで確認できませんでした。")
                return render_template('users_login/password_input.html')

        except sqlite3.DatabaseError as db_err:
            # データベース関連のエラー記録
            logging.error(f"データベースエラー発生: {db_err}")
            flash("データベースエラーが発生しました。後ほどお試しください。", "error")
            return render_template('users_login/password_input.html')

        except Exception as ex:
            # 予期せぬエラー記録
            logging.error(f"予期せぬエラー発生: {ex}")
            flash("システムエラーが発生しました。後ほどお試しください。", "error")
            return render_template('users_login/password_input.html')

        finally:
            conn.close()

    # GETメソッドの場合の処理
    return render_template('users_login/password_input.html')