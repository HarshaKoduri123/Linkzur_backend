from rest_framework import serializers
from .models import (
    Notification,
    CustomUser,
    Product,
    ProductVariant,
    CartItem,
    WishlistItem,
    Order,
    OrderItem,
    Quotation,
    ProductConversation,
    ProductMessage,
    QuotationRequest,
    Review,
    Invoice,
    PendingUser,
)

# ==========================================================
# USER REGISTRATION
# ==========================================================
class RegisterSerializer(serializers.Serializer):
    # Common
    role = serializers.CharField()
    name = serializers.CharField()
    phone = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField()
    confirm_password = serializers.CharField()

    # Buyer
    username = serializers.CharField(required=False)
    buyerCategory = serializers.CharField(required=False)
    organizationName = serializers.CharField(required=False)
    city = serializers.CharField(required=False)
    state = serializers.CharField(required=False)
    pincode = serializers.CharField(required=False)

    # Seller
    businessName = serializers.CharField(required=False)
    entityType = serializers.CharField(required=False)
    gstNumber = serializers.CharField(required=False)
    panNumber = serializers.CharField(required=False)
    sellerCategories = serializers.ListField(required=False)
    designation = serializers.CharField(required=False)
    addressLine1 = serializers.CharField(required=False)
    addressLine2 = serializers.CharField(required=False)
    websiteUrl = serializers.CharField(required=False)
    linkedinUrl = serializers.CharField(required=False)

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match.")
        return data


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)


# ==========================================================
# PRODUCT & VARIANTS
# ==========================================================
class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ["id", "variant_label", "est_price", "price", "created_at"]


class ProductSerializer(serializers.ModelSerializer):
    seller = serializers.StringRelatedField(read_only=True)
    variants = ProductVariantSerializer(many=True, required=False)
    average_rating = serializers.SerializerMethodField()
    total_reviews = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id", "name", "ref_no", "description", "category", "hsn",
            "discount", "brand", "cas_no", "image", "seller", "gst",
            "created_at", "updated_at", "average_rating", "total_reviews", "variants",
        ]
        read_only_fields = ["created_at", "updated_at", "seller"]

    def get_average_rating(self, obj):
        reviews = getattr(obj, "reviews", None)
        if not reviews:
            return None
        total = reviews.count()
        if total == 0:
            return None
        avg = sum([r.rating for r in reviews.all()]) / total
        return round(avg, 1)

    def get_total_reviews(self, obj):
        reviews = getattr(obj, "reviews", None)
        return reviews.count() if reviews else 0

    def create(self, validated_data):
        variants_data = validated_data.pop("variants", [])
        product = Product.objects.create(**validated_data)
        for variant_data in variants_data:
            ProductVariant.objects.create(product=product, **variant_data)
        return product

    def update(self, instance, validated_data):
        variants_data = validated_data.pop("variants", [])
        instance = super().update(instance, validated_data)
        instance.variants.all().delete()
        for variant_data in variants_data:
            ProductVariant.objects.create(product=instance, **variant_data)
        return instance


# ==========================================================
# CART & WISHLIST
# ==========================================================
class CartItemSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source="product", write_only=True
    )

    variant = ProductVariantSerializer(read_only=True)
    variant_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.all(), source="variant", write_only=True, required=False
    )

    class Meta:
        model = CartItem
        fields = ["id", "product", "product_id", "variant", "variant_id", "quantity", "added_at"]

    def get_product(self, obj):
        request = self.context.get("request")
        return ProductSerializer(obj.product, context={"request": request}).data


class WishlistItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source="product", write_only=True
    )

    class Meta:
        model = WishlistItem
        fields = ["id", "product", "product_id", "added_at"]


