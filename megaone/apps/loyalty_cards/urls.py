from django.urls import path
from . import views

app_name = 'loyalty_cards'

urlpatterns = [
    path('my-card/', views.my_loyalty_card, name='my_card'),
    path('my-card/download-pdf/<str:card_number>/', views.download_card_pdf, name='download_pdf'),
    path('my-card/download-image/<str:card_number>/', views.download_card_image, name='download_image'),
    path('verify-qr/<str:qr_token>/', views.verify_qr_token, name='verify_qr'),
    path('checkout-validate/', views.loyalty_checkout_validate, name='checkout_validate'),
    path('checkout-info/', views.loyalty_card_data, name='card_data'),
    path('checkout-info-json/', views.loyalty_checkout_info, name='checkout_info'),

    # Admin
    path('admin/list/', views.admin_loyalty_list, name='admin_loyalty_list'),
    path('admin/card/<str:card_number>/', views.admin_loyalty_detail, name='admin_loyalty_detail'),
    path('admin/card/<str:card_number>/toggle/', views.admin_toggle_card_status, name='admin_toggle_card'),
    path('admin/card/<str:card_number>/reset/', views.admin_reset_points, name='admin_reset_points'),
    path('admin/reports/', views.admin_loyalty_reports, name='admin_reports'),
    path('admin/export-csv/', views.admin_export_loyalty_csv, name='admin_export_csv'),
]
