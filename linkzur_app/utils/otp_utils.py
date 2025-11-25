import random
import logging
from django.core.mail import send_mail, BadHeaderError
from django.conf import settings

logger = logging.getLogger(__name__)


# ============================================
# OTP GENERATION
# ============================================
def generate_otp() -> str:
    """
    Generate a 6-digit numeric OTP as a string.
    """
    return str(random.randint(100000, 999999))


# ============================================
# SEND BUYER OTP EMAIL
# ============================================
def send_otp_email(email: str, otp: str) -> bool:
    """
    Sends an OTP email using Linkzur SMTP setup.
    Returns True if sent successfully, else False.
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
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        logger.info(f"📩 OTP email sent to {email}")
        return True

    except BadHeaderError:
        logger.error(f"❌ Invalid header found while sending OTP to {email}")
        return False

    except Exception as e:
        logger.error(f"❌ Failed to send OTP email to {email}: {e}")
        return False


# ============================================
# SEND SELLER APPROVAL EMAIL
# ============================================
def send_seller_approval_email(email: str, temp_password: str) -> bool:
    """
    Sends a seller approval email with temporary password.
    Returns True if successful, else False.
    """
    subject = "Your Seller Account Has Been Approved – Linkzur"

    message = (
        f"Hello,\n\n"
        f"Congratulations! Your seller account on Linkzur has been approved.\n\n"
        f"Your login details:\n"
        f"Email: {email}\n"
        f"Temporary Password: {temp_password}\n\n"
        f"For security, please log in and change your password immediately.\n\n"
        f"We’re excited to have you onboard!\n\n"
        f"Best regards,\n"
        f"Linkzur Team"
    )
    

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        print("hii")
        logger.info(f"📨 Seller approval email sent to {email}")
        return True

    except BadHeaderError:
        logger.error(f"❌ Invalid header while sending approval email to {email}")
        return False

    except Exception as e:
        logger.error(f"❌ Failed to send approval email to {email}: {e}")
        return False


# ============================================
# SEND SELLER REJECTION EMAIL
# ============================================
def send_seller_reject_email(email: str) -> bool:
    """
    Sends a rejection email to sellers.
    """
    subject = "Your Seller Registration Was Not Approved – Linkzur"

    message = (
        f"Hello,\n\n"
        f"We regret to inform you that your seller registration on Linkzur "
        f"was not approved at this time.\n\n"
        f"You may contact support if you believe this was a mistake.\n\n"
        f"Regards,\n"
        f"Linkzur Team"
    )

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        logger.info(f"⚠️ Seller rejection email sent to {email}")
        return True

    except BadHeaderError:
        logger.error(f"❌ Invalid header while sending rejection email to {email}")
        return False

    except Exception as e:
        logger.error(f"❌ Failed to send rejection email to {email}: {e}")
        return False

