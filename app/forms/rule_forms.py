from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SubmitField,
    FloatField,
    TextAreaField,
)
from wtforms.validators import DataRequired, NumberRange

from app.models import Rule


# ============================================================
# Create Rule Form
# ============================================================

class RuleForm(FlaskForm):

    name = StringField(
        "Rule Name",
        validators=[DataRequired()],
        render_kw={
            "placeholder": "e.g. Positive Cash Flow"
        }
    )

    conclusion = StringField(
        "Conclusion",
        validators=[DataRequired()],
        render_kw={
            "placeholder": "Conclusion when the rule matches"
        }
    )

    certainty = FloatField(
        "Certainty",
        validators=[
            DataRequired(),
            NumberRange(
                min=0.0,
                max=1.0,
                message=(
                    "Certainty must be between "
                    "0.0 and 1.0 (e.g. 0.85)"
                )
            )
        ],
        render_kw={
            "placeholder": "e.g. 0.85"
        }
    )

    advice = TextAreaField(
        "Advice",
        validators=[DataRequired()],
        render_kw={
            "placeholder": (
                "Enter financial advice, one step per line..."
            ),
            "rows": 8
        }
    )

    submit = SubmitField("Create")


# ============================================================
# Edit Rule Form
# ============================================================

class EditRuleForm(FlaskForm):

    name = StringField(
        "Rule Name",
        validators=[DataRequired()],
        render_kw={
            "placeholder": "e.g. Positive Cash Flow"
        }
    )

    conclusion = StringField(
        "Conclusion",
        validators=[DataRequired()],
        render_kw={
            "placeholder": "Conclusion when the rule matches"
        }
    )

    certainty = FloatField(
        "Certainty",
        validators=[
            DataRequired(),
            NumberRange(
                min=0.0,
                max=1.0,
                message=(
                    "Certainty must be between "
                    "0.0 and 1.0 (e.g. 0.85)"
                )
            )
        ],
        render_kw={
            "placeholder": "e.g. 0.85"
        }
    )

    advice = TextAreaField(
        "Advice",
        validators=[DataRequired()],
        render_kw={
            "placeholder": (
                "Enter financial advice, one step per line..."
            ),
            "rows": 8
        }
    )

    submit = SubmitField("Update")

    def __init__(self, original_rule: Rule, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_rule = original_rule


# ============================================================
# Confirm Delete Form
# ============================================================

class ConfirmDeleteForm(FlaskForm):

    submit = SubmitField("Confirm Delete")
