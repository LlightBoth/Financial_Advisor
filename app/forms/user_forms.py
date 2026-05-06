import re
from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, SubmitField, PasswordField, SelectField, EmailField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional

from app.models import User, Role
from app.services.role_services import RoleServices
from extension import db

# ----- Helpers -----
def strong_password(form, field):
    password = field.data or ""
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long.")
    
    if not re.search(r"[A-Z]", password):
        raise ValidationError("Password must contain at least one uppercase letter.")
    
    if not re.search(r"[a-z]", password):
        raise ValidationError("Password must contain at least one lowercase letter.")
    
    if not re.search(r"[0-9]", password):
        raise ValidationError("Password must contain at least one digit.")
    
    if not re.search(r"[!@#$%^&*(),.?:{}\/<>_\-+=]", password):
        raise ValidationError("Password must contain at least one special character.")


# ----- UserCreateForm -----
class UserCreateForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[DataRequired(), Length(min=3, max=50)],
        render_kw={"placeholder": "Enter username"}
    )
    email = StringField(
        "Email",
        validators=[DataRequired(), Email()],
        render_kw={"placeholder": "Enter Email"}
    )
    full_name = StringField(
        "Full name",
        validators=[DataRequired(), Length(min=3, max=50)],
        render_kw={"placeholder": "Enter full name"}
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), strong_password],
        render_kw={"placeholder": "Strong Password"}
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Password must match.")],
        render_kw={"placeholder": "Confirm Password"}
    )
    is_active = BooleanField(
        "Active",
        default=True
    )
    role_module = SelectField("Role", choices=[], default="User", coerce=int, validators=[Optional()])
    submit = SubmitField("Save")


    # ----- server-side uniqueness checks -----

    def __init__(self, roles, *arg, **kwargs):
        super().__init__(*arg, **kwargs)
        self.role_module.choices = roles

    def validate_username(self, field):
        exists = db.session.scalar(
            db.select(User).filter(User.username == field.data)
        )
        if exists:
            raise ValidationError("This username is already taken.")
        
    def validate_email(self, field):
        exists = db.session.scalar(
            db.select(User).filter(User.email == field.data)
        )
        if exists:
            raise ValidationError("This email is already taken.")


# ----- UserEditForm -----
class UserEditForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[DataRequired(), Length(min=3, max=50)]
    )
    email = StringField(
        "Email",
        validators=[DataRequired(), Email()]
    )
    full_name = StringField(
        "Full name",
        validators=[DataRequired(), Length(min=3, max=50)]
    )
    role_module = SelectField("Role", choices=[], coerce=int)
    is_active = BooleanField("Active", default=True)
    password = PasswordField(
        "New Password (leave blank to keep current)",
        validators=[Optional(), strong_password],
        render_kw={"placeholder": "New Strong Password (Optional)"}
    )
    confirm_password = PasswordField(
        "Confirm New Password",
        validators=[Optional(), EqualTo("password", message="Password must match.")]
    )
    submit = SubmitField("Update")

    def __init__(self, original_user: User, roles_choices=None, current_role_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_user = original_user

        if roles_choices:
            self.role_module.choices = roles_choices

        # Only preselect if GET (no POST data yet)
        # Preselect current role on GET only
        if not self.role_module.data and current_role_id:
            self.role_module.data = current_role_id
            
    def validate_username(self, field):
        q = db.select(User).filter(User.username == field.data, User.id != self.original_user.id)
        exists = db.session.scalar(q)
        if exists:
            raise ValidationError("This username is already taken.")
        
    def validate_email(self, field):
        q = db.select(User).filter(User.email == field.data, User.id != self.original_user.id)
        exists = db.session.scalar(q)
        if exists:
            raise ValidationError("This email is already taken.")


# ----- ConfirmDeleteForm -----
class ConfirmDeleteForm(FlaskForm):
    submit = SubmitField("Confirm Delete")



# ----- PROFILE FORM -----
class EditProfileForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    email = EmailField("Email", validators=[DataRequired(), Email()])

class ChangePasswordProfileForm(FlaskForm):
    current_password = StringField("Current Password", validators=[DataRequired()])
    new_password = StringField("New Password", validators=[DataRequired()])
    confirm_password = StringField("Confirm Password", validators=[DataRequired()])

