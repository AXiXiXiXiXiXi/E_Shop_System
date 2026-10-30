from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReviewViewSet, AfterSaleRequestViewSet, ChatMessageViewSet

router = DefaultRouter()
router.register(r'reviews', ReviewViewSet)
router.register(r'after-sale-requests', AfterSaleRequestViewSet)
router.register(r'chat-messages', ChatMessageViewSet)

urlpatterns = [
    path('', include(router.urls)),
]