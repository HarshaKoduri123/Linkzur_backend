import time
import json
import re
import requests
from decimal import Decimal
from datetime import timedelta, datetime
from collections import defaultdict

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404, render
from django.db.models import Count, Sum, Avg, Q, F
from django.db.models.functions import TruncHour, TruncDay, TruncWeek, TruncMonth, Coalesce
from django.utils import timezone

from rest_framework.decorators import (
    api_view, permission_classes, parser_classes, renderer_classes
)
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework import status

from .models import (
    CustomUser, Product, ProductVariant, CartItem, WishlistItem, Order,
    OrderItem, Notification, Payment, Quotation,
    ProductConversation, ProductMessage, QuotationRequest, Review, Invoice, PendingUser
)
from .serializers import (
    RegisterSerializer, ProductSerializer, CartItemSerializer,
    WishlistItemSerializer, OrderSerializer, NotificationSerializer,
    QuotationSerializer, ProductConversationSerializer, ProductMessageSerializer,
    QuotationRequestSerializer, OrderStatusUpdateSerializer, ReviewSerializer,
    InvoiceSerializer, VerifyOTPSerializer
)
from .utils.paytm_utils import (
    PAYTM_MID, PAYTM_INITIATE_URL, generate_checksum, verify_checksum
)
from .utils.invoice_utils import generate_invoice_pdf
from .utils.otp_utils import generate_otp, send_otp_email
from django.contrib.auth import get_user_model
import openpyxl

User = get_user_model()

# ==========================================================
# USER ENDPOINTS
# ==========================================================
def index(request):
    return render(request, "index.html")

@api_view(["POST"])
@permission_classes([AllowAny])
def register_user(request):
    serializer = RegisterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    data = serializer.validated_data
    otp = generate_otp()
    PendingUser.objects.update_or_create(
        email=data["email"],
        defaults={
            "name": data["name"],
            "phone": data.get("phone", ""),
            "role": data.get("role", ""),
            "password": data["password"],
            "otp": otp,
        },
    )
    send_otp_email(data["email"], otp)
    return Response({"message": "OTP sent to your email."})

@api_view(["POST"])
@permission_classes([AllowAny])
def verify_otp_register(request):
    serializer = VerifyOTPSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    email = serializer.validated_data["email"]
    otp = serializer.validated_data["otp"]
    try:
        pending = PendingUser.objects.get(email=email, otp=otp)
    except PendingUser.DoesNotExist:
        return Response({"error": "Invalid OTP or email"}, status=400)
    if not pending.is_valid():
        pending.delete()
        return Response({"error": "OTP expired, please register again"}, status=400)
    user = User.objects.create_user(
        name=pending.name,
        phone=pending.phone,
        email=pending.email,
        role=pending.role,
        password=pending.password,
    )
    pending.delete()
    return Response({"message": "Registration successful, please login."}, status=201)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_profile(request):
    u = request.user
    return Response({
        "id": u.id,
        "name": u.name,
        "email": u.email,
        "phone": u.phone,
        "role": u.role
    })

