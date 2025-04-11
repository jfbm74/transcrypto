from flask_login import LoginManager
from modules.auth.models import User

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, inicia sesión para acceder a esta página.'

@login_manager.user_loader
def load_user(id):
    # En Flask-SQLAlchemy 3.0+ se recomienda usar get_or_404 o usar filtros explícitos
    return User.query.filter_by(id=int(id)).first()