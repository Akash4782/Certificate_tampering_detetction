# database.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

def init_db(app):
    """Initialize database and login manager with Flask app"""
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # User loader for Flask-Login
    from models.user_model import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
