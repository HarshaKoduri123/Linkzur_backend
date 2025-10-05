import time
import requests
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404

from rest_framework.decorators import (
    api_view, permission_classes, parser_classes, renderer_classes
)
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.renderers import JSONRenderer
from rest_framework import status

from .models import (
    CustomUser, Product, CartItem, WishlistItem, Order,
    OrderItem, Notification, Payment, Quotation,
    ProductConversation, ProductMessage, QuotationRequest
)
from .serializers import (
    RegisterSerializer, ProductSerializer, CartItemSerializer,
    WishlistItemSerializer, OrderSerializer, NotificationSerializer,
    QuotationSerializer, ProductConversationSerializer, ProductMessageSerializer,
    QuotationRequestSerializer
)
from .utils.paytm_utils import (
    PAYTM_MID, PAYTM_INITIATE_URL, generate_checksum, verify_checksum
)


# ------------------------
# User Endpoints
# ------------------------
def index(request):
    return render(request, 'index.html')

    
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    user = request.user
    data = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "role": user.role,
    }
    return Response(data)


# ------------------------
# Product Endpoints
# ------------------------
@api_view(['GET'])
@permission_classes([AllowAny])
def list_products(request):
    products = Product.objects.all()
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def add_product(request):
    if request.user.role != "seller":
        return Response({"detail": "Only sellers can add products."}, status=status.HTTP_403_FORBIDDEN)

    serializer = ProductSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(seller=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def update_product(request, pk):
    try:
        product = Product.objects.get(pk=pk, seller=request.user)
    except Product.DoesNotExist:
        return Response({"detail": "Product not found or not owned by you."}, status=404)

    serializer = ProductSerializer(product, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=400)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_product(request, pk):
    try:
        product = Product.objects.get(pk=pk, seller=request.user)
    except Product.DoesNotExist:
        return Response({"detail": "Product not found or not owned by you."}, status=404)

    product.delete()
    return Response({"detail": "Product deleted successfully."}, status=204)


# ------------------------
# Cart Endpoints
# ------------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def view_cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    serializer = CartItemSerializer(cart_items, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    serializer = CartItemSerializer(data=request.data)
    if serializer.is_valid():
        product = serializer.validated_data["product"]
        quantity = serializer.validated_data["quantity"]
        cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)
        if not created:
            cart_item.quantity = quantity
        cart_item.save()
        return Response(CartItemSerializer(cart_item).data, status=201)
    return Response(serializer.errors, status=400)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def remove_from_cart(request, pk):
    try:
        item = CartItem.objects.get(pk=pk, user=request.user)
        if item.quantity > 1:
            item.quantity -= 1
            item.save()
            return Response({"detail": f"Decreased quantity to {item.quantity}"}, status=200)
        else:
            item.delete()
            return Response({"detail": "Removed from cart"}, status=200)
    except CartItem.DoesNotExist:
        return Response({"detail": "Not found"}, status=404)


# ------------------------
# Wishlist Endpoints
# ------------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def view_wishlist(request):
    wishlist_items = WishlistItem.objects.filter(user=request.user)
    serializer = WishlistItemSerializer(wishlist_items, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_to_wishlist(request):
    serializer = WishlistItemSerializer(data=request.data)
    if serializer.is_valid():
        product = serializer.validated_data["product"]
        wishlist_item, created = WishlistItem.objects.get_or_create(user=request.user, product=product)
        if not created:
            return Response({"detail": "Already in wishlist"}, status=200)
        return Response(WishlistItemSerializer(wishlist_item).data, status=201)
    return Response(serializer.errors, status=400)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def remove_from_wishlist(request, pk):
    try:
        item = WishlistItem.objects.get(pk=pk, user=request.user)
        item.delete()
        return Response({"detail": "Removed from wishlist"}, status=200)
    except WishlistItem.DoesNotExist:
        return Response({"detail": "Not found"}, status=404)


# ------------------------
# Order Endpoints
# ------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def place_order(request):
    serializer = OrderSerializer(data=request.data, context={"request": request})
    if serializer.is_valid():
        order = serializer.save()
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def view_orders(request):
    orders = Order.objects.filter(buyer=request.user).prefetch_related("items")
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)


# ------------------------
# Notification Endpoints
# ------------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by("-created_at")
    serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, pk):
    try:
        notif = Notification.objects.get(pk=pk, user=request.user)
        notif.is_read = True
        notif.save()
        return Response({"detail": "Notification marked as read"})
    except Notification.DoesNotExist:
        return Response({"detail": "Not found"}, status=404)


# ------------------------
# Paytm Payment Endpoints
# ------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def initiate_paytm_payment(request, order_id):
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
        "txnAmount": {
            "value": f"{order.total_price:.2f}",
            "currency": "INR"
        },
        "userInfo": {
            "custId": str(request.user.id)
        }
    }

    checksum = generate_checksum(body)
    payload = {"body": body, "head": {"signature": checksum}}
    url = f"{PAYTM_INITIATE_URL}?mid={PAYTM_MID}&orderId={unique_order_id}"
    print(url)

    try:
        response = requests.post(url, json=payload, timeout=15)
        print("Status Code:", response.status_code)
        print("Response Text:", response.text)
        data = response.json()
        print("Paytm Initiate Response:", data)
    except Exception as e:
        print("Paytm request error:", e)
        return Response({"detail": "Failed to connect to Paytm"}, status=500)

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
    data = request.POST.dict()
    print("PAYTM CALLBACK DATA:", data)

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

    return Response("status success")


