from datetime import date
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SubmitField,
    FloatField,
    DateField,
    SelectField,
)
from wtforms.validators import DataRequired, Optional, NumberRange

from app.models import Income
from app.utils.i18n import _l, I18NTranslations


class BaseLocalizedForm(FlaskForm):
    class Meta:
        def get_translations(self, form):
            return I18NTranslations()


# ----- IncomeForm -----
class IncomeForm(BaseLocalizedForm):
    amount = FloatField(
        _l("finance.amount"),
        validators=[
            DataRequired(message=_l("validation.required")),
            NumberRange(min=0.01, message=_l("validation.amount_positive"))
        ],
        render_kw={
            "placeholder": "e.g. 1500.00"
        }
    )

    description = StringField(
        _l("common.description"),
        validators=[Optional()],
        render_kw={
            "placeholder": "e.g. August salary"
        }
    )

    category = SelectField(
        _l("finance.category"),
        choices=[
            ("Salary", _l("category.salary")),
            ("Business", _l("category.business")),
            ("Freelance", _l("category.freelance")),
            ("Investment", _l("category.investment")),
            ("Rental", _l("category.rental")),
            ("Other", _l("category.other")),
        ],
        validators=[DataRequired(message=_l("validation.required"))]
    )

    income_date = DateField(
        _l("income.income_date"),
        validators=[DataRequired(message=_l("validation.required"))],
        default=date.today,
        format='%Y-%m-%d'
    )

    recurring_period = SelectField(
        _l("income.recurring_period"),
        choices=[
            ("", _l("period.not_recurring")),
            ("Weekly", _l("period.weekly")),
            ("Monthly", _l("period.monthly")),
            ("Yearly", _l("period.yearly")),
        ],
        validators=[Optional()]
    )

    submit = SubmitField(_l("income.add_income"))


# ----- EditIncomeForm -----
class EditIncomeForm(BaseLocalizedForm):
    amount = FloatField(
        _l("finance.amount"),
        validators=[
            DataRequired(message=_l("validation.required")),
            NumberRange(min=0.01, message=_l("validation.amount_positive"))
        ],
        render_kw={
            "placeholder": "e.g. 1500.00"
        }
    )

    description = StringField(
        _l("common.description"),
        validators=[Optional()],
        render_kw={
            "placeholder": "e.g. August salary"
        }
    )

    category = SelectField(
        _l("finance.category"),
        choices=[
            ("Salary", _l("category.salary")),
            ("Business", _l("category.business")),
            ("Freelance", _l("category.freelance")),
            ("Investment", _l("category.investment")),
            ("Rental", _l("category.rental")),
            ("Other", _l("category.other")),
        ],
        validators=[DataRequired(message=_l("validation.required"))]
    )

    income_date = DateField(
        _l("income.income_date"),
        validators=[DataRequired(message=_l("validation.required"))]
    )

    recurring_period = SelectField(
        _l("income.recurring_period"),
        choices=[
            ("", _l("period.not_recurring")),
            ("Weekly", _l("period.weekly")),
            ("Monthly", _l("period.monthly")),
            ("Yearly", _l("period.yearly")),
        ],
        validators=[Optional()]
    )

    submit = SubmitField(_l("common.update"))

    def __init__(self, original_income: Income, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_income = original_income


# ----- ConfirmDeleteForm -----
class IncomeDeleteForm(BaseLocalizedForm):
    submit = SubmitField(_l("common.confirm_delete"))