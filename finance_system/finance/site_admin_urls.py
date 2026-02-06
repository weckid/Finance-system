# site_admin_urls.py — маршруты кастомной админ-панели под /admin/
from django.urls import path
from . import site_admin_views

urlpatterns = [
    path('', site_admin_views.site_admin_dashboard, name='admin_dashboard'),
    path('categories/', site_admin_views.site_admin_categories, name='admin_categories'),
    path('categories/create/', site_admin_views.site_admin_category_create, name='admin_category_create'),
    path('categories/<uuid:pk>/delete/', site_admin_views.site_admin_category_delete, name='admin_category_delete'),
    path('users/', site_admin_views.site_admin_users, name='admin_users'),
    path('users/<uuid:pk>/block/', site_admin_views.site_admin_user_block, name='admin_user_block'),
    path('users/<uuid:pk>/unblock/', site_admin_views.site_admin_user_unblock, name='admin_user_unblock'),
]
