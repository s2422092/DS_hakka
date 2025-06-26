# routes/general/explamation.py
from flask import Blueprint, render_template

general_bp = Blueprint('general', __name__, url_prefix='/general')

@general_bp.route('/explamation')
def show_explamation():
    return render_template('general/explamation.html')
