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
        
        if 'acta_text' not in columns:
            # Crear una nueva columna
            with db.engine.begin() as conn:
                conn.execute(sa.text("ALTER TABLE transcription ADD COLUMN acta_text TEXT"))
                print("Columna acta_text añadida a la tabla transcription")
        else:
            print("La columna acta_text ya existe")
        
        # Verificar que la columna se añadió correctamente
        inspector = sa.inspect(db.engine)
        columns = [c['name'] for c in inspector.get_columns('transcription')]
        if 'acta_text' in columns:
            print("Verificación: la columna acta_text está presente en la tabla")
        else:
            print("ERROR: La columna acta_text no se añadió correctamente")

if __name__ == "__main__":
    migrate_database()