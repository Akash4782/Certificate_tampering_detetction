# models/certificate_model.py
from database import db
from datetime import datetime
import json

class Certificate(db.Model):
    """Certificate model to store certificate/marksheet information"""
    __tablename__ = 'certificates'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Link to student user
    student_name = db.Column(db.String(150), nullable=False, index=True)
    course_name = db.Column(db.String(150), nullable=False, index=True)
    issue_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    issued_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Admin who issued
    pdf_path = db.Column(db.String(500), nullable=False)
    qr_path = db.Column(db.String(500), nullable=False)
    blockchain_hash = db.Column(db.String(256), unique=True, nullable=False, index=True)
    block_index = db.Column(db.Integer, nullable=True)  # Block index in blockchain
    is_active = db.Column(db.Boolean, default=True)
    
    # Marksheet specific fields (stored as JSON for flexibility)
    marksheet_data = db.Column(db.Text, nullable=True)  # JSON string with all marksheet details
    
    # Relationships
    verification_logs = db.relationship('VerificationLog', backref='certificate', lazy=True, cascade='all, delete-orphan')
    
    def get_marksheet_data(self):
        """Get marksheet data as dictionary"""
        if self.marksheet_data:
            return json.loads(self.marksheet_data)
        return {}
    
    def set_marksheet_data(self, data):
        """Set marksheet data from dictionary"""
        self.marksheet_data = json.dumps(data) if data else None
    
    def __repr__(self):
        return f'<Certificate {self.student_name} - {self.course_name}>'
