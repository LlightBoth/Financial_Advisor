import re
from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, SubmitField, PasswordField, IntegerField
from wtforms.validators import DataRequired

from app.models import Role, User
from extension import db

class RoleForm(FlaskForm):
    name = StringField(
        "Name", 
        validators=[DataRequired()],
        render_kw={"placeholder": "Role Name"}
        )
    descriptions = StringField(
        "Descriptions",
        validators=[DataRequired()],
        render_kw={"placeholder": "Short description (optional)"}
    )
    submit = SubmitField('Create')


# ----- EditRoleForm -----
class EditRoleForm(FlaskForm):
    name = StringField(
        "Name", 
        validators=[DataRequired()],
        render_kw={"placeholder": "Role Name"}
        )
    descriptions = StringField(
        "Descriptions",
        validators=[DataRequired()],
        render_kw={"placeholder": "Short description (optional)"}
    )
    submit = SubmitField('Update')

    def __init__(self, original_role: Role, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_role = original_role



# ----- ConfirmDeleteForm -----
class ConfirmDeleteForm(FlaskForm):
    submit = SubmitField("Confirm Delete")
