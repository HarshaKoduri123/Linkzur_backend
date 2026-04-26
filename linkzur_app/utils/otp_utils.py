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
    Sends a seller approval email with temporary password + reset password link.
    Returns True if successful, else False.
    """

    reset_link = "https://www.linkzur.com/reset-password"  # 🔥 Update this!

    subject = "Your Seller Account Has Been Approved – Linkzur"

    message = (
        f"Hello,\n\n"
        f"Congratulations! Your seller account on Linkzur has been approved.\n\n"
        f"Your login details:\n"
        f"Email: {email}\n"
        f"Temporary Password: {temp_password}\n\n"
        f"For security, please log in and change your password immediately.\n"
        f"You can reset your password by clicking on forget-password\n"
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

def send_password_reset_email(email: str, code: str) -> bool:
    subject = "Linkzur – Password Reset Code"
    message = (
        f"Hello,\n\n"
        f"We received a password reset request for your Linkzur account.\n\n"
        f"Your reset code is: {code}\n"
        f"This code is valid for 10 minutes.\n\n"
        f"If you didn't request this, ignore this email.\n\n"
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
        logger.info(f"🔐 Password reset email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"❌ Could not send reset email: {e}")
        return False


def send_delivery_otp_email(email: str, otp: str) -> bool:
    """
    Sends a delivery confirmation OTP to the buyer.
    OTP will be used by the seller to verify delivery.
    Valid for 1 hour.
    """
    subject = "Linkzur – Delivery Confirmation OTP"

    message = (
        f"Hello,\n\n"
        f"Your delivery confirmation OTP for your Linkzur order is: {otp}\n"
        f"This OTP is valid for 1 hour.\n\n"
        f"Share this code only with the delivery agent.\n\n"
        f"If you did not expect a delivery, please contact Linkzur support immediately.\n\n"
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
        logger.info(f"📩 Delivery OTP sent to {email}")
        return True

    except BadHeaderError:
        logger.error(f"❌ Invalid header sending delivery OTP to {email}")
        return False

    except Exception as e:
        logger.error(f"❌ Failed to send delivery OTP to {email}: {e}")
        return False

import logging
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


# ------------------------------------------------
# BUYER ORDER CONFIRMATION EMAIL
# ------------------------------------------------
def send_order_confirmation_email(email: str, order):
   
    subject = f"Order #{order.id} Confirmed – Linkzur"
    message = (
        f"Hello,\n\n"
        f"Your order #{order.id} has been successfully placed.\n"
        f"Total Amount: ₹{order.total_price}\n"
        f"Status: {order.status}\n\n"
        f"Thank you for shopping with Linkzur!\n\n"
        f"Regards,\n"
        f"Linkzur Team"
    )

    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
        logger.info(f"📧 Order confirmation email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to send confirmation email to {email}: {e}")
        return False



# ------------------------------------------------
# SELLER ORDER ALERT EMAIL
# ------------------------------------------------
def send_seller_new_order_email(email: str, order):
    print(order)
    print(order.buyer.email)
    subject = f"New Order Received – Order #{order.id}"
    message = (
        f"Hello Seller,\n\n"
        f"You have received a new order containing your products.\n"
        f"Order ID: #{order.id}\n"
        f"Buyer: {order.buyer.email}\n\n"
        f"Please review and process the order.\n\n"
        f"- Linkzur Team"
    )

    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
        logger.info(f"📧 Seller alert email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to send seller order alert to {email}: {e}")
        return False



# ------------------------------------------------
# BUYER STATUS UPDATE EMAIL
# ------------------------------------------------
def send_order_status_update_email(email: str, order):
    subject = f"Order #{order.id} Status Updated"
    message = (
        f"Hello,\n\n"
        f"The status of your order #{order.id} has been updated.\n"
        f"New Status: {order.status}\n\n"
        f"Thank you for shopping with Linkzur!\n\n"
        f"- Linkzur Team"
    )

    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
        logger.info(f"📧 Order status update email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to send status update email: {e}")
        return False
