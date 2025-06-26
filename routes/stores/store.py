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
@store_bp.route('/info_confirmed', methods=['POST', 'GET'])
def info_confirmed():
    return render_template('stores/info_confirmed.html')


