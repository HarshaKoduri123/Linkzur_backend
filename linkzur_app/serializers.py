from rest_framework import serializers
from .models import (
    Notification,
    CustomUser,
    Product,
    CartItem,
    WishlistItem,
    Order,
    OrderItem,
    Quotation,
    ProductConversation,
    ProductMessage,
    QuotationRequest,  
)


# ------------------------
# User Registration
# ------------------------
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "name",
            "phone",
            "email",
            "role",
            "password",
            "confirm_password",
        ]

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        return CustomUser.objects.create_user(**validated_data)


# ------------------------
# Product
# ------------------------
class ProductSerializer(serializers.ModelSerializer):
    seller = serializers.StringRelatedField(read_only=True)  # ✅ seller added

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "price",
            "category",
            "image",
            "created_at",
            "updated_at",
            "seller",   # ✅ must include seller
        ]
        read_only_fields = ["created_at", "updated_at", "seller"]


# ------------------------
# Cart & Wishlist
# ------------------------
class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source="product", write_only=True
    )

    class Meta:
        model = CartItem
        fields = ["id", "product", "product_id", "quantity", "added_at"]


class WishlistItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source="product", write_only=True
    )

    class Meta:
        model = WishlistItem
        fields = ["id", "product", "product_id", "added_at"]


# ------------------------
# Orders
# ------------------------
class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source="product", write_only=True
    )

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_id", "quantity", "price"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ["id", "buyer", "status", "total_price", "created_at", "items"]
        read_only_fields = ["buyer", "status", "total_price", "created_at"]

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        buyer = self.context["request"].user
        order = Order.objects.create(buyer=buyer, **validated_data)

        total_price = 0
        for item_data in items_data:
            product = item_data["product"]
            quantity = item_data["quantity"]
            price = product.price * quantity
            OrderItem.objects.create(
                order=order, product=product, quantity=quantity, price=price
            )
            total_price += price

            # ---- Notify Seller ----
            seller = product.seller
            message = f"Buyer {buyer.name} purchased {quantity} x {product.name}"
            Notification.objects.create(user=seller, message=message)

        order.total_price = total_price
        order.save()
        return order


# ------------------------
# Notifications
# ------------------------
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "message", "is_read", "created_at"]


# ------------------------
# Quotations (post-order)
# ------------------------
class QuotationSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.StringRelatedField(read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Quotation
        fields = [
            "id",
            "request",
            "uploaded_by",
            "file",
            "file_url",
            "note",
            "is_invoice",
            "created_at",
        ]
        read_only_fields = ["uploaded_by", "created_at", "file_url"]

    def get_file_url(self, obj):
        request = self.context.get("request")
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None


# ------------------------
# Quotation Request (pre-order)
# ------------------------
class QuotationRequestSerializer(serializers.ModelSerializer):
    buyer = serializers.StringRelatedField(read_only=True)
    seller = serializers.StringRelatedField(read_only=True)
    product = ProductSerializer(read_only=True)

    class Meta:
        model = QuotationRequest
        fields = ["id", "product", "buyer", "seller", "created_at", "is_resolved"]
        read_only_fields = ["buyer", "seller", "created_at", "is_resolved"]


# ------------------------
# Product Conversations + Messages
# ------------------------
class ProductMessageSerializer(serializers.ModelSerializer):
    sender = serializers.StringRelatedField(read_only=True)
    attachment_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductMessage
        fields = [
            "id",
            "conversation",
            "sender",
            "text",
            "attachment",
            "attachment_url",
            "created_at",
            "is_read",
        ]
        read_only_fields = ["sender", "created_at", "is_read", "attachment_url"]

    def get_attachment_url(self, obj):
        request = self.context.get("request")
        if obj.attachment and request:
            return request.build_absolute_uri(obj.attachment.url)
        return None


class ProductConversationSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    buyer = serializers.StringRelatedField(read_only=True)
    seller = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ProductConversation
        fields = ["id", "order", "product", "buyer", "seller", "created_at"]
        read_only_fields = ["buyer", "seller", "created_at"]
