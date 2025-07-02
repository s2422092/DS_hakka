from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
import sqlite3
import csv
from werkzeug.utils import secure_filename
import os
from functools import wraps
import io
import json
import pandas as pd


stores_detail_bp = Blueprint('stores_detail', __name__, url_prefix='/stores')

def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'app.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@stores_detail_bp.route('/store_home')
def store_home():
    if 'store_id' not in session:
        flash("ログインしてください")
        return redirect(url_for('store.store_login'))

    store_name = session.get('store_name', 'ゲスト')
    return render_template('stores_detail/store_home.html', store_name=store_name)


@stores_detail_bp.route('/store_home_menu')
def store_home_menu():
    if 'store_id' not in session:
        flash("ログインしてください")
        return redirect(url_for('store.store_login'))

    store_name = session.get('store_name', 'ゲスト')
    store_id = session.get('store_id')

    # 商品一覧を取得
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT menu_name, price, category, soldout FROM menus WHERE store_id = ?", (store_id,))
    menus = cur.fetchall()
    conn.close()

    return render_template('stores_detail/store_home_menu.html', store_name=store_name , menus=menus)


# --- ヘルパー関数 ---
def parse_menu_file(file):
    """アップロードされたCSVまたはExcelファイルを解析して、辞書のリストを返す"""
    filename = file.filename
    menus = []
    
    try:
        if filename.endswith('.csv'):
            stream = io.StringIO(file.stream.read().decode("utf-8-sig"))
            csv_data = csv.DictReader(stream)
            required_headers = {'menu_name', 'price'}
            if not required_headers.issubset(set(csv_data.fieldnames or [])):
                return None, f'CSVヘッダーが無効です。必須ヘッダー({", ".join(required_headers)})がありません。'
            menus = list(csv_data)

        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file.stream, dtype=str) # 全て文字列として読み込む
            required_headers = {'menu_name', 'price'}
            if not required_headers.issubset(set(df.columns)):
                 return None, f'Excelヘッダーが無効です。必須ヘッダー({", ".join(required_headers)})がありません。'
            df['category'] = df['category'].fillna('')
            df['soldout'] = df['soldout'].fillna('0')
            menus = df.to_dict('records')
        else:
            return None, '対応していないファイル形式です。.csvまたは.xlsxファイルをアップロードしてください。'
        
        return menus, None
    except Exception as e:
        return None, f"ファイルの読み込み中にエラーが発生しました: {e}"


def validate_menu_data(menus_data):
    """メニューデータのバリデーションを行う"""
    validated_menus = []
    errors = []
    for i, row in enumerate(menus_data):
        row_num_str = f"行 {i+2}" if len(menus_data) > 1 else "手動入力"
        
        menu_name = row.get('menu_name')
        price_str = str(row.get('price', '')).strip()
        soldout_str = str(row.get('soldout', '0')).strip()
        category = row.get('category', '')

        if not menu_name or not price_str:
            errors.append(f"{row_num_str}: 必須項目 (menu_name, price) が空です。")
            continue
        
        try:
            price = int(float(price_str))
            if price < 0:
                raise ValueError
        except (ValueError, TypeError):
            errors.append(f"{row_num_str}: 価格の値 ('{price_str}') が不正です。0以上の数値を入力してください。")
            continue

        try:
            soldout = int(float(soldout_str))
            if soldout not in [0, 1]:
                raise ValueError
        except (ValueError, TypeError):
            errors.append(f"{row_num_str}: 在庫の値 ('{soldout_str}') が不正です。0 (販売中) か 1 (売り切れ) で入力してください。")
            continue
        
        validated_menus.append({
            'menu_name': menu_name,
            'category': category,
            'price': price,
            'soldout': soldout
        })
    return validated_menus, errors


# --- ルート定義 ---

