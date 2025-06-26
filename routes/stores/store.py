# routes/general/explamation.py
#from flask import Blueprint, render_template

#store_bp = Blueprint('store', __name__, url_prefix='/store')

#@store_bp.route('/store_registration')
#def store_registration():
#    return render_template('/stores/store_registration.html')
#@store_bp.route('/info_confirmed')
#def info_confirmed():
#    return render_template('/stores/info_confirmed.html')





from flask import Blueprint, render_template, request

store_bp = Blueprint('store', __name__, url_prefix='/store')

# 店舗登録フォームの表示
@store_bp.route('/store_registration')
def store_registration():
    return render_template('stores/store_registration.html')
# 入力確認ページ（POSTでフォームデータ受け取り）
@store_bp.route('/info_confirmed', methods=['POST'])
def info_confirmed():
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
        'weekend_closed': request.form.get('weekend_closed', '0')  # チェックなしなら '0'
    }
    return render_template('stores/info_confirmed.html', store=store_info)

# 登録処理（DB保存などをここに書く）
@store_bp.route('/register', methods=['POST'])
def register():
    # request.form から受け取って DB に保存する処理を書く
    # ここでは例として内容を表示
    store_data = dict(request.form)
    # 実際はここで DB へ INSERT 処理を行う
    return f"以下の店舗データを登録しました：<br>{store_data}"
