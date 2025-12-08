# models/verification_log_model.py
from database import db
from datetime import datetime

class VerificationLog(db.Model):
    """Verification log model to track certificate verification attempts"""
    __tablename__ = 'verification_logs'

    id = db.Column(db.Integer, primary_key=True)
    certificate_id = db.Column(db.Integer, db.ForeignKey('certificates.id'), nullable=True)  # Nullable if hash not found
    blockchain_hash = db.Column(db.String(256), nullable=False, index=True)  # Hash that was verified
    verified_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    status = db.Column(db.String(50), nullable=False)  # 'Valid' or 'Invalid'
    ip_address = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    
    def __repr__(self):
        return f'<VerificationLog {self.status} - {self.verified_at}>'