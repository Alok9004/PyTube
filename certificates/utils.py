import uuid
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from django.conf import settings
from .models import Certificate
import os
import qrcode
from datetime import datetime

def generate_certificate(user, channel):
    cert_id = str(uuid.uuid4())[:8]
    filename = f"{user.username}_{channel.name}_{cert_id}.pdf"
    folder_path = os.path.join(settings.MEDIA_ROOT, 'certificates')
    os.makedirs(folder_path, exist_ok=True)
    filepath = os.path.join(folder_path, filename)

    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4

    # Outer black border
    c.setStrokeColor(colors.black)
    c.setLineWidth(4)
    c.rect(20, 20, width - 40, height - 40)

    # Logo path (place your logo in static folder)
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')
    if os.path.exists(logo_path):
        c.drawImage(logo_path, width/2 - 50, height - 120, width=100, preserveAspectRatio=True, mask='auto')

    # Title
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(width/2, height - 180, "Certificate of Completion")

    # Subtitle
    c.setFont("Helvetica", 16)
    c.drawCentredString(width/2, height - 220, "This is proudly presented to")

    # User name
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(width/2, height - 260, user.username)

    # Completion message
    c.setFont("Helvetica", 14)
    text = f"For successfully completing the course: {channel.name}"
    c.drawCentredString(width/2, height - 300, text)

    # Issue date
    issue_date = datetime.now().strftime("%d %B %Y")
    c.setFont("Helvetica-Oblique", 12)
    c.drawCentredString(width/2, height - 340, f"Issued on: {issue_date}")

    # QR Code generation
    qr_data = f"Certificate ID: {cert_id} | User: {user.username} | Course: {channel.name}"
    qr = qrcode.make(qr_data)
    qr_filename = f"{cert_id}.png"
    qr_path = os.path.join(folder_path, qr_filename)
    qr.save(qr_path)
    c.drawImage(qr_path, width - 150, 40, width=100, preserveAspectRatio=True, mask='auto')

    # Signature placeholder
    c.setFont("Helvetica", 12)
    c.drawString(60, 60, "Authorized Sign")
    c.line(60, 80, 200, 80)

    # Save PDF
    c.save()

    cert = Certificate.objects.create(
        user=user,
        channel=channel,
        certificate_id=cert_id,
        pdf=f"certificates/{filename}"
    )
    return cert
