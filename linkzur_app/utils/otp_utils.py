import random
from django.core.mail import send_mail, BadHeaderError
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def generate_otp() -> str:
    """
    Generate a 6-digit numeric OTP as a string.
    """
    return str(random.randint(100000, 999999))


def send_otp_email(email: str, otp: str) -> bool:
    """
    Sends an OTP email using your Linkzur company SMTP setup.
    Returns True if successful, False otherwise.
    """
    subject = "Your Linkzur OTP Verification Code"
    message = (
        f"Hello,\n\n"
        f"Your OTP for Linkzur verification is: {otp}\n"
        f"This code will expire in 10 minutes.\n\n"
        f"If you didn’t request this, please ignore this email.\n\n"
        f"Best regards,\n"
        f"Linkzur Team"
    )

    try:
    
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,  # contact@linkzur.com from .env
            [email],
            fail_silently=False,
        )
        logger.info(f"✅ OTP email sent successfully to {email}")
        return True
    except BadHeaderError:
        logger.error(f"❌ Invalid header found while sending OTP to {email}")
        return False
    except Exception as e:
        logger.error(f"❌ Failed to send OTP to {email}: {e}")
        return False
