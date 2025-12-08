# BCT Project - Blockchain Certificate Tracking

A secure, blockchain-based certificate verification system built with Flask.

## Features

- 🔐 Blockchain-secured certificates
- 📜 PDF certificate generation with QR codes
- ✅ Public verification portal
- 👥 Admin and student dashboards
- 📊 Analytics and reporting
- 📧 Email notifications
- 🔍 Certificate search and filtering

## Quick Start

### Local Development

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Run the Application**
```bash
python app.py
```

3. **Access the App**
- URL: `http://localhost:5000`
- Default admin credentials: `admin` / `admin123`

## Deployment

See [deployment_guide.md](.gemini/antigravity/brain/998819c2-d379-4703-871a-394ad6698a4f/deployment_guide.md) for detailed deployment instructions.

### Quick Deploy to Render

1. Push code to GitHub
2. Connect repository to Render
3. Render will auto-detect `render.yaml` and deploy

## Tech Stack

- **Backend**: Flask, SQLAlchemy
- **Database**: SQLite (dev) / PostgreSQL (production)
- **Blockchain**: Custom implementation
- **PDF Generation**: wkhtmltopdf, ReportLab
- **Authentication**: Flask-Login

## License

MIT License - feel free to use for your projects!
