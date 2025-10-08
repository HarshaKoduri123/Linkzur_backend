from django.contrib import admin
from .models import (
    CustomUser, Product, CartItem, WishlistItem,
    Order, OrderItem, Notification, Payment,
    QuotationRequest, Quotation, ProductConversation, ProductMessage
)


# ---------- User ----------
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("email", "name", "phone", "role", "is_active", "is_staff")
    search_fields = ("email", "name", "phone")
    list_filter = ("role", "is_active", "is_staff")


# ---------- Product ----------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "seller", "created_at")
    search_fields = ("name", "seller__email")
    list_filter = ("category",)


# ---------- Cart ----------
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "quantity", "added_at")
    search_fields = ("user__email", "product__name")


# ---------- Wishlist ----------
@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "added_at")
    search_fields = ("user__email", "product__name")


# ---------- Orders ----------
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "buyer", "status", "total_price", "created_at")
    search_fields = ("buyer__email",)
    list_filter = ("status",)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "quantity", "price")
    search_fields = ("order__buyer__email", "product__name")


# ---------- Notifications ----------
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "message", "is_read", "created_at")
    search_fields = ("user__email", "message")
    list_filter = ("is_read",)


# ---------- Payments ----------
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("order", "amount", "status", "txn_id")
    search_fields = ("order__buyer__email", "txn_id")
    list_filter = ("status",)


# ---------- Quotations ----------
@admin.register(QuotationRequest)
class QuotationRequestAdmin(admin.ModelAdmin):
    list_display = ("product", "buyer", "seller", "is_resolved", "created_at")
    search_fields = ("buyer__email", "seller__email", "product__name")
    list_filter = ("is_resolved",)


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ("id", "request", "uploaded_by", "is_invoice", "created_at")
    search_fields = ("uploaded_by__email",)
    list_filter = ("is_invoice",)


# ---------- Conversations ----------
@admin.register(ProductConversation)
class ProductConversationAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "buyer", "seller", "created_at")
    search_fields = ("buyer__email", "seller__email", "product__name")


@admin.register(ProductMessage)
class ProductMessageAdmin(admin.ModelAdmin):
    list_display = ("conversation", "sender", "text", "created_at", "is_read")
    search_fields = ("sender__email", "conversation__product__name")
    list_filter = ("is_read",)
