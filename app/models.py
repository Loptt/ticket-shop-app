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

	@hybrid_property
	def boletos(self):
		boletos = BoletoVirtual.query.filter_by(user_id=self.id)
		boletos = BoletoPresencial.query.filter_by(user_id=self.id) if len(list(boletos)) == 0 else boletos
		return boletos


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
	precio_general = db.Column(db.Float)
	precio_vip = db.Column(db.Float)

	@hybrid_property
	def organizador(self):
		return User.query.filter_by(id=self.user_id).first()

	@hybrid_property
	def tipo(self):
		if EventoVirtual.query.filter_by(id=self.id).first():
			return "Virtual"
		if EventoPresencial.query.filter_by(id=self.id).first():
			return "Presencial"


class EventoVirtual(Evento):
	id = db.Column(db.Integer, db.ForeignKey('evento.id'), primary_key=True)
	sala_virtual = db.Column(db.String(320), nullable=False)


class EventoPresencial(Evento):
	id = db.Column(db.Integer, db.ForeignKey('evento.id'), primary_key=True)
	ubicacion = db.Column(db.String(320), nullable=False)


class Boleto(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	evento_id = db.Column(db.Integer, db.ForeignKey('evento_virtual.id'))
	fecha_compra = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

	@abstractmethod
	def mostrarAcceso(self):
		pass

	@hybrid_property
	def boleto_impl(self):
		boleto = BoletoGeneralImpl.query.filter_by(id=self.id).first()
		return BoletoVIPImpl.query.filter_by(id=self.id).first() if boleto is None else boleto

	@hybrid_property
	def tipo(self):
		if BoletoVirtual.query.filter_by(id=self.id).first():
			return "Virtual"
		if BoletoPresencial.query.filter_by(id=self.id).first():
			return "Presencial"

	@hybrid_property
	def evento(self):
		return Evento.query.filter_by(id=self.evento_id).first()


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

class BoletoImpl(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	boleto_id = db.Column(db.Integer, db.ForeignKey('boleto.id'))

	@abstractmethod
	def mostrarAccesoDev(self):
		pass

class BoletoGeneralImpl(BoletoImpl):
	id = db.Column(db.Integer, db.ForeignKey('boleto_impl.id'), primary_key=True)

	def mostrarAccesoDev(self):
		return "General"

class BoletoVIPImpl(BoletoImpl):
	id = db.Column(db.Integer, db.ForeignKey('boleto_impl.id'), primary_key=True)

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
		return BoletoVirtual(user_id=user.id, evento_id=evento.id, link=evento.sala_virtual) # Generar link de alguna forma

	def makeEvento(self, nombre, descripcion, fecha, sala_virtual, user, precio_general, precio_vip):
		return EventoVirtual(nombre=nombre, descripcion=descripcion, fecha=fecha, sala_virtual=sala_virtual, user_id=user.id, precio_general=precio_general, precio_vip=precio_vip)


class PresencialFactory(AbstractFactory):
	def makeBoleto(self, user, evento):
		return BoletoPresencial(user_id=user.id, evento_id=evento.id, qr_entrada="") # Generar QR de alguna forma

	def makeEvento(self, nombre, descripcion, fecha, ubicacion, user, precio_general, precio_vip):
		return EventoPresencial(nombre=nombre, descripcion=descripcion, fecha=fecha, ubicacion=ubicacion, user_id=user.id,  precio_general=precio_general, precio_vip=precio_vip)
class Carrito():
	boletos = []
	def set_memento(self,boletos):
		boletos = boletos
		pass
	
	def create_memento(self,boletos):
		boletos = boletos
		pass

class CarritoMemento():
	state = Carrito

class CarritoManager():
	carrito = Carrito
	carrito_memento = CarritoMemento

	def agregar(self,boleto):
		self.carrito_memento.state = self.carrito
		self.carrito.boletos.append(boleto)
	
	def elminar(self,boleto):
		self.carrito_memento.state = self.carrito
		self.carrito.boletos.remove(boleto)
	
	def undo(self):
		self.carrito = self.carrito_memento.state
		
	def vaciar(self):
		self.carrito.boletos = []
	
	def comprar(self):
		pass
