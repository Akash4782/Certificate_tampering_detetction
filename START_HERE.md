# 🚀 How to Start Certificate Tampering Detection

## Quick Start (5 Steps)

### ✅ Step 1: Activate Virtual Environment

Open PowerShell or Command Prompt in the project folder and run:

```powershell
# PowerShell
.\venv\Scripts\Activate.ps1

# OR Command Prompt
venv\Scripts\activate.bat
```

You should see `(venv)` at the beginning of your command prompt.

### ✅ Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### ✅ Step 3: Create .env File

Create a file named `.env` in the project root with this content:

```
SECRET_KEY=dev-secret-key-change-in-production-2024
DATABASE_URL=sqlite:///bct_project.db
```

**OR** run this PowerShell command:
```powershell
"SECRET_KEY=dev-secret-key-change-in-production-2024`nDATABASE_URL=sqlite:///bct_project.db" | Out-File -FilePath .env -Encoding utf8
```

### ✅ Step 4: Initialize Database

```bash
python init_db.py
```

Expected output:
```
✓ Database schema is up to date
✓ Default admin user created:
  Username: admin
  Password: admin123
  ⚠️  Please change the password after first login!

Database Statistics:
  Users: 1
  Certificates: 0
```

**Note**: If you see "Creating/updating database schema...", that's normal for first-time setup.

### ✅ Step 5: Start the Application

```bash
python app.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
 * Running on http://0.0.0.0:5000
```

### 🌐 Step 6: Open in Browser

Open your web browser and go to:
```
http://localhost:5000
```

### 🔐 Login Credentials

- **Username**: `admin`
- **Password**: `admin123`

---

## 🎯 First Actions After Starting

1. **Login** with admin credentials
2. **Change Password** (recommended)
3. **Issue a Test Certificate**:
   - Click "Issue Certificate"
   - Fill in: Student Name, Course Name, Date
   - Click "Generate Certificate"
   - PDF will download automatically

---

## ⚠️ Important Notes

### PDF Generation (Optional but Recommended)

To generate PDF certificates, install **wkhtmltopdf**:

1. Download from: https://wkhtmltopdf.org/downloads.html
2. Install to: `C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe`
3. If installed elsewhere, update path in `app.py` (around line 58)

**Without wkhtmltopdf**: The app will work, but PDF generation will fail.

---

## 🐛 Common Issues & Solutions

### "Module not found"
```bash
# Make sure venv is activated, then:
pip install -r requirements.txt
```

### "Port 5000 already in use"
Change port in `app.py`:
```python
app.run(debug=True, port=5001)  # Change 5000 to 5001
```

### "Database locked"
- Close other instances of the app
- Close any database viewers

### "Can't login"
Run database initialization again:
```bash
python init_db.py
```

---

## 📋 Complete Command Sequence

Copy and paste these commands one by one:

```powershell
# 1. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 2. Install dependencies (if not already installed)
pip install -r requirements.txt

# 3. Create .env file (if not exists)
if (-not (Test-Path .env)) {
    "SECRET_KEY=dev-secret-key-change-in-production-2024" | Out-File -FilePath .env -Encoding utf8
    "DATABASE_URL=sqlite:///bct_project.db" | Out-File -FilePath .env -Append -Encoding utf8
}

# 4. Initialize database
python init_db.py

# 5. Start application
python app.py
```

---

## ✨ You're Ready!

Once you see "Running on http://127.0.0.1:5000", open your browser and start using the application!

For more details, see `README.md` or `QUICKSTART.md`.