# ------------------------
# Quotation Upload (post-order existing behavior)
# ------------------------
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

    # Only the seller of this request can upload
    if request.user != quotation_request.seller:
        return Response({"detail": "Not authorized"}, status=403)

    data = request.data.copy()
    data["request"] = quotation_request.id  # assign request id

    serializer = QuotationSerializer(data=data, context={"request": request})
    if serializer.is_valid():
        quotation = serializer.save(uploaded_by=request.user)
        # mark request as resolved
        quotation_request.is_resolved = True
        quotation_request.save()
        return Response(QuotationSerializer(quotation, context={"request": request}).data, status=201)
    return Response(serializer.errors, status=400)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_order_quotations(request, order_id):
    try:
        order = Order.objects.get(pk=order_id)
    except Order.DoesNotExist:
        return Response({"detail": "Order not found."}, status=404)

    sellers_in_order = {item.product.seller.id for item in order.items.all()}
    if request.user != order.buyer and request.user.id not in sellers_in_order and not request.user.is_staff:
        return Response({"detail": "Unauthorized"}, status=403)

    quotations = order.quotations.all().order_by("-created_at")
    serializer = QuotationSerializer(quotations, many=True, context={"request": request})
    return Response(serializer.data)


# ------------------------
# Pre-order: Buyer requests a Quotation (new)
# ------------------------
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
            message=f"Buyer {request.user.name} requested a quotation for {product.name}"
        )

    serializer = QuotationRequestSerializer(req, context={"request": request})
    return Response(serializer.data, status=201 if created else 200)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_my_quotation_requests(request):
    """
    Buyers: list requests they created
    Sellers: list requests they received
    """
    if request.user.role == "buyer":
        qs = QuotationRequest.objects.filter(buyer=request.user).select_related("product", "seller")
    else:
        qs = QuotationRequest.objects.filter(seller=request.user).select_related("product", "buyer")
    serializer = QuotationRequestSerializer(qs, many=True, context={"request": request})
    return Response(serializer.data)


# ------------------------
# Seller uploads Quotation for a QuotationRequest (pre-order)
# ------------------------
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
            message=f"Seller {request.user.name} uploaded a quotation for {qreq.product.name}"
        )

        return Response(QuotationSerializer(quotation, context={"request": request}).data, status=201)

    return Response(serializer.errors, status=400)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_quotation_for_request(request, request_id):
    """
    Returns the quotation for a given QuotationRequest (if uploaded).
    """
    qreq = get_object_or_404(QuotationRequest, pk=request_id)
    # only involved parties or staff can view
    if request.user not in [qreq.buyer, qreq.seller] and not request.user.is_staff:
        return Response({"detail": "Unauthorized"}, status=403)

    if hasattr(qreq, "quotation"):
        serializer = QuotationSerializer(qreq.quotation, context={"request": request})
        return Response(serializer.data)
    return Response({"detail": "Quotation not uploaded yet."}, status=404)


# ------------------------
# Product Conversations & Messages 
# ------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def start_or_get_conversation(request):
    order_id = request.data.get("order_id")
    product_id = request.data.get("product_id")

    if not order_id or not product_id:
        return Response({"detail": "order_id and product_id are required"}, status=400)

    order = get_object_or_404(Order, pk=order_id, buyer=request.user)
    product = get_object_or_404(Product, pk=product_id)

    if not order.items.filter(product=product).exists():
        return Response({"detail": "This product is not in the given order"}, status=400)

    buyer = order.buyer
    seller = product.seller

    conv, created = ProductConversation.objects.get_or_create(
        order=order,
        product=product,
        buyer=buyer,
        seller=seller
    )

    serializer = ProductConversationSerializer(conv, context={"request": request})
    return Response(serializer.data, status=201 if created else 200)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_conversations_for_user(request):
    if request.user.role == "buyer":
        convs = ProductConversation.objects.filter(buyer=request.user).select_related("product", "seller", "order")
    else:
        convs = ProductConversation.objects.filter(seller=request.user).select_related("product", "buyer", "order")

    serializer = ProductConversationSerializer(convs, many=True, context={"request": request})
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_messages(request, conversation_id):
    conv = get_object_or_404(ProductConversation, pk=conversation_id)
    if request.user not in [conv.buyer, conv.seller] and not request.user.is_staff:
        return Response({"detail": "Unauthorized"}, status=403)

    messages = conv.messages.all().order_by("created_at")
    serializer = ProductMessageSerializer(messages, many=True, context={"request": request})

    unread = messages.filter(is_read=False).exclude(sender=request.user)
    unread.update(is_read=True)

    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def send_message(request, conversation_id):
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
            message=f"New message on {conv.product.name} from {request.user.name}"
        )
        return Response(ProductMessageSerializer(msg, context={"request": request}).data, status=201)
    return Response(serializer.errors, status=400)
