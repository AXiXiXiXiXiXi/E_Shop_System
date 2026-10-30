from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OrderViewSet, OrderItemViewSet, OrderStatusHistoryViewSet, OrderRefundViewSet,
    CreateOrderView
)
import logging

# 设置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

router = DefaultRouter()
router.register(r'orders', OrderViewSet)
router.register(r'order-items', OrderItemViewSet)
router.register(r'order-status-history', OrderStatusHistoryViewSet)
router.register(r'refunds', OrderRefundViewSet)

# 记录已注册的路由
logger.debug("订单系统路由注册：")
logger.debug(f"- Orders: {router.urls}")

urlpatterns = [
    path('', include(router.urls)),
    path('create-order/', CreateOrderView.as_view(), name='create-order'),
    # 添加明确的按订单号查找的路由
    path('orders/by-number/<str:order_number>/', OrderViewSet.as_view({'get': 'retrieve_by_order_number'}), name='order-by-number'),
    # 添加按订单号取消订单的路由
    path('orders/by-number/<str:order_number>/cancel/', OrderViewSet.as_view({'post': 'cancel_by_order_number'}), name='cancel-order-by-number'),
    # 添加退款申请路由
    path('refunds/apply_refund/', OrderRefundViewSet.as_view({'post': 'apply_refund'}), name='apply-refund'),
    # 添加完成退款路由
    path('refunds/<int:pk>/complete/', OrderRefundViewSet.as_view({'post': 'complete_refund'}), name='complete-refund'),
]