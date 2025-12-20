from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    register_buyer,
    register_seller,
    verify_otp_register,
    user_profile,
    update_user_profile,
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
    request_quotation_preproduct,
    list_my_quotation_requests,
    upload_quotation_for_request,
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
    upload_products,
    request_password_reset,
    verify_password_reset,
    verify_delivery_otp,
    upload_invoice,
    add_recent_view,
    get_recently_viewed
)

urlpatterns = [
    # ------------------------
    # Authentication & User
    # ------------------------
    path("register-buyer/", register_buyer, name="register_buyer"),
    path("register-seller/", register_seller, name="register_seller"),

    path("verify-otp/", verify_otp_register, name="verify_otp_register"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("profile/", user_profile, name="profile"),

    path("update-profile/", update_user_profile, name="update_user_profile"),

    path("request-password-reset/", request_password_reset),
    path("verify-password-reset/", verify_password_reset),


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
    path("orders/<int:order_id>/verify-otp/", verify_delivery_otp),
     path("orders/<int:order_id>/upload-invoice/", upload_invoice, name="upload-invoice"),
    path("seller/orders/", seller_orders, name="seller-orders"),

    # ------------------------
    # Notifications
    # ------------------------
    path("notifications/", get_notifications, name="notification-list"),
    path("notifications/<int:pk>/read/", mark_notification_read, name="notification-read"),


    # ------------------------
    # Quotations
    # ------------------------
    path("products/<int:product_id>/request-preproduct-quotation/",request_quotation_preproduct,name="request-preproduct-quotation"),
    path("quotation-requests/", list_my_quotation_requests, name="list-quotation-requests"),
    path("quotation-requests/<int:request_id>/upload/", upload_quotation_for_request, name="upload-quotation-request"),

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

    path("products/<int:product_id>/recent-view/", add_recent_view),
    path("recently-viewed/", get_recently_viewed),
]
