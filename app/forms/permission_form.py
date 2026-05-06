from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, ValidationError


from app.models import Permission
from extension import db

class PermissionCreateForm(FlaskForm):
    code = StringField(
        "Code",
        validators=[DataRequired()],
        render_kw={"placeholder": "e.g user.view"}
    )
    name = StringField(
        "Name",
        validators=[DataRequired()],
        render_kw={"placeholder": "Human-readable name"}
    )
    module = SelectField(
        "Module",
        validators=[DataRequired()],
        default="General",
        choices=[
            ("General","General"),
            ("Permission","Permission"),
            ("Roles","Roles"),
            ("Users","Users"),
            ]
    )
    descriptions = TextAreaField(
        "Descriptions",
        validators=[DataRequired()],
        render_kw={"placeholder": "What does this permission allow?"}
    )
    submit = SubmitField("Apply")


class PermissionEditForm(FlaskForm):
    def __init__(self, original_permission, *arg, **kwargs):
        super().__init__(*arg, **kwargs)
        self.original_permission = original_permission

    code = StringField(
        "Code",
        validators=[DataRequired()],
    )
    name = StringField(
        "Name",
        validators=[DataRequired()],
    )
    module = SelectField(
        "Module",
        default="General",
        choices=[
            ("General","General"),
            ("Permission","Permission"),
            ("Roles","Roles"),
            ("Users","Users"),
            ]
    )
    descriptions = TextAreaField(
        "Descriptions",
        validators=[DataRequired()],
    )
    
    submit = SubmitField("Apply")


class PermissionDeleteForm(FlaskForm):
    submit = SubmitField("Delete")