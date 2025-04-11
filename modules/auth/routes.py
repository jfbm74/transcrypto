from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse  # Usar urllib.parse en lugar de werkzeug
from modules.auth.models import User, db
from modules.auth.forms import LoginForm, RegistrationForm

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Nombre de usuario o contraseña incorrectos')
            return redirect(url_for('auth.login'))
            
        login_user(user, remember=form.remember_me.data)
        
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':  # Usar urlparse en lugar de url_parse
            next_page = url_for('index')
            
        return redirect(next_page)
        
    return render_template('auth/login.html', title='Iniciar sesión', form=form)

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        flash('¡Felicidades, ahora estás registrado!')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html', title='Registro', form=form)

@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html', title='Perfil')