from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
import hashlib
import json
import pdfkit
import os
import base64
from datetime import datetime
from functools import wraps
from io import BytesIO
import io
import csv

from flask_mail import Mail, Message

from config import Config
from database import db, init_db, login_manager
from blockchain import Blockchain
from models import User, Certificate, VerificationLog

# Initialize Flask app
app = Flask(__name__)
# Add ProxyFix for proper URL generation behind proxies (like Nginx/PythonAnywhere)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
app.config.from_object(Config)

# Initialize Mail
mail = Mail(app)

# Initialize extensions
init_db(app)

# Initialize Database & Default Admin (Critical for first run on Railway)
with app.app_context():
    db.create_all()
    # Check if admin exists
    if not User.query.filter_by(username='admin').first():
        print("Creating default admin user...")
        admin = User(username='admin', email='admin@certificateverifier.com', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("✓ Default admin created: admin / admin123")

# Initialize blockchain
blockchain = Blockchain(persist_file=app.config.get('BLOCKCHAIN_FILE'))

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['QR_FOLDER'], exist_ok=True)


# Decorators
def admin_required(f):
    """Require admin role to access route"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('student_dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def get_base_url():
    """Get the base URL for the application"""
    try:
        # Try to get from request context
        from flask import request
        return request.url_root.rstrip('/')
    except:
        # Fallback to localhost for development
        return 'http://localhost:5000'




def send_certificate_email(student_email, student_name, certificate):
    """Send email with certificate attachment"""
    try:
        if not app.config.get('MAIL_USERNAME'):
            print(f"📧 Mock Email to {student_email}: Certificate Issued (ID: {certificate.id})")
            return True
            
        subject = f"Certificate Issued - {certificate.course_name}"
        msg = Message(subject, recipients=[student_email])
        
        # Render HTML body
        msg.html = render_template('email_notification.html',
            name=student_name,
            course=certificate.course_name,
            cert_id=certificate.id,
            date=certificate.issue_date.strftime('%B %d, %Y'),
            block_index=certificate.block_index,
            verify_url=url_for('verify', _external=True, cert_id=certificate.id, hash=certificate.blockchain_hash),
            year=datetime.now().year
        )
        
        # Attach PDF
        with app.open_resource(certificate.pdf_path) as fp:
            msg.attach(f"{student_name}_Certificate.pdf", "application/pdf", fp.read())
            
        mail.send(msg)
        return True
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False


# Routes
@app.route('/')
def index():
    """Redirect to login"""
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))


@app.route('/health')
def health():
    """Health check endpoint for Render"""
    return {'status': 'healthy', 'service': 'Certificate Tampering Detection'}, 200


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Please provide both username and password.', 'error')
            return render_template('login.html')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=True)
            flash(f'Welcome back, {user.username}!', 'success')
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            if user.is_admin():
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('login.html')


@app.route('/register')
def register():
    """Registration disabled - only admins can create accounts"""
    flash('Registration is disabled. Please contact your administrator to create an account.', 'info')
    return redirect(url_for('login'))


@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))


@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard with analytics"""
    # Statistics
    total_certificates = Certificate.query.count()
    total_students = User.query.filter_by(role='student').count()
    recent_certificates = Certificate.query.order_by(Certificate.issue_date.desc()).limit(5).all()
    recent_verifications = VerificationLog.query.order_by(VerificationLog.verified_at.desc()).limit(10).all()

    # Blockchain info
    chain_info = blockchain.get_chain_info()

    # Certificates by month (for chart - Last 6 months)
    certificates_by_month = {}
    
    # improved chart data generation
    end_date = datetime.now()
    chart_labels = []
    chart_data = []
    
    # Generate last 6 months buckets
    for i in range(5, -1, -1):
        # Calculate month and year
        # Create a date object for the first day of the 'i'th month ago
        if end_date.month - i > 0:
            month = end_date.month - i
            year = end_date.year
        else:
            month = (end_date.month - i) % 12
            if month == 0: month = 12
            year = end_date.year - 1 + ((end_date.month - i) // 12)
            
        month_label = f"{datetime(year, month, 1).strftime('%b %Y')}"
        month_key = f"{year}-{month:02d}"
        
        chart_labels.append(month_label)
        
        # Count certificates for this month
        count = Certificate.query.filter(
            db.extract('year', Certificate.issue_date) == year,
            db.extract('month', Certificate.issue_date) == month
        ).count()
        chart_data.append(count)

    return render_template('admin_dashboard.html',
                         total_certificates=total_certificates,
                         total_students=total_students,
                         recent_certificates=recent_certificates,
                         recent_verifications=recent_verifications,
                         chain_info=chain_info,
                         chart_labels=json.dumps(chart_labels),
                         chart_data=json.dumps(chart_data))



@app.route('/admin/batch-issue', methods=['GET', 'POST'])
@admin_required
def admin_batch_issue():
    """Batch issue certificates from CSV"""
    if request.method == 'POST':
        # 1. Get Common Details
        degree_name = request.form.get('degree_name', '').strip()
        university_name = request.form.get('university_name', '').strip()
        result_date = request.form.get('result_date', '').strip()
        
        if not degree_name or not university_name or not result_date:
            flash('Please fill in all common details.', 'error')
            return redirect(url_for('admin_batch_issue'))

        try:
            result_date_obj = datetime.strptime(result_date, '%Y-%m-%d')
        except ValueError:
            flash('Invalid date format.', 'error')
            return redirect(url_for('admin_batch_issue'))

        # 2. Get CSV File
        if 'csv_file' not in request.files:
            flash('No CSV file uploaded.', 'error')
            return redirect(url_for('admin_batch_issue'))
            
        csv_file = request.files['csv_file']
        if not csv_file or not csv_file.filename.endswith('.csv'):
            flash('Please upload a valid CSV file.', 'error')
            return redirect(url_for('admin_batch_issue'))

        # 3. Process CSV
        try:
            stream = io.StringIO(csv_file.stream.read().decode("UTF8"), newline=None)
            csv_reader = csv.DictReader(stream)
            
            # Validate headers
            required_headers = ['Student Name', 'Email', 'Roll Number', 'Marks']
            if not all(h in csv_reader.fieldnames for h in required_headers):
                flash(f'CSV missing required headers. Expected: {", ".join(required_headers)}', 'error')
                return redirect(url_for('admin_batch_issue'))
                
            success_count = 0
            errors = []
            
            # PDF Config (Reusable)
            wkhtmltopdf_path = os.environ.get('WKHTMLTOPDF_PATH')
            if not wkhtmltopdf_path:
                # Fallback for Windows local dev
                possible_paths = [
                    r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe",
                    r"C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe"
                ]
                for path in possible_paths:
                    if os.path.exists(path):
                        wkhtmltopdf_path = path
                        break
            
            # If still not found (e.g. on Linux/Mac), pdfkit might find it in PATH automatically
            # or we set it to None to let pdfkit decide (usually 'wkhtmltopdf')
            
            if wkhtmltopdf_path and os.path.exists(wkhtmltopdf_path):
                config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
            else:
                config = pdfkit.configuration() # Let pdfkit find it in PATH

            options = {
                'enable-local-file-access': None,
                'page-size': 'A4',
                'margin-top': '10mm',
                'margin-bottom': '10mm',
                'margin-left': '10mm',
                'margin-right': '10mm'
            }
            base_url = get_base_url()

            for row_idx, row in enumerate(csv_reader):
                try:
                    student_name = row['Student Name'].strip()
                    email = row['Email'].strip()
                    roll_number = row['Roll Number'].strip()
                    marks_str = row['Marks'].strip()
                    
                    if not student_name or not roll_number:
                        continue # Skip empty rows

                    # Parse marks
                    subjects = []
                    if ':' in marks_str:
                        items = marks_str.split(',')
                        for item in items:
                            if ':' in item:
                                s_name, s_grade = item.split(':')
                                subjects.append({
                                    'code': s_name.strip()[:3].upper() + '101',
                                    'type': 'Core',
                                    'credits': '4',
                                    'grade': s_grade.strip(),
                                    'internal_marks': '-',
                                    'external_marks': '-'
                                })
                    else:
                        subjects.append({
                            'code': 'GEN101',
                            'type': 'Core',
                            'credits': '4',
                            'grade': marks_str,
                            'internal_marks': '-',
                            'external_marks': '-'
                        })

                    # Check/Create Student User
                    student_user = None
                    if email:
                        student_user = User.query.filter_by(email=email).first()
                        if not student_user:
                            username = email.split('@')[0]
                            if User.query.filter_by(username=username).first():
                                username = f"{username}_{int(datetime.now().timestamp())}"
                                
                            student_user = User(username=username, email=email, role='student')
                            student_user.set_password('default123')
                            db.session.add(student_user)
                            db.session.flush()

                    # Prepare Marksheet Data
                    marksheet_data = {
                        'university_name': university_name,
                        'university_address': 'Global Blockchain Campus',
                        'roll_number': roll_number,
                        'college_id': 'COL-001',
                        'college_name': 'School of Engineering',
                        'student_name': student_name,
                        'father_name': '',
                        'mother_name': '',
                        'degree_name': degree_name,
                        'semester_info': 'Final', 
                        'result_date': result_date,
                        'subjects': subjects
                    }

                    # --- Certificate Generation Logic ---
                    cert_id = f"{roll_number}_{int(datetime.utcnow().timestamp())}_{row_idx}"
                    pdf_filename = secure_filename(f"{student_name}_{roll_number}.pdf")
                    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
                    qr_filename = secure_filename(f"{cert_id}.png")
                    qr_path = os.path.join(app.config['QR_FOLDER'], qr_filename)
                    
                    # Ensure QR folder exists
                    os.makedirs(app.config['QR_FOLDER'], exist_ok=True)
                    
                    # Iterative Hash Convergence
                    previous_hash = None
                    current_hash = None
                    iteration = 0
                    
                    print(f"\n{'='*60}")
                    print(f"Processing: {student_name} ({roll_number})")
                    print(f"{'='*60}")
                    
                    while iteration < 5:
                        iteration += 1
                        print(f"\n🔄 Iteration {iteration}:")
                        
                        verification_url = f"{base_url}/verify?cert_id={cert_id}"
                        if current_hash:
                            verification_url += f"&hash={current_hash}"
                        
                        print(f"   URL: {verification_url}")
                        
                        
                        
                        # Render HTML with base64 QR
                        html = render_template('certificate_template.html',
                            name=student_name,
                            roll_number=roll_number,
                            father_name='',
                            mother_name='',
                            college_id='COL-001',
                            college_name='School of Engineering',
                            university_name=university_name,
                            university_address='Global Blockchain Campus',
                            degree_name=degree_name,
                            semester_info='Final',
                            result_date=result_date_obj.strftime('%d.%m.%Y'),
                            issue_date=result_date_obj.strftime('%B %d, %Y'),
                            subjects=subjects,

                            # qr_code_base64 removed
                            # qr_code_path removed
                            cert_hash=current_hash or '',
                            cert_id=cert_id,
                            verification_url=verification_url
                        )
                        
                        # Generate PDF
                        pdfkit.from_string(html, pdf_path, configuration=config, options=options)
                        print(f"   ✓ PDF generated: {pdf_path}")
                        
                        # Compute hash
                        with open(pdf_path, 'rb') as f:
                            current_hash = hashlib.sha256(f.read()).hexdigest()
                        
                        print(f"   📊 Hash: {current_hash[:16]}...")
                        
                        if previous_hash == current_hash:
                            print(f"   ✅ Hash converged!")
                            break
                        previous_hash = current_hash

                    # Add to Blockchain
                    blockchain_data = json.dumps({'cert_id': cert_id, 'pdf_hash': current_hash}, sort_keys=True)
                    new_block = blockchain.add_block(blockchain_data)
                    print(f"\n✓ Added to blockchain at block #{new_block.index}")

                    # Save to DB
                    cert = Certificate(
                        student_id=student_user.id if student_user else None,
                        student_name=student_name,
                        course_name=degree_name,
                        issue_date=result_date_obj,
                        issued_by=current_user.id,
                        pdf_path=pdf_path,
                        qr_path=qr_path,
                        blockchain_hash=current_hash,
                        block_index=new_block.index
                    )
                    cert.set_marksheet_data(marksheet_data)
                    db.session.add(cert)
                    db.session.flush()
                    
                    # Send email
                    if email:
                        send_certificate_email(email, student_name, cert)
                        
                    success_count += 1
                    print(f"✅ Certificate saved to database\n")
                    
                except Exception as e:
                    errors.append(f"Row {row_idx+1}: {str(e)}")
                    print(f"❌ Error processing row {row_idx}: {e}\n")

            db.session.commit()
            
            if success_count > 0:
                flash(f'✅ Successfully issued {success_count} certificates!', 'success')
            
            if errors:
                flash(f'⚠️ Encountered {len(errors)} errors: {"; ".join(errors[:3])}...', 'warning')
                
            return redirect(url_for('admin_certificates'))

        except Exception as e:
            flash(f'❌ Error processing CSV: {str(e)}', 'error')
            print(f"CSV Error: {e}")
            return redirect(url_for('admin_batch_issue'))

    return render_template('admin_batch_issue.html')


@app.route('/admin/sample-csv')
@admin_required
def download_sample_csv():
    """Download sample CSV for batch issue"""
    csv_content = "Student Name,Email,Roll Number,Marks\nJohn Doe,john@example.com,CSE001,Blockchain:A+\nJane Smith,jane@example.com,CSE002,Cryptography:A"
    
    mem = io.BytesIO()
    mem.write(csv_content.encode('utf-8'))
    mem.seek(0)
    
    return send_file(
        mem,
        mimetype='text/csv',
        as_attachment=True,
        download_name='sample_students.csv'
    )


@app.route('/admin/issue', methods=['GET', 'POST'])
@admin_required
def admin_issue():
    """Issue new marksheet/certificate"""
    if request.method == 'POST':
        # Collect all form data
        student_name = request.form.get('student_name', '').strip()
        student_email = request.form.get('student_email', '').strip()
        roll_number = request.form.get('roll_number', '').strip()
        father_name = request.form.get('father_name', '').strip()
        mother_name = request.form.get('mother_name', '').strip()
        college_id = request.form.get('college_id', '').strip()
        college_name = request.form.get('college_name', '').strip()
        university_name = request.form.get('university_name', '').strip()
        university_address = request.form.get('university_address', '').strip()
        degree_name = request.form.get('degree_name', '').strip()
        semester_info = request.form.get('semester_info', '').strip()
        result_date = request.form.get('result_date', '').strip()

        # Collect subjects
        subject_codes = request.form.getlist('subject_code[]')
        subject_types = request.form.getlist('subject_type[]')
        subject_credits = request.form.getlist('subject_credits[]')
        subject_grades = request.form.getlist('subject_grade[]')
        subject_internal = request.form.getlist('subject_internal[]')
        subject_external = request.form.getlist('subject_external[]')

        # Validation
        if not student_name or not roll_number or not result_date:
            flash('Please fill in all required fields.', 'error')
            return render_template('admin_issue.html')

        if not subject_codes or len(subject_codes) == 0:
            flash('Please add at least one subject.', 'error')
            return render_template('admin_issue.html')

        try:
            result_date_obj = datetime.strptime(result_date, '%Y-%m-%d')
        except ValueError:
            flash('Invalid date format.', 'error')
            return render_template('admin_issue.html')

        # Build subjects list
        subjects = []
        for i in range(len(subject_codes)):
            if subject_codes[i].strip():
                subjects.append({
                    'code': subject_codes[i].strip(),
                    'type': subject_types[i].strip() if i < len(subject_types) else '',
                    'credits': subject_credits[i] if i < len(subject_credits) else '0',
                    'grade': subject_grades[i] if i < len(subject_grades) else '',
                    'internal_marks': subject_internal[i] if i < len(subject_internal) and subject_internal[i] else '-',
                    'external_marks': subject_external[i] if i < len(subject_external) and subject_external[i] else '-'
                })

        course_name = degree_name or semester_info or 'Marksheet'

        # Check if student exists
        student_user = None
        if student_email:
            student_user = User.query.filter_by(email=student_email).first()
            if not student_user:
                email_prefix = student_email.split('@')[0]
                student_user = User.query.filter_by(username=email_prefix).first()

        if not student_user and student_name:
            student_user = User.query.filter(
                (User.username.ilike(f"%{student_name}%")) |
                (User.email.ilike(f"%{student_name}%"))
            ).filter_by(role='student').first()

        if not student_user and student_email:
            student_user = User(
                username=student_email.split('@')[0],
                email=student_email,
                role='student'
            )
            student_user.set_password('default123')
            db.session.add(student_user)
            db.session.flush()

        # Build marksheet data
        marksheet_data = {
            'university_name': university_name,
            'university_address': university_address,
            'roll_number': roll_number,
            'college_id': college_id,
            'college_name': college_name,
            'student_name': student_name,
            'father_name': father_name,
            'mother_name': mother_name,
            'degree_name': degree_name,
            'semester_info': semester_info,
            'result_date': result_date,
            'subjects': subjects
        }

        # Generate unique certificate ID
        cert_id = f"{roll_number}_{int(datetime.utcnow().timestamp())}"

        # Generate PDF marksheet filename
        pdf_filename = secure_filename(f"{student_name}_{roll_number}.pdf")
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)

        # Ensure QR folder exists
        os.makedirs(app.config['QR_FOLDER'], exist_ok=True)

        base_url = get_base_url()
        qr_filename = secure_filename(f"{cert_id}.png")
        qr_path = os.path.join(app.config['QR_FOLDER'], qr_filename)
        
        # Initialize hash iteration
        previous_hash = None
        current_hash = None
        max_iterations = 5
        iteration = 0
        
        # PDF generation config
        wkhtmltopdf_path = os.environ.get('WKHTMLTOPDF_PATH')
        if not wkhtmltopdf_path:
            # Fallback for Windows local dev
            possible_paths = [
                r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe",
                r"C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe"
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    wkhtmltopdf_path = path
                    break
                    
        if wkhtmltopdf_path and os.path.exists(wkhtmltopdf_path):
            config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
        else:
            config = pdfkit.configuration()

        options = {
            'enable-local-file-access': None,
            'page-size': 'A4',
            'margin-top': '10mm',
            'margin-bottom': '10mm',
            'margin-left': '10mm',
            'margin-right': '10mm'
        }
        
        print(f"\n{'='*60}")
        print(f"Generating certificate for: {student_name}")
        print(f"Roll Number: {roll_number}")
        print(f"{'='*60}")
        
        # Iterate until hash stabilizes
        while iteration < max_iterations:
            iteration += 1
            
            print(f"\n🔄 Iteration {iteration}:")
            
            # Generate verification URL
            if current_hash:
                verification_url = f"{base_url}/verify?cert_id={cert_id}&hash={current_hash}"
            else:
                verification_url = f"{base_url}/verify?cert_id={cert_id}"
            
            print(f"   URL: {verification_url}")
            

            # Generate PDF with QR code embedded
            print(f"   ⏳ Rendering HTML template...")
            html = render_template(
                'certificate_template.html',
                name=student_name,
                roll_number=roll_number,
                father_name=father_name,
                mother_name=mother_name,
                college_id=college_id,
                college_name=college_name,
                university_name=university_name,
                university_address=university_address,
                degree_name=degree_name,
                semester_info=semester_info,
                result_date=result_date_obj.strftime('%d.%m.%Y'),
                issue_date=result_date_obj.strftime('%B %d, %Y'),
                subjects=subjects,

                # qr_code_base64 removed
                # qr_code_path removed
                cert_hash=current_hash or '',
                cert_id=cert_id,
                verification_url=verification_url
            )
            
            print(f"   ✓ HTML rendered")
            
            try:
                print(f"   ⏳ Generating PDF...")
                pdfkit.from_string(html, pdf_path, configuration=config, options=options)
                print(f"   ✓ PDF generated: {pdf_path}")
                
            except Exception as e:
                flash(f'❌ PDF generation error: {str(e)}. Please ensure wkhtmltopdf is installed.', 'error')
                print(f"❌ PDF Error: {e}")
                return render_template('admin_issue.html')
            
            # Compute hash of generated PDF
            try:
                with open(pdf_path, 'rb') as f:
                    pdf_bytes = f.read()
                previous_hash = current_hash
                current_hash = hashlib.sha256(pdf_bytes).hexdigest()
                
                print(f"   📊 Hash: {current_hash[:16]}...")
                
            except Exception as e:
                flash(f'❌ Error computing hash: {str(e)}', 'error')
                print(f"❌ Hash Error: {e}")
                return render_template('admin_issue.html')
            
            # Check convergence
            if previous_hash == current_hash:
                print(f"   ✅ Hash converged! Stable after iteration {iteration}")
                break
        
        final_pdf_hash = current_hash
        
        print(f"\n📋 Final Hash: {final_pdf_hash}")
        
        # Store final hash on blockchain
        try:
            print(f"⏳ Adding to blockchain...")
            blockchain_data = json.dumps({
                'cert_id': cert_id,
                'pdf_hash': final_pdf_hash
            }, sort_keys=True)
            new_block = blockchain.add_block(blockchain_data)
            print(f"✅ Added to blockchain at block #{new_block.index}")
            
        except Exception as e:
            flash(f'❌ Blockchain error: {str(e)}', 'error')
            print(f"❌ Blockchain Error: {e}")
            return render_template('admin_issue.html')

        # Save certificate to database
        try:
            print(f"⏳ Saving to database...")
            certificate = Certificate(
                student_id=student_user.id if student_user else None,
                student_name=student_name,
                course_name=course_name,
                issue_date=result_date_obj,
                issued_by=current_user.id,
                pdf_path=pdf_path,
                qr_path=qr_path,
                blockchain_hash=final_pdf_hash,
                block_index=new_block.index
            )
            certificate.set_marksheet_data(marksheet_data)
            db.session.add(certificate)
            db.session.commit()
            print(f"✅ Certificate saved to database")

            # Send email
            if student_email:
                send_certificate_email(student_email, student_name, certificate)

            flash(f'✅ Marksheet issued successfully for {student_name}! Certificate ID: {cert_id}', 'success')
            print(f"\n{'='*60}")
            print(f"✅ PROCESS COMPLETE")
            print(f"{'='*60}\n")
            return redirect(url_for('admin_certificates'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Database error: {str(e)}', 'error')
            print(f"❌ Database Error: {e}")
            return render_template('admin_issue.html')

    return render_template('admin_issue.html')


@app.route('/admin/students', methods=['GET', 'POST'])
@admin_required
def admin_students():
    """Manage students - create, view, and manage student accounts"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not email or not password:
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('admin_students'))

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return redirect(url_for('admin_students'))

        if User.query.filter_by(username=username).first():
            flash(f'Username "{username}" already exists. Please choose a different one.', 'error')
            return redirect(url_for('admin_students'))

        if User.query.filter_by(email=email).first():
            flash(f'Email "{email}" is already registered.', 'error')
            return redirect(url_for('admin_students'))

        new_student = User(
            username=username,
            email=email,
            role='student'
        )
        new_student.set_password(password)

        try:
            db.session.add(new_student)
            db.session.commit()
            flash(f'✅ Student account created successfully! Username: {username}', 'success')
            return redirect(url_for('admin_students'))
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error creating student account: {str(e)}', 'error')
            return redirect(url_for('admin_students'))

    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()

    query = User.query.filter_by(role='student')

    if search:
        query = query.filter(
            (User.username.contains(search)) |
            (User.email.contains(search))
        )

    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page,
        per_page=app.config['CERTIFICATES_PER_PAGE'],
        error_out=False
    )

    students = pagination.items

    return render_template('admin_students.html',
                         students=students,
                         pagination=pagination,
                         search=search)


@app.route('/admin/students/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_student(user_id):
    """Delete a student account"""
    student = User.query.get_or_404(user_id)

    if student.role != 'student':
        flash('Only student accounts can be deleted through this route.', 'error')
        return redirect(url_for('admin_students'))

    cert_count = Certificate.query.filter_by(student_id=user_id).count()
    if cert_count > 0:
        flash(f'❌ Cannot delete student. They have {cert_count} certificate(s) associated.', 'error')
        return redirect(url_for('admin_students'))

    try:
        db.session.delete(student)
        db.session.commit()
        flash(f'✅ Student "{student.username}" deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Error deleting student: {str(e)}', 'error')

    return redirect(url_for('admin_students'))


@app.route('/admin/students/<int:user_id>/reset-password', methods=['POST'])
@admin_required
def reset_student_password(user_id):
    """Reset student password"""
    student = User.query.get_or_404(user_id)

    if student.role != 'student':
        flash('Only student passwords can be reset through this route.', 'error')
        return redirect(url_for('admin_students'))

    new_password = request.form.get('new_password', '').strip()

    if not new_password or len(new_password) < 6:
        flash('Password must be at least 6 characters long.', 'error')
        return redirect(url_for('admin_students'))

    try:
        student.set_password(new_password)
        db.session.commit()
        flash(f'✅ Password reset successfully for "{student.username}".', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Error resetting password: {str(e)}', 'error')

    return redirect(url_for('admin_students'))


@app.route('/admin/certificates')
@admin_required
def admin_certificates():
    """View all certificates with search and pagination"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    course_filter = request.args.get('course', '').strip()

    query = Certificate.query

    if search:
        query = query.filter(
            (Certificate.student_name.contains(search)) |
            (Certificate.course_name.contains(search)) |
            (Certificate.blockchain_hash.contains(search))
        )

    if course_filter:
        query = query.filter(Certificate.course_name == course_filter)

    pagination = query.order_by(Certificate.issue_date.desc()).paginate(
        page=page,
        per_page=app.config['CERTIFICATES_PER_PAGE'],
        error_out=False
    )

    certificates = pagination.items
    courses = db.session.query(Certificate.course_name.distinct()).all()
    course_list = [c[0] for c in courses]

    return render_template('admin_certificates.html',
                         certificates=certificates,
                         pagination=pagination,
                         search=search,
                         course_filter=course_filter,
                         courses=course_list)


@app.route('/student/dashboard')
@login_required
def student_dashboard():
    """Student dashboard"""
    if current_user.is_admin():
        certificates = Certificate.query.order_by(Certificate.issue_date.desc()).all()
    else:
        linked_certs = Certificate.query.filter_by(student_id=current_user.id).all()
        name_matched_certs = Certificate.query.filter(
            Certificate.student_name.ilike(f"%{current_user.username}%")
        ).filter(
            Certificate.student_id.is_(None)
        ).all()

        all_cert_ids = {c.id for c in linked_certs}
        for cert in name_matched_certs:
            if cert.id not in all_cert_ids:
                linked_certs.append(cert)

        certificates = sorted(linked_certs, key=lambda x: x.issue_date, reverse=True)

    # Calculate course stats ONLY for this student's certificates
    course_stats = {}
    for cert in certificates:
        course_stats[cert.course_name] = course_stats.get(cert.course_name, 0) + 1

    # Additional statistics
    latest_cert_date = certificates[0].issue_date if certificates else None
    total_courses = len(course_stats)
    
    # User profile info
    user_info = {
        'username': current_user.username,
        'email': current_user.email,
        'member_since': current_user.created_at,
        'total_certificates': len(certificates),
        'total_courses': total_courses,
        'latest_cert_date': latest_cert_date
    }

    return render_template('student_dashboard.html',
                         certificates=certificates,
                         course_stats=course_stats,
                         user_info=user_info)


@app.route('/student/claim', methods=['POST'])
@login_required
def claim_certificate():
    """Allow student to claim/link a certificate by hash"""
    if current_user.is_admin():
        flash('Admins cannot claim certificates.', 'error')
        return redirect(url_for('admin_dashboard'))

    cert_hash = request.form.get('hash', '').strip()
    if not cert_hash:
        flash('Please provide a certificate hash.', 'error')
        return redirect(url_for('student_dashboard'))

    certificate = Certificate.query.filter_by(blockchain_hash=cert_hash).first()

    if not certificate:
        flash('Certificate not found with the provided hash.', 'error')
        return redirect(url_for('student_dashboard'))

    if certificate.student_name.lower() != current_user.username.lower() and \
       certificate.student_name.lower() not in current_user.email.lower():
        flash('This certificate does not appear to belong to you. Name mismatch.', 'error')
        return redirect(url_for('student_dashboard'))

    if certificate.student_id != current_user.id:
        certificate.student_id = current_user.id
        db.session.commit()
        flash('✅ Certificate successfully linked to your account!', 'success')
    else:
        flash('✅ Certificate is already linked to your account.', 'info')

    return redirect(url_for('student_dashboard'))


@app.route('/verify', methods=['GET', 'POST'])
def verify():
    """Verify certificate - shows verification page"""
    cert_id = request.args.get('cert_id', '').strip()
    qr_hash = request.args.get('hash', '').strip()

    if cert_id and qr_hash:
        certificate = None
        try:
            certificate = Certificate.query.filter_by(blockchain_hash=qr_hash).first()
        except:
            pass

        return render_template('verify_public.html',
                             cert_id=cert_id,
                             qr_hash=qr_hash,
                             certificate=certificate,
                             result=None)

    hash_input = request.args.get('hash', '').strip() or request.form.get('hash', '').strip()

    if hash_input:
        block_index = blockchain.verify_certificate(hash_input)
        certificate = Certificate.query.filter_by(blockchain_hash=hash_input).first()

        if block_index is not None:
            block = blockchain.get_block_by_hash(hash_input)
            result = 'Valid'
            block_info = {
                'index': block.index,
                'hash': block.hash,
                'previous_hash': block.previous_hash,
                'timestamp': block.timestamp.isoformat()
            }
        else:
            result = 'Invalid'
            block_info = None

        return render_template('verify_public.html',
                             result=result,
                             certificate=certificate,
                             block_info=block_info,
                             cert_id=None,
                             qr_hash=hash_input)

    return render_template('verify_public.html',
                         cert_id=None,
                         qr_hash=None,
                         result=None,
                         certificate=None)


@app.route('/verify_upload', methods=['POST'])
def verify_upload():
    """Verify uploaded PDF by comparing hashes"""
    cert_id = request.form.get('cert_id', '').strip()
    qr_hash = request.form.get('hash', '').strip()

    if not cert_id or not qr_hash:
        flash('Missing certificate ID or hash.', 'error')
        return redirect(url_for('verify'))

    if 'file' not in request.files:
        flash('No file uploaded.', 'error')
        return redirect(url_for('verify', cert_id=cert_id, hash=qr_hash))

    uploaded_file = request.files['file']

    if uploaded_file.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('verify', cert_id=cert_id, hash=qr_hash))

    if not uploaded_file.filename.lower().endswith('.pdf'):
        flash('Please upload a PDF file.', 'error')
        return redirect(url_for('verify', cert_id=cert_id, hash=qr_hash))

    try:
        uploaded_bytes = uploaded_file.read()
        uploaded_hash = hashlib.sha256(uploaded_bytes).hexdigest()
        chain_hash = blockchain.get_hash_by_cert_id(cert_id)

        if uploaded_hash == chain_hash:
            certificate = Certificate.query.filter_by(blockchain_hash=uploaded_hash).first()

            log = VerificationLog(
                certificate_id=certificate.id if certificate else None,
                blockchain_hash=uploaded_hash,
                status='Valid',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')
            )
            db.session.add(log)
            db.session.commit()

            verification_msg = '✅ Certificate is authentic and has not been tampered with.'
            
            return render_template('verify_public.html',
                                 cert_id=cert_id,
                                 qr_hash=qr_hash,
                                 uploaded_hash=uploaded_hash,
                                 chain_hash=chain_hash,
                                 result='VALID',
                                 certificate=certificate,
                                 verification_message=verification_msg)
        else:
            log = VerificationLog(
                certificate_id=None,
                blockchain_hash=uploaded_hash,
                status='Tampered',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')
            )
            db.session.add(log)
            db.session.commit()

            return render_template('verify_public.html',
                                 cert_id=cert_id,
                                 qr_hash=qr_hash,
                                 uploaded_hash=uploaded_hash,
                                 chain_hash=chain_hash,
                                 result='TAMPERED',
                                 certificate=None,
                                 verification_message='❌ Certificate has been altered! Hashes do not match.')

    except Exception as e:
        flash(f'❌ Error verifying certificate: {str(e)}', 'error')
        return redirect(url_for('verify', cert_id=cert_id, hash=qr_hash))


@app.route('/blockchain')
def blockchain_explorer():
    """Public blockchain explorer"""
    chain_data = []
    for block in blockchain.chain:
        block_content = block.certificate_hash
        try:
            data = json.loads(block.certificate_hash)
            if isinstance(data, dict):
                block_content = json.dumps(data, indent=2)
        except:
            pass
            
        chain_data.append({
            'index': block.index,
            'timestamp': block.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'previous_hash': block.previous_hash,
            'hash': block.hash,
            'data': block_content,
            'is_genesis': block.index == 0
        })
    
    return render_template('blockchain.html', chain=chain_data)


@app.route('/certificate/<int:cert_id>/download')
@login_required
def download_certificate(cert_id):
    """Download certificate PDF"""
    certificate = Certificate.query.get_or_404(cert_id)

    if not current_user.is_admin() and certificate.student_id != current_user.id:
        flash('You do not have permission to access this certificate.', 'error')
        return redirect(url_for('student_dashboard'))

    if not os.path.exists(certificate.pdf_path):
        flash('Certificate file not found.', 'error')
        return redirect(url_for('student_dashboard'))

    return send_file(certificate.pdf_path, as_attachment=True, download_name=f"{certificate.student_name}_{certificate.course_name}.pdf")


@app.route('/certificate/<int:cert_id>/view')
@login_required
def view_certificate(cert_id):
    """View certificate PDF"""
    certificate = Certificate.query.get_or_404(cert_id)

    if not current_user.is_admin() and certificate.student_id != current_user.id:
        flash('You do not have permission to access this certificate.', 'error')
        return redirect(url_for('student_dashboard'))

    if not os.path.exists(certificate.pdf_path):
        flash('Certificate file not found.', 'error')
        return redirect(url_for('student_dashboard'))

    return send_file(certificate.pdf_path)


@app.route('/api/blockchain/status')
@login_required
def blockchain_status():
    """API endpoint for blockchain status"""
    if not current_user.is_admin():
        return jsonify({'error': 'Unauthorized'}), 403

    info = blockchain.get_chain_info()
    return jsonify(info)


@app.route('/api/verify/qr', methods=['POST'])
def verify_qr():
    """API endpoint for QR code verification"""
    data = request.get_json()
    hash_input = data.get('hash', '').strip()

    if not hash_input:
        return jsonify({'error': 'Hash required'}), 400

    block_index = blockchain.verify_certificate(hash_input)
    certificate = Certificate.query.filter_by(blockchain_hash=hash_input).first()

    if block_index is not None:
        block = blockchain.get_block_by_hash(hash_input)
        return jsonify({
            'valid': True,
            'certificate': {
                'student_name': certificate.student_name if certificate else None,
                'course_name': certificate.course_name if certificate else None,
                'issue_date': certificate.issue_date.isoformat() if certificate else None
            },
            'block': {
                'index': block.index,
                'hash': block.hash,
                'timestamp': block.timestamp.isoformat()
            }
        })
    else:
        return jsonify({'valid': False})


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error_code=404, error_message='Page not found'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('error.html', error_code=500, error_message='Internal server error'), 500


def create_tables():
    """Create database tables and initial admin user"""
    with app.app_context():
        from sqlalchemy import inspect, text

        inspector = inspect(db.engine)
        if 'certificates' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('certificates')]
            if 'marksheet_data' not in columns:
                try:
                    db.session.execute(text('ALTER TABLE certificates ADD COLUMN marksheet_data TEXT'))
                    db.session.commit()
                    print("✓ Added marksheet_data column")
                except Exception:
                    pass

        db.create_all()

        try:
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(
                    username='admin',
                    email='admin@bctproject.com',
                    role='admin'
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("✅ Default admin user created: username='admin', password='admin123'")
        except Exception as e:
            print(f"Database schema issue detected: {e}")
            print("Recreating database...")
            db.drop_all()
            db.create_all()
            admin = User(
                username='admin',
                email='admin@bctproject.com',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Database recreated. Default admin user created: username='admin', password='admin123'")


if __name__ == '__main__':
    create_tables()

    print("\n" + "="*50)
    print("🚀 Certificate Tampering Detection is running!")
    print("📱 Open your browser and go to: http://localhost:5000")
    print("🔐 Login credentials: admin / admin123")
    print("="*50 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)