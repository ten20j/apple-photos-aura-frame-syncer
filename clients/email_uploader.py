import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
from .logger import setup_logger

load_dotenv()
logger = setup_logger(__name__)

AURA_FRAME_EMAIL = os.getenv("AURA_FRAME_EMAIL")
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_SMTP = os.getenv("EMAIL_SMTP", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 465))

def send_photos_via_email(photo_paths, subject="Photos for Aura Frame", body="Sent automatically."):
    if not photo_paths:
        logger.warning("No photos to send.")
        return False
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = AURA_FRAME_EMAIL
    msg.set_content(body)
    for path in photo_paths:
        with open(path, "rb") as f:
            data = f.read()
            filename = os.path.basename(path)
            maintype, subtype = ("application", "octet-stream")
            if filename.lower().endswith(('.jpg', '.jpeg')):
                maintype, subtype = ("image", "jpeg")
            elif filename.lower().endswith('.png'):
                maintype, subtype = ("image", "png")
            msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=filename)
    try:
        with smtplib.SMTP_SSL(EMAIL_SMTP, EMAIL_PORT) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            result = smtp.send_message(msg)
            if result == {}:
                logger.info(f"Sent {len(photo_paths)} photo(s) to {AURA_FRAME_EMAIL} (all recipients accepted).")
            else:
                logger.warning(f"Some recipients were refused: {result}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False 