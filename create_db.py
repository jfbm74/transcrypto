"""
Script para crear la base de datos e inicializar las tablas.
Ejecutar este script antes de iniciar la aplicación por primera vez.
"""
import os
from flask import Flask
from config import Config
from modules.auth.models import db, User
from modules.transcription.models import Transcription
from modules.subscription.models import Subscription

def create_db():
    # Crear una aplicación Flask mínima
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Inicializar la base de datos
    db.init_app(app)
    
    # Crear las tablas dentro del contexto de la aplicación
    with app.app_context():
        print("Creando tablas de la base de datos...")
        db.create_all()
        
        # Verificar si existe un usuario administrador
        admin = User.query.filter_by(username="admin").first()
        if not admin:
            print("Creando usuario administrador...")
            admin = User(username="admin", email="admin@example.com", is_admin=True)
            admin.set_password("adminpassword")
            db.session.add(admin)
            db.session.commit()
            print("Usuario administrador creado.")
        else:
            print("El usuario administrador ya existe.")
        
        print("Base de datos inicializada correctamente.")

if __name__ == "__main__":
    # Verificar si el directorio instance existe
    if not os.path.exists("instance"):
        os.makedirs("instance")
        print("Directorio 'instance' creado.")
    
    create_db()
    print("\nPuedes iniciar la aplicación con 'python app.py'")