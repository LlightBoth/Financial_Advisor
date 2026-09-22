from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    SelectField,
    StringField,
    SubmitField,
)
from wtforms.validators import DataRequired

from app.models import Fact


# ============================================================
# Create Fact Form
# ============================================================

class FactForm(FlaskForm):
    tags = StringField(
        "Tags",
        validators=[DataRequired()],
        render_kw={
            "placeholder": "Fact name, e.g. has_savings"
        }
    )

    description = StringField(
        "Description",
        validators=[DataRequired()],
        render_kw={
            "placeholder": "Short description of the fact"
        }
    )

    type = SelectField(
        "Type",
        choices=[
            ("boolean", "Boolean"),
            ("number", "Number"),
        ],
        validators=[DataRequired()],
    )

    value = StringField(
        "Value",
        validators=[DataRequired()],
        render_kw={
            "placeholder": "e.g. true, 5000, employed"
        }
    )

    submit = SubmitField("Create")


# ============================================================
# Edit Fact Form
# ============================================================

class EditFactForm(FlaskForm):
    tags = StringField(
        "Tags",
        validators=[DataRequired()],
        render_kw={
            "placeholder": "Fact name, e.g. has_savings"
        }
    )

    description = StringField(
        "Description",
        validators=[DataRequired()],
        render_kw={
            "placeholder": "Short description of the fact"
        }
    )

    type = SelectField(
        "Type",
        choices=[
            ("boolean", "Boolean"),
            ("number", "Number"),
        ],
        validators=[DataRequired()],
    )

    value = StringField(
        "Value",
        validators=[DataRequired()],
        render_kw={
            "placeholder": "e.g. true, 5000, employed"
        }
    )

    submit = SubmitField("Update")

    def __init__(self, original_fact: Fact, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_fact = original_fact


# ============================================================
# Confirm Delete Form
# ============================================================

class ConfirmDeleteForm(FlaskForm):
    submit = SubmitField("Confirm Delete")
