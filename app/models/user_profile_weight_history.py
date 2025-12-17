from datetime import datetime
from app.extensions import db

class UserProfileWeightHistory(db.Model):
    __tablename__ = "user_profile_weight_history"

    id = db.Column(db.BigInteger, primary_key=True)
    user_profile_id = db.Column(db.BigInteger, db.ForeignKey("user_profiles.id"), nullable=False)
    height_cm = db.Column(db.Float)
    weight_kg = db.Column(db.Float)
    bmi = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
