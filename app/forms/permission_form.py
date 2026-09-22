from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired


MODULE_CHOICES = [
    ("General", "General"),
    ("Dashboard", "Dashboard"),
    ("Users", "Users"),
    ("Roles", "Roles"),
    ("Permission", "Permission"),
    ("Rules", "Rules"),
    ("Facts", "Facts"),
    ("Plans", "Plans"),
    ("Incomes", "Incomes"),
    ("Expenses", "Expenses"),
    ("Histories", "Histories"),
    ("Advisors", "Advisors"),
    ("Loans", "Loans"),
]


class PermissionCreateForm(FlaskForm):
    code = StringField(
        "Permission Code",
        validators=[DataRequired()],
        render_kw={"placeholder": "e.g. user.view, plan.create"}
    )
    name = StringField(
        "Display Name",
        validators=[DataRequired()],
        render_kw={"placeholder": "e.g. View Users, Create Savings Plan"}
    )
    module = SelectField(
        "Module",
        validators=[DataRequired()],
        default="General",
        choices=MODULE_CHOICES
    )
    descriptions = TextAreaField(
        "Description",
        validators=[DataRequired()],
        render_kw={"placeholder": "Describe what capabilities this permission grants..."}
    )
    submit = SubmitField("Create Permission")


class PermissionEditForm(FlaskForm):
    def __init__(self, original_permission, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_permission = original_permission

    code = StringField(
        "Permission Code",
        validators=[DataRequired()],
        render_kw={"placeholder": "e.g. user.view"}
    )
    name = StringField(
        "Display Name",
        validators=[DataRequired()],
        render_kw={"placeholder": "e.g. View Users"}
    )
    module = SelectField(
        "Module",
        default="General",
        choices=MODULE_CHOICES
    )
    descriptions = TextAreaField(
        "Description",
        validators=[DataRequired()],
        render_kw={"placeholder": "Describe what capabilities this permission grants..."}
    )
    submit = SubmitField("Update Permission")


class PermissionDeleteForm(FlaskForm):
    submit = SubmitField("Delete")