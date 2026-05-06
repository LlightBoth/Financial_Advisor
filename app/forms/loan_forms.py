from flask_wtf import FlaskForm
from wtforms import FloatField, RadioField, SubmitField, SelectField, IntegerField
from wtforms.validators import InputRequired, Optional

class LoanForm(FlaskForm):
    loan_goal = FloatField(
        "Loan Goal Amount",
        validators=[InputRequired()],
        render_kw={"placeholder": "e.g. 10,000"}
    )

    loan_term = SelectField(
        "Loan Term",
        choices= [
            (1, 'Less Than 6 Month'),
            (2, '6 Month'),
            (3, '12 Month'),
            (4, '24 Month'),
            (5, 'More Than 24 Month'),
        ],
        coerce=int
    )

    repayment_frequency = SelectField(
        "Repayment Frequency",
        choices=[
            (1, 'Monthly'),
            (2, 'Quarterly'),
            (3, 'Annually')
        ],
        validators=[InputRequired()],
        coerce=int
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

    total_debt_amount = FloatField(
        "Total Outstanding Debt Amount",
        validators=[Optional()],
        render_kw={"placeholder": "e.g. 5,000"}
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

    loan_history = RadioField(
        "4/ Describe Previous Loan History?",
        choices=[
            (1, 'Yes, I have taken a loan before'),
            (0, 'No, I have never taken a loan')
        ],
        validators=[InputRequired()],
        coerce=int
    )

    submit = SubmitField("Get Loan Advice")
