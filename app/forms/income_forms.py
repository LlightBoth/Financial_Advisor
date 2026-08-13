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

# ----- IncomeForm -----
class IncomeForm(FlaskForm):
    amount = FloatField(
        "Amount",
        validators=[
            DataRequired(),
            NumberRange(min=0.01)
        ],
        render_kw={
            "placeholder": "e.g. 1500.00"
        }
    )

    description = StringField(
        "Description",
        validators=[Optional()],
        render_kw={
            "placeholder": "e.g. August salary"
        }
    )

    category = SelectField(
        "Category",
        choices=[
            ("Salary", "Salary"),
            ("Business", "Business"),
            ("Freelance", "Freelance"),
            ("Investment", "Investment"),
            ("Rental", "Rental"),
            ("Other", "Other"),
        ],
        validators=[DataRequired()]
    )

    income_date = DateField(
        "Income Date",
        validators=[DataRequired()]
    )

    recurring_period = SelectField(
        "Recurring Period",
        choices=[
            ("", "Not Recurring"),
            ("Weekly", "Weekly"),
            ("Monthly", "Monthly"),
            ("Yearly", "Yearly"),
        ],
        validators=[Optional()]
    )

    submit = SubmitField("Add Income")
    


# ----- EditIncomeForm -----
class EditIncomeForm(FlaskForm):
    amount = FloatField(
        "Amount",
        validators=[
            DataRequired(),
            NumberRange(min=0.01)
        ],
        render_kw={
            "placeholder": "e.g. 1500.00"
        }
    )

    description = StringField(
        "Description",
        validators=[Optional()],
        render_kw={
            "placeholder": "e.g. August salary"
        }
    )

    category = SelectField(
        "Category",
        choices=[
            ("Salary", "Salary"),
            ("Business", "Business"),
            ("Freelance", "Freelance"),
            ("Investment", "Investment"),
            ("Rental", "Rental"),
            ("Other", "Other"),
        ],
        validators=[DataRequired()]
    )

    income_date = DateField(
        "Income Date",
        validators=[DataRequired()]
    )

    recurring_period = SelectField(
        "Recurring Period",
        choices=[
            ("", "Not Recurring"),
            ("Weekly", "Weekly"),
            ("Monthly", "Monthly"),
            ("Yearly", "Yearly"),
        ],
        validators=[Optional()]
    )

    submit = SubmitField("Update")

    def __init__(self, original_income: Income, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_income = original_income


# ----- ConfirmDeleteForm -----
class IncomeDeleteForm(FlaskForm):

    submit = SubmitField("Confirm Delete")