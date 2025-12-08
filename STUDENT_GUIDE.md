# 📚 Student Guide - BCT Project

## How Students Can Access Their Certificates

### Step 1: Register/Login

**Option A: Register as New Student**
1. Go to: `http://localhost:5000/register`
2. Fill in:
   - Username (your preferred username)
   - Email (your email address)
   - Password (minimum 6 characters)
   - Confirm Password
3. Click "Register"
4. You'll be redirected to login page

**Option B: Login (if already registered)**
1. Go to: `http://localhost:5000/login`
2. Enter your username and password
3. Click "Login"

### Step 2: Access Your Dashboard

After logging in, you'll be automatically redirected to your **Student Dashboard** at:
```
http://localhost:5000/student/dashboard
```

### Step 3: View Your Certificates

Your dashboard shows:
- **Statistics**: Number of certificates and courses completed
- **Course Chart**: Visual representation of your completed courses
- **My Certificates**: All certificates issued to you

### Step 4: Link Certificates (If Needed)

If you received a certificate but don't see it in your dashboard:

1. **Get the Certificate Hash**:
   - Open your certificate PDF
   - Find the hash at the bottom of the certificate
   - Or scan the QR code to get the hash

2. **Link the Certificate**:
   - On your dashboard, find the "Link Your Certificates" section
   - Paste the certificate hash
   - Click "Link Certificate"
   - The certificate will be linked to your account if the name matches

## How Certificates Are Linked

### Automatic Linking

Certificates are automatically linked to your account when:
- ✅ Admin issues certificate using your **email address**
- ✅ Admin issues certificate and your **username/name matches** the certificate name
- ✅ You manually link a certificate using the hash

### Manual Linking

If a certificate was issued before you registered, or if the name doesn't match exactly:
1. Use the "Link Your Certificates" feature on your dashboard
2. Enter the certificate hash from your PDF
3. System will verify the name matches
4. Certificate will be linked to your account

## Student Features

### ✅ What Students Can Do:

1. **View All Certificates**
   - See all certificates issued to you
   - View certificate details (course, date, hash)

2. **Download Certificates**
   - Download PDF certificates anytime
   - Certificates are blockchain-verified

3. **Verify Certificates**
   - Verify authenticity of your certificates
   - View blockchain proof

4. **View Statistics**
   - See total certificates count
   - View courses completed
   - See visual charts of achievements

5. **Link Certificates**
   - Manually link certificates using hash
   - Claim certificates issued before registration

## Important Notes

### For Students:

- **Registration**: Only creates student accounts (not admin)
- **Name Matching**: Certificates are linked by email or name matching
- **Privacy**: You can only see certificates issued to you
- **Verification**: All certificates are blockchain-verified

### For Administrators:

When issuing certificates:
- **Always provide student email** for automatic linking
- If email not available, use student's registered username as the name
- Students can manually link certificates later if needed

## Troubleshooting

### "No Certificates Yet" Message

**Possible reasons:**
1. No certificates have been issued to you yet
2. Certificate was issued with a different name/email
3. Certificate needs to be manually linked

**Solutions:**
- Contact your administrator
- Use "Link Your Certificates" feature with certificate hash
- Verify your name matches the certificate

### Can't Link Certificate

**Check:**
- Certificate hash is correct (64 characters)
- Your name matches the certificate name
- Certificate exists in the system

### Forgot Password

Currently, password reset is not implemented. Contact your administrator for assistance.

## Quick Access URLs

- **Register**: `http://localhost:5000/register`
- **Login**: `http://localhost:5000/login`
- **Student Dashboard**: `http://localhost:5000/student/dashboard`
- **Verify Certificate**: `http://localhost:5000/verify`

---

**Need Help?** Contact your system administrator or check the main README.md file.

