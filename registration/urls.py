from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .payment_views import (
    payment_dashboard, add_funds, payment_success, payment_cancel, 
    manual_payment, payment_lookup, stripe_webhook
)
from .export_views_fixed import export_dashboard, export_all_data_csv
from .pass_views import purchase_pass, pass_purchase_success, pass_purchase_cancel, my_passes


urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('parent_register/', views.parent_register, name='parent_register'),
    
    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('password_reset/', views.password_reset, name='password_reset'),
    
    # Parent dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile_edit/', views.profile_edit, name='profile_edit'),
    
    # Child management
    path('add_child/', views.add_child, name='add_child'),
    path('child/<int:child_id>/edit/', views.edit_child, name='edit_child'),
    path('child/<int:child_id>/remove/', views.remove_child, name='remove_child'),
    path('child/<int:child_id>/qr/', views.child_qr_code, name='child_qr_code'),
    
    # Staff/Teacher functions
    path('attendance_scan/', views.attendance_scan, name='attendance_scan'),
    path('teacher_dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('checkout/<int:child_id>/', views.checkout_child, name='checkout_child'),
    path('manual_sign_in/', views.manual_sign_in, name='manual_sign_in'),
    path('manual_checkin/<int:child_id>/', views.manual_checkin_child, name='manual_checkin_child'),
    path('change_status/<int:child_id>/', views.change_child_status, name='change_child_status'),
    path('admin_add_payment/', views.admin_add_payment, name='admin_add_payment'),
    
    # preview helper pages (for template testing)
    path("preview/", views.preview_index, name="preview_index"),
    path("preview/<str:page_name>/", views.preview_template, name="preview_template"),
    
    # site map for testing functionality
    path("sitemap/", views.site_map, name="site_map"),
    
    # Payment system
    path('payment/dashboard/', payment_dashboard, name='payment_dashboard'),
    path('payment/add_funds/', add_funds, name='add_funds'),
    path('payment/success/', payment_success, name='payment_success'),
    path('payment/cancel/', payment_cancel, name='payment_cancel'),
    path('payment/manual/', manual_payment, name='manual_payment'),
    path('payment/lookup/', payment_lookup, name='payment_lookup'),
    path('payment/webhook/', stripe_webhook, name='stripe_webhook'),
    
    # Data export
    path('export/', export_dashboard, name='export_dashboard'),
    path('export/all/', export_all_data_csv, name='export_all_data'),
    
    # Pass purchase system
    path('passes/purchase/', purchase_pass, name='purchase_pass'),
    path('passes/success/', pass_purchase_success, name='pass_purchase_success'),
    path('passes/cancel/', pass_purchase_cancel, name='pass_purchase_cancel'),
    path('passes/', my_passes, name='my_passes'),
]



# OLD URL PATTERNS
#    urlpatterns = [
#    # Public pages
#    path('', views.home, name='home'),
#    path('register/', views.parent_register, name='parent_register'),
#    
#    # Authentication
#    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
#    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
#    
#    # Parent dashboard
#    path('dashboard/', views.dashboard, name='dashboard'),
#    path('profile/edit/', views.profile_edit, name='profile_edit'),
#    
#    # Child management
#    path('child/add/', views.add_child, name='add_child'),
#    path('child/<int:child_id>/edit/', views.edit_child, name='edit_child'),
#    path('child/<int:child_id>/qr/', views.child_qr_code, name='child_qr_code'),
#    
#    # Staff/Teacher functions
#    path('scan/', views.attendance_scan, name='attendance_scan'),
#    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
#    path('checkout/<int:child_id>/', views.checkout_child, name='checkout_child'),
#]
