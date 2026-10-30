from django.contrib import admin
from .models import Cart, CartItem

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_items', 'total_price', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at', 'total_items', 'total_price']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('items')

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart_user', 'product_info', 'quantity', 'unit_price', 'subtotal', 'created_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['cart__user__username', 'product_name']
    readonly_fields = ['created_at', 'updated_at', 'unit_price', 'subtotal']
    
    def cart_user(self, obj):
        return obj.cart.user.username
    cart_user.short_description = '用户'
    
    def product_info(self, obj):
        variant_info = f" - {obj.variant_name}" if obj.variant_name else ""
        return f"{obj.product_name}{variant_info}"
    product_info.short_description = '商品信息'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('cart__user')