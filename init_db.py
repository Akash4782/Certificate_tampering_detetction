# init_db.py
from app import app, db
from models import User, Certificate, VerificationLog
from sqlalchemy import inspect, text

def init_database():
    """Initialize database and create default admin user"""
    with app.app_context():
        # Check if marksheet_data column exists in certificates table
        inspector = inspect(db.engine)
        needs_update = False
        
        if 'certificates' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('certificates')]
            if 'marksheet_data' not in columns:
                print("Adding marksheet_data column to certificates table...")
                try:
                    db.session.execute(text('ALTER TABLE certificates ADD COLUMN marksheet_data TEXT'))
                    db.session.commit()
                    print("✓ Column added successfully!")
                    needs_update = True
                except Exception as e:
                    print(f"Error adding column: {e}")
                    print("Dropping and recreating tables...")
                    db.drop_all()
                    db.create_all()
                    print("✓ Database tables recreated!")
                    needs_update = True
        else:
            # Tables don't exist, create them
            db.create_all()
            print("✓ Database tables created successfully!")
            needs_update = True
        
        if not needs_update:
            # Double check by inspecting columns
            inspector = inspect(db.engine)
            if 'certificates' in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns('certificates')]
                if 'marksheet_data' not in columns:
                    print("marksheet_data column missing, adding it...")
                    try:
                        db.session.execute(text('ALTER TABLE certificates ADD COLUMN marksheet_data TEXT'))
                        db.session.commit()
                        print("✓ Column added!")
                    except Exception as e:
                        print(f"Error: {e}, recreating database...")
                        db.drop_all()
                        db.create_all()
                        print("✓ Database recreated!")
                else:
                    print("✓ Database schema is up to date")
            else:
                db.create_all()
                print("✓ Database tables created!")
        
        # Create default admin user if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@bctproject.com',
                role='admin'
            )
            admin.set_password('admin123')  # Change this in production!
            db.session.add(admin)
            db.session.commit()
            print("✓ Default admin user created:")
            print("  Username: admin")
            print("  Password: admin123")
            print("  ⚠️  Please change the password after first login!")
        else:
            print("✓ Admin user already exists")
        
        # Display statistics
        try:
            user_count = User.query.count()
            cert_count = Certificate.query.count()
            print(f"\nDatabase Statistics:")
            print(f"  Users: {user_count}")
            print(f"  Certificates: {cert_count}")
        except Exception as e:
            print(f"Note: Could not get statistics: {e}")

if __name__ == '__main__':
    init_database()
