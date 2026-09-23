from flask import Blueprint, render_template
from flask_login import login_required

currency_bp = Blueprint("currencies", __name__, url_prefix="/currencies")

@currency_bp.route("/currency")
@login_required
def converter():
    return render_template("currency_converter/index.html")
