from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user

from app.forms.advisor_forms import AdvisorForm
from app.services.advisor_services import AdvisorServices
from app.services.plan_services import PlanServices
from google import genai
from google.genai import types

from app.security.limiter import limiter


from app.security.cookie import check_cookie_token
# from app.security.role_check import role_user_only

advisor_bp = Blueprint("advisors", __name__, url_prefix="/advisors")
client = genai.Client()


# Instruction function for AI
def FINANCIAL_SYSTEM_INSTRUCTION(data):
    return f"""
        You are a Financial AI Assistant.

        Analyze the user's financial situation and provide practical,
        short, actionable financial advice.

        USER FINANCIAL DATA:

        Goal: ${data["goal_cost"]}
        Monthly Income: ${data["income"]}
        Monthly Expenses: ${data["expense"]}
        Marital Status: {data["marital_status"]}
        Employment Status: {data["is_employed"]}
        Debt Status: {data["is_debt"]}
        Spending Habit: {data["is_spending"]}

        Calculate:

        Monthly Savings = Monthly Income - Monthly Expenses

        Determine:

        - Savings percentage
        - Expense percentage
        - Whether the goal is achievable
        - Estimated months to reach the goal
        - Practical actions the user should take

        CERTAINTY:

        Return a certainty value between 0.0 and 1.0.

        0.0 = very low confidence
        0.5 = moderate confidence
        0.9 = high confidence
        1.0 = extremely high confidence

        The certainty should reflect how complete and consistent
        the user's financial information is.

        Keep the conclusion short.

        Provide exactly 4 actionable recommendations.
    """


# Middleware route
@advisor_bp.before_request
def check_token():
    check_cookie_token(current_user)


@advisor_bp.route("/", methods=["GET", "POST"])
@login_required
@limiter.limit("3 per minute")
def index():
    form = AdvisorForm()
    advice = None
    ai_error = None
    income = 0.0
    expense = 0.0
    goal_cost = 0.0
    total_plan = PlanServices.get_user_all_plan_total(current_user)

    if form.validate_on_submit():
        income = float(form.income.data or 0)
        expense = float(form.expense.data or 0)
        goal_cost = float(form.goal_cost.data or income)
        data = {
            "goal_cost": goal_cost,
            "income": income,
            "expense": expense,
            "marital_status": form.martial_status.data,
            "is_employed": form.employment_status.data,
            "is_debt": form.debt_status.data,
            "is_spending": form.spending_habit.data,
        }

        # Connect and get response via AI
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents="Analyze this user's financial situation.",

                config=types.GenerateContentConfig(
                    system_instruction=FINANCIAL_SYSTEM_INSTRUCTION(data),
                    temperature=0.2,
                    response_mime_type="application/json",
                    response_schema=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "remain_percentage": types.Schema(
                                type=types.Type.NUMBER
                            ),
                            "expense_percentage": types.Schema(
                                type=types.Type.NUMBER
                            ),
                            "months_to_goal": types.Schema(
                                type=types.Type.INTEGER,
                                nullable=True
                            ),
                            "conclusion": types.Schema(
                                type=types.Type.STRING
                            ),
                            "advice": types.Schema(
                                type=types.Type.ARRAY,
                                items=types.Schema(
                                    type=types.Type.STRING
                                )
                            ),
                            "certainty": types.Schema(
                                type=types.Type.NUMBER
                            )
                        },
                        required=[
                            "remain_percentage",
                            "expense_percentage",
                            "months_to_goal",
                            "conclusion",
                            "advice",
                            "certainty"
                        ]
                    )
                )
            )
            advice = response.parsed

        except Exception as e:
            print(f"[Gemini API Error]: {type(e).__name__} - {e}")
            ai_error = (
                "AI analysis is temporarily unavailable. "
                "Please try again in a few seconds."
            )


    return render_template(
        "advisors/index.html",
        form=form,
        income=income,
        expense=expense,
        goal_cost=goal_cost,
        total_plan=total_plan,
        advice=advice,
        ai_error=ai_error
    )

@advisor_bp.route("/personal-analyse", methods=["POST"])
@login_required
@limiter.limit("5 per minute")
def personalAnalyse():
    # Read values submitted by dashboard form
    income = float(request.form.get("income", 0.0))
    expense = float(request.form.get("expense", 0.0))
    data = {
        "income": income,
        "expense": expense,
        "marital_status": request.form.get("marital_status", "Single")
    }

    # Execute financial scan
    advice_result = AdvisorServices.persoal_analyse(data)

    # Fetch required dashboard variables
    total_plan = PlanServices.get_user_all_plan_total(current_user)
    sum_saving = income - expense
    sum_saving_rate = advice_result.get("remain_percentage", 0.0)
    user_plans = PlanServices.get_user_all_plan_total(current_user)

    return render_template(
        "advisors/analyse.html",  # Renders the updated template
        income=income,
        expense=expense,
        sum_saving=sum_saving,
        sum_saving_rate=sum_saving_rate,
        user_plans=user_plans,
        total_plan=total_plan,
        advice=advice_result
    )