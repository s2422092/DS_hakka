from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import sqlite3
import csv
from werkzeug.utils import secure_filename
import os # ファイルパス操作のためにosモジュールをインポート

stores_detail_bp = Blueprint('stores_detail', __name__, url_prefix='/stores')

# データベース接続をヘルパー関数として定義
def get_db_connection():
    # app.dbのパスを適切に設定してください。プロジェクトのルートディレクトリにあると仮定します。
    # 例: os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'app.db')
    # または、アプリの起動スクリプトで設定された絶対パスを使用する
    conn = sqlite3.connect('app.db') # このパスを環境に合わせて調整してください
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

    if request.method == 'POST':
        # ファイルがリクエストに含まれているかチェック
        if 'csv_file' not in request.files:
            flash('ファイルが選択されていません', 'error')
            return redirect(request.url)

        file = request.files['csv_file']

        # ファイル名が空かどうかチェック
        if file.filename == '':
            flash('ファイルが選択されていません', 'error')
            return redirect(request.url)

        # ファイルがCSVファイルかどうかをチェック
        if file and file.filename.endswith('.csv'):
            filename = secure_filename(file.filename)
            # ファイルを一時的に保存せず、直接読み込む
            stream = file.stream.read().decode("utf-8")
            csv_data = csv.reader(stream.splitlines())

            # ヘッダー行をスキップし、期待されるカラム名を確認
            headers = next(csv_data)
            expected_headers = ['menu_name', 'category', 'price']
            if not all(h in headers for h in expected_headers):
                flash('CSVファイルのヘッダーが無効です。`menu_name`, `category`, `price`が必要です。', 'error')
                return redirect(request.url)

            store_id = session.get('store_id')
            if not store_id:
                flash("ストアIDが見つかりません。ログインし直してください。", 'error')
                return redirect(url_for('store.store_login'))

            conn = get_db_connection()
            cursor = conn.cursor()
            inserted_count = 0
            error_rows = []

            for i, row in enumerate(csv_data):
                # ヘッダーのインデックスを使ってデータを取得
                row_dict = dict(zip(headers, row))
                
                menu_name = row_dict.get('menu_name')
                category = row_dict.get('category')
                price_str = row_dict.get('price')

                # 必須フィールドのチェック
                if not menu_name or not price_str:
                    error_rows.append(f"行 {i+2}: 必須フィールド (menu_name, price) が不足しています。")
                    continue

                try:
                    price = int(price_str)
                except ValueError:
                    error_rows.append(f"行 {i+2}: 価格が無効な数値です ('{price_str}')。")
                    continue
                
                try:
                    cursor.execute(
                        "INSERT INTO menus (store_id, menu_name, category, price) VALUES (?, ?, ?, ?)",
                        (store_id, menu_name, category, price)
                    )
                    inserted_count += 1
                except sqlite3.Error as e:
                    error_rows.append(f"行 {i+2}: データベースエラーが発生しました - {e}")
                    # ロールバックするかどうかは、エラーの性質によるが、ここでは個別の行エラーとして記録
                    conn.rollback() # エラーが発生した場合はロールバック
                    # 必要であれば、処理を中止するか、次の行に進むかを判断

            conn.commit()
            conn.close()

            if inserted_count > 0:
                flash(f'{inserted_count}件のメニューを登録しました。', 'success')
            if error_rows:
                for err in error_rows:
                    flash(err, 'warning')
                if inserted_count == 0:
                    flash('メニューの登録に失敗しました。', 'error')

            return redirect(url_for('stores_detail.menu_check')) # 登録後、メニュー確認ページにリダイレクト

        else:
            flash('CSVファイルを選択してください。', 'error')

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
