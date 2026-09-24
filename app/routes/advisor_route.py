from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user

from app.forms.advisor_forms import AdvisorForm
from app.services.advisor_services import AdvisorServices
from app.services.plan_services import PlanServices
from app.security.limiter import limiter
from app.security.cookie import check_cookie_token
from extension import csrf

advisor_bp = Blueprint("advisors", __name__, url_prefix="/advisors")
consult_api_bp = Blueprint("consult_api", __name__)
csrf.exempt(consult_api_bp)

# Middleware route
@advisor_bp.before_request
def check_token():
    # check_cookie_token(current_user)
    pass


@consult_api_bp.route("/api/consult/extract", methods=["POST"])
@advisor_bp.route("/api/consult/extract", methods=["POST"])
@csrf.exempt
def extract_api():
    """
    Extracts 7 canonical financial facts from natural language text
    using Trained Financial Advisor AI + llm_output_normalizer.
    """
    data = request.get_json(silent=True) or (request.form.to_dict() if request.form else {})
    text = data.get("text") or data.get("message") or data.get("statement") or ""
    if not text:
        return jsonify({"success": False, "error": {"message": "Text is required."}}), 400

    from app.services.llm_service import LLMService
    slots = LLMService.extract_financial_profile(text)
    return jsonify({"success": True, "slots": slots}), 200


@consult_api_bp.route("/api/consult", methods=["POST"])
@consult_api_bp.route("/evaluate", methods=["POST"])
@advisor_bp.route("/api/consult", methods=["POST"])
@advisor_bp.route("/evaluate", methods=["POST"])
@csrf.exempt
def evaluate_api():
    """
    Structured Financial Consultant API Endpoint (Step 7H).
    
    Accepts JSON or form payload, validates strictly against schema,
    and returns a structured JSON response without calculating any metrics
    in the route.
    """
    if request.content_type and "application/json" in request.content_type:
        raw_data = request.get_json(silent=True)
        if raw_data is None and request.data:
            return jsonify({
                "success": False,
                "error": {
                    "code": "MALFORMED_REQUEST",
                    "message": "Malformed JSON request payload."
                }
            }), 400
        raw_data = raw_data if raw_data is not None else {}
    elif request.is_json:
        raw_data = request.get_json(silent=True)
        if raw_data is None and request.data:
            return jsonify({
                "success": False,
                "error": {
                    "code": "MALFORMED_REQUEST",
                    "message": "Malformed JSON request payload."
                }
            }), 400
        raw_data = raw_data if raw_data is not None else {}
    elif request.form:
        raw_data = request.form.to_dict()
    else:
        raw_data = request.get_json(silent=True)
        if raw_data is None:
            if request.data:
                return jsonify({
                    "success": False,
                    "error": {
                        "code": "MALFORMED_REQUEST",
                        "message": "Malformed JSON request payload."
                    }
                }), 400
            raw_data = {}

    try:
        result_dto, error_dto = AdvisorServices.consult(raw_data)
        if error_dto:
            return jsonify({
                "success": False,
                "error": error_dto
            }), 400

        return jsonify(result_dto), 200
    except Exception:
        return jsonify({
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An error occurred while evaluating financial consultation."
            }
        }), 500


@advisor_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    form = AdvisorForm()
    advice_rule = None

    if form.validate_on_submit():
        # Collect data
        data = {
            "goal_cost": form.goal_cost.data,
            "income": form.income.data,
            "expense": form.expense.data,
            "martial_status": form.martial_status.data,
            "is_employed": form.employment_status.data,
            "is_debt": form.debt_status.data,
            "is_spending": form.spending_habit.data,
        }
        advice_rule = AdvisorServices.get_advise(data)

    return render_template("advisors/index.html", form=form, advice=advice_rule)


def _format_matched_rules(advice_data):
    """Formats matched advice rules into the localized structure expected by analyse.html."""
    if not advice_data:
        return []

    from app.utils.rule_translations import localize_rule
    from app.utils.i18n import get_locale

    lang = get_locale()
    rules = advice_data.get("matched_rules")
    if not rules:
        best_advice = advice_data.get("get_advice")
        if best_advice and getattr(best_advice, "certainty", 0.0) > 0:
            rules = [best_advice]
        elif best_advice and isinstance(best_advice, dict) and best_advice.get("certainty", 0.0) > 0:
            rules = [best_advice]
        else:
            return []

    formatted = []
    for r in rules:
        if not r:
            continue
        # Avoid empty advice placeholders
        if getattr(r, "certainty", 0.0) == 0.0 and getattr(r, "conclusion", "") == "No recommendations are currently available.":
            continue
        formatted.append(localize_rule(r, lang))
    return formatted




@advisor_bp.route("/analyse", methods=["GET", "POST"])
@login_required
def analyseIndex():
    form = AdvisorForm()
    advice_rule = None
    matched_rules = []
    total_plan = PlanServices.get_user_all_plan_total(current_user)

    income = request.form.get("income", 0.0, type=float)
    expense = request.form.get("expense", 0.0, type=float)
    default_goal = income
    goal_cost = request.form.get("goal_cost", default_goal, type=float)

    if request.method == "POST":
        data = {
            "goal_cost": goal_cost,
            "income": income,
            "expense": expense,
            "martial_status": request.form.get("marital_status", "Single"),
            "is_employed": request.form.get("employment_status", "not employed"),
            "is_debt": request.form.get("debt_status", "no debt"),
            "is_spending": request.form.get("spending_habit", "average spend"),
        }
        advice_rule = AdvisorServices.get_advise(data)
        matched_rules = _format_matched_rules(advice_rule)

        return render_template(
            "advisors/analyse.html",
            form=form,
            income=income,
            expense=expense,
            total_plan=total_plan,
            advice=advice_rule,
            matched_rules=matched_rules
        )

    return render_template(
        "advisors/analyse.html",
        form=form,
        income=income,
        expense=expense,
        total_plan=total_plan,
        advice=advice_rule,
        matched_rules=matched_rules
    )


@advisor_bp.route("/personal-analyse", methods=["GET", "POST"])
@login_required
@limiter.limit("15 per minute")
def personalAnalyse():
    form = AdvisorForm()
    if request.method == "GET" and "income" not in request.args and "expense" not in request.args:
        return redirect(url_for("advisors.analyseIndex"))

    income = request.values.get("income", 0.0, type=float) or 0.0
    expense = request.values.get("expense", 0.0, type=float) or 0.0
    data = {
        "income": income,
        "expense": expense,
        "marital_status": request.values.get("marital_status", "Single")
    }

    advice_result = AdvisorServices.persoal_analyse(data)
    matched_rules = _format_matched_rules(advice_result)

    total_plan = PlanServices.get_user_all_plan_total(current_user)
    sum_saving = income - expense
    sum_saving_rate = advice_result.get("remain_percentage", 0.0)
    user_plans = PlanServices.get_user_all_plan_total(current_user)

    return render_template(
        "advisors/analyse.html",
        form=form,
        income=income,
        expense=expense,
        sum_saving=sum_saving,
        sum_saving_rate=sum_saving_rate,
        user_plans=user_plans,
        total_plan=total_plan,
        advice=advice_result,
        matched_rules=matched_rules
    )