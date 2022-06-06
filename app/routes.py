from flask import render_template, url_for, flash, request, send_file, jsonify, redirect, abort
from app.forms import *
from app.models import *
from app import app, db, bcrypt
from flask_login import login_user, current_user, logout_user, login_required
import os
import secrets


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
		evento = factory.makeEvento(form.nombre.data, form.descripcion.data, form.fecha.data, form.ubicacion.data if form.modalidad.data == "Presencial" else form.sala_virtual.data, current_user)
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
	return render_template('evento.html', evento=evento)


@app.route('/user/<username>')
@login_required
def profile(username):
	user = User.query.filter_by(username=username).first_or_404()
	return render_template('profile.html', user=user)


@app.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('home'))
