from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Senha", validators=[DataRequired(), Length(min=6, max=128)])
    remember = BooleanField("Manter conectado")
    submit = SubmitField("Entrar")
