from datetime import date

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    StringField,
    SubmitField,
    FloatField,
    DateField,
    TextAreaField,
    RadioField,
    SelectField,
)
from wtforms.validators import (
    DataRequired,
    Optional,
    NumberRange,
    InputRequired,
)

from app.models import Plan
from app.utils.i18n import _l, I18NTranslations


class BaseLocalizedForm(FlaskForm):
    class Meta:
        def get_translations(self, form):
            return I18NTranslations()


class PlanForm(BaseLocalizedForm):

    # =========================
    # Goal information
    # =========================

    goal = StringField(
        _l("plan.goal"),
        validators=[DataRequired(message=_l("validation.required"))],
        render_kw={"placeholder": _l("plan.goal_placeholder")}
    )

    goal_cost = FloatField(
        _l("plan.goal_cost"),
        validators=[
            DataRequired(message=_l("validation.required")),
            NumberRange(min=0.01, message=_l("validation.budget_positive"))
        ],
        render_kw={"placeholder": _l("plan.cost_placeholder")}
    )

    in_between = DateField(
        _l("plan.target_date"),
        format="%Y-%m-%d",
        default=date.today,
        validators=[DataRequired(message=_l("validation.required"))]
    )

    description = TextAreaField(
        _l("common.description"),
        validators=[Optional()],
        render_kw={"placeholder": _l("plan.description_placeholder")}
    )

    # =========================
    # Financial information
    # =========================

    income = FloatField(
        _l("advisor.monthly_income"),
        validators=[
            Optional(),
            NumberRange(min=0, message=_l("validation.amount_positive"))
        ],
        default=0.0,
        render_kw={"placeholder": "e.g. 5000"}
    )

    expense = FloatField(
        _l("advisor.monthly_expense"),
        validators=[
            Optional(),
            NumberRange(min=0, message=_l("validation.amount_positive"))
        ],
        default=0.0,
        render_kw={"placeholder": "e.g. 2500"}
    )

    debt_amount = FloatField(
        _l("category.debt"),
        validators=[
            Optional(),
            NumberRange(min=0, message=_l("validation.amount_positive"))
        ],
        default=0.0,
        render_kw={"placeholder": "e.g. 1000"}
    )

    savings_amount = FloatField(
        _l("plan.total_saved"),
        validators=[
            Optional(),
            NumberRange(min=0, message=_l("validation.amount_positive"))
        ],
        default=0.0,
        render_kw={"placeholder": "e.g. 3000"}
    )

    has_budget = BooleanField(
        _l("plan.has_budget"),
        default=False
    )

    # =========================
    # Personal information
    # =========================

    marital_status = SelectField(
        _l("advisor.marital_status"),
        choices=[
            ("single", _l("advisor.single")),
            ("married", _l("advisor.married")),
        ],
        validators=[Optional()],
        default="single",
        coerce=str
    )

    employment_status = RadioField(
        _l("advisor.q_employment"),
        choices=[
            ("employed", _l("advisor.employed_yes")),
            ("not_employed", _l("advisor.employed_no")),
            ("unspecified", _l("advisor.prefer_not_say")),
        ],
        validators=[Optional()],
        default="employed"
    )

    # =========================
    # Debt information
    # =========================

    debt_status = RadioField(
        _l("advisor.q_debt"),
        choices=[
            ("debt", _l("advisor.debt_yes")),
            ("no_debt", _l("advisor.debt_no")),
            ("unspecified", _l("advisor.prefer_not_say")),
        ],
        validators=[Optional()],
        default="no_debt"
    )

    # =========================
    # Spending information
    # =========================

    spending_habit = RadioField(
        _l("advisor.q_spending"),
        choices=[
            ("big_spend", _l("advisor.spending_high")),
            ("average_spend", _l("advisor.spending_moderate")),
            ("low_spend", _l("advisor.spending_low")),
            ("unspecified", _l("advisor.prefer_not_say")),
        ],
        validators=[Optional()],
        default="average_spend"
    )

    # =========================
    # Plan status
    # =========================

    is_active = BooleanField(
        _l("plan.status"),
        default=True
    )

    value = BooleanField(
        _l("plan.status"),
        default=True
    )

    submit = SubmitField(_l("plan.launch_strategy"))


