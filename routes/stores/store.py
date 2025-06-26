# routes/general/explamation.py
from flask import Blueprint, render_template

store_bp = Blueprint('store', __name__, url_prefix='/store')

@store_bp.route('/info_confirmed')
def store():
    return render_template('store/info_confirmed.html')
