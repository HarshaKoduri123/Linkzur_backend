from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    register_user,
    user_profile,
    list_products,
    add_product,
    update_product,
    delete_product,
    view_cart,
    add_to_cart,
    remove_from_cart,
    view_wishlist,
    add_to_wishlist,
    remove_from_wishlist,
)

urlpatterns = [
    # User registration
    path("register/", register_user, name="register"),

    # JWT token login & refresh
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Profile
    path("profile/", user_profile, name="profile"),

    # Products
    path("products/", list_products, name="product-list"),
    path("products/add/", add_product, name="product-add"),
    path("products/update/<int:pk>/", update_product, name="product-update"),
    path("products/<int:pk>/delete/", delete_product, name="product-delete"),

    # Cart
    path("cart/", view_cart, name="cart-view"),
    path("cart/add/", add_to_cart, name="cart-add"),
    path("cart/remove/<int:pk>/", remove_from_cart, name="cart-remove"),

    # Wishlist
    path("wishlist/", view_wishlist, name="wishlist-view"),
    path("wishlist/add/", add_to_wishlist, name="wishlist-add"),
    path("wishlist/remove/<int:pk>/", remove_from_wishlist, name="wishlist-remove"),
]
