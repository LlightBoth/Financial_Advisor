import re
from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, SubmitField, PasswordField, IntegerField
from wtforms.validators import DataRequired

from app.models import Fact
from extension import db

class FactForm(FlaskForm):
    tags = StringField(
        "Tags", 
        validators=[DataRequired()],
        render_kw={"placeholder": "Tags Name"}
        )
    description = StringField(
        "Description",
        validators=[DataRequired()],
        render_kw={"placeholder": "Short description describe fact"}
    )
    value = BooleanField(
        "Value",
    )
    submit = SubmitField('Create')


# ----- EditFactForm -----
class EditFactForm(FlaskForm):
    tags = StringField(
        "Tags", 
        validators=[DataRequired()],
        render_kw={"placeholder": "Tags Name"}
        )
    description = StringField(
        "Description",
        validators=[DataRequired()],
        render_kw={"placeholder": "Short description describe fact"}
    )
    value = BooleanField(
        "Value",
        validators=[DataRequired()],
    )
    submit = SubmitField('Create')

    def __init__(self, original_fact: Fact, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_fact = original_fact



# ----- ConfirmDeleteForm -----
class ConfirmDeleteForm(FlaskForm):
    submit = SubmitField("Confirm Delete")