@stores_detail_bp.route('/download-template')
def download_template():
    """商品登録用のExcelテンプレートファイルを生成してダウンロードさせる"""
    try:
        # テンプレート用のデータフレームを作成
        template_data = {
            'menu_name': ['日替わり弁当', '唐揚げ単品', '緑茶'],
            'category': ['お弁当', '惣菜', 'ドリンク'],
            'price': [800, 350, 150],
            'soldout': [0, 0, 1] # 0: 販売中, 1: 売り切れ
        }
        df = pd.DataFrame(template_data)

        # Excelファイルをメモリ上で作成
        output = io.BytesIO()
        df.to_excel(output, index=False, sheet_name='メニュー')
        output.seek(0)

        # ファイルとして送信
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='menu_template.xlsx'
        )
    except Exception as e:
        flash(f"テンプレートファイルの生成中にエラーが発生しました: {e}", "error")
        return redirect(url_for('stores_detail.menu_registration'))


@stores_detail_bp.route('/menu-registration', methods=['GET'])
def menu_registration():
    if 'store_id' not in session:
        flash("ログインしてください", "warning")
        return redirect(url_for('store.store_login'))

    store_id = session['store_id']
    store_name = session.get('store_name', 'ゲスト')
    
    conn = get_db_connection()
    try:
        existing_menus = conn.execute(
            "SELECT menu_id, menu_name, category, price, soldout FROM menus WHERE store_id = ? ORDER BY menu_id DESC",
            (store_id,)
        ).fetchall()
    except sqlite3.Error as e:
        flash(f"メニューの読み込み中にエラーが発生しました: {e}", "error")
        existing_menus = []
    finally:
        conn.close()

    return render_template(
        'stores_detail/menu_registration.html',
        store_name=store_name,
        menus=[dict(row) for row in existing_menus]
    )


@stores_detail_bp.route('/menu-preview', methods=['POST'])
def menu_preview():
    if 'store_id' not in session:
        flash("ログインしてください", "warning")
        return redirect(url_for('store.store_login'))

    menus_to_check = []
    errors = []
    file = request.files.get('product_csv')

    # 1. ファイルアップロードの処理
    if file and file.filename:
        menus_data, file_error = parse_menu_file(file)
        if file_error:
            flash(file_error, 'error')
            return redirect(url_for('stores_detail.menu_registration'))
        menus_to_check, errors = validate_menu_data(menus_data)

    # 2. 手動入力の処理 (ファイルがない場合)
    else:
        product_name = request.form.get('product_name')
        product_price_str = request.form.get('product_price')

        if product_name or product_price_str:
            if not product_name or not product_price_str:
                flash('手動で入力する場合、商品名と値段の両方が必須です。', 'error')
                return redirect(url_for('stores_detail.menu_registration'))
            
            manual_data = [{
                'menu_name': product_name,
                'price': product_price_str,
                'category': request.form.get('product_description', ''),
                'soldout': '0'
            }]
            menus_to_check, errors = validate_menu_data(manual_data)
        
        # 3. ファイルも手動入力もない場合
        else:
            flash('登録するデータをアップロードするか、フォームに入力してください。', 'error')
            return redirect(url_for('stores_detail.menu_registration'))

    if errors:
        for error in errors:
            flash(error, 'warning')
        if not menus_to_check:
            flash('有効なデータがなかったため、プレビューできませんでした。', 'error')
            return redirect(url_for('stores_detail.menu_registration'))

    if not menus_to_check:
        flash('登録するデータがありません。', 'info')
        return redirect(url_for('stores_detail.menu_registration'))

    session['menus_to_confirm'] = menus_to_check
    return redirect(url_for('stores_detail.menu_check'))


@stores_detail_bp.route('/menu-check', methods=['GET'])
def menu_check():
    if 'store_id' not in session:
        flash("ログインしてください", "warning")
        return redirect(url_for('store.store_login'))
    
    menus_to_check = session.get('menus_to_confirm', [])
    if not menus_to_check:
        flash('確認するメニューがありません。登録画面からやり直してください。', 'info')
        return redirect(url_for('stores_detail.menu_registration'))

    store_name = session.get('store_name', 'ゲスト')
    return render_template(
        'stores_detail/menu_check.html',
        store_name=store_name,
        menus_to_check=menus_to_check
    )