# ==========================================================
# PRODUCT ENDPOINTS (variant-aware)
# ==========================================================
@api_view(["GET"])
@permission_classes([AllowAny])
def list_products(request):
    qs = Product.objects.select_related("seller").prefetch_related("variants", "reviews").order_by("-created_at")
    category = request.GET.get("category")
    seller = request.GET.get("seller")
    if category:
        qs = qs.filter(category=category)
    if seller:
        qs = qs.filter(seller_id=seller)
    return Response(ProductSerializer(qs, many=True, context={"request": request}).data)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def add_product(request):
    if request.user.role != "seller":
        return Response({"detail": "Only sellers can add products."}, status=403)
    data = request.data.copy()
    variants = []
    if "variants" in data:
        raw = data.get("variants")
        try:
            variants = json.loads(raw) if isinstance(raw, str) else raw
        except json.JSONDecodeError:
            return Response({"variants": ["Invalid JSON format."]}, status=400)
    serializer = ProductSerializer(data=data, context={"request": request})
    if serializer.is_valid():
        product = serializer.save(seller=request.user)
        for v in variants:
            product.variants.create(**v)
        return Response(ProductSerializer(product, context={"request": request}).data, status=201)
    return Response(serializer.errors, status=400)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_products(request):
    """
    Bulk upload products with variants via Excel file.
    Expected Excel format:
    -------------------------------------------------------------------------
    | name | ref_no | description | category | hsn | discount | brand | cas_no | variant_label | est_price | price |
    -------------------------------------------------------------------------
    Each row = one variant of a product.
    Multiple rows can share the same ref_no for multiple variants.
    """
    excel_file = request.FILES.get("file")
    if not excel_file:
        return Response({"detail": "No file uploaded."}, status=400)

    try:
        wb = openpyxl.load_workbook(excel_file)
        ws = wb.active
    except Exception as e:
        return Response({"detail": f"Invalid Excel file: {str(e)}"}, status=400)

    headers = [cell.value for cell in ws[1]]
    required_fields = ["name", "ref_no", "category", "brand", "variant_label", "est_price"]
    for field in required_fields:
        if field not in headers:
            return Response({"detail": f"Missing required column: '{field}'"}, status=400)

    created_products = []
    products_map = {}  # {ref_no: product_instance}

    for row in ws.iter_rows(min_row=2, values_only=True):
        row_data = dict(zip(headers, row))
        ref_no = str(row_data.get("ref_no")).strip() if row_data.get("ref_no") else None
        if not ref_no:
            continue

        # Create product only once per ref_no
        if ref_no not in products_map:
            product_data = {
                "name": row_data.get("name"),
                "ref_no": ref_no,
                "description": row_data.get("description"),
                "category": row_data.get("category"),
                "hsn": row_data.get("hsn"),
                "discount": row_data.get("discount"),
                "brand": row_data.get("brand"),
                "cas_no": row_data.get("cas_no"),
            }

            serializer = ProductSerializer(data=product_data, context={"request": request})
            if serializer.is_valid():
                product = serializer.save(seller=request.user)
                products_map[ref_no] = product
                created_products.append(product)
            else:
                return Response({"detail": "Validation error", "errors": serializer.errors}, status=400)

        # Add variant
        product = products_map[ref_no]
        variant_data = {
            "variant_label": row_data.get("variant_label"),
            "est_price": row_data.get("est_price"),
            "price": row_data.get("price"),
        }

        try:
            ProductVariant.objects.create(product=product, **variant_data)
        except Exception as e:
            return Response({"detail": f"Error creating variant for {ref_no}: {str(e)}"}, status=400)

    serialized = ProductSerializer(created_products, many=True, context={"request": request})
    return Response({"created": len(created_products), "products": serialized.data}, status=201)

