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
    document_type = db.Column(sa.String(20), default='acta')
    processing_time = db.Column(sa.Float)
    created_at = db.Column(sa.DateTime, default=datetime.utcnow)

    # Campos para integración con Confluence
    confluence_page_id = db.Column(sa.String(50), nullable=True)
    confluence_page_url = db.Column(sa.String(500), nullable=True)
    confluence_published_at = db.Column(sa.DateTime, nullable=True)

    # Campos para diarización de hablantes
    has_diarization = db.Column(sa.Boolean, default=False)
    speakers_count = db.Column(sa.Integer, nullable=True)
    diarization_segments = db.Column(sa.Text, nullable=True)  # JSON string con segmentos

    def __repr__(self):
        return f'<Transcription {self.original_filename}>'
