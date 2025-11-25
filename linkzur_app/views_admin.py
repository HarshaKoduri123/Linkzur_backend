from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail

from .models import SellerProfile


def approve_seller(request, seller_id):
    profile = get_object_or_404(SellerProfile, id=seller_id)
    user = profile.user

    # Mark approved
    profile.is_approved = True
    profile.save()

    # Send login email with temporary password
    send_mail(
        subject="Your Seller Account Has Been Approved",
        message=(
            f"Congratulations! Your Linkzur seller account has been approved.\n\n"
            f"Login Email: {user.email}\n"
            f"Temporary Password: {profile.temp_password}\n\n"
            "Please log in and change your password immediately."
        ),
        from_email="no-reply@linkzur.com",
        recipient_list=[user.email],
        fail_silently=True,
    )

    # Remove temp password for security
    profile.temp_password = None
    profile.save()

    messages.success(request, f"Seller {user.email} approved successfully!")
    return redirect("/admin/linkzur_app/sellerprofile/")

    
def reject_seller(request, seller_id):
    profile = get_object_or_404(SellerProfile, id=seller_id)
    user = profile.user

    send_mail(
        subject="Your Seller Registration Was Rejected",
        message="We are sorry, but your seller registration was not approved.",
        from_email="no-reply@linkzur.com",
        recipient_list=[user.email],
        fail_silently=True,
    )

    # Delete profile and user
    profile.delete()
    user.delete()

    messages.warning(request, f"Seller {user.email} rejected and removed.")
    return redirect("/admin/linkzur_app/sellerprofile/")
