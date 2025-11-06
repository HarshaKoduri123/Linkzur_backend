from django.contrib import admin
from .models import (
    CustomUser,
    Product,
    CartItem,
    WishlistItem,
    Order,
    OrderItem,
    Notification,
    Payment,
    QuotationRequest,
    Quotation,
    ProductConversation,
    ProductMessage,
    Review,
    Invoice,
    PendingUser,
    ProductVariant
)

# ------------------------
# Custom User
# ------------------------
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "name", "phone", "role", "is_active", "is_staff")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("email", "name", "phone")


# ------------------------
# Product
# ------------------------
# Inline editor for variants under each product

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1  # how many empty rows to show
    fields = ["variant_label", "est_price", "price", "created_at"]
    readonly_fields = ["created_at"]
    show_change_link = True


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "ref_no",
        "brand",
        "category",
        "seller",
        "created_at",
        "updated_at",
    )
    list_filter = ("category", "seller", "brand", "created_at")
    search_fields = ("name", "brand", "ref_no", "seller__email")
    readonly_fields = ("created_at", "updated_at")
    inlines = [ProductVariantInline]

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("variant_label", "product", "est_price", "price", "created_at")
    search_fields = ("variant_label", "product__name", "product__brand")
    list_filter = ("created_at",)
    readonly_fields = ("created_at",)

# ------------------------
# Cart & Wishlist
# ------------------------
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "quantity", "added_at")
    search_fields = ("user__email", "product__product_name")


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "added_at")
    search_fields = ("user__email", "product__product_name")


# ------------------------
# Orders
# ------------------------
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "buyer", "status", "total_price", "created_at")
    list_filter = ("status",)
    search_fields = ("buyer__email",)
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "quantity", "price")
    search_fields = ("order__buyer__email", "product__product_name")


# ------------------------
# Notifications
# ------------------------
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "message", "is_read", "created_at")
    list_filter = ("is_read",)
    search_fields = ("user__email", "message")


# ------------------------
# Payments
# ------------------------
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("order", "amount", "status", "txn_id", "paytm_order_id")
    list_filter = ("status",)
    search_fields = ("txn_id", "paytm_order_id")


# ------------------------
# Quotations
# ------------------------
@admin.register(QuotationRequest)
class QuotationRequestAdmin(admin.ModelAdmin):
    list_display = ("product", "buyer", "seller", "is_resolved", "created_at")
    list_filter = ("is_resolved",)
    search_fields = ("product__product_name", "buyer__email", "seller__email")


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ("id", "request", "uploaded_by", "is_invoice", "created_at")
    list_filter = ("is_invoice",)
    search_fields = ("uploaded_by__email", "request__product__product_name")


# ------------------------
# Conversations & Messages
# ------------------------
@admin.register(ProductConversation)
class ProductConversationAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "buyer", "seller", "created_at")
    search_fields = ("product__product_name", "buyer__email", "seller__email")


@admin.register(ProductMessage)
class ProductMessageAdmin(admin.ModelAdmin):
    list_display = ("conversation", "sender", "text", "is_read", "created_at")
    list_filter = ("is_read",)
    search_fields = ("sender__email", "conversation__product__product_name")


# ------------------------
# Reviews
# ------------------------
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "buyer", "rating", "created_at")
    list_filter = ("rating",)
    search_fields = ("product__product_name", "buyer__email")


# ------------------------
# Invoice
# ------------------------
@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "invoice_number",
        "order",
        "buyer",
        "seller",
        "subtotal",
        "tax_amount",
        "total_amount",
        "status",
        "issue_date",
    )
    list_filter = ("status", "issue_date")
    search_fields = ("invoice_number", "buyer__email", "seller__email")


# ------------------------
# Pending Users
# ------------------------
@admin.register(PendingUser)
class PendingUserAdmin(admin.ModelAdmin):
    list_display = ("email", "name", "role", "otp", "created_at")
    search_fields = ("email", "name")
