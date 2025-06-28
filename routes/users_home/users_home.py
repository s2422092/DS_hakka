from flask import Blueprint, render_template, session, redirect, url_for, flash
import sqlite3

users_home_bp = Blueprint('users_home', __name__, url_prefix='/users_home')

@users_home_bp.route('/logout')
def logout():
    session.clear()
    flash("ログアウトしました")
    return redirect(url_for('general.explamation'))

@users_home_bp.route('/home')
def home():
    if 'id' not in session:
        flash("ログインしてください")
        return redirect(url_for('users_login.login'))

    # データベース接続
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT store_id, store_name, description
        FROM store
        ORDER BY store_id
    """)
    stores = [
        {
            'id': row[0],
            'name': row[1],
            'description': row[2],
        } for row in cursor.fetchall()
    ]
    conn.close()

    return render_template('users_home/home.html', stores=stores, u_name=session.get('u_name', 'ゲスト'))

@users_home_bp.route('/map_shop')
def map_shop():
    if 'id' not in session:
        flash("ログインしてください")
        return redirect(url_for('users_login.login'))

    # データベース接続
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()

    # store テーブルと locations テーブルを JOIN
    cursor.execute("""
        SELECT s.store_id, s.store_name, s.description,
               s.email, s.representative,
               l.latitude, l.longitude
        FROM store s
        JOIN locations l ON s.store_id = l.travel_data_id
        ORDER BY s.store_id
    """)

    stores = stores = [
    {
        'id': row[0],  # ←ここを 'id' に変更
        'store_name': row[1],
        'description': row[2],
        'email': row[3],
        'representative': row[4],
        'lat': row[5],
        'lng': row[6]
    } for row in cursor.fetchall()
]

    conn.close()

    u_name = session.get('u_name', 'ゲスト')

    return render_template('users_home/map_shop.html', stores=stores, u_name=u_name)


@users_home_bp.route('/payment_history')
def payment_history():
    if 'id' not in session:
        flash("ログインしてください")
        return redirect(url_for('users_login.login'))
    u_name = session.get('u_name', 'ゲスト')
    return render_template('users_home/payment_history.html', u_name=u_name)

@users_home_bp.route('/users_data')
def users_data():
    # セッションチェック
    if 'id' not in session:
        flash("ログインしてください")
        return redirect(url_for('users_login.login'))

    u_name = session.get('u_name', 'ゲスト')

    # ユーザー情報をデータベースから取得
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u_name, email, created_at
        FROM users_table
        WHERE id = ?
    """, (session['id'],))  # セッションから取得したユーザーIDを使用
    user_data = cursor.fetchone()
    conn.close()

    # データが存在する場合に辞書として構築
    user = None
    if user_data:
        user = {
            'username': user_data[0],
            'email': user_data[1],
            'registration_date': user_data[2]
        }

    # 必要な情報をテンプレートに渡す
    return render_template(
        'users_home/users_data.html',
        user=user,  # 単一のユーザーデータを渡す
        u_name=u_name
    )