from flask_wtf import FlaskForm
from flask_wtf.form import _Auto
from wtforms import ( StringField, SubmitField, FloatField, DateField, SelectField )
from wtforms.validators import DataRequired, Optional, NumberRange

from app.models import Expense

# ----- ExpenseForm -----
class ExpenseForm(FlaskForm):
    amount = FloatField(
        "Amount",
        validators=[
            DataRequired(),
            NumberRange(min=0.01)
        ],
        render_kw={
            "placeholder": "e.g. 250.00"
        }
    )

    description = StringField(
        "Description",
        validators=[Optional()],
        render_kw={
            "placeholder": "e.g. Monthly food expenses"
        }
    )

    category = SelectField(
        "Category",
        choices=[
            ("Food", "Food"),
            ("Transportation", "Transportation"),
            ("Housing", "Housing"),
            ("Utilities", "Utilities"),
            ("Education", "Education"),
            ("Healthcare", "Healthcare"),
            ("Shopping", "Shopping"),
            ("Entertainment", "Entertainment"),
            ("Debt", "Debt"),
            ("Other", "Other"),
        ],
        validators=[DataRequired()]
    )

    expense_date = DateField(
        "Expense Date",
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

    submit = SubmitField("Add Expense")


# ----- EditExpenseForm -----
class EditExpenseForm(FlaskForm):
    amount = FloatField(
        "Amount",
        validators=[
            DataRequired(),
            NumberRange(min=0.01)
        ],
        render_kw={
            "placeholder": "e.g. 250.00"
        }
    )

    description = StringField(
        "Description",
        validators=[Optional()],
        render_kw={
            "placeholder": "e.g. Monthly food expenses"
        }
    )

    category = SelectField(
        "Category",
        choices=[
            ("Food", "Food"),
            ("Transportation", "Transportation"),
            ("Housing", "Housing"),
            ("Utilities", "Utilities"),
            ("Education", "Education"),
            ("Healthcare", "Healthcare"),
            ("Shopping", "Shopping"),
            ("Entertainment", "Entertainment"),
            ("Debt", "Debt"),
            ("Other", "Other"),
        ],
        validators=[DataRequired()]
    )

    expense_date = DateField(
        "Expense Date",
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

    def __init__(self, original_expense: Expense, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_expense = original_expense


# ----- ConfirmDeleteForm -----
class ExpenseDeleteForm(FlaskForm):
    submit = SubmitField("Confirm Delete")