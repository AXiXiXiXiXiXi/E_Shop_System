from django.urls import path, include
from django.contrib import admin
from django.views.generic import RedirectView

urlpatterns = [ 
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.authentication.urls')),  # 认证路由
    path('api/password-reset/', include('password_reset.urls')),  # 密码重置路由
    path('api/order/', include('apps.order.urls')),
    path('api/review/', include('apps.review.urls')),
    path('api/coupon/', include('apps.coupon.urls')),
    path('api/member/', include('apps.member.urls')),
    path('api/adminsys/', include('apps.adminsys.urls')),
    path('api/cart/', include('apps.cart.urls')),
    path('api/product/', include('apps.product.urls')),  # 商品模块路由
    # 其他模块路由后续添加
    path('', RedirectView.as_view(url='/admin/', permanent=False)),  # 根路径重定向到管理页面
    path('api/docs/', include('rest_framework.urls')),  # 文档路由
]