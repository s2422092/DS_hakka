# routes/general/explamation.py
from flask import Blueprint, render_template

store_detail_bp = Blueprint('store_detail', __name__, url_prefix='/store_detail')

@store_detail_bp.route('/store_detail')
def store_detail():
    return render_template('store_detail/menu_check.html')
