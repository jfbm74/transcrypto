# Este archivo establece las relaciones entre los modelos
# después de que todos han sido definidos

from modules.auth.models import User, db
from modules.transcription.models import Transcription

# Establecer la relación entre User y Transcription
User.transcriptions = db.relationship('Transcription', backref='user', lazy='dynamic')