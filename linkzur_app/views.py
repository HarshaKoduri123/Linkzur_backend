from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from .models import CustomUser, Product, CartItem, WishlistItem
from .serializers import RegisterSerializer, ProductSerializer, CartItemSerializer, WishlistItemSerializer


# ------------------------
# User Endpoints
# ------------------------

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
            cart_item.quantity += quantity
        cart_item.save()
        return Response(CartItemSerializer(cart_item).data, status=201)
    return Response(serializer.errors, status=400)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def remove_from_cart(request, pk):
    try:
        item = CartItem.objects.get(pk=pk, user=request.user)
        item.delete()
        return Response({"detail": "Removed from cart"})
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
    print(serializer.data)
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
        return Response({"detail": "Removed from wishlist"})
    except WishlistItem.DoesNotExist:
        return Response({"detail": "Not found"}, status=404)
