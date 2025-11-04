from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.orm import relationship
from cryptography.fernet import Fernet
import os

db = SQLAlchemy()

# Clave de encriptación para tokens de Confluence (debe estar en .env en producción)
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key()).encode() if isinstance(os.environ.get('ENCRYPTION_KEY', Fernet.generate_key()), str) else os.environ.get('ENCRYPTION_KEY', Fernet.generate_key())
cipher_suite = Fernet(ENCRYPTION_KEY)

class User(UserMixin, db.Model):
    id = db.Column(sa.Integer, primary_key=True)
    username = db.Column(sa.String(64), unique=True, nullable=False, index=True)
    email = db.Column(sa.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(sa.String(128))
    created_at = db.Column(sa.DateTime, default=datetime.utcnow)
    is_admin = db.Column(sa.Boolean, default=False)
    ai_provider = db.Column(sa.String(20), default='openai')  # 'openai' o 'google'

    # Campos para integración con Confluence
    confluence_email = db.Column(sa.String(120), nullable=True)
    confluence_api_token_encrypted = db.Column(sa.Text, nullable=True)
    confluence_url = db.Column(sa.String(255), nullable=True)
    confluence_default_space = db.Column(sa.String(100), nullable=True)

    # Relación con las transcripciones
    transcriptions = relationship('Transcription', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_transcription_count(self):
        """Devuelve el número de transcripciones realizadas por el usuario"""
        return self.transcriptions.count()
    
    def can_transcribe(self, free_limit):
        """Comprueba si el usuario puede realizar más transcripciones gratuitas"""
        # Aquí podríamos comprobar si tiene una suscripción activa
        # Por ahora, solo comprobamos el límite gratuito
        return self.get_transcription_count() < free_limit

    def set_confluence_token(self, token):
        """Encripta y guarda el token de Confluence"""
        if token:
            encrypted_token = cipher_suite.encrypt(token.encode())
            self.confluence_api_token_encrypted = encrypted_token.decode()

    def get_confluence_token(self):
        """Desencripta y devuelve el token de Confluence"""
        if self.confluence_api_token_encrypted:
            try:
                decrypted_token = cipher_suite.decrypt(self.confluence_api_token_encrypted.encode())
                return decrypted_token.decode()
            except Exception:
                return None
        return None

    def has_confluence_configured(self):
        """Verifica si el usuario tiene Confluence configurado"""
        return bool(self.confluence_email and self.confluence_api_token_encrypted and self.confluence_url)

    def __repr__(self):
        return f'<User {self.username}>'