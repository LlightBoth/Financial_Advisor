from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, EmailField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from app.utils.i18n import _l, I18NTranslations


class BaseLocalizedForm(FlaskForm):
    class Meta:
        def get_translations(self, form):
            return I18NTranslations()


class LoginForm(BaseLocalizedForm):
    email = EmailField(
        _l('auth.email'),
        validators=[
            DataRequired(message=_l('validation.required')),
            Email(message=_l('validation.invalid_email')),
        ],
    )
    password = PasswordField(
        _l('auth.password'),
        validators=[
            DataRequired(message=_l('validation.required')),
            Length(min=7, message=_l('validation.password_min_length')),
        ],
    )
    is_remember = BooleanField(_l('auth.remember_me'), default=False)
    submit = SubmitField(_l('auth.login'))


class RegisterForm(BaseLocalizedForm):
    username = StringField(
        _l('auth.username'),
        validators=[DataRequired(message=_l('validation.required'))],
    )
    full_name = StringField(
        _l('auth.full_name'),
        validators=[DataRequired(message=_l('validation.required'))],
    )
    email = EmailField(
        _l('auth.email'),
        validators=[
            DataRequired(message=_l('validation.required')),
            Email(message=_l('validation.invalid_email')),
        ],
    )
    password = PasswordField(
        _l('auth.password'),
        validators=[
            DataRequired(message=_l('validation.required')),
            Length(min=7, message=_l('validation.password_min_length')),
        ],
    )
    confirm_password = PasswordField(
        _l('auth.confirm_password'),
        validators=[
            DataRequired(message=_l('validation.required')),
            Length(min=7, message=_l('validation.password_min_length')),
            EqualTo('password', message=_l('validation.password_mismatch')),
        ],
    )
    is_active = BooleanField(_l('auth.remember_me'), default=True)
    submit = SubmitField(_l('auth.sign_up'))


class ForgotPasswordForm(BaseLocalizedForm):
    email = StringField(
        _l('auth.email_address'),
        validators=[
            DataRequired(message=_l('validation.required')),
            Email(message=_l('validation.invalid_email')),
        ],
    )
    submit = SubmitField(_l('auth.send_reset_link'))