from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    register_user,
    verify_otp_register,
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
    seller_orders,
    update_order_status,
    get_notifications,
    mark_notification_read,
    initiate_paytm_payment,
    payment_callback,
    upload_quotation,
    list_order_quotations,
    request_quotation_preorder,
    list_my_quotation_requests,
    upload_quotation_for_request,
    get_quotation_for_request,
    start_or_get_conversation,
    list_conversations_for_user,
    list_messages,
    send_message,
    list_reviews,
    add_review,
    search_products,
    seller_dashboard_stats,
    seller_sales_trends,
    seller_product_performance,
    seller_customer_insights,
    clear_from_cart,
    upload_products
)

urlpatterns = [
    # ------------------------
    # Authentication & User
    # ------------------------
    path("register/", register_user, name="register"),
    path("verify-otp/", verify_otp_register, name="verify_otp_register"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("profile/", user_profile, name="profile"),

    # ------------------------
    # Products
    # ------------------------
    path("products/", list_products, name="product-list"),
    path("products/add/", add_product, name="product-add"),
    path("products/upload_products/", upload_products, name="upload_products"),

    path("products/<int:pk>/update/", update_product, name="product-update"),
    path("products/<int:pk>/delete/", delete_product, name="product-delete"),
    path("search/", search_products, name="search-products"),

    # ------------------------
    # Cart
    # ------------------------
    path("cart/", view_cart, name="cart-view"),
    path("cart/add/", add_to_cart, name="cart-add"),
    path("cart/remove/<int:pk>/", remove_from_cart, name="cart-remove"),
    path("cart/clear/<int:pk>/", clear_from_cart, name="cart-clear"),

    # ------------------------
    # Wishlist
    # ------------------------
    path("wishlist/", view_wishlist, name="wishlist-view"),
    path("wishlist/add/", add_to_wishlist, name="wishlist-add"),
    path("wishlist/remove/<int:product_id>/", remove_from_wishlist, name="wishlist-remove"),

    # ------------------------
    # Orders
    # ------------------------
    path("orders/place/", place_order, name="order-place"),
    path("orders/", view_orders, name="order-list"),
    path("orders/<int:order_id>/update-status/", update_order_status, name="order-update-status"),
    path("seller/orders/", seller_orders, name="seller-orders"),

    # ------------------------
    # Notifications
    # ------------------------
    path("notifications/", get_notifications, name="notification-list"),
    path("notifications/<int:pk>/read/", mark_notification_read, name="notification-read"),

    # ------------------------
    # Paytm
    # ------------------------
    path("paytm/initiate/<int:order_id>/", initiate_paytm_payment, name="paytm-initiate"),
    path("paytm/callback/", payment_callback, name="paytm-callback"),

    # ------------------------
    # Quotations
    # ------------------------
    path("quotation-requests/<int:request_id>/quotations/upload/", upload_quotation, name="upload-quotation"),
    path("orders/<int:order_id>/quotations/", list_order_quotations, name="list-quotations"),
    path("quotation-requests/products/<int:product_id>/request/", request_quotation_preorder, name="request-quotation-preorder"),
    path("quotation-requests/", list_my_quotation_requests, name="list-quotation-requests"),
    path("quotation-requests/<int:request_id>/upload/", upload_quotation_for_request, name="upload-quotation-request"),
    path("quotation-requests/<int:request_id>/quotation/", get_quotation_for_request, name="get-quotation-request"),

    # ------------------------
    # Product Conversations
    # ------------------------
    path("conversations/start-or-get/", start_or_get_conversation, name="start-conversation"),
    path("conversations/", list_conversations_for_user, name="list-conversations"),
    path("conversations/<int:conversation_id>/messages/", list_messages, name="list-messages"),
    path("conversations/<int:conversation_id>/messages/send/", send_message, name="send-message"),

    # ------------------------
    # Reviews
    # ------------------------
    path("products/<int:product_id>/reviews/", list_reviews, name="list-reviews"),
    path("products/<int:product_id>/reviews/add/", add_review, name="add-review"),

    # ------------------------
    # Seller Dashboard
    # ------------------------
    path("seller/dashboard/stats/", seller_dashboard_stats, name="seller-dashboard-stats"),
    path("seller/dashboard/sales-trends/", seller_sales_trends, name="seller-sales-trends"),
    path("seller/dashboard/product-performance/", seller_product_performance, name="seller-product-performance"),
    path("seller/dashboard/customer-insights/", seller_customer_insights, name="seller-customer-insights"),
]
