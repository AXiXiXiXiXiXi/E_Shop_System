from django.urls import path
from . import views

urlpatterns = [
    # 用户认证
    path('', views.home, name='home'),
    path('register/', views.user_register, name='user_register'),
    path('login/', views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('password/change/', views.password_change, name='password_change'),
    
    # 忘记密码
    path('forgot-password/', views.forgot_password_step1, name='forgot_password_step1'),
    path('forgot-password/choose-method/', views.forgot_password_choose_method, name='forgot_password_choose_method'),
    path('forgot-password/security/', views.forgot_password_security, name='forgot_password_security'),
    path('security-question/set/', views.security_question_set, name='security_question_set'),
    
    # 失物信息
    path('lost-items/', views.lost_item_list, name='lost_item_list'),
    path('lost-items/create/', views.lost_item_create, name='lost_item_create'),
    path('lost-items/<int:pk>/', views.lost_item_detail, name='lost_item_detail'),
    path('lost-items/<int:pk>/edit/', views.lost_item_edit, name='lost_item_edit'),
    path('lost-items/<int:pk>/delete/', views.lost_item_delete, name='lost_item_delete'),
    
    # 招领信息
    path('found-items/', views.found_item_list, name='found_item_list'),
    path('found-items/create/', views.found_item_create, name='found_item_create'),
    path('found-items/<int:pk>/', views.found_item_detail, name='found_item_detail'),
    path('found-items/<int:pk>/edit/', views.found_item_edit, name='found_item_edit'),
    path('found-items/<int:pk>/delete/', views.found_item_delete, name='found_item_delete'),
    path('found-items/<int:pk>/mark-returned/', views.found_item_mark_returned, name='found_item_mark_returned'),
    path('found-items/<int:pk>/admin-mark-status/', views.found_item_admin_mark_status, name='found_item_admin_mark_status'),
    
    # 认领申请
    path('claims/', views.claim_list, name='claim_list'),
    path('claims/<int:pk>/', views.claim_detail, name='claim_detail'),
    path('claims/create/<int:lost_item_id>/', views.claim_create, name='claim_create'),
    path('claims/<int:pk>/review/', views.claim_review, name='claim_review'),
    
    # 公告
    path('notices/', views.notice_list, name='notice_list'),
    path('notices/create/', views.notice_create, name='notice_create'),
    path('notices/<int:pk>/', views.notice_detail, name='notice_detail'),
    path('notices/<int:pk>/edit/', views.notice_edit, name='notice_edit'),
    path('notices/<int:pk>/delete/', views.notice_delete, name='notice_delete'),
    path('notices/<int:pk>/toggle-pin/', views.notice_toggle_pin, name='notice_toggle_pin'),
    
    # 信息页面
    path('info/data-isolation/', views.data_isolation_info, name='data_isolation_info'),
    path('info/responsibility/', views.responsibility_info, name='responsibility_info'),

    # 用户管理（仅超级管理员）
    path('superadmin/users/', views.user_management_list, name='user_management_list'),
    path('superadmin/users/<int:user_id>/toggle-role/', views.user_toggle_role, name='user_toggle_role'),
    path('superadmin/users/<int:user_id>/toggle-active/', views.user_toggle_active, name='user_toggle_active'),
    path('superadmin/users/<int:user_id>/reset-password/', views.user_reset_password, name='user_reset_password'),
]

