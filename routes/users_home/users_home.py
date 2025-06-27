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
    if 'user_id' not in session:
        flash("ログインしてください")
        return redirect(url_for('users_login.login'))

    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.store_name, s.description, l.latitude, l.longitude
        FROM store s
        LEFT JOIN locations l ON s.store_id = l.travel_data_id
    """)
    stores = [
        {
            'name': row[0],
            'description': row[1],
            'latitude': row[2],
            'longitude': row[3]
        } for row in cursor.fetchall()
    ]
    conn.close()
    return render_template('users_home/home.html', stores=stores, u_name=session.get('u_name', 'ゲスト'))

@users_home_bp.route('/map_shop')
def map_shop():
    if 'user_id' not in session:
        flash("ログインしてください")
        return redirect(url_for('users_login.login'))

    u_name = session.get('u_name', 'ゲスト')
    return render_template('users_home/map_shop.html', u_name=u_name)  # ← locations を渡さない



@users_home_bp.route('/payment_history')
def payment_history():
    if 'user_id' not in session:
        flash("ログインしてください")
        return redirect(url_for('users_login.login'))
    u_name = session.get('u_name', 'ゲスト')
    return render_template('users_home/payment_history.html', u_name=u_name)