@api_view(["PUT"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def update_product(request, pk):
    try:
        product = Product.objects.get(pk=pk, seller=request.user)
    except Product.DoesNotExist:
        return Response({"detail": "Not found"}, status=404)
    data = request.data.copy()
    variants = []
    if "variants" in data:
        raw = data.get("variants")
        try:
            variants = json.loads(raw) if isinstance(raw, str) else raw
        except json.JSONDecodeError:
            return Response({"variants": ["Invalid JSON format."]}, status=400)
    serializer = ProductSerializer(product, data=data, partial=True, context={"request": request})
    if serializer.is_valid():
        updated = serializer.save()
        updated.variants.all().delete()
        for v in variants:
            updated.variants.create(**v)
        return Response(ProductSerializer(updated, context={"request": request}).data)
    return Response(serializer.errors, status=400)

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_product(request, pk):
    try:
        p = Product.objects.get(pk=pk, seller=request.user)
    except Product.DoesNotExist:
        return Response({"detail": "Not found"}, status=404)
    p.delete()
    return Response({"detail": "Product deleted."}, status=204)

# ==========================================================
# CART & WISHLIST (variant-aware)
# ==========================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def view_cart(request):
    items = CartItem.objects.filter(user=request.user).select_related("product", "user")
    return Response(CartItemSerializer(items, many=True).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    product_id = request.data.get("product_id")
    variant_id = request.data.get("variant_id")
    quantity = int(request.data.get("quantity", 1))

    product = get_object_or_404(Product, pk=product_id)
    variant = None

    if variant_id:
        variant = get_object_or_404(ProductVariant, pk=variant_id, product=product)
        price = variant.price if variant.price else variant.est_price or 0
    else:
        price = product.variants.first().price if product.variants.exists() else 0

    item, created = CartItem.objects.get_or_create(
        user=request.user,
        product=product,
        variant=variant,
        defaults={"quantity": quantity}
    )

    if not created:
        # ✅ SET quantity instead of incrementing
        item.quantity = quantity
    item.save()

    return Response(CartItemSerializer(item).data, status=201)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def remove_from_cart(request, pk):
    try:
        item = CartItem.objects.get(pk=pk, user=request.user)
    except CartItem.DoesNotExist:
        return Response({"detail": "Not found"}, status=404)
    if item.quantity > 1:
        item.quantity -= 1
        item.save()
        return Response({"detail": f"Quantity decreased to {item.quantity}"})
    item.delete()
    return Response({"detail": "Removed from cart"})

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def clear_from_cart(request, pk):
    """
    Completely remove a product variant (CartItem) from the user's cart.
    """
    try:
        item = CartItem.objects.get(pk=pk, user=request.user)
    except CartItem.DoesNotExist:
        return Response({"detail": "Not found"}, status=404)

    item.delete()
    return Response({"detail": "Item completely removed from cart."})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def view_wishlist(request):
    items = WishlistItem.objects.filter(user=request.user).select_related("product", "user")
    return Response(WishlistItemSerializer(items, many=True).data)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_to_wishlist(request):
    product_id = request.data.get("product")
    variant_id = request.data.get("variant_id")
    product = get_object_or_404(Product, pk=product_id)
    variant = get_object_or_404(ProductVariant, pk=variant_id, product=product)
    obj, created = WishlistItem.objects.get_or_create(user=request.user, product=product, variant=variant)
    if not created:
        return Response({"detail": "Already in wishlist"})
    return Response(WishlistItemSerializer(obj).data, status=201)

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def remove_from_wishlist(request, product_id):
    try:
        item = WishlistItem.objects.get(product_id=product_id, user=request.user)
    except WishlistItem.DoesNotExist:
        return Response({"detail": "Not found"}, status=404)
    item.delete()
    return Response({"detail": "Removed from wishlist"})

# ==========================================================
# ORDERS & INVOICES (variant-aware)
# ==========================================================
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def place_order(request):
    """
    Creates a new order including variant-specific items
    and automatically generates an invoice.
    """
    serializer = OrderSerializer(data=request.data, context={"request": request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    order = serializer.save()

    # =============================
    # APPLY DISCOUNTED PRICE HERE
    # =============================
    for item in order.items.all():
        variant = item.variant or item.product.variants.first()

        # Base price from variant
        base_price = 0
        if variant:
            base_price = variant.price or variant.est_price or 0

        # Product discount
        discount = item.product.discount or 0

        # Final discounted price
        final_price = (
            base_price - (base_price * (discount / 100))
            if discount > 0
            else base_price
        )

        # Save corrected price
        item.price = final_price
        item.save()

    # =============================
    # SUBTOTAL, TAX & TOTAL
    # =============================
    subtotal = sum(i.price * i.quantity for i in order.items.all())
    tax = subtotal * Decimal("0.18")
    total = subtotal + tax

    # =============================
    # CREATE INVOICE
    # =============================
    invoice = Invoice.objects.create(
        order=order,
        buyer=order.buyer,
        seller=order.items.first().product.seller,
        subtotal=subtotal,
        tax_amount=tax,
        total_amount=total,
    )

    pdf = generate_invoice_pdf(invoice)
    invoice.pdf_file.save(f"{invoice.invoice_number}.pdf", pdf)
    invoice.save()

    return Response({
        "order": OrderSerializer(order).data,
        "invoice": InvoiceSerializer(invoice, context={"request": request}).data,
    }, status=201)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def view_orders(request):
    """
    Lists all orders placed by the current user (buyer).
    """
    orders = Order.objects.filter(buyer=request.user).prefetch_related("items__variant", "items__product")
    return Response(OrderSerializer(orders, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def seller_orders(request):
    """
    Lists all orders that contain products belonging to the seller.
    """
    orders = (
        Order.objects.filter(items__product__seller=request.user)
        .distinct()
        .prefetch_related("items__product", "items__variant")
        .order_by("-created_at")
    )
    return Response(OrderSerializer(orders, many=True).data, status=200)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_order_status(request, order_id):
    """
    Allows sellers involved in an order to update its status.
    """
    try:
        order = Order.objects.prefetch_related("items__product__seller").get(id=order_id)
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=404)

    # authorization
    if request.user not in [i.product.seller for i in order.items.all()]:
        return Response({"error": "Not authorized"}, status=403)

    serializer = OrderStatusUpdateSerializer(order, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        Notification.objects.create(
            user=order.buyer,
            message=f"Your order #{order.id} status changed to '{order.status}'."
        )
        return Response({"message": f"Order #{order.id} updated to '{order.status}'."})
    return Response(serializer.errors, status=400)


# ==========================================================
# REVIEWS (variant-aware)
# ==========================================================
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def add_review(request, product_id):
    """
    GET → Check eligibility  
    POST → Submit review for a specific product variant.
    """
    product = get_object_or_404(Product, pk=product_id)
    variant_id = request.data.get("variant_id")

    if request.method == "GET":
        eligible = OrderItem.objects.filter(
            order__buyer=request.user,
            product=product,
            variant_id=variant_id,
            order__status__in=["delivered", "processing"]
        ).exists()
        return Response({"eligible": eligible})

    # POST
    variant = get_object_or_404(ProductVariant, pk=variant_id, product=product)
    has_purchased = OrderItem.objects.filter(
        order__buyer=request.user,
        product=product,
        variant=variant,
        order__status__in=["delivered", "processing"]
    ).exists()

    if not has_purchased:
        return Response({"detail": "You can only review purchased variants."}, status=403)

    data = request.data.copy()
    data["product"] = product.id
    data["variant"] = variant.id
    serializer = ReviewSerializer(data=data, context={"request": request})
    if serializer.is_valid():
        serializer.save(buyer=request.user)
        Notification.objects.create(
            user=product.seller,
            message=f"New review for {product.name} ({variant.variant_label})"
        )
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)


@api_view(["GET"])
@permission_classes([AllowAny])
def list_reviews(request, product_id):
    """
    Returns all reviews for a product or a specific variant.
    """
    variant_id = request.GET.get("variant_id")
    qs = Review.objects.filter(product_id=product_id)
    if variant_id:
        qs = qs.filter(variant_id=variant_id)
    return Response(ReviewSerializer(qs, many=True).data)


# ==========================================================
# NOTIFICATIONS
# ==========================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_notifications(request):
    """
    Retrieve all notifications for the logged-in user.
    """
    notifications = Notification.objects.filter(user=request.user).order_by("-created_at")
    return Response(NotificationSerializer(notifications, many=True).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, pk):
    """
    Mark a single notification as read.
    """
    try:
        notif = Notification.objects.get(pk=pk, user=request.user)
        notif.is_read = True
        notif.save()
        return Response({"detail": "Notification marked as read"})
    except Notification.DoesNotExist:
        return Response({"detail": "Not found"}, status=404)


# ==========================================================
# PAYTM PAYMENT ENDPOINTS
# ==========================================================
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def initiate_paytm_payment(request, order_id):
    """
    Initiate Paytm payment and generate transaction token.
    """
    try:
        order = Order.objects.get(id=order_id, buyer=request.user)
    except Order.DoesNotExist:
        return Response({"detail": "Order not found"}, status=404)

    unique_order_id = f"{order.id}_{int(time.time())}"

    body = {
        "requestType": "Payment",
        "mid": PAYTM_MID,
        "websiteName": "WEBSTAGING",
        "orderId": unique_order_id,
        "callbackUrl": "http://localhost:8000/api/paytm/callback/",
        "txnAmount": {"value": f"{order.total_price:.2f}", "currency": "INR"},
        "userInfo": {"custId": str(request.user.id)},
    }

    checksum = generate_checksum(body)
    payload = {"body": body, "head": {"signature": checksum}}
    url = f"{PAYTM_INITIATE_URL}?mid={PAYTM_MID}&orderId={unique_order_id}"

    try:
        response = requests.post(url, json=payload, timeout=15)
        data = response.json()
    except Exception as e:
        return Response({"detail": f"Paytm error: {e}"}, status=500)

    if "body" in data and "txnToken" in data["body"]:
        Payment.objects.create(
            order=order,
            amount=order.total_price,
            status="pending",
            paytm_order_id=unique_order_id
        )
        return Response({
            "txnToken": data["body"]["txnToken"],
            "orderId": unique_order_id
        })
    return Response(data, status=400)


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
@renderer_classes([JSONRenderer])
def payment_callback(request):
    """
    Handles Paytm's callback and updates payment/order status.
    """
    data = request.POST.dict()
    paytm_order_id = data.get("ORDERID")
    checksum = data.get("CHECKSUMHASH")

    if not paytm_order_id or not checksum:
        return Response({"status": "failed", "detail": "Invalid callback data"}, status=400)

    if not verify_checksum(data, checksum):
        return Response({"status": "failed", "detail": "Checksum mismatch"}, status=400)

    try:
        payment = Payment.objects.get(paytm_order_id=paytm_order_id)
        order = payment.order
    except Payment.DoesNotExist:
        return Response({"status": "failed", "detail": "Payment not found"}, status=404)

    txn_status = data.get("STATUS")
    txn_id = data.get("TXNID")

    if txn_id:
        payment.txn_id = txn_id

    payment.status = "success" if txn_status == "TXN_SUCCESS" else "failed"
    payment.save()

    order.status = "processing" if payment.status == "success" else "pending"
    order.save()

    Notification.objects.create(
        user=order.buyer,
        message=f"Payment for order #{order.id} {'succeeded' if payment.status == 'success' else 'failed'}."
    )

    return Response({"status": payment.status})

# ==========================================================
# QUOTATIONS (pre-order and post-order)
# ==========================================================
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_quotation(request, request_id):
    """
    Seller uploads a quotation for a pre-order QuotationRequest.
    """
    try:
        quotation_request = QuotationRequest.objects.get(pk=request_id)
    except QuotationRequest.DoesNotExist:
        return Response({"detail": "QuotationRequest not found."}, status=404)

    if request.user != quotation_request.seller:
        return Response({"detail": "Not authorized"}, status=403)

    data = request.data.copy()
    data["request"] = quotation_request.id
    serializer = QuotationSerializer(data=data, context={"request": request})
    if serializer.is_valid():
        quotation = serializer.save(uploaded_by=request.user)
        quotation_request.is_resolved = True
        quotation_request.save()

        Notification.objects.create(
            user=quotation_request.buyer,
            message=f"Seller {request.user.name} uploaded a quotation for {quotation_request.product.name}."
        )

        return Response(QuotationSerializer(quotation, context={"request": request}).data, status=201)
    return Response(serializer.errors, status=400)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_order_quotations(request, order_id):
    """
    View quotations linked to a specific order.
    """
    try:
        order = Order.objects.get(pk=order_id)
    except Order.DoesNotExist:
        return Response({"detail": "Order not found."}, status=404)

    sellers_in_order = {item.product.seller.id for item in order.items.all()}
    if request.user != order.buyer and request.user.id not in sellers_in_order and not request.user.is_staff:
        return Response({"detail": "Unauthorized"}, status=403)

    quotations = order.quotations.all().order_by("-created_at")
    return Response(QuotationSerializer(quotations, many=True, context={"request": request}).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def request_quotation_preorder(request, product_id):
    """
    Buyer requests a quotation for a product before placing an order.
    """
    product = get_object_or_404(Product, pk=product_id)
    seller = product.seller

    if request.user.role != "buyer":
        return Response({"detail": "Only buyers can request quotations."}, status=403)

    req, created = QuotationRequest.objects.get_or_create(
        product=product,
        buyer=request.user,
        seller=seller
    )

    if created:
        Notification.objects.create(
            user=seller,
            message=f"Buyer {request.user.name} requested a quotation for {product.name}."
        )

    serializer = QuotationRequestSerializer(req, context={"request": request})
    return Response(serializer.data, status=201 if created else 200)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_my_quotation_requests(request):
    """
    Buyers → view their quotation requests  
    Sellers → view received quotation requests
    """
    if request.user.role == "buyer":
        qs = QuotationRequest.objects.filter(buyer=request.user).select_related("product", "seller")
    else:
        qs = QuotationRequest.objects.filter(seller=request.user).select_related("product", "buyer")
    return Response(QuotationRequestSerializer(qs, many=True, context={"request": request}).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_quotation_for_request(request, request_id):
    """
    Seller uploads a quotation file in response to a pre-order QuotationRequest.
    """
    qreq = get_object_or_404(QuotationRequest, pk=request_id, seller=request.user)

    if qreq.is_resolved:
        return Response({"detail": "Quotation already provided for this request."}, status=400)

    data = request.data.copy()
    data["request"] = qreq.id
    serializer = QuotationSerializer(data=data, context={"request": request})

    if serializer.is_valid():
        quotation = serializer.save(uploaded_by=request.user)
        qreq.is_resolved = True
        qreq.save()

        Notification.objects.create(
            user=qreq.buyer,
            message=f"Seller {request.user.name} uploaded a quotation for {qreq.product.name}."
        )

        return Response(QuotationSerializer(quotation, context={"request": request}).data, status=201)
    return Response(serializer.errors, status=400)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_quotation_for_request(request, request_id):
    """
    Returns the quotation for a specific QuotationRequest.
    """
    qreq = get_object_or_404(QuotationRequest, pk=request_id)
    if request.user not in [qreq.buyer, qreq.seller] and not request.user.is_staff:
        return Response({"detail": "Unauthorized"}, status=403)

    if hasattr(qreq, "quotation"):
        return Response(QuotationSerializer(qreq.quotation, context={"request": request}).data)
    return Response({"detail": "Quotation not uploaded yet."}, status=404)


# ==========================================================
# PRODUCT CONVERSATIONS & MESSAGES
# ==========================================================
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def start_or_get_conversation(request):
    """
    Start or fetch a conversation between buyer and seller for an ordered product.
    """
    order_id = request.data.get("order_id")
    product_id = request.data.get("product_id")

    if not order_id or not product_id:
        return Response({"detail": "order_id and product_id are required"}, status=400)

    order = get_object_or_404(Order, pk=order_id, buyer=request.user)
    product = get_object_or_404(Product, pk=product_id)

    if not order.items.filter(product=product).exists():
        return Response({"detail": "Product not part of this order."}, status=400)

    conv, created = ProductConversation.objects.get_or_create(
        order=order,
        product=product,
        buyer=order.buyer,
        seller=product.seller
    )

    if created:
        Notification.objects.create(
            user=product.seller,
            message=f"New conversation started on {product.name} by {order.buyer.name}."
        )

    return Response(ProductConversationSerializer(conv, context={"request": request}).data, status=201 if created else 200)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_conversations_for_user(request):
    """
    Fetch all conversations for a user (buyer or seller).
    """
    if request.user.role == "buyer":
        qs = ProductConversation.objects.filter(buyer=request.user).select_related("product", "seller", "order")
    else:
        qs = ProductConversation.objects.filter(seller=request.user).select_related("product", "buyer", "order")

    return Response(ProductConversationSerializer(qs, many=True, context={"request": request}).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_messages(request, conversation_id):
    """
    Fetch all messages in a specific conversation.
    """
    conv = get_object_or_404(ProductConversation, pk=conversation_id)
    if request.user not in [conv.buyer, conv.seller] and not request.user.is_staff:
        return Response({"detail": "Unauthorized"}, status=403)

    messages = conv.messages.all().order_by("created_at")
    serializer = ProductMessageSerializer(messages, many=True, context={"request": request})

    # Mark unread messages as read
    conv.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def send_message(request, conversation_id):
    """
    Send a new message within a product conversation.
    """
    conv = get_object_or_404(ProductConversation, pk=conversation_id)
    if request.user not in [conv.buyer, conv.seller] and not request.user.is_staff:
        return Response({"detail": "Unauthorized"}, status=403)

    data = request.data.copy()
    data["conversation"] = conv.id
    serializer = ProductMessageSerializer(data=data, context={"request": request})

    if serializer.is_valid():
        msg = serializer.save(sender=request.user)
        other_user = conv.seller if request.user == conv.buyer else conv.buyer
        Notification.objects.create(
            user=other_user,
            message=f"New message on {conv.product.name} from {request.user.name}."
        )
        return Response(ProductMessageSerializer(msg, context={"request": request}).data, status=201)

    return Response(serializer.errors, status=400)


# ==========================================================
# SEARCH (by name or CAS)
# ==========================================================
from django.db.models import Value, DecimalField
from django.db.models.functions import Coalesce
from django.db.models import Min

from django.db.models import Q
import re

import re
from django.db.models import Q, Min
from django.db.models.functions import Coalesce
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

@api_view(["GET"])
@permission_classes([AllowAny])
def search_products(request):
    """
    Search products by name, CAS No, Ref No, or HSN code.

    Examples:
      /api/search/?q=acetone
      /api/search/?q=67-64-1
      /api/search/?q=P001
      /api/search/?q=2207
    """
    query = request.GET.get("q", "").strip()
    if not query:
        return Response({"detail": "Query parameter 'q' is required."}, status=400)

    # Detect CAS number pattern (e.g., 67-64-1 or 7732-18-5)
    is_cas_no = bool(re.match(r"^\d{2,7}-\d{2}-\d$", query))

    # Build search filter dynamically
    filters = Q()

    if is_cas_no:
        filters |= Q(cas_no__icontains=query)
    else:
        filters |= (
            Q(name__icontains=query)
            | Q(ref_no__icontains=query)
            | Q(hsn__icontains=query)
            | Q(cas_no__icontains=query)
        )

    products = (
        Product.objects.filter(filters)
        .select_related("seller")
        .prefetch_related("variants", "reviews")
        .annotate(
            min_effective_price=Min(
                Coalesce("variants__price", "variants__est_price")
            )
        )
        .order_by("name")
    )

    serializer = ProductSerializer(products, many=True, context={"request": request})
    return Response(serializer.data, status=200)


# ==========================================================
# SELLER DASHBOARD — STATS
# ==========================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def seller_dashboard_stats(request):
    """
    Main dashboard statistics for sellers.
    Uses OrderItem.price when present; otherwise falls back to
    the item's variant price → variant est_price.
    """
    if request.user.role != "seller":
        return Response({"error": "Only sellers can access this endpoint"}, status=403)

    # Period selector
    period = request.GET.get("period", "month")  # day, week, month, year
    today = timezone.now().date()

    if period == "day":
        start_date = today
    elif period == "week":
        start_date = today - timedelta(days=7)
    elif period == "month":
        start_date = today.replace(day=1)
    else:  # year
        start_date = today.replace(month=1, day=1)

    # Basic counts
    total_products = Product.objects.filter(seller=request.user).count()
    total_orders_distinct = (
        Order.objects.filter(items__product__seller=request.user).distinct().count()
    )

    # Revenue with safe fallback on variant price / est_price
    revenue_qs = OrderItem.objects.filter(
        product__seller=request.user,
        order__created_at__date__gte=start_date,
    ).annotate(
        eff_price=Coalesce(
            "price",
            Coalesce("variant__price", "variant__est_price"),
            output_field=DecimalField(max_digits=18, decimal_places=2),
        )
    )

    revenue_data = revenue_qs.aggregate(
        total_revenue=Sum(F("quantity") * F("eff_price")),
        total_units=Sum("quantity"),
        total_orders=Count("order", distinct=True),
    )

    total_revenue = float(revenue_data.get("total_revenue") or 0)
    total_units_sold = int(revenue_data.get("total_units") or 0)
    total_orders_placed = int(revenue_data.get("total_orders") or 0)
    avg_order_value = (total_revenue / total_orders_placed) if total_orders_placed else 0.0

    # Order status breakdown (counts)
    order_status = (
        Order.objects.filter(items__product__seller=request.user)
        .values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )

    # Recent orders (last 5)
    recent_orders = (
        Order.objects.filter(items__product__seller=request.user)
        .distinct()
        .order_by("-created_at")[:5]
    )

    recent_orders_data = [
        {
            "id": o.id,
            "buyer": o.buyer.name,
            "total_price": float(o.total_price),
            "status": o.status,
            "created_at": o.created_at,
            "items_count": o.items.count(),
        }
        for o in recent_orders
    ]

    return Response(
        {
            "period": period,
            "total_products": total_products,
            "total_orders": total_orders_placed,
            "distinct_orders": total_orders_distinct,
            "total_revenue": total_revenue,
            "total_units_sold": total_units_sold,
            "avg_order_value": round(avg_order_value, 2),
            "order_status_breakdown": list(order_status),
            "recent_orders": recent_orders_data,
        }
    )


# ==========================================================
# SELLER DASHBOARD — SALES TRENDS
# ==========================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def seller_sales_trends(request):
    """
    Aggregated sales trends for the seller over a period.
    Uses eff_price (OrderItem.price → variant.price → variant.est_price).
    """
    if request.user.role != "seller":
        return Response({"error": "Only sellers can access this endpoint"}, status=403)

    period = request.GET.get("period", "month")  # day, week, month, year
    now = timezone.now()
    today = now.date()

    if period == "day":  # last 24 hours, grouped by hour
        start_dt = now - timedelta(hours=24)
        trunc_func = TruncHour("order__created_at")
        time_filter = Q(order__created_at__gte=start_dt)
        fmt = "%Y-%m-%d %H:%M"
    elif period == "week":
        start_date = today - timedelta(days=7)
        trunc_func = TruncDay("order__created_at")
        time_filter = Q(order__created_at__date__gte=start_date)
        fmt = "%Y-%m-%d"
    elif period == "month":
        start_date = today.replace(day=1)
        trunc_func = TruncDay("order__created_at")
        time_filter = Q(order__created_at__date__gte=start_date)
        fmt = "%Y-%m-%d"
    else:  # year
        start_date = today.replace(month=1, day=1)
        trunc_func = TruncMonth("order__created_at")
        time_filter = Q(order__created_at__date__gte=start_date)
        fmt = "%Y-%m"

    base = (
        OrderItem.objects.filter(product__seller=request.user)
        .filter(time_filter)
        .annotate(
            eff_price=Coalesce(
                "price",
                Coalesce("variant__price", "variant__est_price"),
                output_field=DecimalField(max_digits=18, decimal_places=2),
            ),
            period=trunc_func,
        )
        .values("period")
        .annotate(
            revenue=Sum(F("quantity") * F("eff_price")),
            units_sold=Sum("quantity"),
            order_count=Count("order", distinct=True),
        )
        .order_by("period")
    )

    data = [
        {
            "period": row["period"].strftime(fmt),
            "revenue": float(row["revenue"] or 0),
            "units_sold": int(row["units_sold"] or 0),
            "order_count": int(row["order_count"] or 0),
        }
        for row in base
    ]

    return Response({"period": period, "sales_trends": data})


# ==========================================================
# SELLER DASHBOARD — PRODUCT PERFORMANCE
# ==========================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def seller_product_performance(request):
    """
    Product performance metrics for the seller.
    Revenue is based on OrderItem.price (with fallback to variant price/est_price).
    Also returns per-product derived min_effective_price from variants.
    """
    if request.user.role != "seller":
        return Response({"error": "Only sellers can access this endpoint"}, status=403)

    period = request.GET.get("period", "month")
    today = timezone.now().date()

    if period == "day":
        start_date = today
    elif period == "week":
        start_date = today - timedelta(days=7)
    elif period == "month":
        start_date = today.replace(day=1)
    else:  # year
        start_date = today.replace(month=1, day=1)

    # Base queryset of products for seller; annotate min effective variant price
    products_qs = (
        Product.objects.filter(seller=request.user)
        .annotate(
            min_effective_price=Min(
                Coalesce("variants__price", "variants__est_price")
            )
        )
        .prefetch_related("variants", "reviews")
    )

    # OrderItem aggregates (revenue/units/orders) per product over period with eff_price fallback
    perf_rows = (
        OrderItem.objects.filter(
            product__seller=request.user, order__created_at__date__gte=start_date
        )
        .annotate(
            eff_price=Coalesce(
                "price",
                Coalesce("variant__price", "variant__est_price"),
                output_field=DecimalField(max_digits=18, decimal_places=2),
            )
        )
        .values("product_id")
        .annotate(
            total_sales=Sum("quantity"),
            total_revenue=Sum(F("quantity") * F("eff_price")),
            order_count=Count("order", distinct=True),
        )
    )
    # Map aggregates by product_id
    by_pid = {
        r["product_id"]: {
            "total_sales": int(r["total_sales"] or 0),
            "total_revenue": float(r["total_revenue"] or 0),
            "order_count": int(r["order_count"] or 0),
        }
        for r in perf_rows
    }

    # Compose response
    out = []
    for p in products_qs:
        # product-level ratings
        avg_rating = p.reviews.aggregate(avg=Avg("rating")).get("avg") or 0
        review_count = p.reviews.count()

        # merged aggregates
        agg = by_pid.get(p.id, {"total_sales": 0, "total_revenue": 0.0, "order_count": 0})

        out.append(
            {
                "id": p.id,
                "name": p.name,
                "category": p.category,
                # Derived display price from variants (not a raw product.price)
                "min_effective_price": float(p.min_effective_price or 0),
                "total_sales": agg["total_sales"],
                "total_revenue": agg["total_revenue"],
                "order_count": agg["order_count"],
                "average_rating": round(float(avg_rating), 1),
                "review_count": review_count,
            }
        )

    # Sort by revenue desc and return top 10 for convenience
    out_sorted = sorted(out, key=lambda x: x["total_revenue"], reverse=True)[:10]
    return Response({"top_products": out_sorted})


# ==========================================================
# SELLER DASHBOARD — CUSTOMER INSIGHTS
# ==========================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def seller_customer_insights(request):
    """
    Customer insights and behavior for the seller.
    Uses Order.total_price for CLV; if you want a variant-aware fallback here,
    ensure total_price is written correctly at order creation (it is in place_order).
    """
    if request.user.role != "seller":
        return Response({"error": "Only sellers can access this endpoint"}, status=403)

    period = request.GET.get("period", "month")
    today = timezone.now().date()

    if period == "day":
        start_date = today
    elif period == "week":
        start_date = today - timedelta(days=7)
    elif period == "month":
        start_date = today.replace(day=1)
    else:  # year
        start_date = today.replace(month=1, day=1)

    # All orders that include this seller's items
    customer_data = (
        Order.objects.filter(
            items__product__seller=request.user,
            created_at__date__gte=start_date,
        )
        .values("buyer")
        .annotate(
            order_count=Count("id", distinct=True),
            total_spent=Sum("total_price"),
        )
        .order_by("-total_spent")
    )

    repeat_customers = 0
    new_customers = 0
    total_customers = len(customer_data)
    total_spend_all = 0.0

    for c in customer_data:
        if (c.get("order_count") or 0) > 1:
            repeat_customers += 1
        else:
            new_customers += 1
        total_spend_all += float(c.get("total_spent") or 0)

    return Response(
        {
            "total_customers": total_customers,
            "repeat_customers": repeat_customers,
            "new_customers": new_customers,
            "repeat_rate": (repeat_customers / total_customers * 100) if total_customers else 0.0,
            "avg_customer_value": (total_spend_all / total_customers) if total_customers else 0.0,
        }
    )
