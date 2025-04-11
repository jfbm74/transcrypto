from modules.auth.models import db
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.orm import relationship

# Modelo para futura implementación de suscripciones
class Subscription(db.Model):
    id = db.Column(sa.Integer, primary_key=True)
    user_id = db.Column(sa.Integer, sa.ForeignKey('user.id'), nullable=False)
    plan_name = db.Column(sa.String(50), nullable=False)
    start_date = db.Column(sa.DateTime, default=datetime.utcnow)
    end_date = db.Column(sa.DateTime)
    is_active = db.Column(sa.Boolean, default=True)
    
    # Relación con el usuario
    user = relationship('User', backref='subscriptions')
    
    def __repr__(self):
        return f'<Subscription {self.plan_name} for User {self.user_id}>'