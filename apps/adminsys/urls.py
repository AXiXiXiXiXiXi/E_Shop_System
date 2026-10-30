from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RoleViewSet, AdminUserViewSet, PermissionViewSet, AdminMemberViewSet, AdminMemberLevelViewSet,
    after_sale_chat_admin, after_sale_chat_reply, get_after_sale_chat_messages, 
    mark_after_sale_complete, admin_chat_page, admin_login
)

router = DefaultRouter()
router.register(r'roles', RoleViewSet)
router.register(r'admin-users', AdminUserViewSet)
router.register(r'permissions', PermissionViewSet)
router.register(r'admin-members', AdminMemberViewSet)
router.register(r'admin-member-levels', AdminMemberLevelViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('admin-login/', admin_login, name='admin-login'),
    path('chat-page/', admin_chat_page, name='admin-chat-page'),
    path('after-sale-chat/', after_sale_chat_admin, name='after-sale-chat-admin'),
    path('after-sale-chat/reply/', after_sale_chat_reply, name='after-sale-chat-reply'),
    path('after-sale-chat/<int:after_sale_id>/messages/', get_after_sale_chat_messages, name='get-after-sale-chat-messages'),
    path('after-sale-chat/<int:after_sale_id>/complete/', mark_after_sale_complete, name='mark-after-sale-complete'),
]