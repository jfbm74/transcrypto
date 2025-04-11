from modules.auth.models import db
from datetime import datetime
import sqlalchemy as sa

class Transcription(db.Model):
    id = db.Column(sa.Integer, primary_key=True)
    user_id = db.Column(sa.Integer, sa.ForeignKey('user.id'), nullable=False)
    original_filename = db.Column(sa.String(255), nullable=False)
    file_path = db.Column(sa.String(255), nullable=False)
    transcript_path = db.Column(sa.String(255), nullable=False)
    transcript_text = db.Column(sa.Text)
    acta_text = db.Column(sa.Text, nullable=True)
    processing_time = db.Column(sa.Float)
    created_at = db.Column(sa.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Transcription {self.original_filename}>'
