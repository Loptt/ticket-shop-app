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
	eventos = db.relationship('Evento', backref='creator', lazy=True)

	@hybrid_property
	def tipo(self):
		if Administrador.query.filter_by(id=self.id).first():
			return "Administrador"
		elif Comprador.query.filter_by(id=self.id).first():
			return "Comprador"
		elif Organizador.query.filter_by(id=self.id).first():
			return "Organizador"


class Administrador(User):
	id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)


class Organizador(User):
	id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)


class Comprador(User):
	id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)


class Factory:
	def makeUsuario(self, tipo, nombre, username, email, password):
		if tipo == "Administrador" or tipo == "Organizador" or tipo == "Comprador":
			return eval(tipo)(username=username, email=email, password=password, nombre=nombre)


class Evento(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	nombre = db.Column(db.String(320), nullable=False)
	descripcion = db.Column(db.Text)
	fecha = db.Column(db.DateTime, nullable=False)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

	@hybrid_property
	def organizador(self):
		return User.query.filter_by(id=self.user_id).first()


class EventoVirtual(Evento):
	id = db.Column(db.Integer, db.ForeignKey('evento.id'), primary_key=True)
	sala_virtual = db.Column(db.String(320), nullable=False)


class EventoPresencial(Evento):
	id = db.Column(db.Integer, db.ForeignKey('evento.id'), primary_key=True)
	ubicacion = db.Column(db.String(320), nullable=False)


class Boleto(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
	evento_id = db.Column(db.Integer, db.ForeignKey('evento_virtual.id'), primary_key=True)
	fecha_compra = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
	boleto_impl = None

	@abstractmethod
	def mostrarAcceso(self):
		pass


class BoletoVirtual(Boleto):
	id = db.Column(db.Integer, db.ForeignKey('boleto.id'), primary_key=True)
	link = db.Column(db.String(320), nullable=False)

	def mostrarAcceso(self):
		datos = self.boleto_impl.mostrarAccesoDev()
		return self.generarLink(datos)

	def generarLink(self, datos):
		return "zoom.us/123456789"


class BoletoPresencial(Boleto):
	id = db.Column(db.Integer, db.ForeignKey('boleto.id'), primary_key=True)
	qr_entrada = db.Column(db.String(20), nullable=False)

	def mostrarAcceso(self):
		datos = self.boleto_impl.mostrarAccesoDev()
		return self.generarQREntrada(datos)
	
	def generarQREntrada(self, datos):
		return f"QR {datos}"

class BoletoImpl(metaclass=ABCMeta):
	@abstractmethod
	def mostrarAccesoDev(self):
		pass

class BoletoGeneralImpl(BoletoImpl):
	def mostrarAccesoDev(self):
		return "General"

class BoletoVIPImpl(BoletoImpl):
	def mostrarAccesoDev(self):
		return "VIP"

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

	def makeEvento(self, nombre, descripcion, fecha, sala_virtual, user):
		return EventoVirtual(nombre=nombre, descripcion=descripcion, fecha=fecha, sala_virtual=sala_virtual, user_id=user.id)


class PresencialFactory(AbstractFactory):
	def makeBoleto(self, user, evento):
		return BoletoPresencial(user_id=user.id, evento_id=evento.id, qr_entrada="") # Generar QR de alguna forma

	def makeEvento(self, nombre, descripcion, fecha, ubicacion, user):
		return EventoPresencial(nombre=nombre, descripcion=descripcion, fecha=fecha, ubicacion=ubicacion, user_id=user.id)
