from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.utils import timezone
from datetime import timedelta
from django.db import models
from django.conf import settings
from django.db.models import JSONField

CATEGORIES = [
    ("chemicals", "Chemicals"),
    ("instruments", "Instruments"),
    ("consumables", "Consumables"),
    ("ppe", "PPE"),
    ("edevices", "E-Devices"),
    ("glassware", "Glassware"),
    ("biologics", "Biologics"),
    ("solvents", "Solvents"),
    ("books_stationery", "Books & Stationery"),
    ("furniture", "Furniture"),
]


# ============================
# Custom User Model
# ============================
class CustomUserManager(BaseUserManager):
    def create_user(self, email, name, phone, role, password=None):
        if not email:
            raise ValueError("Email required")

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            name=name,
            phone=phone,
            role=role
        )
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(
        self, email, name="Admin", phone="0000", role="buyer", password=None
    ):
        user = self.create_user(email, name, phone, role, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class CustomUser(AbstractBaseUser, PermissionsMixin):
    USER_TYPE_CHOICES = (
        ("buyer", "Buyer"),
        ("seller", "Seller"),
    )

    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=15)
    role = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "phone", "role"]

    objects = CustomUserManager()

    def __str__(self):
        return self.email


# ============================
# Buyer Profile
# ============================
class BuyerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="buyer_profile"
    )

    username = models.CharField(max_length=100)
    buyer_category = models.CharField(max_length=100)
    organization_name = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=20)

    def __str__(self):
        return f"BuyerProfile: {self.user.email}"

class ShippingAddress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shipping_addresses"
    )

    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=20)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.city} ({'Default' if self.is_default else 'Other'})"


class BillingAddress(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="billing_address"
    )

    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=20)

    def __str__(self):
        return f"BillingAddress({self.user.email})"


# ============================
# Seller Profile
# ============================
class SellerProfile(models.Model):
    ENTITY_TYPES = (
        ("Proprietorship", "Proprietorship"),
        ("Partnership", "Partnership"),
        ("Private Limited", "Private Limited"),
        ("Public Limited", "Public Limited"),
        ("LLP", "LLP"),
        ("Other", "Other"),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="seller_profile"
    )

    business_name = models.CharField(max_length=255)
    entity_type = models.CharField(max_length=50, choices=ENTITY_TYPES)
    gst_number = models.CharField(max_length=20)
    pan_number = models.CharField(max_length=20)

    temp_password = models.CharField(max_length=128, null=True, blank=True)


    business_document = models.FileField(
        upload_to="seller_documents/",
        validators=[FileExtensionValidator(["pdf", "jpg", "jpeg", "png"])],
        null=True, blank=True
    )

    gst_certificate = models.FileField(
        upload_to="seller_gst_docs/",
        validators=[FileExtensionValidator(["pdf", "jpg", "jpeg", "png"])],
        null=True, blank=True
    )

    seller_categories = JSONField(default=list)

    designation = models.CharField(max_length=100, blank=True, null=True)
    website_url = models.URLField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)

    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=20)

    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"SellerProfile: {self.user.email}"


class PasswordResetToken(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens"
    )
    token = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return timezone.now() < self.created_at + timedelta(minutes=10)

    def __str__(self):
        return f"PasswordResetToken({self.user.email})"


class Product(models.Model):
    CATEGORY_CHOICES = CATEGORIES

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="products"
    )

    name = models.CharField(max_length=255)
    ref_no = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    hsn = models.CharField(max_length=20, blank=True, null=True)
    gst = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    brand = models.CharField(max_length=255)
    cas_no = models.CharField(max_length=50, blank=True, null=True)
    image = models.ImageField(upload_to="product_images/", null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("seller", "ref_no")
        indexes = [
            models.Index(fields=["seller", "ref_no"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.seller.email})"



# -----------------------------------------------------
# 🧮 ProductVariant — Multiple quantity & price options
# -----------------------------------------------------
# models.py
#QuantatyVarient
class ProductVariant(models.Model):

    product = models.ForeignKey("Product", on_delete=models.CASCADE, related_name="variants")
    variant_label = models.CharField(max_length=100)
    est_price = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    discount = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True
    )
    #seller varient id

    def __str__(self):
        return f"{self.variant_label} - {self.product.name}"




# ------------------------
# Cart & Wishlist
# ------------------------
class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product", "variant")  # now each variant can be added separately

    def __str__(self):
        variant_label = f" ({self.variant.variant_label})" if self.variant else ""
        return f"{self.product.name}{variant_label} x {self.quantity} ({self.user.email})"


class WishlistItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlist_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")

    def __str__(self):
        return f"{self.product.name} (Wishlist - {self.user.email})"


# ------------------------
# Orders
# ------------------------


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("completed", "Completed"),   # ✅ ADDED
        ("cancelled", "Cancelled"),
    ]

    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    address = models.TextField(blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # OTP for delivery confirmation
    delivery_otp = models.CharField(max_length=6, blank=True, null=True)
    is_delivered_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} by {self.buyer.email}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.SET_NULL, null=True, blank=True, related_name="order_items"
    )  
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        variant_label = f" ({self.variant.variant_label})" if self.variant else ""
        return f"{self.product.name}{variant_label} x {self.quantity}"


