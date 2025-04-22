from flask import Flask
from config import Config
from modules.auth.models import db
from modules.transcription.models import Transcription
import sqlalchemy as sa

def migrate_database():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        # Verificar si la columna ya existe
        inspector = sa.inspect(db.engine)
        columns = [c['name'] for c in inspector.get_columns('transcription')]
        
        if 'document_type' not in columns:
            # Crear una nueva columna
            with db.engine.begin() as conn:
                conn.execute(sa.text("ALTER TABLE transcription ADD COLUMN document_type VARCHAR(20) DEFAULT 'acta'"))
                print("Columna document_type añadida a la tabla transcription")
        else:
            print("La columna document_type ya existe")
        
        # Verificar que la columna se añadió correctamente
        inspector = sa.inspect(db.engine)
        columns = [c['name'] for c in inspector.get_columns('transcription')]
        if 'document_type' in columns:
            print("Verificación: la columna document_type está presente en la tabla")
        else:
            print("ERROR: La columna document_type no se añadió correctamente")

if __name__ == "__main__":
    migrate_database()