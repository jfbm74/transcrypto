import os
from dotenv import load_dotenv

# Cargar variables desde archivo .env
load_dotenv()

# Ruta base de la aplicación
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Configuración básica
    SECRET_KEY = os.environ.get('SECRET_KEY', 'supersecretkey')
    
    # Configuración de la base de datos con ruta absoluta simple
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración para la aplicación de transcripción
    UPLOAD_FOLDER = os.path.join(basedir, "uploads")
    TRANSCRIPT_FOLDER = os.path.join(basedir, "transcripciones")
    STATIC_FOLDER = os.path.join(basedir, "static")
    
    # Clave de API de OpenAI
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    
    # Límites de transcripción
    FREE_TRANSCRIPTIONS_LIMIT = 10