from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, EmailField
from wtforms.validators import DataRequired, Email, Length, EqualTo

class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=7)])
    is_remember = BooleanField("Remember me", default=False)
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    full_name = StringField('Full Name', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=7)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), Length(min=7)])
    is_active = BooleanField("Remember ", default=True)
    submit = SubmitField('Sign-up')