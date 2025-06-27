from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import sqlite3
import csv
from werkzeug.utils import secure_filename
import os

stores_detail_bp = Blueprint('stores_detail', __name__, url_prefix='/stores')

# データベース接続をヘルパー関数として定義
def get_db_connection():
    # ユーザーが指定した絶対パスを使用
    conn = sqlite3.connect('/Users/namboshunsuke/ds_hakka/DS_hakka/app.db')
    conn.row_factory = sqlite3.Row
    return conn

@stores_detail_bp.route('/store_home')
def store_home():
    if 'store_id' not in session:
        flash("ログインしてください")
        return redirect(url_for('store.store_login'))

    store_name = session.get('store_name', '未登録')
    return render_template('stores_detail/store_home.html', store_name=store_name)


@stores_detail_bp.route('/menu-registration', methods=['GET', 'POST'])
def menu_registration():
    if 'store_id' not in session:
        flash("ログインしてください")
        return redirect(url_for('store.store_login'))

    store_id = session.get('store_id')
    if not store_id:
        flash("ストアIDが見つかりません。ログインし直してください。", 'error')
        return redirect(url_for('store.store_login'))

    if request.method == 'POST':
        # CSVファイルアップロードの処理
        # HTMLのinput name="product_csv" に合わせる
        file = request.files.get('product_csv') 

        # ファイルが選択され、かつファイル名がある場合、CSVとして処理
        if file and file.filename != '': 
            if file.filename.endswith('.csv'):
                try:
                    # UTF-8 BOM付きの可能性も考慮してdecode
                    stream = file.stream.read().decode("utf-8-sig")
                except UnicodeDecodeError:
                    flash('CSVファイルの文字コードがUTF-8ではありません。UTF-8形式のCSVをアップロードしてください。', 'error')
                    return redirect(request.url)

                # CSVデータをDictReaderで読み込み
                csv_data = csv.DictReader(stream.splitlines())

                # CSVヘッダーの存在チェック
                csv_headers_set = set(csv_data.fieldnames if csv_data.fieldnames else []) 
                required_headers = {'menu_name', 'price'}

                if not required_headers.issubset(csv_headers_set):
                    missing_headers = required_headers - csv_headers_set
                    flash(f'CSVファイルのヘッダーが無効です。必須ヘッダーが不足しています: {", ".join(missing_headers)}', 'error')
                    return redirect(request.url)

                conn = get_db_connection()
                cursor = conn.cursor()
                inserted_count = 0
                error_rows = []

                # CSVの各行を処理し、データベースに挿入
                for i, row_dict in enumerate(csv_data):
                    menu_name = row_dict.get('menu_name')
                    # HTMLのdescriptionをcategoryとして扱うため、CSVのcategoryもそのままcategoryとして利用
                    category = row_dict.get('category', '')
                    price_str = row_dict.get('price')
                    soldout_str = row_dict.get('soldout', '0')

                    # 必須フィールドの存在チェック
                    if not menu_name or not price_str:
                        error_rows.append(f"行 {i+2}: 必須フィールド (menu_name, price) が不足しているか空です。")
                        continue

                    # 価格の型変換とバリデーション
                    try:
                        price = int(price_str)
                    except ValueError:
                        error_rows.append(f"行 {i+2}: 価格が無効な数値です ('{price_str}')。")
                        continue
                    
                    # soldoutの型変換とバリデーション
                    try:
                        soldout = int(soldout_str)
                        if soldout not in [0, 1]:
                            raise ValueError("0または1ではありません")
                    except ValueError:
                        error_rows.append(f"行 {i+2}: soldoutが無効な値です ('{soldout_str}')。0または1を入力してください。")
                        continue

                    # データベースへの挿入
                    try:
                        cursor.execute(
                            "INSERT INTO menus (store_id, menu_name, category, price, soldout) VALUES (?, ?, ?, ?, ?)",
                            (store_id, menu_name, category, price, soldout)
                        )
                        inserted_count += 1
                    except sqlite3.Error as e:
                        error_rows.append(f"行 {i+2}: データベースエラーが発生しました - {e}")
                
                conn.commit() # トランザクションをコミット
                conn.close()

                # 登録結果のフラッシュメッセージ
                if inserted_count > 0:
                    flash(f'{inserted_count}件のメニューを登録しました。', 'success')
                if error_rows:
                    for err in error_rows:
                        flash(err, 'warning')
                    if inserted_count == 0:
                        flash('メニューの登録に失敗しました。詳細を警告メッセージで確認してください。', 'error')
                
                return redirect(url_for('stores_detail.menu_check'))

            else:
                flash('CSVファイルを選択してください。', 'error')
                return redirect(request.url)

        # CSVファイルがアップロードされていない場合、手動入力を試みる
        else: 
            product_name = request.form.get('product_name')
            product_price_str = request.form.get('product_price')
            # 商品説明をcategoryカラムとして扱う
            product_description = request.form.get('product_description', '') 

            # 手動入力の必須フィールドチェック
            if product_name and product_price_str: 
                try:
                    product_price = int(product_price_str)
                except ValueError:
                    flash('値段が無効な数値です。', 'error')
                    return redirect(request.url)

                conn = get_db_connection()
                cursor = conn.cursor()
                try:
                    # データベースへの挿入 (soldoutはデフォルト0)
                    cursor.execute(
                        "INSERT INTO menus (store_id, menu_name, category, price, soldout) VALUES (?, ?, ?, ?, ?)",
                        (store_id, product_name, product_description, product_price, 0) 
                    )
                    conn.commit()
                    flash(f'メニュー「{product_name}」を登録しました。', 'success')
                    return redirect(url_for('stores_detail.menu_check'))
                except sqlite3.Error as e:
                    flash(f"メニューの登録中にデータベースエラーが発生しました: {e}", 'error')
                finally:
                    conn.close()
            else:
                flash('CSVファイルを選択するか、手動で商品名と値段を入力してください。', 'error')
                return redirect(request.url)

    return render_template('stores_detail/menu_registration.html')


@stores_detail_bp.route('/menu-check')
def menu_check():
    # ストアIDがセッションにない場合はログインページにリダイレクト
    if 'store_id' not in session:
        flash("ログインしてください")
        return redirect(url_for('store.store_login'))

    store_id = session.get('store_id')
    menus = []
    conn = None
    try:
        conn = get_db_connection()
        # 特定のstore_idに紐づくメニューのみを取得
        cursor = conn.execute("SELECT menu_id, menu_name, category, price, soldout FROM menus WHERE store_id = ?", (store_id,))
        menus = cursor.fetchall() # 結果をリストとして取得
    except sqlite3.Error as e:
        flash(f"メニューの取得中にエラーが発生しました: {e}", 'error')
    finally:
        if conn:
            conn.close()

    # menusはsqlite3.Rowオブジェクトのリストなので、辞書形式に変換してテンプレートに渡す
    menus_data = [dict(menu) for menu in menus]
    return render_template('stores_detail/menu_check.html', menus=menus_data)


@stores_detail_bp.route('/order-list')
def order_list():
    # この関数は変更なし
    return render_template('stores_detail/order_list.html')


@stores_detail_bp.route('/procedure')
def procedure():
    # この関数は変更なし
    return render_template('stores_detail/procedure.html')


@stores_detail_bp.route('/paypay_linking')
def paypay_linking():
    # この関数は変更なし
    return render_template('stores_detail/paypay_linking.html')

@stores_detail_bp.route('/store_info_page')
def store_info_page():
    # この関数は変更なし
    return render_template('stores_detail/store_info_page.html')
