# BCT Project Deployment Guide

## Overview

This guide walks you through deploying the BCT (Blockchain Certificate Tracking) Project to **Render**, a free hosting platform that supports Python applications with PostgreSQL databases.

## Prerequisites

- A GitHub account
- Your BCT Project code pushed to a GitHub repository
- A Render account (free tier available at https://render.com)

## Deployment Steps

### 1. Prepare Your Repository

Ensure your project has the following files (already created):
- `requirements.txt` - Python dependencies
- `render.yaml` - Render service configuration
- `build.sh` - Build script for installing wkhtmltopdf
- Updated `app.py` with health check endpoint
- Updated `config.py` with PostgreSQL support

### 2. Push to GitHub

```bash
cd c:\Users\office\Documents\BCT_project
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### 3. Deploy on Render

#### Option A: Using render.yaml (Recommended)

1. Go to https://render.com and sign in
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub repository
4. Render will automatically detect `render.yaml` and create:
   - A web service for your Flask app
   - A PostgreSQL database
5. Click **"Apply"** to start deployment

#### Option B: Manual Setup

1. **Create PostgreSQL Database**:
   - Click **"New +"** → **"PostgreSQL"**
   - Name: `bct-db`
   - Database: `bct_project`
   - User: `bct_user`
   - Plan: **Free**
   - Click **"Create Database"**

2. **Create Web Service**:
   - Click **"New +"** → **"Web Service"**
   - Connect your GitHub repository
   - Configure:
     - **Name**: `bct-project`
     - **Region**: Oregon (or closest to you)
     - **Branch**: `main`
     - **Runtime**: Python 3
     - **Build Command**: `./build.sh`
     - **Start Command**: `gunicorn app:app`
   - Click **"Advanced"** and add environment variables:
     - `PYTHON_VERSION`: `3.11.0`
     - `FLASK_ENV`: `production`
     - `SECRET_KEY`: (click "Generate" for a secure random key)
     - `DATABASE_URL`: (select your PostgreSQL database from dropdown)
   - Plan: **Free**
   - Click **"Create Web Service"**

### 4. Wait for Deployment

- Render will:
  1. Clone your repository
  2. Run `build.sh` (installs wkhtmltopdf and dependencies)
  3. Initialize the database
  4. Start your application with gunicorn

- This takes about 5-10 minutes for the first deployment
- You can monitor progress in the Render dashboard logs

### 5. Access Your Application

Once deployed, Render provides a URL like:
```
https://bct-project-xxxx.onrender.com
```

## Post-Deployment Verification

### Test Authentication Flow

1. Navigate to your production URL
2. **Verify**: Login page appears first (not dashboard)
3. Login with default admin credentials:
   - Username: `admin`
   - Password: `admin123`
4. **Verify**: Redirected to admin dashboard after login

### Test Certificate Generation

1. Login as admin
2. Navigate to **"Issue Certificate"**
3. Fill in the form with test data:
   - Student Name: Test Student
   - Roll Number: TEST001
   - Email: test@example.com
   - Add at least one subject
4. Click **"Issue Certificate"**
5. Download the generated PDF
6. **CRITICAL**: Open the PDF and verify:
   - The verification URL contains your production domain (e.g., `https://bct-project-xxxx.onrender.com/verify?cert_id=...`)
   - **NOT** `http://localhost:5000`
7. Scan or click the QR code to verify it works

### Test Certificate Verification

1. Copy the verification URL from the PDF
2. Open it in a new browser tab
3. **Verify**: Certificate details display correctly
4. **Verify**: Blockchain verification shows valid

### Test Role-Based Access

1. Logout from admin
2. Try accessing `/admin/dashboard` directly → should redirect to login
3. Create a student account (as admin)
4. Login as student
5. **Verify**: Student dashboard appears
6. Try accessing `/admin/dashboard` → should be denied

## Important Notes

### Default Credentials

**⚠️ SECURITY WARNING**: Change the default admin password immediately after deployment!

1. Login as admin
2. Navigate to profile/settings
3. Change password from `admin123` to a strong password

### Free Tier Limitations

Render's free tier has some limitations:
- **Sleep after inactivity**: Apps sleep after 15 minutes of inactivity
- **Cold start**: First request after sleep takes 30-60 seconds
- **Database**: 90-day expiration on free PostgreSQL (backup your data!)
- **Build time**: 500 build minutes/month

### Environment Variables

If you need to update environment variables:
1. Go to Render dashboard
2. Select your web service
3. Click **"Environment"** tab
4. Add/edit variables
5. Service will automatically redeploy

### Email Configuration (Optional)

To enable email notifications for certificates:
1. Add these environment variables in Render:
   - `MAIL_SERVER`: `smtp.gmail.com`
   - `MAIL_PORT`: `587`
   - `MAIL_USERNAME`: your Gmail address
   - `MAIL_PASSWORD`: your Gmail app password
   - `MAIL_DEFAULT_SENDER`: your email

## Troubleshooting

### Build Fails

- Check Render logs for errors
- Ensure `build.sh` has execute permissions: `chmod +x build.sh`
- Verify all dependencies in `requirements.txt` are correct

### PDF Generation Fails

- Check logs for wkhtmltopdf errors
- Ensure `build.sh` successfully installed wkhtmltopdf
- Verify the build log shows: "Installing wkhtmltopdf..."

### Database Connection Errors

- Verify `DATABASE_URL` environment variable is set
- Check PostgreSQL database is running
- Ensure database credentials are correct

### Application Won't Start

- Check `gunicorn` is in `requirements.txt`
- Verify start command is: `gunicorn app:app`
- Check logs for Python errors

### URLs Still Show Localhost

- Verify `get_base_url()` function is using `request.url_root`
- Check that you're testing on the production URL, not locally
- Clear browser cache and regenerate certificate

## Updating Your Deployment

To deploy updates:

```bash
# Make your changes locally
git add .
git commit -m "Your update message"
git push origin main
```

Render will automatically detect the push and redeploy your application.

## Monitoring

- **Logs**: View real-time logs in Render dashboard
- **Metrics**: Monitor CPU, memory, and request metrics
- **Health Check**: Render pings `/health` endpoint to ensure app is running

## Support

If you encounter issues:
1. Check Render documentation: https://render.com/docs
2. Review application logs in Render dashboard
3. Verify all environment variables are set correctly
4. Test locally first to isolate deployment-specific issues

## Next Steps

After successful deployment:
1. ✅ Change default admin password
2. ✅ Create student accounts
3. ✅ Test certificate generation and verification
4. ✅ Share production URL with users
5. ✅ Set up regular database backups
6. ✅ Monitor application performance

---

**Production URL**: `https://bct-project-xxxx.onrender.com` (replace with your actual URL)

**Admin Login**: `admin` / `admin123` (⚠️ CHANGE THIS!)
