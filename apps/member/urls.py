from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MemberViewSet, AddressViewSet

# 创建路由器
router = DefaultRouter()
router.register(r'members', MemberViewSet, basename='member')
router.register(r'addresses', AddressViewSet, basename='address')

urlpatterns = [
    path('', include(router.urls)),
]