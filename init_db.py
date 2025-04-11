"""
Script para inicializar la base de datos desde cero.
Este script crea el archivo de base de datos y las tablas necesarias.
"""

import os
import sys
from flask import Flask
from config import Config
from modules.auth.models import db, User

def init_database():
    """Inicializa la base de datos y crea un usuario admin"""
    
    # Crear una aplicación temporal para inicializar la base de datos
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Verificar y mostrar dónde se creará la base de datos
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    print(f"Inicializando base de datos en: {db_path}")
    
    # Asegurar que el directorio padre existe
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        print(f"Directorio creado: {db_dir}")
    
    # Inicializar la base de datos
    db.init_app(app)
    
    with app.app_context():
        try:
            # Crear todas las tablas
            db.create_all()
            print("Tablas creadas exitosamente")
            
            # Crear usuario administrador
            if not User.query.filter_by(username="admin").first():
                admin = User(username="admin", email="admin@example.com", is_admin=True)
                admin.set_password("adminpassword")
                db.session.add(admin)
                db.session.commit()
                print("Usuario administrador creado con éxito (usuario: admin, contraseña: adminpassword)")
            else:
                print("El usuario administrador ya existe")
                
            return True
        except Exception as e:
            print(f"Error al inicializar la base de datos: {str(e)}")
            return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)