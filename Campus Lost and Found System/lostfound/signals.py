# -*- coding: utf-8 -*-
"""
Django 信号处理
自动为新创建的用户创建 Profile 对象
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    当创建新用户时，自动创建对应的 Profile
    
    参数:
        sender: User 模型
        instance: 新创建的 User 实例
        created: 是否是新创建的（True）还是更新的（False）
    """
    if created:
        # 判断是否是超级管理员
        if instance.is_superuser:
            # 超级管理员：不绑定学校
            Profile.objects.create(
                user=instance,
                school=None,  # 超级管理员不绑定学校
                role='admin',  # 角色设为管理员
                student_id=f'SUPER_{instance.id:03d}'  # 自动生成工号
            )
            print(f"[+] 已为超级管理员 {instance.username} 创建 Profile（不绑定学校）")
        else:
            # 普通用户：创建 Profile，但不绑定学校（需要在注册时手动绑定）
            # 注意：这里不设置 school，因为普通用户需要在注册表单中选择学校
            # 如果通过 createsuperuser 创建普通用户，需要后续手动设置学校
            Profile.objects.create(
                user=instance,
                school=None,  # 暂不绑定，等待注册流程设置
                role='user'
            )
            print(f"[+] 已为用户 {instance.username} 创建 Profile（待绑定学校）")


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    当用户保存时，同时保存 Profile
    
    参数:
        sender: User 模型
        instance: User 实例
    """
    # 确保 Profile 存在
    if hasattr(instance, 'profile'):
        instance.profile.save()

