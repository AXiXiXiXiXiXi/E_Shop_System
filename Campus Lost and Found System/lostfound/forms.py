from django import forms
from django.contrib.auth.models import User
from .models import School, Profile, LostItem, FoundItem, Claim, Notice


class UserRegisterForm(forms.Form):
    """用户注册表单 - 必须选择学校"""
    username = forms.CharField(
        max_length=150,
        min_length=3,
        label='用户名',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入用户名（3-150个字符）'})
    )
    password = forms.CharField(
        max_length=20,
        min_length=6,
        label='密码',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '请输入密码（6-20位）'})
    )
    password_confirm = forms.CharField(
        max_length=20,
        min_length=6,
        label='确认密码',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '请再次输入密码（6-20位）'})
    )
    email = forms.EmailField(
        required=True,
        label='邮箱',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': '请输入邮箱'})
    )
    school = forms.ModelChoiceField(
        queryset=School.objects.all(),
        label='所属学校',
        empty_label='请选择学校',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        label='联系电话',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入联系电话'})
    )
    student_id = forms.CharField(
        max_length=50,
        required=False,
        label='学号/工号',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入学号或工号'})
    )
    dorm = forms.CharField(
        max_length=100,
        required=False,
        label='宿舍/住址',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入宿舍或住址'})
    )

    def clean_username(self):
        """验证用户名唯一性"""
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('该用户名已被注册，请使用其他用户名')
        return username
    
    def clean_email(self):
        """验证邮箱唯一性和格式"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('该邮箱已被注册，请使用其他邮箱')
        return email
    
    def clean_password(self):
        """验证密码格式：6-20位，必须包含字母和数字"""
        password = self.cleaned_data.get('password')
        
        # 检查长度（6-20位）
        if len(password) < 6:
            raise forms.ValidationError('密码长度不能少于6位')
        if len(password) > 20:
            raise forms.ValidationError('密码长度不能超过20位')
        
        # 检查是否包含字母
        has_letter = any(c.isalpha() for c in password)
        # 检查是否包含数字
        has_digit = any(c.isdigit() for c in password)
        
        if not has_letter:
            raise forms.ValidationError('密码必须包含至少一个字母')
        if not has_digit:
            raise forms.ValidationError('密码必须包含至少一个数字')
        
        return password

    def clean_phone(self):
        """验证手机号唯一性"""
        phone = self.cleaned_data.get('phone')
        if phone and Profile.objects.filter(phone=phone).exists():
            raise forms.ValidationError('该手机号已被注册')
        return phone

    def clean_student_id(self):
        """验证学号唯一性"""
        student_id = self.cleaned_data.get('student_id')
        if student_id and Profile.objects.filter(student_id=student_id).exists():
            raise forms.ValidationError('该学号/工号已被注册')
        return student_id

    def clean(self):
        """验证两次密码是否一致和学校是否选择"""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        school = cleaned_data.get('school')

        # 验证两次密码是否一致
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('两次输入的密码不一致，请重新输入')
        
        # 验证是否选择了学校
        if not school:
            raise forms.ValidationError('请选择所属学校')

        return cleaned_data


class UserLoginForm(forms.Form):
    """用户登录表单"""
    username = forms.CharField(
        max_length=150,
        label='用户名',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入用户名'})
    )
    password = forms.CharField(
        max_length=128,
        label='密码',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '请输入密码'})
    )


class LostItemForm(forms.ModelForm):
    """失物信息表单"""
    class Meta:
        model = LostItem
        fields = ['title', 'description', 'category', 'lost_time', 'lost_location', 'contact', 'image']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入失物标题'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': '请详细描述失物特征'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'lost_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'lost_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入丢失地点'}),
            'contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入联系方式'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'title': '失物标题',
            'description': '详细描述',
            'category': '物品分类',
            'lost_time': '丢失时间',
            'lost_location': '丢失地点',
            'contact': '联系方式',
            'image': '物品图片',
        }


class FoundItemForm(forms.ModelForm):
    """招领信息表单"""
    class Meta:
        model = FoundItem
        fields = ['title', 'description', 'category', 'found_time', 'found_location', 'contact', 'image']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入招领物品标题'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': '请详细描述物品特征'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'found_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'found_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入拾取地点'}),
            'contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入联系方式'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'title': '招领标题',
            'description': '详细描述',
            'category': '物品分类',
            'found_time': '拾取时间',
            'found_location': '拾取地点',
            'contact': '联系方式',
            'image': '物品图片',
        }


class ClaimForm(forms.ModelForm):
    """认领申请表单"""
    class Meta:
        model = Claim
        fields = ['claim_reason']
        widgets = {
            'claim_reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '请详细说明认领理由，包括物品特征、丢失经过等信息'
            }),
        }
        labels = {
            'claim_reason': '认领说明',
        }


class ClaimReviewForm(forms.Form):
    """认领审核表单"""
    status = forms.ChoiceField(
        choices=[('approved', '通过'), ('rejected', '拒绝')],
        label='审核结果',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    admin_note = forms.CharField(
        required=False,
        label='审核备注',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': '请输入审核备注（可选）'
        })
    )


class NoticeForm(forms.ModelForm):
    """公告表单"""
    class Meta:
        model = Notice
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入公告标题'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': '请输入公告内容'}),
        }
        labels = {
            'title': '公告标题',
            'content': '公告内容',
        }


class ProfileEditForm(forms.Form):
    """个人信息编辑表单 - 只允许编辑学号、联系电话、宿舍"""
    student_id = forms.CharField(
        max_length=50,
        required=False,
        label='学号/工号',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入学号或工号'})
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        label='联系电话',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入联系电话'})
    )
    dorm = forms.CharField(
        max_length=100,
        required=False,
        label='宿舍/住址',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入宿舍或住址'})
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_phone(self):
        """验证手机号唯一性（排除当前用户）"""
        phone = self.cleaned_data.get('phone')
        if phone:
            existing = Profile.objects.filter(phone=phone).exclude(user=self.user)
            if existing.exists():
                raise forms.ValidationError('该手机号已被其他用户使用')
        return phone

    def clean_student_id(self):
        """验证学号唯一性（排除当前用户）"""
        student_id = self.cleaned_data.get('student_id')
        if student_id:
            existing = Profile.objects.filter(student_id=student_id).exclude(user=self.user)
            if existing.exists():
                raise forms.ValidationError('该学号/工号已被其他用户使用')
        return student_id


class PasswordChangeForm(forms.Form):
    """密码修改表单"""
    old_password = forms.CharField(
        max_length=128,
        label='当前密码',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '请输入当前密码'})
    )
    new_password = forms.CharField(
        max_length=128,
        label='新密码',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '请输入新密码'})
    )
    new_password_confirm = forms.CharField(
        max_length=128,
        label='确认新密码',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '请再次输入新密码'})
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        """验证旧密码是否正确"""
        old_password = self.cleaned_data.get('old_password')
        if self.user and not self.user.check_password(old_password):
            raise forms.ValidationError('当前密码不正确')
        return old_password

    def clean(self):
        """验证两次新密码是否一致"""
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        new_password_confirm = cleaned_data.get('new_password_confirm')

        if new_password and new_password_confirm:
            if new_password != new_password_confirm:
                raise forms.ValidationError('两次输入的新密码不一致')
            
            # 验证新密码不能与旧密码相同
            old_password = cleaned_data.get('old_password')
            if old_password and new_password == old_password:
                raise forms.ValidationError('新密码不能与当前密码相同')

        return cleaned_data


class ForgotPasswordStep1Form(forms.Form):
    """忘记密码 - 步骤1：输入用户名"""
    username = forms.CharField(
        max_length=150,
        label='用户名',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入您的用户名'})
    )

    def clean_username(self):
        """验证用户名是否存在"""
        username = self.cleaned_data.get('username')
        try:
            user = User.objects.get(username=username)
            self.user = user
        except User.DoesNotExist:
            raise forms.ValidationError('该用户名不存在')
        return username


class ForgotPasswordSecurityForm(forms.Form):
    """忘记密码 - 安全问题验证"""
    security_answer = forms.CharField(
        max_length=200,
        label='安全问题答案',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入安全问题的答案'})
    )
    new_password = forms.CharField(
        max_length=128,
        label='新密码',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '请输入新密码'})
    )
    new_password_confirm = forms.CharField(
        max_length=128,
        label='确认新密码',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '请再次输入新密码'})
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_security_answer(self):
        """验证安全问题答案"""
        answer = self.cleaned_data.get('security_answer')
        if self.user and self.user.profile.security_answer != answer:
            raise forms.ValidationError('安全问题答案不正确')
        return answer

    def clean(self):
        """验证两次密码是否一致"""
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        new_password_confirm = cleaned_data.get('new_password_confirm')

        if new_password and new_password_confirm and new_password != new_password_confirm:
            raise forms.ValidationError('两次输入的密码不一致')

        return cleaned_data


class SecurityQuestionForm(forms.Form):
    """设置密保问题表单"""
    QUESTION_CHOICES = [
        ('', '请选择密保问题'),
        ('你的学号后4位是？', '你的学号后4位是？'),
        ('你的入学年份是？', '你的入学年份是？'),
        ('你的出生月日是？（如0101）', '你的出生月日是？（如0101）'),
        ('你母亲的姓名是？', '你母亲的姓名是？'),
        ('你的家乡是哪个城市？', '你的家乡是哪个城市？'),
        ('你最喜欢的老师姓什么？', '你最喜欢的老师姓什么？'),
    ]
    
    security_question = forms.ChoiceField(
        choices=QUESTION_CHOICES,
        label='密保问题',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    security_answer = forms.CharField(
        max_length=200,
        label='密保答案',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入答案'})
    )
    security_answer_confirm = forms.CharField(
        max_length=200,
        label='确认答案',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请再次输入答案'})
    )

    def clean(self):
        """验证两次答案是否一致"""
        cleaned_data = super().clean()
        answer = cleaned_data.get('security_answer')
        answer_confirm = cleaned_data.get('security_answer_confirm')

        if answer and answer_confirm and answer != answer_confirm:
            raise forms.ValidationError('两次输入的答案不一致')

        return cleaned_data

