from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CouponViewSet, 
    MemberCouponViewSet, CouponUsageRecordViewSet
)

router = DefaultRouter()
router.register(r'coupons', CouponViewSet)
router.register(r'member-coupons', MemberCouponViewSet, basename='member-coupons')
router.register(r'coupon-usage-records', CouponUsageRecordViewSet, basename='coupon-usage-records')

urlpatterns = [
    path('', include(router.urls)),
]