from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator


# ------------------------
# Custom User
# ------------------------
class CustomUserManager(BaseUserManager):
    def create_user(self, email, name, phone, role, password=None):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, phone=phone, role=role)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, phone, role='buyer', password=None):
        user = self.create_user(email, name, phone, role, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class CustomUser(AbstractBaseUser, PermissionsMixin):
    USER_TYPE_CHOICES = (('buyer', 'Buyer'), ('seller', 'Seller'))

    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=15)
    role = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'phone', 'role']

    def __str__(self):
        return self.email


# ------------------------
# Products
# ------------------------
class Product(models.Model):
    CATEGORY_CHOICES = (
        ('chemicals', 'Chemicals'),
        ('instruments', 'Instruments'),
        ('biologists', 'Biologists'),
    )

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="products"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    image = models.ImageField(upload_to="product_images/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.seller.email})"


# ------------------------
# Cart & Wishlist
# ------------------------
class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")

    def __str__(self):
        return f"{self.product.name} x {self.quantity} ({self.user.email})"


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
        ("cancelled", "Cancelled"),
    ]

    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} by {self.buyer.email}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


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
# QuotationRequest (pre-order)
# ------------------------
class QuotationRequest(models.Model):
    """
    Buyer can request quotation for a product before placing an order.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="quotation_requests")
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_quotation_requests")
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_quotation_requests")
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        unique_together = ("product", "buyer", "seller")

    def __str__(self):
        return f"QuotationRequest: {self.product.name} by {self.buyer.email}"


# ------------------------
# Quotation (can be post-order or pre-order)
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

