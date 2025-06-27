from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import sqlite3

stores_detail_bp = Blueprint('stores_detail', __name__, url_prefix='/stores')


@stores_detail_bp.route('/store_home')
def store_home():
    if 'store_id' not in session:
        flash("ログインしてください")
        return redirect(url_for('store.store_login'))

    store_name = session.get('store_name', '未登録')
    return render_template('stores_detail/store_home.html', store_name=store_name)


@stores_detail_bp.route('/menu-registration', methods=['GET', 'POST'])
def menu_registration():
    # ログインチェック
    if 'store_id' not in session:
        flash("ログインしてください")
        return redirect(url_for('store.store_login'))

    return render_template('stores_detail/menu_registration.html')


@stores_detail_bp.route('/menu-check')
def menu_check():
    # ログインチェック
    if 'store_id' not in session:
        flash("ログインしてください")
        return redirect(url_for('store.store_login'))

    return render_template('stores_detail/menu_check.html')


@stores_detail_bp.route('/order-list')
def order_list():
    # ログインチェック
    if 'store_id' not in session:
        flash("ログインしてください")
        return redirect(url_for('store.store_login'))

    return render_template('stores_detail/order_list.html')


@stores_detail_bp.route('/procedure')
def procedure():
    # ログインチェック
    if 'store_id' not in session:
        flash("ログインしてください")
        return redirect(url_for('store.store_login'))

    return render_template('stores_detail/procedure.html')


@stores_detail_bp.route('/paypay_linking')
def paypay_linking():
    # ログインチェック
    if 'store_id' not in session:
        flash("ログインしてください")
        return redirect(url_for('store.store_login'))

    return render_template('stores_detail/paypay_linking.html')


@stores_detail_bp.route('/store_info')
def store_info():
    # ログインチェック
    if 'store_id' not in session:
        flash("ログインしてください")
        return redirect(url_for('store.store_login'))

    return render_template('stores_detail/store_info.html')


# 🔴 ログアウト機能追加
@stores_detail_bp.route('/logout')
def logout():
    session.pop('store_id', None)
    session.pop('store_name', None)
    flash("ログアウトしました")
    return redirect(url_for('store.store_login'))