@stores_detail_bp.route('/menu-finalize', methods=['POST'])
def menu_finalize():
    if 'store_id' not in session:
        flash("ログインしてください", "warning")
        return redirect(url_for('store.store_login'))


    store_id = session['store_id']
    
    menus_data_str = request.form.get('menus_data')
    if not menus_data_str:
        flash('登録データが見つかりませんでした。', 'error')
        return redirect(url_for('stores_detail.menu_registration'))
    
    try:
        menus_to_insert = json.loads(menus_data_str)
    except json.JSONDecodeError:
        flash('登録データの形式が不正です。', 'error')
        return redirect(url_for('stores_detail.menu_registration'))

    conn = get_db_connection()
    cursor = conn.cursor()
    inserted_count = 0
    try:
        for menu in menus_to_insert:
            cursor.execute(
                "INSERT INTO menus (store_id, menu_name, category, price, soldout) VALUES (?, ?, ?, ?, ?)",
                (store_id, menu['menu_name'], menu['category'], menu['price'], menu['soldout'])
            )
            inserted_count += 1
        conn.commit()
        flash(f'{inserted_count}件のメニューを登録しました。', 'success')
    except sqlite3.Error as e:
        conn.rollback()
        flash(f"データベースへの登録中にエラーが発生しました: {e}", "error")
    finally:
        conn.close()
        session.pop('menus_to_confirm', None)

    return redirect(url_for('stores_detail.menu_registration'))


@stores_detail_bp.route('/menu-delete/<int:menu_id>', methods=['POST'])
def menu_delete(menu_id):
    if 'store_id' not in session:
        flash("ログインしてください", "warning")
        return redirect(url_for('store.store_login'))
    
    store_id = session['store_id']
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM menus WHERE menu_id = ? AND store_id = ?", (menu_id, store_id))
        conn.commit()
        if cursor.rowcount > 0:
            flash("メニューを削除しました。", "success")
        else:
            flash("削除対象のメニューが見つからないか、権限がありません。", "error")
    except sqlite3.Error as e:
        flash(f"削除中にエラーが発生しました: {e}", "error")
    finally:
        conn.close()

    return redirect(url_for('stores_detail.menu_registration'))



@stores_detail_bp.route('/order-list')
def order_list():
    store_id = session.get('store_id')
    store_name = session.get('store_name', 'ゲスト')
    
    conn = get_db_connection()
    query = """
        SELECT
            o.order_id, o.datetime, o.total_amount, o.status,
            u.u_name, m.menu_name, oi.quantity, oi.price_at_order
        FROM orders AS o
        JOIN order_items AS oi ON o.order_id = oi.order_id
        JOIN menus AS m ON oi.menu_id = m.menu_id
        JOIN users_table AS u ON o.user_id = u.id
        WHERE o.store_id = ?
        ORDER BY o.datetime DESC;
    """
    orders_raw = conn.execute(query, (store_id,)).fetchall()
    conn.close()

    orders_dict = {}
    for row in orders_raw:
        order_id = row['order_id']
        if order_id not in orders_dict:
            orders_dict[order_id] = {
                'id': order_id, 'datetime': row['datetime'], 'status': row['status'],
                'user_name': row['u_name'], 'total_amount': row['total_amount'],
                'items_list': []
            }
        orders_dict[order_id]['items_list'].append({
            'name': row['menu_name'], 'quantity': row['quantity'], 'price': row['price_at_order']
        })
    
    orders_list = list(orders_dict.values())
    return render_template('stores_detail/order_list.html', orders=orders_list, store_name=store_name)


@stores_detail_bp.route('/procedure')
def procedure():
    if 'store_id' not in session:
        flash("ログインしてください")
        return redirect(url_for('store.store_login'))

    store_name = session.get('store_name', 'ゲスト')
    return render_template('stores_detail/procedure.html', store_name=store_name)


@stores_detail_bp.route('/paypay_linking')
def paypay_linking():
    if 'store_id' not in session:
        flash("ログインしてください")
        return redirect(url_for('store.store_login'))

    store_name = session.get('store_name', 'ゲスト')
    return render_template('stores_detail/paypay_linking.html', store_name=store_name)


@stores_detail_bp.route('/store_info')
def store_info():
    if 'store_id' not in session:
        flash("ログインしてください")
        return redirect(url_for('store.store_login'))

    store_name = session.get('store_name', 'ゲスト')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT store_name, email, location, representative, description, created_at FROM store WHERE store_id = ?", (session['store_id'],))
    store_data = cur.fetchone()
    conn.close()

    return render_template('stores_detail/store_info.html', store_name=store_name, store=store_data)

