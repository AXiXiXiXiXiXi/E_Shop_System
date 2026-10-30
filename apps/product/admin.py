from django.contrib import admin
from .models import Category, Product, ProductVariant

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'is_active', 'sort_order')
    list_filter = ('is_active',)
    search_fields = ('name',)

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'brand', 'base_price', 'status', 'is_featured', 'sales_count')
    list_filter = ('status', 'is_featured', 'category')
    search_fields = ('name', 'description', 'brand')
    inlines = [ProductVariantInline]

class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('name', 'product', 'sku', 'price', 'original_price', 'stock', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'sku', 'product__name')

admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductVariant, ProductVariantAdmin) 