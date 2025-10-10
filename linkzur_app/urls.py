from django.urls import path, re_path
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
    place_order,
    view_orders,
    get_notifications,
    mark_notification_read,
    initiate_paytm_payment,
    payment_callback,
    upload_quotation,
    list_order_quotations,
    start_or_get_conversation,
    list_conversations_for_user,
    list_messages,
    send_message,
    request_quotation_preorder,
    list_my_quotation_requests,
    upload_quotation_for_request,
    get_quotation_for_request,
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
    path("wishlist/remove/<int:product_id>/", remove_from_wishlist, name="remove-from-wishlist"),

    # Orders
    path("orders/place/", place_order, name="order-place"),
    path("orders/", view_orders, name="order-list"),

    # Notifications
    path("notifications/", get_notifications, name="notification-list"),
    path("notifications/<int:pk>/read/", mark_notification_read, name="notification-read"),

    # Paytm
    path("paytm/initiate/<int:order_id>/", initiate_paytm_payment, name="paytm-initiate"),
    path('paytm/callback/', payment_callback, name='paytm-callback'),

    # Quotations / invoices (post-order)
    path("orders/<int:order_id>/quotations/upload/", upload_quotation, name="upload-quotation"),
    path("orders/<int:order_id>/quotations/", list_order_quotations, name="list-quotations"),

    # Pre-order quotation requests
    path("quotation-requests/products/<int:product_id>/request/", request_quotation_preorder, name="request-quotation-preorder"),
    path("quotation-requests/", list_my_quotation_requests, name="list-quotation-requests"),
    path("quotation-requests/<int:request_id>/upload/", upload_quotation_for_request, name="upload-quotation-request"),
    path("quotation-requests/<int:request_id>/quotation/", get_quotation_for_request, name="get-quotation-request"),

    # Product chat (post-order)
    path("conversations/start-or-get/", start_or_get_conversation, name="start-conversation"),
    path("conversations/", list_conversations_for_user, name="list-conversations"),
    path("conversations/<int:conversation_id>/messages/", list_messages, name="list-messages"),
    path("conversations/<int:conversation_id>/messages/send/", send_message, name="send-message"),

    

]
