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
	# eventos = db.relationship('Evento', backref='creator', lazy=True)

	@hybrid_property
	def tipo(self):
		if Comprador.query.filter_by(id=self.id).first():
			return "Comprador"
		elif Organizador.query.filter_by(id=self.id).first():
			return "Organizador"

	@hybrid_property
	def boletos(self):
		boletos = [boleto for boleto in BoletoPresencial.query.filter_by(user_id=self.id)]
		boletos = boletos + [boleto for boleto in BoletoVirtual.query.filter_by(user_id=self.id)]
		return boletos



class Organizador(User):
	id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)

	@hybrid_property
	def eventos(self):
		eventos = [evento for evento in EventoPresencial.query.filter_by(user_id=self.id)]
		eventos = eventos + [evento for evento in EventoVirtual.query.filter_by(user_id=self.id)]
		return eventos


class Comprador(User):
	id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)


class Factory:
	def makeUsuario(self, tipo, nombre, username, email, password):
		if tipo == "Organizador" or tipo == "Comprador":
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
	evento_id = db.Column(db.Integer, db.ForeignKey('evento.id'))
	fecha_compra = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
	comprado = db.Column(db.Integer) # Booleano

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
		return BoletoVirtual(user_id=user.id, evento_id=evento.id, link=evento.sala_virtual, comprado=0) # Generar link de alguna forma

	def makeEvento(self, nombre, descripcion, fecha, sala_virtual, user, precio_general, precio_vip):
		return EventoVirtual(nombre=nombre, descripcion=descripcion, fecha=fecha, sala_virtual=sala_virtual, user_id=user.id, precio_general=precio_general, precio_vip=precio_vip)


class PresencialFactory(AbstractFactory):
	def makeBoleto(self, user, evento):
		return BoletoPresencial(user_id=user.id, evento_id=evento.id, qr_entrada="", comprado=0) # Generar QR de alguna forma

	def makeEvento(self, nombre, descripcion, fecha, ubicacion, user, precio_general, precio_vip):
		return EventoPresencial(nombre=nombre, descripcion=descripcion, fecha=fecha, ubicacion=ubicacion, user_id=user.id,  precio_general=precio_general, precio_vip=precio_vip)

class Carrito():
	boletos = []
	def set_memento(self, carrito_memento):
		#if not carrito_memento.state:
		#	return

		print("Setting boletos with ", carrito_memento.state)
		self.boletos = carrito_memento.state.copy()
	
	def create_memento(self):
		return CarritoMemento(self)

class CarritoMemento():
	state = []

	def __init__(self, carrito=Carrito()):
		print("Creating memento with ", carrito.boletos)
		self.state = carrito.boletos.copy()

class CarritoManager():
	carrito = Carrito
	carrito_memento = CarritoMemento()

	def __init__(self, carrito):
		self.carrito = carrito
		self.carrito_memento = CarritoMemento(carrito)

	def agregar(self,boleto):
		self.carrito_memento = self.carrito.create_memento()
		self.carrito.boletos.append(boleto)
	
	def elminar(self,boleto):
		self.carrito_memento = self.carrito.create_memento()
		self.carrito.boletos.remove(boleto)
	
	def undo(self):
		self.carrito.set_memento(self.carrito_memento)
		
	def vaciar(self):
		self.carrito_memento = self.carrito.create_memento()
		self.carrito.boletos = []
	
	def comprar(self, session):
		for id in self.carrito.boletos:
			boleto = Boleto.query.filter_by(id=id).first()
			boleto = BoletoVirtual.query.filter_by(id=id).first() if boleto.tipo == "Virtual" else BoletoPresencial.query.filter_by(id=id).first()
			boleto.comprado = 1
			session.commit()
		
		self.vaciar()

	def get_boletos(self):
		return self.carrito.boletos

# Dummy payment processor
class PaymentProcessor:
	def pay(self, data):
		print("Processed payment for ", data)

# Dummy logger
class Logger:
	def log(self, data):
		print(f"{datetime.now()}: {data}")

class Command(metaclass=ABCMeta):
	@abstractmethod
	def execute(self, data):
		pass

class ProcessPaymentCommand(Command):
	def __init__(self, payment_processor):
		self.payment_processor = payment_processor

	def execute(self, data):
		self.payment_processor.pay(data)

class LogTransactionCommand(Command):
	def __init__(self, logger):
		self.logger = logger
	
	def execute(self, data):
		self.logger.log(data)
		