# ==========================================
# Edit Plan Form
# ==========================================

class EditPlanForm(BaseLocalizedForm):

    goal = StringField(
        _l("plan.goal"),
        validators=[DataRequired(message=_l("validation.required"))],
        render_kw={"placeholder": _l("plan.goal_placeholder")}
    )

    goal_cost = FloatField(
        _l("plan.goal_cost"),
        validators=[
            DataRequired(message=_l("validation.required")),
            NumberRange(min=0.01, message=_l("validation.budget_positive"))
        ],
        render_kw={"placeholder": _l("plan.cost_placeholder")}
    )

    in_between = DateField(
        _l("plan.target_date"),
        format="%Y-%m-%d",
        validators=[DataRequired(message=_l("validation.required"))]
    )

    description = TextAreaField(
        _l("common.description"),
        validators=[Optional()],
        render_kw={"placeholder": _l("plan.description_placeholder")}
    )

    income = FloatField(
        _l("advisor.monthly_income"),
        validators=[
            Optional(),
            NumberRange(min=0, message=_l("validation.amount_positive"))
        ],
        default=0.0,
        render_kw={"placeholder": "e.g. 5000"}
    )

    expense = FloatField(
        _l("advisor.monthly_expense"),
        validators=[
            Optional(),
            NumberRange(min=0, message=_l("validation.amount_positive"))
        ],
        default=0.0,
        render_kw={"placeholder": "e.g. 2500"}
    )

    debt_amount = FloatField(
        _l("category.debt"),
        validators=[
            Optional(),
            NumberRange(min=0, message=_l("validation.amount_positive"))
        ],
        default=0.0,
        render_kw={"placeholder": "e.g. 10000"}
    )

    savings_amount = FloatField(
        _l("plan.total_saved"),
        validators=[
            Optional(),
            NumberRange(min=0, message=_l("validation.amount_positive"))
        ],
        default=0.0,
        render_kw={"placeholder": "e.g. 3000"}
    )

    has_budget = BooleanField(
        _l("plan.has_budget"),
        default=False
    )

    marital_status = SelectField(
        _l("advisor.marital_status"),
        choices=[
            ("single", _l("advisor.single")),
            ("married", _l("advisor.married")),
        ],
        validators=[Optional()],
        default="single",
        coerce=str
    )

    employment_status = RadioField(
        _l("advisor.q_employment"),
        choices=[
            ("employed", _l("advisor.employed_yes")),
            ("not_employed", _l("advisor.employed_no")),
            ("unspecified", _l("advisor.prefer_not_say")),
        ],
        validators=[Optional()],
        default="employed"
    )

    debt_status = RadioField(
        _l("advisor.q_debt"),
        choices=[
            ("debt", _l("advisor.debt_yes")),
            ("no_debt", _l("advisor.debt_no")),
            ("unspecified", _l("advisor.prefer_not_say")),
        ],
        validators=[Optional()],
        default="no_debt"
    )

    spending_habit = RadioField(
        _l("advisor.q_spending"),
        choices=[
            ("big_spend", _l("advisor.spending_high")),
            ("average_spend", _l("advisor.spending_moderate")),
            ("low_spend", _l("advisor.spending_low")),
            ("unspecified", _l("advisor.prefer_not_say")),
        ],
        validators=[Optional()],
        default="average_spend"
    )

    is_active = BooleanField(
        _l("plan.status"),
        default=True
    )

    value = BooleanField(
        _l("plan.status"),
        default=True
    )

    submit = SubmitField(_l("common.update"))

    def __init__(self, original_plan: Plan, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_plan = original_plan


# ==========================================
# Confirm Delete
# ==========================================

class ConfirmDeleteForm(BaseLocalizedForm):

    submit = SubmitField(_l("common.confirm_delete"))
