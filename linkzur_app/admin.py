from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    CustomUser, BuyerProfile, SellerProfile, Product, ProductVariant,
    CartItem, WishlistItem, Order, OrderItem, Notification,
    Payment, QuotationRequest, Quotation, ProductConversation,
    ProductMessage, Review, Invoice, PendingUser
)

# Import reusable email helpers
from .utils.otp_utils import (
    send_seller_approval_email,
    send_seller_reject_email,
)


# ================================
# CustomUser Admin
# ================================
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ("email", "name", "phone", "role", "is_active", "is_staff")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("email", "name", "phone")
    ordering = ("email",)

    fieldsets = (
        ("Login Info", {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("name", "phone", "role")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "name", "phone", "role", "password1", "password2", "is_staff", "is_superuser"),
        }),
    )


# ================================
# BuyerProfile Admin
# ================================
class BuyerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "username", "buyer_category", "organization_name")
    search_fields = ("user__email", "username", "organization_name")


# ================================
# SellerProfile Admin
# ================================
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "business_name", "gst_number", "is_approved")
    list_filter = ("is_approved", "entity_type")
    search_fields = ("user__email", "business_name", "gst_number")

    def save_model(self, request, obj, form, change):
        """
        Trigger email only when seller is newly approved.
        """
        if change:
            old_obj = SellerProfile.objects.get(pk=obj.pk)

            # Detect approval
            if not old_obj.is_approved and obj.is_approved:
                # Send approval email
              
                send_seller_approval_email(
                    obj.user.email,
                    obj.temp_password
                )

                # Clear temp password after sending
                obj.temp_password = None

        super().save_model(request, obj, form, change)


# ================================
# ProductVariant Inline
# ================================
class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


# ================================
# Product Admin
# ================================
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "seller", "ref_no", "category", "brand")
    search_fields = ("name", "ref_no", "brand", "seller__email")
    list_filter = ("category",)
    inlines = [ProductVariantInline]


# ================================
# Order Items Inline
# ================================
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


# ================================
# Order Admin
# ================================
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "buyer", "status", "total_price", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("buyer__email",)
    inlines = [OrderItemInline]


# ================================
# Quotation Admin
# ================================
class QuotationAdmin(admin.ModelAdmin):
    list_display = ("id", "uploaded_by", "request", "is_invoice", "created_at")
    search_fields = ("uploaded_by__email",)


# ================================
# Conversation Admin
# ================================
class ProductMessageInline(admin.TabularInline):
    model = ProductMessage
    extra = 0


class ProductConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "product", "buyer", "seller", "created_at")
    inlines = [ProductMessageInline]


# ================================
# Registering ALL MODELS
# ================================
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(BuyerProfile, BuyerProfileAdmin)
admin.site.register(SellerProfile, SellerProfileAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductVariant)
admin.site.register(CartItem)
admin.site.register(WishlistItem)
admin.site.register(Order, OrderAdmin)
admin.site.register(Notification)
admin.site.register(Payment)
admin.site.register(QuotationRequest)
admin.site.register(Quotation, QuotationAdmin)
admin.site.register(ProductConversation, ProductConversationAdmin)
admin.site.register(Review)
admin.site.register(Invoice)
admin.site.register(PendingUser)

