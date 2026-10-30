from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseRedirect
from .models import Review, AfterSaleRequest, AfterSaleChatMessage

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'product_name', 'rating', 'created_at')
    search_fields = ('product_name', 'user__username')

class AfterSaleChatMessageInline(admin.TabularInline):
    model = AfterSaleChatMessage
    extra = 0
    readonly_fields = ('sender_type', 'sender', 'message', 'is_read', 'created_at')
    fields = ('sender_type', 'sender', 'message', 'is_read', 'created_at')
    can_delete = False
    
    def has_add_permission(self, request, obj):
        return False

@admin.register(AfterSaleRequest)
class AfterSaleRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'order_item_info', 'status', 'handler', 'unread_count', 'chat_action', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'order_item__id', 'reason')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [AfterSaleChatMessageInline]
    
    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'order_item', 'reason')
        }),
        ('处理信息', {
            'fields': ('status', 'handler')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:object_id>/chat/', self.admin_site.admin_view(self.chat_view), name='review_aftersalerequest_chat'),
            path('<int:object_id>/send_reply/', self.admin_site.admin_view(self.send_reply), name='review_aftersalerequest_send_reply'),
        ]
        return custom_urls + urls
    
    def order_item_info(self, obj):
        return f"{obj.order_item.product_name} (订单: {obj.order_item.order.order_number})"
    order_item_info.short_description = '商品信息'
    
    def unread_count(self, obj):
        count = obj.chat_messages.filter(sender_type='user', is_read=False).count()
        if count > 0:
            return format_html('<span style="background: #dc3545; color: white; padding: 2px 6px; border-radius: 10px; font-size: 11px;">{}</span>', count)
        return '0'
    unread_count.short_description = '未读消息'
    
    def chat_action(self, obj):
        if obj.can_chat:
            return format_html(
                '<a class="button" href="{}" style="background: #007bff; color: white; padding: 5px 10px; text-decoration: none; border-radius: 4px;">💬 聊天</a>',
                f'/admin/review/aftersalerequest/{obj.pk}/chat/'
            )
        return format_html('<span style="color: #6c757d;">已完成</span>')
    chat_action.short_description = '聊天操作'
    
    def chat_view(self, request, object_id):
        """聊天界面视图"""
        after_sale_request = get_object_or_404(AfterSaleRequest, pk=object_id)
        
        # 标记用户消息为已读（静默处理，不显示消息）
        after_sale_request.chat_messages.filter(sender_type='user', is_read=False).update(is_read=True)
        
        messages_list = after_sale_request.chat_messages.all().order_by('created_at')
        
        context = {
            'title': f'售后聊天 - AS{after_sale_request.id:06d}',
            'after_sale_request': after_sale_request,
            'messages': messages_list,
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request, after_sale_request),
            'original': after_sale_request,
        }
        
        return render(request, 'admin/review/aftersalerequest/chat.html', context)
    
    def send_reply(self, request, object_id):
        """发送回复（静默处理）"""
        after_sale_request = get_object_or_404(AfterSaleRequest, pk=object_id)
        
        if not after_sale_request.can_chat:
            return redirect(f'/admin/review/aftersalerequest/{object_id}/chat/')
        
        if request.method == 'POST':
            message_content = request.POST.get('message', '').strip()
            action = request.POST.get('action')
            
            if message_content:
                # 创建回复消息（不显示成功消息）
                AfterSaleChatMessage.objects.create(
                    after_sale_request=after_sale_request,
                    sender_type='admin',
                    sender=request.user,
                    message=message_content
                )
                
                # 设置处理人员
                if not after_sale_request.handler:
                    after_sale_request.handler = request.user
                    after_sale_request.save()
            
            # 如果选择了标记完成
            if action == 'complete':
                after_sale_request.status = 'completed'
                after_sale_request.handler = request.user
                after_sale_request.save()
                return redirect('admin:review_aftersalerequest_changelist')
        
        return redirect(f'/admin/review/aftersalerequest/{object_id}/chat/')
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = ['created_at', 'updated_at']
        if not request.user.is_superuser:
            readonly_fields.extend(['user', 'order_item', 'reason'])
        return readonly_fields

@admin.register(AfterSaleChatMessage)
class AfterSaleChatMessageAdmin(admin.ModelAdmin):
    list_display = ('after_sale_request', 'sender_type', 'sender', 'message_preview', 'is_read', 'created_at')
    list_filter = ('sender_type', 'is_read', 'created_at')
    search_fields = ('after_sale_request__user__username', 'sender__username', 'message')
    readonly_fields = ('created_at',)
    
    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = '消息预览'
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # 编辑现有对象时，大部分字段为只读
            return ['after_sale_request', 'sender_type', 'sender', 'created_at']
        return ['created_at']