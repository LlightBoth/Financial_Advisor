import re
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired

from app.models import Rule
from extension import db

class RuleForm(FlaskForm):
    conclusion = StringField(
        "Conclusion", 
        validators=[DataRequired()],
        render_kw={"placeholder": "Conclusion Name"}
        )
    certainty = FloatField(
        "Certainty",
        validators=[DataRequired()],
        render_kw={"placeholder": "Certain from (0-1) percentage"}
    )
    advice = StringField(
        "Advice",
        validators=[DataRequired()],
        render_kw={"placeholder": "Advice for users"}
    )
    submit = SubmitField('Create')


# ----- EditRuleForm -----
class EditRuleForm(FlaskForm):
    conclusion = StringField(
        "Conclusion", 
        validators=[DataRequired()],
        render_kw={"placeholder": "Conclusion Name"}
        )
    certainty = FloatField(
        "Certainty",
        validators=[DataRequired()],
        render_kw={"placeholder": "Certain from (0-1) percentage"}
    )
    advice = StringField(
        "Advice",
        validators=[DataRequired()],
        render_kw={"placeholder": "Advice for users"}
    )
    submit = SubmitField('Create')

    def __init__(self, original_rule: Rule, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_rule = original_rule



# ----- ConfirmDeleteForm -----
class ConfirmDeleteForm(FlaskForm):
    submit = SubmitField("Confirm Delete")
