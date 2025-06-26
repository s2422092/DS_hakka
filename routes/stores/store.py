from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash
import sqlite3
from geopy.geocoders import Nominatim

store_bp = Blueprint('store', __name__, url_prefix='/store')


@store_bp.route('/store_registration', methods=['GET', 'POST'])
def store_registration():
    if request.method == 'POST':
        store_info = {
            'store_name': request.form.get('store_name'),
            'email': request.form.get('email'),
            'password': request.form.get('password'),
            'location': request.form.get('location'),
            'representative': request.form.get('representative'),
            'weekday_open': request.form.get('weekday_open'),
            'weekday_close': request.form.get('weekday_close'),
            'weekend_open': request.form.get('weekend_open'),
            'weekend_close': request.form.get('weekend_close'),
            'weekend_closed': request.form.get('weekend_closed', '0')
        }
        session['store_info'] = store_info
        return redirect(url_for('store.info_confirmed'))

    return render_template('stores/store_registration.html')


@store_bp.route('/info_confirmed', methods=['GET'])
def info_confirmed():
    store_info = session.get('store_info')
    if not store_info:
        flash("セッションが切れています")
        return redirect(url_for('store.store_registration'))

    return render_template('stores/info_confirmed.html', store=store_info)


@store_bp.route('/registration_complete', methods=['POST'])
def registration_complete():
    store_info = session.get('store_info')
    if not store_info:
        flash("セッションが切れています。もう一度入力してください。")
        return redirect(url_for('store.store_registration'))

    # 営業時間説明文
    weekend_info = "休業" if store_info['weekend_closed'] == '1' else f"{store_info['weekend_open']}〜{store_info['weekend_close']}"
    description = f"月〜金: {store_info['weekday_open']}〜{store_info['weekday_close']}, 土日祝: {weekend_info}"

    # 緯度経度取得
    geolocator = Nominatim(user_agent="store_locator")
    try:
        location_result = geolocator.geocode(store_info['location'], timeout=10)
        latitude = location_result.latitude if location_result else None
        longitude = location_result.longitude if location_result else None
    except:
        latitude = longitude = None

    try:
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()

        # store テーブルに挿入
        cursor.execute("""
            INSERT INTO store (store_name, email, password, location, representative, description)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            store_info['store_name'],
            store_info['email'],
            generate_password_hash(store_info['password']),
            store_info['location'],
            store_info['representative'],
            description
        ))
        store_id = cursor.lastrowid

        # locations テーブルに挿入
        if latitude and longitude:
            cursor.execute("""
                INSERT INTO locations (location_title, travel_data_id, latitude, longitude)
                VALUES (?, ?, ?, ?)
            """, (store_info['location'], store_id, latitude, longitude))

        conn.commit()
        conn.close()

        flash("店舗情報を登録しました")
        session.pop('store_info', None)

    except sqlite3.IntegrityError:
        flash("このメールアドレスはすでに登録されています")
        return redirect(url_for('store.store_registration'))

    return render_template('stores/registration_complete.html')
