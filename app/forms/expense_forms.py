from datetime import date
from flask_wtf import FlaskForm
from wtforms import ( StringField, SubmitField, FloatField, DateField, SelectField )
from wtforms.validators import DataRequired, Optional, NumberRange

from app.models import Expense
from app.utils.i18n import _l, I18NTranslations


class BaseLocalizedForm(FlaskForm):
    class Meta:
        def get_translations(self, form):
            return I18NTranslations()


# ----- ExpenseForm -----
class ExpenseForm(BaseLocalizedForm):
    amount = FloatField(
        _l("finance.amount"),
        validators=[
            DataRequired(message=_l("validation.required")),
            NumberRange(min=0.01, message=_l("validation.amount_positive"))
        ],
        render_kw={
            "placeholder": "e.g. 250.00"
        }
    )

    description = StringField(
        _l("common.description"),
        validators=[Optional()],
        render_kw={
            "placeholder": "e.g. Monthly food expenses"
        }
    )

    category = SelectField(
        _l("finance.category"),
        choices=[
            ("Food", _l("category.food")),
            ("Transportation", _l("category.transportation")),
            ("Housing", _l("category.housing")),
            ("Utilities", _l("category.utilities")),
            ("Education", _l("category.education")),
            ("Healthcare", _l("category.healthcare")),
            ("Shopping", _l("category.shopping")),
            ("Entertainment", _l("category.entertainment")),
            ("Debt", _l("category.debt")),
            ("Other", _l("category.other")),
        ],
        validators=[DataRequired(message=_l("validation.required"))]
    )

    expense_date = DateField(
        _l("expense.expense_date"),
        validators=[DataRequired(message=_l("validation.required"))],
        default=date.today,
        format='%Y-%m-%d'
    )

    recurring_period = SelectField(
        _l("expense.recurring_period"),
        choices=[
            ("", _l("period.not_recurring")),
            ("Weekly", _l("period.weekly")),
            ("Monthly", _l("period.monthly")),
            ("Yearly", _l("period.yearly")),
        ],
        validators=[Optional()]
    )

    submit = SubmitField(_l("expense.add_expense"))


# ----- EditExpenseForm -----
class EditExpenseForm(BaseLocalizedForm):
    amount = FloatField(
        _l("finance.amount"),
        validators=[
            DataRequired(message=_l("validation.required")),
            NumberRange(min=0.01, message=_l("validation.amount_positive"))
        ],
        render_kw={
            "placeholder": "e.g. 250.00"
        }
    )

    description = StringField(
        _l("common.description"),
        validators=[Optional()],
        render_kw={
            "placeholder": "e.g. Monthly food expenses"
        }
    )

    category = SelectField(
        _l("finance.category"),
        choices=[
            ("Food", _l("category.food")),
            ("Transportation", _l("category.transportation")),
            ("Housing", _l("category.housing")),
            ("Utilities", _l("category.utilities")),
            ("Education", _l("category.education")),
            ("Healthcare", _l("category.healthcare")),
            ("Shopping", _l("category.shopping")),
            ("Entertainment", _l("category.entertainment")),
            ("Debt", _l("category.debt")),
            ("Other", _l("category.other")),
        ],
        validators=[DataRequired(message=_l("validation.required"))]
    )

    expense_date = DateField(
        _l("expense.expense_date"),
        validators=[DataRequired(message=_l("validation.required"))]
    )

    recurring_period = SelectField(
        _l("expense.recurring_period"),
        choices=[
            ("", _l("period.not_recurring")),
            ("Weekly", _l("period.weekly")),
            ("Monthly", _l("period.monthly")),
            ("Yearly", _l("period.yearly")),
        ],
        validators=[Optional()]
    )

    submit = SubmitField(_l("common.update"))

    def __init__(self, original_expense: Expense, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_expense = original_expense


# ----- ConfirmDeleteForm -----
class ExpenseDeleteForm(BaseLocalizedForm):
    submit = SubmitField(_l("common.confirm_delete"))