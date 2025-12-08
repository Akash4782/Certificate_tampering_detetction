#!/usr/bin/env python
"""Regenerate QR images for all certificates using current PUBLIC_URL.

Run with the virtualenv activated:
    python scripts/regenerate_qr.py

This will recreate QR PNG files in the `static/qr` folder and update certificate.qr_path
if necessary.
"""
import os
import sys
from urllib.parse import quote_plus

# Ensure project root is on sys.path so imports work when script is run from scripts/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import app
from database import db
from models import Certificate
import qrcode
import qrcode.constants
from werkzeug.utils import secure_filename


def regenerate_all():
    with app.app_context():
        os.makedirs(app.config['QR_FOLDER'], exist_ok=True)
        public_base = app.config.get('PUBLIC_URL') or ''
        certs = Certificate.query.all()
        print(f"Found {len(certs)} certificates to process...")

        for cert in certs:
            try:
                # Build verification URL using stored blockchain_hash
                if not cert.blockchain_hash:
                    print(f"Skipping cert id={cert.id}: no blockchain_hash")
                    continue

                if public_base:
                    base_url = public_base.rstrip('/')
                else:
                    # fallback to localhost; this will only be useful locally
                    base_url = 'http://localhost:5000'

                verification_url = f"{base_url}/verify?hash={quote_plus(cert.blockchain_hash)}"

                # Create filename based on certificate id and block index to avoid collisions
                qr_filename = secure_filename(f"cert_{cert.id}_block_{cert.block_index or 0}.png")
                qr_path = os.path.join(app.config['QR_FOLDER'], qr_filename)

                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_H,
                    box_size=8,
                    border=2,
                )
                qr.add_data(verification_url)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                try:
                    img = img.resize((600, 600), resample=1)
                except Exception:
                    img = img.resize((600, 600))
                img.save(qr_path, 'PNG')

                # Store relative static path
                rel_path = os.path.join('static', 'qr', qr_filename).replace('\\', '/')
                cert.qr_path = rel_path
                db.session.add(cert)
                print(f"Regenerated QR for cert id={cert.id} -> {rel_path}")
            except Exception as e:
                print(f"Error regenerating cert id={cert.id}: {e}")

        db.session.commit()
        print("Done. Restart your app if necessary.")


if __name__ == '__main__':
    regenerate_all()
