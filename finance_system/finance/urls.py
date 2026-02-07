# urls.py
from django.urls import path
from . import views
from . import site_admin_views
from .views import redirect_to_admin

urlpatterns = [
    path('', views.index, name='index'),
    # Кастомная админ-панель по /admin/ (только is_staff)
    path('admin/', site_admin_views.site_admin_dashboard, name='admin_dashboard'),
    path('admin/categories/', site_admin_views.site_admin_categories, name='admin_categories'),
    path('admin/categories/create/', site_admin_views.site_admin_category_create, name='admin_category_create'),
    path('admin/categories/<uuid:pk>/delete/', site_admin_views.site_admin_category_delete, name='admin_category_delete'),
    path('admin/users/', site_admin_views.site_admin_users, name='admin_users'),
    path('admin/users/<uuid:pk>/block/', site_admin_views.site_admin_user_block, name='admin_user_block'),
    path('admin/users/<uuid:pk>/unblock/', site_admin_views.site_admin_user_unblock, name='admin_user_unblock'),
    path('features/', views.features, name='features'),
    path('pricing/', views.pricing, name='pricing'),
    path('contact/', views.contact, name='contact'),
    path('auth/', views.auth_view, name='auth'),
    path('auth/handle/', views.handle_auth, name='handle_auth'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('site-admin/', redirect_to_admin),

    # Редиректы для старых URL (если где-то используются)
    path('categories/', views.categories_redirect, name='categories'),
    path('transactions/', views.transactions_redirect, name='transactions'),
    path('goals/', views.goals_redirect, name='goals'),

    # AJAX/формы
    path('categories/create/', views.create_category, name='create_category'),
    path('categories/<uuid:category_id>/delete/', views.delete_category, name='delete_category'),
    path('receipt/upload/', views.upload_receipt_redirect, name='upload_receipt'),
    path('receipt/scan/', views.scan_receipt_redirect, name='scan_receipt'),
    path('goals/create/', views.create_goal, name='create_goal'),
    path('goals/<uuid:goal_id>/edit/', views.edit_goal, name='edit_goal'),
    path('goals/<uuid:goal_id>/delete/', views.delete_goal, name='delete_goal'),
    path('goals/<uuid:goal_id>/add-money/', views.add_money_to_goal, name='add_money_to_goal'),
    path('transactions/import-excel/', views.import_transactions_excel, name='import_transactions_excel'),
    path('transactions/add/', views.add_transaction, name='add_transaction'),
    path('transactions/example-excel/', views.download_transactions_example, name='download_transactions_example'),

    # Семья, уведомления, профиль
    path('family/', views.family_list, name='family_list'),
    path('family/create/', views.family_create, name='family_create'),
    path('family/<uuid:family_id>/', views.family_detail, name='family_detail'),
    path('family/<uuid:family_id>/settings/', views.family_settings, name='family_settings'),
    path('family/<uuid:family_id>/member/<uuid:member_id>/display-name/', views.family_member_display_name, name='family_member_display_name'),
    path('family/<uuid:family_id>/goal/create/', views.family_goal_create, name='family_goal_create'),
    path('family/<uuid:family_id>/invite-link/', views.family_get_invite_link, name='family_get_invite_link'),
    path('family/<uuid:family_id>/invite/', views.family_invite, name='family_invite'),
    path('family/<uuid:family_id>/remove-member/', views.family_remove_member, name='family_remove_member'),
    path('family/<uuid:family_id>/admin-chart/', views.family_admin_chart, name='family_admin_chart'),
    path('family/accept/<str:token>/', views.family_accept_invite, name='family_accept_invite'),
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/mark-all-read/', views.notifications_mark_all_read, name='notifications_mark_all_read'),
    path('profile/', views.profile_edit, name='profile_edit'),
]