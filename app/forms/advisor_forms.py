from flask_wtf import FlaskForm
from wtforms import FloatField, RadioField, SubmitField, SelectField
from wtforms.validators import InputRequired

class AdvisorForm(FlaskForm):
    goal_cost = FloatField(
        "Financial Goal Amount",
        validators=[InputRequired()],
        render_kw={"placeholder": "e.g. 10,000"}
    )

    income = FloatField(
        "Monthly Income",
        validators=[InputRequired()],
        render_kw={"placeholder": "e.g. 5,000"}
    )

    expense = FloatField(
        "Monthly Expenses",
        validators=[InputRequired()],
        render_kw={"placeholder": "e.g. 2,500"}
    )

    martial_status = SelectField(
        "Martial Status",
        choices= [
            ('Single','Single'),
            ('Married', 'Married')
        ],
        coerce=str
    )

    employment_status = RadioField(
        "1/ Are you currently employed?",
        choices=[
            ("employed", "Yes, I am employed"),
            ("not employed", "No, I am not employed"),
            ("not employed", "Prefer not to say"),
        ],
        validators=[InputRequired()]
    )

    debt_status = RadioField(
        "2/ Do you have any outstanding debt?",
        choices=[
            ("debt", "Yes, I have debt"),
            ("no debt", "No, I do not have debt"),
            ("no debt", "Prefer not to say"),
        ],
        validators=[InputRequired()]
    )

    spending_habit = RadioField(
        "3/ How would you describe your spending habits?",
        choices=[
            ("big spend", "I tend to spend a lot"),
            ("average spend", "I spend moderately"),
            ("average spend", "Prefer not to say"),
        ],
        validators=[InputRequired()]
    )

    submit = SubmitField("Get Financial Advice")
