from flask import Blueprint, render_template

explamation_bp= Blueprint('general', __name__, url_prefix='/before')

@explamation_bp.route('/')
def index():
    return render_template('general/explamation.html')
