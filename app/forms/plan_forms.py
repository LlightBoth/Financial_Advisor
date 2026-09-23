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
    HiddenField,
)

from wtforms.validators import (
    DataRequired,
    Optional,
    NumberRange,
    InputRequired,
)

from app.models import Plan


class PlanForm(FlaskForm):

    # =========================
    # Goal information
    # =========================

    goal = StringField(
        "Financial Goal",
        validators=[DataRequired()],
        render_kw={
            "placeholder": "e.g. Buy a new car"
        }
    )

    goal_cost = FloatField(
        "Goal Cost",
        validators=[
            DataRequired(),
            NumberRange(
                min=0.01,
                message="Goal cost must be greater than 0."
            )
        ],
        render_kw={
            "placeholder": "e.g. 5000"
        }
    )
    in_between = DateField(
        "Target Date",
        validators=[Optional()],
        format="%Y-%m-%d"
    )
    description = TextAreaField(
        "Description",
        validators=[Optional()],
        render_kw={
            "placeholder": "Describe your financial goal..."
        }
    )


    # =========================
    # Financial information
    # =========================

    income = FloatField(
        "Monthly Income/Fund",
        validators=[
            InputRequired(),
            NumberRange(
                min=0,
                message="Income cannot be negative."
            )
        ],
        render_kw={
            "placeholder": "e.g. 5000"
        }
    )

    expense = FloatField(
        "Monthly Expenses",
        validators=[
            InputRequired(),
            NumberRange(
                min=0,
                message="Expenses cannot be negative."
            )
        ],
        render_kw={
            "placeholder": "e.g. 2500"
        }
    )

    debt_amount = FloatField(
        "Debt Amount",
        validators=[
            Optional(),
            NumberRange(
                min=0,
                message="Debt amount cannot be negative."
            )
        ],
        render_kw={
            "placeholder": "e.g. 10000"
        },
        default=0
    )

    saving = FloatField(
        "Saving Amount",
        validators=[
            Optional(),
            NumberRange(
                min=0,
                message="Savings amount cannot be negative."
            )
        ],
        default=0,
        render_kw={
            "placeholder": "e.g. 100"
        }
    )


    saving_type = SelectField(
        "Saving Type",
        choices=[
            ("daily", "Daily"),
            ("monthly", "Monthly"),
            ("manual", "Flexible"),
        ],
        validators=[DataRequired()]
    )



    has_budget = BooleanField("I have a budget/Fund")


    # =========================
    # Personal information
    # =========================

    marital_status = SelectField(
        "Marital Status",
        choices=[
            ("single", "Single"),
            ("married", "Married"),
        ],
        validators=[InputRequired()],
        coerce=str
    )

    employment_status = RadioField(
        "Are you currently employed?",
        choices=[
            ("employed", "Yes, I am employed"),
            ("not_employed", "No, I am not employed"),
            ("unspecified", "Prefer not to say"),
        ],
        validators=[InputRequired()]
    )


    # =========================
    # Debt information
    # =========================

    debt_status = RadioField(
        "Do you have any outstanding debt?",
        choices=[
            ("debt", "Yes, I have debt"),
            ("no_debt", "No, I do not have debt"),
            ("unspecified", "Prefer not to say"),
        ],
        validators=[InputRequired()]
    )


    # =========================
    # Spending information
    # =========================

    spending_habit = RadioField(
        "How would you describe your spending habits?",
        choices=[
            ("big_spend", "I tend to spend a lot"),
            ("average_spend", "I spend moderately"),
            ("low_spend", "I spend very little"),
            ("unspecified", "Prefer not to say"),
        ],
        validators=[InputRequired()]
    )


    # =========================
    # Plan status
    # =========================

    is_active = BooleanField(
        "Active",
        default=True
    )

    submit = SubmitField(
        "Launch Strategy"
    )


# ==========================================
# Edit Plan Form
# ==========================================

class EditPlanForm(FlaskForm):

    goal = StringField(
        "Financial Goal",
        validators=[DataRequired()],
        render_kw={
            "placeholder": "e.g. Buy a new car"
        }
    )

    goal_cost = FloatField(
        "Goal Cost",
        validators=[
            DataRequired(),
            NumberRange(
                min=0.01,
                message="Goal cost must be greater than 0."
            )
        ],
        render_kw={
            "placeholder": "e.g. 5000"
        }
    )
    in_between = DateField(
        "Target Date",
        validators=[Optional()],
        format="%Y-%m-%d"
    )
    description = TextAreaField(
        "Description",
        validators=[Optional()],
        render_kw={
            "placeholder": "Describe your financial goal..."
        }
    )

    income = FloatField(
        "Monthly Income/Fund",
        validators=[
            InputRequired(),
            NumberRange(
                min=0,
                message="Income cannot be negative."
            )
        ],
        render_kw={
            "placeholder": "e.g. 5000"
        }
    )

    expense = FloatField(
        "Monthly Expenses",
        validators=[
            InputRequired(),
            NumberRange(
                min=0,
                message="Expenses cannot be negative."
            )
        ],
        render_kw={
            "placeholder": "e.g. 2500"
        }
    )

    debt_amount = FloatField(
        "Debt Amount",
        validators=[
            Optional(),
            NumberRange(
                min=0,
                message="Debt amount cannot be negative."
            )
        ],
        render_kw={
            "placeholder": "e.g. 10000"
        },
        default=0
    )

    saving = FloatField(
        "Savings Amount",
        validators=[
            Optional(),
            NumberRange(
                min=0,
                message="Savings amount cannot be negative."
            )
        ],
        render_kw={
            "placeholder": "e.g. 3000"
        },
        default=0
    )

    saving_type = SelectField(
        "Saving Type",
        choices=[
            ("daily", "Daily"),
            ("monthly", "Monthly"),
            ("manual", "Flexible"),
        ],
        validators=[DataRequired()]
    )


    has_budget = BooleanField("I have a budget/Fund")


    # =========================
    # Personal information
    # =========================

    marital_status = SelectField(
        "Marital Status",
        choices=[
            ("single", "Single"),
            ("married", "Married"),
        ],
        validators=[InputRequired()],
        coerce=str
    )

    employment_status = RadioField(
        "Are you currently employed?",
        choices=[
            ("employed", "Yes, I am employed"),
            ("not_employed", "No, I am not employed"),
            ("unspecified", "Prefer not to say"),
        ],
        validators=[InputRequired()]
    )


    # =========================
    # Debt information
    # =========================

    debt_status = RadioField(
        "Do you have any outstanding debt?",
        choices=[
            ("debt", "Yes, I have debt"),
            ("no_debt", "No, I do not have debt"),
            ("unspecified", "Prefer not to say"),
        ],
        validators=[InputRequired()]
    )


    # =========================
    # Spending information
    # =========================

    spending_habit = RadioField(
        "How would you describe your spending habits?",
        choices=[
            ("big_spend", "I tend to spend a lot"),
            ("average_spend", "I spend moderately"),
            ("low_spend", "I spend very little"),
            ("unspecified", "Prefer not to say"),
        ],
        validators=[InputRequired()]
    )


    is_active = BooleanField(
        "Active"
    )

    submit = SubmitField(
        "Update"
    )


    def __init__(
        self,
        original_plan: Plan,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)

        self.original_plan = original_plan


# ==========================================
# Confirm Delete
# ==========================================

class ConfirmDeleteForm(FlaskForm):

    submit = SubmitField(
        "Confirm Delete"
    )
