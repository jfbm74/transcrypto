from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.orm import relationship

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(sa.Integer, primary_key=True)
    username = db.Column(sa.String(64), unique=True, nullable=False, index=True)
    email = db.Column(sa.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(sa.String(128))
    created_at = db.Column(sa.DateTime, default=datetime.utcnow)
    is_admin = db.Column(sa.Boolean, default=False)
    
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
    
    def __repr__(self):
        return f'<User {self.username}>'