from django.db import models
from django.contrib.auth.models import User


class School(models.Model):
    """学校表 - 系统核心实体，用于实现多学校数据隔离"""
    name = models.CharField(max_length=150, verbose_name='学校名称')
    code = models.CharField(max_length=50, unique=True, verbose_name='学校代码')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '学校'
        verbose_name_plural = '学校'
        db_table = 'school'

    def __str__(self):
        return self.name


class Profile(models.Model):
    """用户扩展信息表 - 关联 Django User，普通用户必须绑定学校，超级管理员可以不绑定"""
    ROLE_CHOICES = [
        ('user', '普通用户'),
        ('admin', '管理员'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='用户')
    school = models.ForeignKey(
        School, 
        on_delete=models.CASCADE, 
        null=True,  # 允许为空（超级管理员）
        blank=True,
        verbose_name='所属学校'
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name='联系电话')
    student_id = models.CharField(max_length=50, blank=True, verbose_name='学号/工号')
    dorm = models.CharField(max_length=100, blank=True, verbose_name='宿舍/住址')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user', verbose_name='角色')
    
    # 密保问题字段
    security_question = models.CharField(max_length=200, blank=True, verbose_name='密保问题')
    security_answer = models.CharField(max_length=200, blank=True, verbose_name='密保答案')
    
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '用户信息'
        verbose_name_plural = '用户信息'
        db_table = 'profile'

    def __str__(self):
        if self.school:
            return f"{self.user.username} - {self.school.name}"
        """如果没有返回上面的姓名和学校，则返回下面为超级管理员"""
        return f"{self.user.username} - 超级管理员"
    
    def has_security_question(self):
        """判断是否已设置密保问题"""
        return bool(self.security_question and self.security_answer)


class LostItem(models.Model):
    """失物信息表 - 必须关联学校，实现学校数据隔离"""
    STATUS_CHOICES = [
        ('unclaimed', '未认领'),
        ('claimed', '已认领'),
    ]

    CATEGORY_CHOICES = [
        ('electronics', '电子产品'),
        ('documents', '证件文件'),
        ('accessories', '饰品配件'),
        ('books', '书籍资料'),
        ('clothing', '衣物鞋帽'),
        ('sports', '运动器材'),
        ('other', '其他物品'),
    ]

    title = models.CharField(max_length=200, verbose_name='标题')
    description = models.TextField(verbose_name='详细描述')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name='物品分类')
    lost_time = models.DateTimeField(verbose_name='丢失时间')
    lost_location = models.CharField(max_length=200, verbose_name='丢失地点')
    contact = models.CharField(max_length=100, verbose_name='联系方式')
    image = models.ImageField(upload_to='lost_items/', blank=True, null=True, verbose_name='物品图片')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unclaimed', verbose_name='状态')
    publish_user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='发布用户')
    #外键关联学校，数据隔离
    school = models.ForeignKey(School, on_delete=models.CASCADE, verbose_name='所属学校')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='发布时间')

    class Meta:
        verbose_name = '失物信息'
        verbose_name_plural = '失物信息'
        db_table = 'lost_item'
        ordering = ['-create_time']

    def __str__(self):
        return f"{self.title} - {self.school.name}"


class FoundItem(models.Model):
    """招领信息表 - 必须关联学校，实现学校数据隔离"""
    STATUS_CHOICES = [
        ('unclaimed', '待认领'),
        ('returned', '已归还'),
    ]

    CATEGORY_CHOICES = [
        ('electronics', '电子产品'),
        ('documents', '证件文件'),
        ('accessories', '饰品配件'),
        ('books', '书籍资料'),
        ('clothing', '衣物鞋帽'),
        ('sports', '运动器材'),
        ('other', '其他物品'),
    ]

    title = models.CharField(max_length=200, verbose_name='标题')
    description = models.TextField(verbose_name='详细描述')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name='物品分类')
    found_time = models.DateTimeField(verbose_name='拾取时间')
    found_location = models.CharField(max_length=200, verbose_name='拾取地点')
    contact = models.CharField(max_length=100, verbose_name='联系方式')
    image = models.ImageField(upload_to='found_items/', blank=True, null=True, verbose_name='物品图片')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unclaimed', verbose_name='状态')
    publish_user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='发布用户')
    #外键关联学校，数据隔离
    school = models.ForeignKey(School, on_delete=models.CASCADE, verbose_name='所属学校')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='发布时间')

    class Meta:
        verbose_name = '招领信息'
        verbose_name_plural = '招领信息'
        db_table = 'found_item'
        ordering = ['-create_time']

    def __str__(self):
        return f"{self.title} - {self.school.name}"


class Claim(models.Model):
    """认领申请表 - 通过 lost_item 间接关联学校，确保只能认领本校失物"""
    STATUS_CHOICES = [
        ('pending', '待审核'),
        ('approved', '已通过'),
        ('rejected', '已拒绝'),
    ]

    lost_item = models.ForeignKey(LostItem, on_delete=models.CASCADE, verbose_name='失物信息')
    claim_user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='认领用户')
    claim_reason = models.TextField(verbose_name='认领说明')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='审核状态')
    admin_note = models.TextField(blank=True, verbose_name='管理员备注')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='申请时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '认领申请'
        verbose_name_plural = '认领申请'
        db_table = 'claim'
        ordering = ['-create_time']

    def __str__(self):
        return f"{self.claim_user.username} 认领 {self.lost_item.title}"


class Notice(models.Model):
    """公告表 - 支持系统级公告和校级公告"""
    title = models.CharField(max_length=200, verbose_name='公告标题')
    content = models.TextField(verbose_name='公告内容')
    school = models.ForeignKey(School, on_delete=models.CASCADE, null=True, blank=True, verbose_name='所属学校')
    publish_user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='发布人')
    is_pinned = models.BooleanField(default=False, verbose_name='是否置顶')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='发布时间')

    class Meta:
        verbose_name = '系统公告'
        verbose_name_plural = '系统公告'
        db_table = 'notice'
        ordering = ['-create_time']

    def __str__(self):
        if self.school:
            return f"{self.title} - {self.school.name}"
        return f"{self.title} - 系统公告"
    
    def is_system_notice(self):
        """判断是否为系统级公告"""
        return self.school is None

