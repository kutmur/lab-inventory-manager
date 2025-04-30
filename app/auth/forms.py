from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    SubmitField
)
from wtforms.validators import DataRequired
from app.models import User


class LoginForm(FlaskForm):
    """Form for user login.
    
    Fields:
        username: Username field
        password: Password field
        remember_me: Remember login checkbox
        submit: Submit button
    """
    username = StringField(
        'Username',
        validators=[DataRequired(message='Username is required')]
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired(message='Password is required')]
    )
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')