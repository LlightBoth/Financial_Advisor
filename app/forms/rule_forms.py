from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired, NumberRange

from app.models import Rule


class RuleForm(FlaskForm):
    conclusion = StringField(
        "Conclusion", 
        validators=[DataRequired()],
        render_kw={"placeholder": "Conclusion Name"}
    )
    certainty = FloatField(
        "Certainty",
        validators=[
            DataRequired(),
            NumberRange(min=0.0, max=1.0, message="Certainty must be between 0.0 and 1.0 (e.g. 0.85)")
        ],
        render_kw={"placeholder": "Certainty factor from 0.0 to 1.0"}
    )
    advice = StringField(
        "Advice",
        validators=[DataRequired()],
        render_kw={"placeholder": "Financial advice given when condition matches"}
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
        validators=[
            DataRequired(),
            NumberRange(min=0.0, max=1.0, message="Certainty must be between 0.0 and 1.0 (e.g. 0.85)")
        ],
        render_kw={"placeholder": "Certainty factor from 0.0 to 1.0"}
    )
    advice = StringField(
        "Advice",
        validators=[DataRequired()],
        render_kw={"placeholder": "Financial advice given when condition matches"}
    )
    submit = SubmitField('Update')

    def __init__(self, original_rule: Rule, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_rule = original_rule


# ----- ConfirmDeleteForm -----
class ConfirmDeleteForm(FlaskForm):
    submit = SubmitField("Confirm Delete")
