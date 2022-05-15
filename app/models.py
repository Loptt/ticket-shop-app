from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_property
from abc import ABCMeta, abstractmethod


@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))


class User(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	nombre = db.Column(db.String(320), nullable=False)
	username = db.Column(db.String(25), unique=True, nullable=False)
	email = db.Column(db.String(320), unique=True, nullable=False)
	password = db.Column(db.String(25), nullable=False)


class Administrador(db.Model):
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)


class Organizador(db.Model):
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)


class Comprador(db.Model):
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)


class Factory:
	def makeUsuario(self, tipo, username, email, password):
		if tipo == "Administrador" or tipo == "Organizador" or tipo == "Comprador":
			return eval(tipo)(username=username, email=email, password=password)


class Evento(db.Model):
	__abstract__ = True
	nombre = db.Column(db.String(320), nullable=False)
	descripcion = db.Column(db.Text)
	fecha = db.Column(db.DateTime, nullable=False)


class EventoVirtual(Evento):
	id = db.Column(db.Integer, primary_key=True)
	sala_virtual = db.Column(db.String(320), nullable=False)


class EventoPresencial(Evento):
	id = db.Column(db.Integer, primary_key=True)
	ubicacion = db.Column(db.String(320), nullable=False)


class Boleto(db.Model):
	__abstract__ = True
	fecha_compra = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class BoletoVirtual(Boleto):
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
	evento_id = db.Column(db.Integer, db.ForeignKey('evento_virtual.id'), primary_key=True)
	link = db.Column(db.String(320), nullable=False)


class BoletoPresencial(Boleto):
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
	evento_id = db.Column(db.Integer, db.ForeignKey('evento_presencial.id'), primary_key=True)
	qr_entrada = db.Column(db.String(20), nullable=False)


class AbstractFactory(metaclass=ABCMeta):
	@abstractmethod
	def makeBoleto(self):
		pass

	@abstractmethod
	def makeEvento(self):
		pass


class VirtualFactory(AbstractFactory):
	def makeBoleto(self, user, evento):
		return BoletoVirtual(user_id=user.id, evento_id=evento.id, link="") # Generar link de alguna forma

	def makeEvento(self, nombre, descripcion, fecha, sala_virtual):
		return EventoVirtual(nombre=nombre, descripcion=descripcion, fecha=fecha, sala_virtual=sala_virtual)


class PresencialFactory(AbstractFactory):
	def makeBoleto(self, user, evento):
		return BoletoPresencial(user_id=user.id, evento_id=evento.id, qr_entrada="") # Generar QR de alguna forma

	def makeEvento(self, nombre, descripcion, fecha, ubicacion):
		return EventoPresencial(nombre=nombre, descripcion=descripcion, fecha=fecha, ubicacion=ubicacion)
