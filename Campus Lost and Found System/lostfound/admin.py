from django.contrib import admin
from .models import School, Profile, LostItem, FoundItem, Claim, Notice


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'code', 'create_time']
    search_fields = ['name', 'code']
    list_filter = ['create_time']


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'school', 'role', 'phone', 'student_id', 'create_time']
    search_fields = ['user__username', 'phone', 'student_id']
    list_filter = ['school', 'role', 'create_time']
    raw_id_fields = ['user']


@admin.register(LostItem)
class LostItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'category', 'school', 'publish_user', 'status', 'create_time']
    search_fields = ['title', 'description']
    list_filter = ['school', 'category', 'status', 'create_time']
    raw_id_fields = ['publish_user']


@admin.register(FoundItem)
class FoundItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'category', 'school', 'publish_user', 'create_time']
    search_fields = ['title', 'description']
    list_filter = ['school', 'category', 'create_time']
    raw_id_fields = ['publish_user']


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ['id', 'lost_item', 'claim_user', 'status', 'create_time']
    search_fields = ['claim_reason']
    list_filter = ['status', 'create_time']
    raw_id_fields = ['lost_item', 'claim_user']


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'school', 'is_pinned', 'publish_user', 'create_time']
    search_fields = ['title', 'content']
    list_filter = ['school', 'is_pinned', 'create_time']
    raw_id_fields = ['publish_user']
    list_editable = ['is_pinned']