# ------------------------
# Notifications
# ------------------------
class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.email} - {self.message[:30]}"


# ------------------------
# Payment (Paytm)
# ------------------------
class Payment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[("pending","Pending"),("success","Success"),("failed","Failed")])
    txn_id = models.CharField(max_length=100, null=True, blank=True)
    paytm_order_id = models.CharField(max_length=100, null=True, blank=True)


# ------------------------
# QuotationRequest
# ------------------------
class QuotationRequest(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="quotation_requests")
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name="quotation_requests",
        null=True,
        blank=True
    )

    quantity = models.PositiveIntegerField(default=1)
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_quotation_requests")
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_quotation_requests")

    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        unique_together = ("product", "variant", "buyer", "seller")

    def __str__(self):
        var = f" ({self.variant.variant_label})" if self.variant else ""
        return f"QuotationRequest: {self.product.name}{var} by {self.buyer.email}"


# ------------------------
# Quotation
# ------------------------
class Quotation(models.Model):
    """
    Quotation tied only to a pre-order QuotationRequest.
    """
    request = models.OneToOneField(
        QuotationRequest, on_delete=models.CASCADE, related_name="quotation"
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="uploaded_quotations"
    )
    file = models.FileField(
        upload_to="quotations/%Y/%m/%d/",
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
    )
    note = models.TextField(blank=True, null=True)
    is_invoice = models.BooleanField(default=False, help_text="If true, treat as final invoice")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Quotation #{self.id} for Request #{self.request.id} by {self.uploaded_by.email}"


# ------------------------
# Conversations & Messages (post-order)
# ------------------------
class ProductConversation(models.Model):
    """
    One conversation per (order, product, buyer, seller).
    A seller and buyer can chat only after an order is placed.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="conversations")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="conversations")
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="buyer_conversations")
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="seller_conversations")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("order", "product", "buyer", "seller")

    def __str__(self):
        return f"Conversation: Order#{self.order.id} - {self.product.name} ({self.buyer.email} ↔ {self.seller.email})"


class ProductMessage(models.Model):
    conversation = models.ForeignKey(ProductConversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField(blank=True)
    attachment = models.FileField(
        upload_to="chat_attachments/%Y/%m/%d/",
        validators=[FileExtensionValidator(allowed_extensions=['pdf','png','jpg','jpeg','txt'])],
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message {self.id} in conv {self.conversation.id} by {self.sender.email}"

# ------------------------
# Product Reviews
# ------------------------
class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("product", "buyer")  # one review per product per buyer
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.product.name} - {self.rating}★ by {self.buyer.email}"

# models.py
from django.db import models
from django.conf import settings
from .models import Order

class Invoice(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("issued", "Issued"),
        ("cancelled", "Cancelled"),
    ]

    invoice_number = models.CharField(max_length=20, unique=True)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="invoice")
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="buyer_invoices")
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="seller_invoices")
    address = models.TextField(blank=True, null=True)
    issue_date = models.DateField(auto_now_add=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="issued")
    pdf_file = models.FileField(upload_to="invoices/", null=True, blank=True)

    def __str__(self):
        return f"Invoice {self.invoice_number}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            last = Invoice.objects.order_by("id").last()
            next_num = (last.id + 1) if last else 1
            self.invoice_number = f"INV-{next_num:05d}"
        super().save(*args, **kwargs)


class PendingUser(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, blank=True, null=True)
    password = models.CharField(max_length=128)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        
        return timezone.now() < self.created_at + timedelta(minutes=5)

    def __str__(self):
        return f"{self.email} - {self.otp}"

# models.py

class RecentlyViewed(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recently_viewed"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="recently_viewed_users"
    )
    viewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "product")
        ordering = ["-viewed_at"]

    def __str__(self):
        return f"{self.user.email} viewed {self.product.name}"
