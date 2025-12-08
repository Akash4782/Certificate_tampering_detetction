# 🚀 Quick Start Guide - BCT Project

Follow these steps to get your BCT Project running in minutes!

## Step-by-Step Instructions

### Step 1: Activate Virtual Environment (if not already activated)

```bash
# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Windows Command Prompt
venv\Scripts\activate.bat

# Linux/macOS
source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: If you encounter errors, make sure you're in the virtual environment.

### Step 3: Create Environment File

Create a `.env` file in the project root with the following content:

```env
SECRET_KEY=dev-secret-key-change-in-production-2024
DATABASE_URL=sqlite:///bct_project.db
```

Or copy from `.env.example`:
```bash
# Windows
copy .env.example .env

# Linux/macOS
cp .env.example .env
```

### Step 4: Initialize Database

```bash
python init_db.py
```

This will:
- ✅ Create all database tables
- ✅ Create default admin user (username: `admin`, password: `admin123`)

### Step 5: (Optional) Install wkhtmltopdf for PDF Generation

**Windows:**
1. Download from: https://wkhtmltopdf.org/downloads.html
2. Install to default location: `C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe`
3. If installed elsewhere, update the path in `app.py` (line 58-60)

**Linux:**
```bash
sudo apt-get update
sudo apt-get install wkhtmltopdf
```

**macOS:**
```bash
brew install wkhtmltopdf
```

**Note**: PDF generation will fail without wkhtmltopdf, but the rest of the app will work.

### Step 6: Start the Application

```bash
python app.py
```

You should see output like:
```
Default admin user created: username='admin', password='admin123'
 * Running on http://127.0.0.1:5000
 * Running on http://0.0.0.0:5000
```

### Step 7: Access the Application

Open your web browser and go to:
```
http://localhost:5000
```

### Step 8: Login

Use the default admin credentials:
- **Username**: `admin`
- **Password**: `admin123`

⚠️ **Important**: Change this password after first login!

## 🎯 What's Next?

1. **Issue Your First Certificate**:
   - Go to "Issue Certificate"
   - Fill in student name, course, and date
   - Click "Generate Certificate"
   - PDF will download automatically

2. **Explore the Dashboard**:
   - View statistics and charts
   - See recent certificates and verifications

3. **Verify a Certificate**:
   - Go to "Verify Certificate"
   - Enter the hash from a certificate
   - See blockchain proof

## 🐛 Troubleshooting

### Issue: "Module not found" error
**Solution**: Make sure virtual environment is activated and dependencies are installed:
```bash
pip install -r requirements.txt
```

### Issue: "Database locked" error
**Solution**: Close any other instances of the app or database viewers

### Issue: PDF generation fails
**Solution**: 
- Install wkhtmltopdf (see Step 5)
- Check file path in `app.py` matches your installation
- Ensure `certificates/` folder exists and is writable

### Issue: "Port already in use"
**Solution**: 
- Close other applications using port 5000
- Or change port in `app.py`: `app.run(debug=True, port=5001)`

### Issue: Can't login
**Solution**: 
- Run `python init_db.py` again to recreate admin user
- Check username/password: `admin` / `admin123`

## 📝 Default Credentials

- **Admin**: `admin` / `admin123`
- **Students**: Created by admin when issuing certificates

## 🎉 You're All Set!

Your BCT Project is now running! Start issuing certificates and exploring the features.

