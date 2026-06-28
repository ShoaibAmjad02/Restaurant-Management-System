from django.urls import path
from .views import (
    food_delivery_restaurant_detail,
    logout_view, add_product, product_list,
    edit_product, delete_product,
    admin_dashboard, food_delivery_login,
    register_view, search_users,
    user_detail_view, user_redirect_view, user_update_view,
)
from megaone.users import views

app_name = "users"

urlpatterns = [
    path("logout/", logout_view, name="logout"),
    path("register/", register_view, name="register"),
    path("checkout/", views.checkout_invoice, name="checkout_invoice"),
    path("guest-checkout/", views.guest_checkout, name="guest_checkout"),

    # Kitchen
    path("kitchen/dashboard/", views.kitchen_dashboard, name="kitchen_dashboard"),
    path("kitchen/order/<int:order_id>/status/", views.update_order_status, name="update_order_status"),
    path("kitchen/search-orders/", views.kitchen_search_orders, name="kitchen_search_orders"),

    # Kitchen User Management
    path("create-kitchen/", views.create_kitchen, name="create_kitchen"),
    path("kitchen/", views.kitchen_list, name="kitchen_list"),
    path("edit-kitchen/<int:id>/", views.edit_kitchen, name="edit_kitchen"),
    path("delete-kitchen/<int:id>/", views.delete_kitchen, name="delete_kitchen"),

    # Orders
    path("search-order/", views.search_order, name="search_order"),
    path("orders-by-status/", views.orders_by_status, name="orders_by_status"),
    path("orders-by-date/", views.orders_by_date, name="orders_by_date"),
    path("my-orders/", views.my_orders, name="my_orders"),

    # Search
    path("search-invoice/", views.search_invoice, name="search_invoice"),
    path("search-users/", search_users, name="search_users"),

    # Timezone
    path("set-timezone/", views.set_timezone, name="set_timezone"),

    # Invoice PDF (secure token-based)
    path("invoice/<str:uuid_token>/", views.invoice_pdf, name="invoice_pdf"),

    # Invoice Verify (for QR scanning)
    path("invoice/<str:uuid_token>/verify/", views.invoice_verify, name="invoice_verify"),

    # Secure Invoice View -> Redirects to PDF
    path("invoice/<str:uuid_token>/details/", views.secure_invoice_view, name="secure_invoice_view"),

    # Order Tracking
    path("order-tracking/<str:invoice_no>/", views.order_tracking, name="order_tracking"),
    path("order-tracking-data/<str:invoice_no>/", views.order_tracking_data, name="order_tracking_data"),

    # Invoice Detail (by invoice_no, legacy) -> Redirects to PDF
    path("invoice-detail/<str:invoice_no>/", views.invoice_detail, name="invoice_detail"),

    # Admin
    path("dashboard/", admin_dashboard, name="admin_dashboard"),
    path("revenue-filter/", views.revenue_filter, name="revenue_filter"),
    path("tax-analytics/", views.tax_analytics, name="tax_analytics"),

    # Products
    path("products/", product_list, name="product_list"),
    path("products/add/", add_product, name="add_product"),
    path("products/<int:pk>/edit/", edit_product, name="edit_product"),
    path("products/<int:pk>/delete/", delete_product, name="delete_product"),

    # Invoice Search Page
    path("invoices/", views.invoice_search_page, name="invoice_search_page"),

    # Kitchen Users Page
    path("kitchen-users/", views.kitchen_users_page, name="kitchen_users_page"),

    # Tables
    path("tables/", views.table_list, name="table_list"),
    path("tables/add/", views.add_table, name="add_table"),
    path("tables/<int:pk>/edit/", views.edit_table, name="edit_table"),
    path("tables/<int:pk>/delete/", views.delete_table, name="delete_table"),
    path("tables/<int:pk>/generate-qr/", views.generate_table_qr, name="generate_table_qr"),

    # Restaurant Detail
    path("restaurant-detail/", food_delivery_restaurant_detail, name="food_delivery_restaurant_detail"),

    # Auth
    path("login/", food_delivery_login, name="login"),
    path("mysql-backup/", views.mysql_backup, name="mysql_backup"),

    # User
    path("<int:pk>/", user_detail_view, name="detail"),
    path("~redirect/", user_redirect_view, name="redirect"),
    path("update/", user_update_view, name="update"),
<<<<<<< HEAD

    # Loyalty Card
    path("loyalty-card/", views.loyalty_card_view, name="loyalty_card_view"),
    path("loyalty-card/history/", views.loyalty_transactions, name="loyalty_transactions"),
    path("loyalty-card/pdf/<str:card_number>/", views.download_loyalty_pdf, name="download_loyalty_pdf"),
    path("loyalty-card/image/<str:card_number>/", views.download_loyalty_image, name="download_loyalty_image"),
    path("loyalty-card/data/", views.loyalty_card_data, name="loyalty_card_data"),
    path("loyalty-card/checkout-info/", views.loyalty_checkout_info, name="loyalty_checkout_info"),
    path("loyalty-card/checkout-validate/", views.loyalty_checkout_validate, name="loyalty_checkout_validate"),
    path("loyalty-card/verify-qr/<str:qr_token>/", views.verify_loyalty_qr, name="verify_loyalty_qr"),
    path("loyalty-card/from-qr/<str:qr_token>/", views.qr_loyalty_redirect, name="qr_loyalty_redirect"),

    # Admin Loyalty
    path("loyalty-card/admin/list/", views.admin_loyalty_list, name="admin_loyalty_list"),
    path("loyalty-card/admin/card/<str:card_number>/", views.admin_loyalty_detail, name="admin_loyalty_detail"),
    path("loyalty-card/admin/card/<str:card_number>/toggle/", views.admin_toggle_card_status, name="admin_toggle_card_status"),
    path("loyalty-card/admin/card/<str:card_number>/reset/", views.admin_reset_points, name="admin_reset_points"),
    path("loyalty-card/admin/reports/", views.admin_loyalty_reports, name="admin_loyalty_reports"),
    path("loyalty-card/admin/export-csv/", views.admin_export_loyalty_csv, name="admin_export_loyalty_csv"),

    # Offers & Deals API
    path("offers/active-data/", views.active_offer_data, name="active_offer_data"),
    path("deals/active-data/", views.active_deal_data, name="active_deal_data"),
    path("offers/banner-data/", views.offer_banner_data, name="offer_banner_data"),

    # Offer CRUD
    path("offers/", views.offer_list, name="offer_list"),
    path("offers/add/", views.offer_add, name="offer_add"),
    path("offers/<int:pk>/", views.offer_detail, name="offer_detail"),
    path("offers/<int:pk>/edit/", views.offer_edit, name="offer_edit"),
    path("offers/<int:pk>/delete/", views.offer_delete, name="offer_delete"),

    # Deal CRUD
    path("deals/", views.deal_list, name="deal_list"),
    path("deals/add/", views.deal_add, name="deal_add"),
    path("deals/<int:pk>/", views.deal_detail, name="deal_detail"),
    path("deals/<int:pk>/edit/", views.deal_edit, name="deal_edit"),
    path("deals/<int:pk>/delete/", views.deal_delete, name="deal_delete"),

    # Public Deal Views
    path("deals/<int:pk>/public/", views.public_deal_detail, name="public_deal_detail"),
    path("deals/<int:pk>/checkout/", views.deal_checkout, name="deal_checkout"),
    path("clear-deal-cart/", views.clear_deal_cart, name="clear_deal_cart"),
=======
>>>>>>> 427514fc76e9737ff20056f57476ad55c9defa49
]
