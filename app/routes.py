from calendar import c
from flask import render_template, url_for, flash, request, send_file, jsonify, redirect, abort
from app.forms import *
from app.models import *
from app import app, db, bcrypt
from flask_login import login_user, current_user, logout_user, login_required
import os
import secrets

carritos = {}

@app.route('/')
@login_required
def home():
	events = Evento.query.all()
	return render_template('index.html', username=current_user.username, events=events)


@app.route('/register', methods=['GET', 'POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form = RegistrationForm()
	if form.validate_on_submit():
		password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
		factory = Factory()
		user = factory.makeUsuario(form.tipo.data, form.nombre.data, form.username.data, form.email.data, password)
		db.session.add(user)
		db.session.commit()
		return redirect(url_for('home'))
	else:
		print(form.errors)
	return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user and bcrypt.check_password_hash(user.password, form.password.data):
			login_user(user, remember=form.recuerdame.data)
			n = request.args.get('next')
			return redirect(n) if n else redirect(url_for('home'))
	return render_template('login.html', form=form)


@app.route('/evento/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_evento():
	if current_user.tipo != "Organizador":
		abort(403)
	form = EventoForm()
	if form.validate_on_submit():
		factory = eval(form.modalidad.data + "Factory")()
		evento = factory.makeEvento(form.nombre.data, form.descripcion.data, form.fecha.data, form.ubicacion.data if form.modalidad.data == "Presencial" else form.sala_virtual.data, current_user, form.precio_general.data, form.precio_vip.data)
		db.session.add(evento)
		db.session.commit()
		return redirect(url_for('evento', evento_id=evento.id))
	else:
		print(form.errors)
	return render_template('nuevo_evento.html', form=form)


@app.route('/evento/<int:evento_id>')
@login_required
def evento(evento_id):
	evento = Evento.query.filter_by(id=evento_id).first_or_404()
	boleto = Boleto.query.filter_by(user_id=current_user.id, evento_id=evento.id).first()
	if boleto:
		boleto = BoletoVirtual.query.filter_by(id=boleto.id).first() if boleto.tipo == "Virtual" else BoletoPresencial.query.filter_by(id=boleto.id).first()
	else:
		boleto = None
	return render_template('evento.html', evento=evento, boleto=boleto)


@app.route('/evento/<int:evento_id>/comprar', methods=['POST'])
@login_required
def comprar_boleto(evento_id):
	tipo = request.form["comprar"]
	if tipo != "General" and tipo != "VIP":
		abort(404)
	evento = Evento.query.filter_by(id=evento_id).first_or_404()
	evento = EventoVirtual.query.filter_by(id=evento_id).first() if evento.tipo == "Virtual" else EventoPresencial.query.filter_by(id=evento_id).first()
	factory = eval(evento.tipo + "Factory")()
	boleto = factory.makeBoleto(current_user, evento)
	db.session.add(boleto)
	boleto_impl = eval("Boleto" + tipo + "Impl")(boleto_id=boleto.id)
	db.session.add(boleto_impl)
	db.session.commit()
	return redirect(url_for('evento', evento_id=evento.id))


@app.route('/carrito/comprar', methods=['POST'])
@login_required
def comprar_carrito():
	if current_user.id not in carritos:
		carritos[current_user.id] = CarritoManager(carrito=Carrito(), carrito_memento=None)

	commands = []

	commands.append(ProcessPaymentCommand(PaymentProcessor()))
	commands.append(LogTransactionCommand(Logger()))
	
	carritos[current_user.id].comprar(db.session)
	
	for command in commands:
		command.execute(current_user.username)

	return redirect(url_for('profile', username=current_user.username))



@app.route('/carrito/agregar/<int:evento_id>', methods=['POST'])
@login_required
def agregar_carrito(evento_id):
	tipo = request.form["comprar"]
	if tipo != "General" and tipo != "VIP":
		abort(404)
	evento = Evento.query.filter_by(id=evento_id).first_or_404()
	evento = EventoVirtual.query.filter_by(id=evento_id).first() if evento.tipo == "Virtual" else EventoPresencial.query.filter_by(id=evento_id).first()
	factory = eval(evento.tipo + "Factory")()
	boleto = factory.makeBoleto(current_user, evento)
	db.session.add(boleto)
	boleto_impl = eval("Boleto" + tipo + "Impl")(boleto_id=boleto.id)
	db.session.commit()
	db.session.add(boleto_impl)
	if current_user.id not in carritos:
		carritos[current_user.id] = CarritoManager(carrito=Carrito())

	db.session.commit()
	carritos[current_user.id].agregar(boleto.id)

	return redirect(url_for('carrito'))

@app.route('/carrito/vaciar', methods=['POST'])
@login_required
def vaciar_carrito():
	if current_user.id not in carritos:
		carritos[current_user.id] = CarritoManager(carrito=Carrito())
	
	carritos[current_user.id].vaciar()

	return redirect(url_for('carrito'))

@app.route('/carrito/undo', methods=['POST'])
@login_required
def undo_carrito():
	if current_user.id not in carritos:
		carritos[current_user.id] = CarritoManager(carrito=Carrito())
	
	carritos[current_user.id].undo()

	return redirect(url_for('carrito'))


@app.route('/carrito', methods=['GET'])
@login_required
def carrito():
	if current_user.id not in carritos:
		carritos[current_user.id] = CarritoManager(carrito=Carrito())
	
	boletos = []
	for id in carritos[current_user.id].get_boletos():
		boleto = Boleto.query.filter_by(id=id).first()
		boleto = BoletoVirtual.query.filter_by(id=id).first() if boleto.tipo == "Virtual" else BoletoPresencial.query.filter_by(id=id).first()
		boletos.append(boleto)

	return render_template('carrito.html', boletos=boletos)

@app.route('/boleto/mostrar/<int:boleto_id>', methods=['GET'])
@login_required
def mostrar_boleto(boleto_id):
	boleto = Boleto.query.filter_by(id=boleto_id).first()
	boleto = BoletoVirtual.query.filter_by(id=boleto_id).first() if boleto.tipo == "Virtual" else BoletoPresencial.query.filter_by(id=boleto_id).first()

	return render_template('mostrar_boleto.html', boleto=boleto)


@app.route('/user/<username>')
@login_required
def profile(username):
	user = User.query.filter_by(username=username).first_or_404()
	user = Comprador.query.filter_by(id=user.id).first() if user.tipo == "Comprador" else Organizador.query.filter_by(id=user.id).first()
	
	return render_template('profile.html', user=user)


@app.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('home'))
