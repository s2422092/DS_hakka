from flask import Blueprint, render_template

explamation_bp = Blueprint("explamation", __name__)

@explamation_bp.route("/")
def explamation():
    return render_template("general/explamation.html")  # ← このままでOK
