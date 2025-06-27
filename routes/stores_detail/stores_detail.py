from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import sqlite3

# Blueprintを定義
# url_prefixは、これらのページのURLがすべて /stores から始まることを意味します
stores_detail_bp = Blueprint('stores_detail', __name__, url_prefix='/stores')

# --- 各ページへのルート（道案内）を定義 ---

# /stores/home にアクセスされた時に呼ばれる
@stores_detail_bp.route('/home')
def store_home():
    if 'store_id' not in session:
        flash("ログインしてください")
        return redirect(url_for('store.store_login')) # 'store'はログインBlueprintのエンドポイント名と仮定

    store_name = session.get('store_name', '未登録')
    # store_home.htmlから各ページへのリンクを生成するために、ここで各ルートのエンドポイント名を確認できます。
    return render_template('stores_detail/store_home.html', store_name=store_name)


# /stores/menu-registration にアクセスされた時に呼ばれる
@stores_detail_bp.route('/menu-registration', methods=['GET', 'POST'])
def menu_registration():
    if 'store_id' not in session: # セッションチェックを追加
        flash("ログインしてください")
        return redirect(url_for('store.store_login'))

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
    if 'store_id' not in session: # セッションチェックを追加
        flash("ログインしてください")
        return redirect(url_for('store.store_login'))
    # templates/stores_detail/menu_check.html を表示
    return render_template('stores_detail/menu_check.html')

# /stores/order-list にアクセスされた時に呼ばれる
@stores_detail_bp.route('/order-list')
def order_list():
    if 'store_id' not in session: # セッションチェックを追加
        flash("ログインしてください")
        return redirect(url_for('store.store_login'))
    # templates/stores_detail/order_list.html を表示
    return render_template('stores_detail/order_list.html')

# /stores/procedure にアクセスされた時に呼ばれる
@stores_detail_bp.route('/procedure')
def procedure():
    if 'store_id' not in session: # セッションチェックを追加
        flash("ログインしてください")
        return redirect(url_for('store.store_login'))
    # templates/stores_detail/procedure.html を表示
    return render_template('stores_detail/procedure.html')