# ==========================================================
# ORDERS
# ==========================================================
class InvoiceSerializer(serializers.ModelSerializer):
    buyer_email = serializers.EmailField(source="buyer.email", read_only=True)
    seller_email = serializers.EmailField(source="seller.email", read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id",
            "invoice_number",
            "order_id",
            "buyer_email",
            "seller_email",
            "subtotal",
            "tax_amount",
            "total_amount",
            "status",
            "issue_date",
            "pdf_file",
        ]



class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True) 
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source="product", write_only=True
    )
    variant_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.all(), source="variant", write_only=True, required=False
    )

    class Meta:
        model = OrderItem
        fields = ["id", "product", "variant", "product_id", "variant_id", "quantity", "price"]

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    invoice = InvoiceSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "buyer",
            "status",
            "total_price",
            "created_at",
            "items",
            "address",
            "invoice",
        ]
        read_only_fields = ["buyer", "status", "total_price", "created_at"]


    def create(self, validated_data):
        items_data = validated_data.pop("items")
        buyer = self.context["request"].user

        order = Order.objects.create(buyer=buyer, **validated_data)

        total_price = 0
        for item_data in items_data:
            product = item_data["product"]
            variant = item_data.get("variant", product.variants.first())
            quantity = item_data["quantity"]

            price = item_data["price"]

            OrderItem.objects.create(
                order=order,
                product=product,
                variant=variant,
                quantity=quantity,
                price=price
            )

            total_price += price

            Notification.objects.create(
                user=product.seller,
                message=f"Buyer {buyer.name} purchased {quantity} x {product.name}"
            )

        order.total_price = total_price
        order.save()
        return order




class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["status"]


# ==========================================================
# NOTIFICATIONS
# ==========================================================
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "message", "is_read", "created_at"]


# ==========================================================
# QUOTATIONS
# ==========================================================
class QuotationSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.StringRelatedField(read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Quotation
        fields = [
            "id", "request", "uploaded_by", "file", "file_url",
            "note", "is_invoice", "created_at",
        ]
        read_only_fields = ["uploaded_by", "created_at", "file_url"]

    def get_file_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.file.url) if obj.file and request else None


# ==========================================================
# QUOTATION REQUESTS (PRE-ORDER)
# ==========================================================
class QuotationRequestSerializer(serializers.ModelSerializer):
    buyer = serializers.StringRelatedField(read_only=True)
    seller = serializers.StringRelatedField(read_only=True)
    product = ProductSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True)

    quotation = QuotationSerializer(read_only=True)  # FULL quotation with file

    class Meta:
        model = QuotationRequest
        fields = [
            "id",
            "product",
            "variant",
            "buyer",
            "seller",
            "created_at",
            "is_resolved",
            "quotation",  # 🔥 includes file_url, note, is_invoice
        ]


# ==========================================================
# PRODUCT CONVERSATIONS & MESSAGES
# ==========================================================
class ProductMessageSerializer(serializers.ModelSerializer):
    sender = serializers.StringRelatedField(read_only=True)
    attachment_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductMessage
        fields = [
            "id", "conversation", "sender", "text",
            "attachment", "attachment_url", "created_at", "is_read",
        ]
        read_only_fields = ["sender", "created_at", "is_read", "attachment_url"]

    def get_attachment_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.attachment.url) if obj.attachment and request else None


class ProductConversationSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    buyer = serializers.StringRelatedField(read_only=True)
    seller = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ProductConversation
        fields = ["id", "order", "product", "buyer", "seller", "created_at"]
        read_only_fields = ["buyer", "seller", "created_at"]


# ==========================================================
# REVIEWS (variant-aware)
# ==========================================================
class ReviewSerializer(serializers.ModelSerializer):
    buyer = serializers.StringRelatedField(read_only=True)
    variant = ProductVariantSerializer(read_only=True)
    variant_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.all(), source="variant", write_only=True, required=False
    )

    class Meta:
        model = Review
        fields = ["id", "product", "variant", "variant_id", "buyer", "rating", "comment", "created_at"]
        read_only_fields = ["buyer", "created_at"]



