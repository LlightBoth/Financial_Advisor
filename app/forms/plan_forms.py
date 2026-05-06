import re
from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, SubmitField, FloatField, DateField, TextAreaField
from wtforms.validators import DataRequired, Optional

from app.models import Plan
from extension import db

class PlanForm(FlaskForm):
    goal = StringField(
        "Goal", 
        validators=[DataRequired()],
        render_kw={"placeholder": "e.g. Annual Marketing Strategy"}
        )
    in_between = DateField(
        "In-Between", 
        validators=[DataRequired()],
        )
    description = TextAreaField(
        "Description",
        validators=[Optional()],
        render_kw={"placeholder": "Short description describe your plan"}
    )
    goal_cost = FloatField(
        "Goal-Cost",
        validators=[DataRequired()],
        render_kw={"placeholder": "How much around does it cost?"}
    )
    value = BooleanField(
        "Value"
    )
    
    submit = SubmitField('Launch Strategy')


# ----- EditPlanForm -----
class EditPlanForm(FlaskForm):
    goal = StringField(
        "Goal", 
        validators=[DataRequired()],
        render_kw={"placeholder": "e.g. Annual Marketing Strategy"}
        )
    in_between = DateField(
        "In-Between", 
        validators=[DataRequired()],
        )
    description = TextAreaField(
        "Description",
        validators=[DataRequired()],
        render_kw={"placeholder": "Short description describe your plan"}
    )
    goal_cost = FloatField(
        "Goal-Cost",
        validators=[DataRequired()],
        render_kw={"placeholder": "How much around does it cost?"}
    )
    value = BooleanField(
        "Value"
    )
    
    submit = SubmitField('Update')

    def __init__(self, original_plan: Plan, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_plan = original_plan



# ----- ConfirmDeleteForm -----
class ConfirmDeleteForm(FlaskForm):
    submit = SubmitField("Confirm Delete")
