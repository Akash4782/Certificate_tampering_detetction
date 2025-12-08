# config.py
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Flask application configuration"""
    
    # Secret key for session management
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production-2024')
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///bct_project.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File upload configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'certificates'
    QR_FOLDER = 'static/qr'
    
    # Certificate configuration
    CERTIFICATE_TEMPLATE = 'certificate_template.html'
    
    # Pagination
    CERTIFICATES_PER_PAGE = 10
    
    # Blockchain configuration
    BLOCKCHAIN_FILE = 'blockchain_data.json'  # Optional: persist blockchain to file

    # Mail Configuration
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@bctproject.com')


