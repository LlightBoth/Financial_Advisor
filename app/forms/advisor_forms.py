from flask_wtf import FlaskForm
from wtforms import FloatField, RadioField, SubmitField, SelectField
from wtforms.validators import InputRequired

from app.utils.i18n import _l, I18NTranslations


class BaseLocalizedForm(FlaskForm):
    class Meta:
        def get_translations(self, form):
            return I18NTranslations()


class AdvisorForm(BaseLocalizedForm):
    goal_cost = FloatField(
        _l("advisor.goal_amount"),
        validators=[InputRequired(message=_l("validation.required"))],
        render_kw={"placeholder": _l("advisor.goal_placeholder")}
    )

    income = FloatField(
        _l("advisor.monthly_income"),
        validators=[InputRequired(message=_l("validation.required"))],
        render_kw={"placeholder": _l("advisor.income_placeholder")}
    )

    expense = FloatField(
        _l("advisor.monthly_expense"),
        validators=[InputRequired(message=_l("validation.required"))],
        render_kw={"placeholder": _l("advisor.expense_placeholder")}
    )

    martial_status = SelectField(
        _l("advisor.marital_status"),
        choices=[
            ('Single', _l('advisor.single')),
            ('Married', _l('advisor.married'))
        ],
        coerce=str
    )

    employment_status = RadioField(
        _l("advisor.q_employment"),
        choices=[
            ("employed", _l("advisor.employed_yes")),
            ("not employed", _l("advisor.employed_no")),
            ("not employed", _l("advisor.prefer_not_say")),
        ],
        validators=[InputRequired(message=_l("validation.required"))]
    )

    debt_status = RadioField(
        _l("advisor.q_debt"),
        choices=[
            ("debt", _l("advisor.debt_yes")),
            ("no debt", _l("advisor.debt_no")),
            ("no debt", _l("advisor.prefer_not_say")),
        ],
        validators=[InputRequired(message=_l("validation.required"))]
    )

    spending_habit = RadioField(
        _l("advisor.q_spending"),
        choices=[
            ("big spend", _l("advisor.spending_high")),
            ("average spend", _l("advisor.spending_moderate")),
            ("average spend", _l("advisor.prefer_not_say")),
        ],
        validators=[InputRequired(message=_l("validation.required"))]
    )

    submit = SubmitField(_l("advisor.get_advice_btn"))

