
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import sqlite3

# Blueprintを定義
# url_prefixは、これらのページのURLがすべて /stores から始まることを意味します
stores_detail_bp = Blueprint('stores_detail', __name__, url_prefix='/stores')

# --- 各ページへのルート（道案内）を定義 ---

# /stores/home にアクセスされた時に呼ばれる
@stores_detail_bp.route('/store_home')
def store_home():
    if 'store_id' not in session:
        flash("ログインしてください")
        return redirect(url_for('store.store_login'))

    store_name = session.get('store_name', '未登録')
    return render_template('stores_detail/store_home.html', store_name=store_name)


# /stores/menu-registration にアクセスされた時に呼ばれる
@stores_detail_bp.route('/menu-registration', methods=['GET', 'POST'])
def menu_registration():
    return render_template('stores_detail/menu_registration.html')


# /stores/menu-check にアクセスされた時に呼ばれる
@stores_detail_bp.route('/menu-check')
def menu_check():
    # templates/stores_detail/menu_check.html を表示
    return render_template('stores_detail/menu_check.html')

# /stores/order-list にアクセスされた時に呼ばれる
@stores_detail_bp.route('/order-list')
def order_list():
    # templates/stores_detail/order_list.html を表示
    return render_template('stores_detail/order_list.html')

# /stores/procedure にアクセスされた時に呼ばれる
@stores_detail_bp.route('/procedure')
def procedure():
    # templates/stores_detail/procedure.html を表示
    return render_template('stores_detail/procedure.html')




@stores_detail_bp.route('/store_info_page')
def store_info_page():
    # templates/stores_detail/store_info_page.html を表示
    return render_template('stores_detail/store_info_page.html')
