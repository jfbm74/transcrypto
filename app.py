from flask import Flask, render_template, redirect, url_for, flash, send_file, jsonify, request
import os
from config import Config
from modules.auth.models import db, User
from modules.auth import login_manager
from modules.auth.routes import auth_bp
from modules.transcription.routes import transcription_bp
from flask_migrate import Migrate
# Importar el archivo que establece las relaciones
import modules.models

def create_app(config_class=Config):
    """Crea y configura la aplicación Flask"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Crear carpetas necesarias
    create_required_folders(app)
    
    # Inicializar extensiones
    db.init_app(app)
    login_manager.init_app(app)
    migrate = Migrate(app, db)
    
    # Añadir filtros personalizados de Jinja2
    @app.template_filter('nl2br')
    def nl2br_filter(s):
        if s is None:
            return ""
        return s.replace('\n', '<br>')
    
    # Registrar blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(transcription_bp)
    
    # Configurar rutas principales
    @app.route("/")
    def index():
        return render_template("index.html")
    
    @app.route("/api-settings")
    def api_settings():
        return render_template("api_settings.html")
    
    @app.route("/set-api-key", methods=["POST"])
    def set_api_key():
        # Ruta para configurar la clave de API
        try:
            data = request.get_json()
            api_type = data.get("api_type", "openai")
            
            if api_type == "openai":
                api_key = data.get("api_key", "")
                if not api_key:
                    return jsonify({"success": False, "error": "No se proporcionó una clave de API válida"})
                app.config['OPENAI_API_KEY'] = api_key
            elif api_type == "google":
                api_key = data.get("google_api_key", "")
                if not api_key:
                    return jsonify({"success": False, "error": "No se proporcionó una clave de Google AI válida"})
                app.config['GOOGLE_AI_API_KEY'] = api_key
            
            return jsonify({"success": True, "message": "Clave de API configurada correctamente"})
            
        except Exception as e:
            app.logger.error(f"Error al configurar la clave de API: {str(e)}")
            return jsonify({"success": False, "error": str(e)})
    
    # Manejo de errores
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500
        
    return app

def create_required_folders(app):
    """Crea las carpetas necesarias para la aplicación"""
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["TRANSCRIPT_FOLDER"], exist_ok=True)
    os.makedirs(os.path.join("static", "css"), exist_ok=True)
    os.makedirs(os.path.join("static", "img"), exist_ok=True)
    
    # Crear el archivo CSS si no existe
    css_path = os.path.join("static", "css", "styles.css")
    if not os.path.exists(css_path):
        with open(css_path, "w", encoding="utf-8") as f:
            # Contenido básico de CSS
            f.write("/* Estilos para la aplicación de transcripción */")

if __name__ == "__main__":
    app = create_app()
    
    # Crear las tablas de la base de datos si no existen
    with app.app_context():
        # Asegurar que la base de datos se inicializa correctamente
        try:
            db.create_all()
            
            # Crear un usuario administrador si no existe
            admin = User.query.filter_by(username="admin").first()
            if not admin:
                admin = User(username="admin", email="admin@example.com", is_admin=True)
                admin.set_password("adminpassword")
                db.session.add(admin)
                db.session.commit()
                print("Usuario administrador creado con éxito.")
        except Exception as e:
            print(f"Error al inicializar la base de datos: {str(e)}")
            
    app.run(debug=True)