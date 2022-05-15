from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, SelectField, TextAreaField, BooleanField, DateField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from app.models import User


class RegistrationForm(FlaskForm):
	nombre = StringField('Nombre completo', validators=[DataRequired(), Length(min=1, max=100)])
	username = StringField('Nombre de usuario', validators=[DataRequired(), Length(min=1, max=25)])
	email = StringField('Correo electrónico', validators=[DataRequired(), Email()])
	password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=1, max=25)])
	confirm_password = PasswordField('Confirmar contraseña', validators=[DataRequired(), EqualTo('password')])
	submit = SubmitField('Registrarse')

	def validate_username(self, username):
		user = User.query.filter_by(username=username.data).first()
		if user:
			raise ValidationError("Nombre de usuario ya ocupado.")

	def validate_email(self, email):
		user = User.query.filter_by(email=email.data).first()
		if user:
			raise ValidationError("Email ya está ocupado.")


class ProfileForm(FlaskForm):
	username = StringField('Nombre de usuario', validators=[DataRequired(), Length(min=1, max=25)])
	email = StringField('Correo electrónico', validators=[DataRequired(), Email()])
	submit = SubmitField('Registrarse')

	def validate_username(self, username):
		user = User.query.filter_by(username=username.data).first()
		if user:
			raise ValidationError("Nombre de usuario ya ocupado.")

	def validate_email(self, email):
		user = User.query.filter_by(email=email.data).first()
		if user:
			raise ValidationError("Email ya está ocupado.")


class LoginForm(FlaskForm):
	email = StringField('Correo electrónico', validators=[DataRequired(), Email()])
	password = PasswordField('Contraseña', validators=[DataRequired()])
	recuerdame = BooleanField('Recuérdame')
	submit = SubmitField('Iniciar sesión')


class EventForm(FlaskForm):
	nombre = StringField('Nombre', validators=[DataRequired()])
	descripcion = TextAreaField('Contenido', validators=[DataRequired()])
	ubicacion = StringField('Ubicación', validators=[DataRequired()])
	fecha = DateField('Fecha', format='%m/%d/%Y')
	submit = SubmitField('Crear evento')
