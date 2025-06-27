# # routes/general/explamation.py
# from flask import Blueprint, render_template

# stores_detail_bp = Blueprint('stores_detail', __name__, url_prefix='/stores_detail')

# @stores_detail_bp.route('/menu_check')
# def menu_check():
#     return render_template('stores_detail/menu_check.html')

# @stores_detail_bp.route('/menu_registration')
# def menu_registration():
#     return render_template('stores_detail/menu_registration.html')

# @stores_detail_bp.route('/order_list')
# def order_list():
#     return render_template('stores_detail/order_list.html')

# @stores_detail_bp.route('/procedure')
# def procedure():
#     return render_template('stores_detail/procedure.html')

# @stores_detail_bp.route('/store_home')
# def store_home():
#     return render_template('stores_detail/store_home.html')

# routes/stores_detail.py

# routes/stores_detail.py

# routes/stores_detail.py

from flask import Blueprint, render_template, request, redirect, url_for

# Blueprintを定義
# url_prefixは、これらのページのURLがすべて /stores から始まることを意味します
stores_detail_bp = Blueprint('stores_detail', __name__, url_prefix='/stores')

# --- 各ページへのルート（道案内）を定義 ---

# /stores/home にアクセスされた時に呼ばれる
@stores_detail_bp.route('/home')
def store_home():
    # templates/stores_detail/store_home.html を表示
    return render_template('stores_detail/store_home.html')

# /stores/menu-registration にアクセスされた時に呼ばれる
@stores_detail_bp.route('/menu-registration', methods=['GET', 'POST'])
def menu_registration():
    # もしフォームが送信されたら
    if request.method == 'POST':
        # ここでフォームから送られたデータを受け取り、DBに保存する処理を書く
        # 例：
        menu_name = request.form.get('menu_name')
        print(f"新しいメニューが登録されました：{menu_name}")
        
        # 登録後はメニュー確認ページなどにリダイレクト（自動で移動）
        return redirect(url_for('stores_detail.menu_check'))

    # 通常のアクセスなら、メニュー登録ページを表示
    # templates/stores_detail/menu_registration.html を表示
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