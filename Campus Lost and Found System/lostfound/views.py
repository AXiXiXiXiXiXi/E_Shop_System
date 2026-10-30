from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .forms import (UserRegisterForm, UserLoginForm, LostItemForm, FoundItemForm, ClaimForm, 
                   ClaimReviewForm, NoticeForm, ProfileEditForm, PasswordChangeForm,
                   ForgotPasswordStep1Form, ForgotPasswordSecurityForm, SecurityQuestionForm)
from .models import Profile, LostItem, FoundItem, Claim, Notice, School
from .decorators import admin_required, get_user_school, check_school_permission, check_owner_permission


def user_register(request):
    """
    用户注册视图
    核心功能：
    1. 用户必须选择所属学校
    2. 创建 User 和 Profile，并绑定 school
    3. 默认角色为普通用户
    """
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            # 获取表单数据
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            email = form.cleaned_data.get('email', '')
            school = form.cleaned_data['school']  # 必须选择学校
            phone = form.cleaned_data.get('phone', '')
            student_id = form.cleaned_data.get('student_id', '')
            dorm = form.cleaned_data.get('dorm', '')

            # 创建 User
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email
            )

            # 创建 Profile，强制绑定学校
            # 注意：由于signals.py中的post_save信号会自动创建Profile，
            # 这里需要先检查是否已存在，避免重复创建
            profile, created = Profile.objects.get_or_create(
                user=user,
                defaults={
                    'school': school,  # 绑定用户所属学校
                    'phone': phone,
                    'student_id': student_id,
                    'dorm': dorm,
                    'role': 'user'  # 默认角色为普通用户
                }
            )
            
            # 如果Profile已存在（由信号创建），更新其字段
            if not created:
                profile.school = school
                profile.phone = phone
                profile.student_id = student_id
                profile.dorm = dorm
                profile.role = 'user'
                profile.save()

            messages.success(request, f'注册成功！欢迎加入 {school.name}')
            return redirect('user_login')
    else:
        form = UserRegisterForm()

    return render(request, 'lostfound/register.html', {'form': form})


def user_login(request):
    """
    用户登录视图
    使用 Django 自带 auth 机制
    """
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            # 使用 Django authenticate 验证用户
            user = authenticate(request, username=username, password=password)

            if user is not None:
                # 登录成功
                login(request, user)
                
                # 获取用户信息
                if user.is_superuser:
                    messages.success(request, f'登录成功！欢迎回来，超级管理员 {username}')
                else:
                    # 检查用户是否有Profile
                    if hasattr(user, 'profile') and user.profile.school:
                        school_name = user.profile.school.name
                        messages.success(request, f'登录成功！欢迎回来，{username}（{school_name}）')
                    else:
                        messages.success(request, f'登录成功！欢迎回来，{username}')
                    
                    # 检查用户是否设置了密保问题，如果没有则在session中标记
                    if hasattr(user, 'profile'):
                        if not user.profile.security_question:
                            request.session['show_security_reminder'] = True
                
                return redirect('home')
            else:
                messages.error(request, '用户名或密码错误')
    else:
        form = UserLoginForm()

    return render(request, 'lostfound/login.html', {'form': form})


def user_logout(request):
    """
    用户登出视图
    """
    logout(request)
    messages.success(request, '您已成功登出')
    return redirect('user_login')


def home(request):
    """
    首页视图
    显示当前登录用户的学校信息和近期公告
    超级管理员：显示管理公告面板（支持筛选和搜索）
    普通用户：显示近期公告（前6条）
    近期公告排序：系统级置顶 > 校级置顶 > 普通公告（按时间倒序）
    """
    if request.user.is_authenticated:
        # 获取用户所属学校
        if request.user.is_superuser:
            user_school = None
            school_display = "超级管理员"
            
            # 超级管理员：管理公告面板
            # 获取筛选参数
            selected_school_id = request.GET.get('school', 'all')
            search_keyword = request.GET.get('search', '').strip()
            
            # 根据学校筛选
            if selected_school_id == 'all':
                notices = Notice.objects.all()
                current_school_filter = 'all'
                current_school_name = '所有学校'
            elif selected_school_id == 'system':
                notices = Notice.objects.filter(school__isnull=True)
                current_school_filter = 'system'
                current_school_name = '系统级公告'
            else:
                try:
                    selected_school = School.objects.get(id=selected_school_id)
                    notices = Notice.objects.filter(
                        Q(school=selected_school) | Q(school__isnull=True)
                    )
                    current_school_filter = selected_school_id
                    current_school_name = selected_school.name
                except School.DoesNotExist:
                    notices = Notice.objects.all()
                    current_school_filter = 'all'
                    current_school_name = '所有学校'
            
            # 关键词搜索
            if search_keyword:
                notices = notices.filter(
                    Q(title__icontains=search_keyword) | Q(content__icontains=search_keyword)
                )
            
            # 应用排序规则
            notices_list = list(notices)
            notices_list.sort(key=lambda x: (
                0 if (x.school is None and x.is_pinned) else  # 系统级置顶
                1 if (x.school is not None and x.is_pinned) else  # 校级置顶
                2,  # 普通公告
                -x.create_time.timestamp()
            ))
            
            # 取前10条
            manage_notices = notices_list[:10]
            
            # 获取所有学校列表
            schools = School.objects.all()
            
            context = {
                'user': request.user,
                'school': user_school,
                'school_display': school_display,
                'manage_notices': manage_notices,
                'schools': schools,
                'current_school_filter': current_school_filter,
                'current_school_name': current_school_name,
                'search_keyword': search_keyword,
                'is_superuser': True,
                'show_security_reminder': request.session.pop('show_security_reminder', False),
            }
        else:
            user_school = request.user.profile.school
            school_display = user_school.name
        
            # 普通用户：近期公告
            notices = Notice.objects.filter(
                Q(school=user_school) | Q(school__isnull=True)
            )
            
            # 应用排序规则
            notices_list = list(notices)
            notices_list.sort(key=lambda x: (
                0 if (x.school is None and x.is_pinned) else  # 系统级置顶
                1 if (x.school is not None and x.is_pinned) else  # 校级置顶
                2,  # 普通公告
                -x.create_time.timestamp()
            ))
            
            # 只取前6条
            recent_notices = notices_list[:6]
            
            context = {
                'user': request.user,
                'school': user_school,
                'school_display': school_display,
                'recent_notices': recent_notices,
                'is_superuser': False,
                'show_security_reminder': request.session.pop('show_security_reminder', False),
            }
        
        return render(request, 'lostfound/home.html', context)
    else:
        return redirect('user_login')


@login_required
def profile_edit(request):
    """
    个人信息编辑视图
    只允许编辑：学号、联系电话、宿舍
    不允许修改：用户名、学校、角色
    """
    profile = request.user.profile
    
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, user=request.user)
        if form.is_valid():
            # 更新 Profile 信息
            profile.student_id = form.cleaned_data.get('student_id', '')
            profile.phone = form.cleaned_data.get('phone', '')
            profile.dorm = form.cleaned_data.get('dorm', '')
            profile.save()
            
            messages.success(request, '个人信息更新成功！')
            return redirect('home')
    else:
        # 初始化表单，填充当前数据
        form = ProfileEditForm(
            user=request.user,
            initial={
                'student_id': profile.student_id,
                'phone': profile.phone,
                'dorm': profile.dorm,
            }
        )
    
    context = {
        'form': form,
        'profile': profile,
    }
    return render(request, 'lostfound/profile_edit.html', context)


@login_required
def password_change(request):
    """
    密码修改视图
    用户需要输入旧密码验证后才能修改密码
    """
    if request.method == 'POST':
        form = PasswordChangeForm(request.POST, user=request.user)
        if form.is_valid():
            # 修改密码
            #set_password( django加密存储哈希字符串)
            new_password = form.cleaned_data['new_password']
            request.user.set_password(new_password)
            request.user.save()
            
            # 修改密码后需要重新登录
            messages.success(request, '密码修改成功！请使用新密码重新登录')
            logout(request)
            return redirect('user_login')
    else:
        form = PasswordChangeForm(user=request.user)
    
    context = {
        'form': form,
    }
    return render(request, 'lostfound/password_change.html', context)


# ==================== ================================
# ==================== 失物信息管理 ====================
# ==================== ================================

@login_required
def lost_item_list(request):
    """
    失物信息列表
    学校隔离：普通用户只显示本校失物信息
    超级管理员：可以通过下拉菜单切换查看不同学校
    状态筛选：可以筛选未认领/已认领的失物
    """
    # 获取状态筛选参数
    status_filter = request.GET.get('status', 'all')
    
    # 超级管理员可以切换学校查看
    if request.user.is_superuser:
        selected_school_id = request.GET.get('school', 'all')
        
        if selected_school_id == 'all':
            lost_items = LostItem.objects.all()
            current_school_name = '所有学校'
            current_school_id = 'all'
        else:
            try:
                selected_school = School.objects.get(id=selected_school_id)
                lost_items = LostItem.objects.filter(school=selected_school)
                current_school_name = selected_school.name
                current_school_id = selected_school_id
            except School.DoesNotExist:
                lost_items = LostItem.objects.all()
                current_school_name = '所有学校'
                current_school_id = 'all'
        
        # 获取所有学校列表供下拉选择
        schools = School.objects.all()
    else:
        # 普通用户只能看本校
        user_school = get_user_school(request)
        lost_items = LostItem.objects.filter(school=user_school)
        current_school_name = user_school.name
        current_school_id = None
        schools = None
    
    # 应用状态筛选
    if status_filter == 'unclaimed':
        lost_items = lost_items.filter(status='unclaimed')
    elif status_filter == 'claimed':
        lost_items = lost_items.filter(status='claimed')
    # 'all' 不需要额外筛选
    
    # 排序
    lost_items = lost_items.order_by('-create_time')
    
    context = {
        'lost_items': lost_items,
        'current_school_name': current_school_name,
        'current_school_id': current_school_id,
        'schools': schools,
        'is_superuser': request.user.is_superuser,
        'status_filter': status_filter,
    }
    return render(request, 'lostfound/lost_item_list.html', context)


@login_required
def lost_item_detail(request, pk):
    """
    失物信息详情
    学校隔离：验证失物所属学校
    """
    lost_item = get_object_or_404(LostItem, pk=pk)
    
    # 验证学校权限
    if not check_school_permission(request.user, lost_item):
        messages.error(request, '您没有权限查看该失物信息（不属于您的学校）')
        return redirect('lost_item_list')
    
    context = {
        'lost_item': lost_item,
    }
    return render(request, 'lostfound/lost_item_detail.html', context)


@login_required
def lost_item_create(request):
    """
    发布失物信息
    学校隔离：自动绑定用户所属学校
    """
    if request.method == 'POST':
        form = LostItemForm(request.POST, request.FILES)
        if form.is_valid():
            lost_item = form.save(commit=False)
            # 强制绑定当前用户和学校
            lost_item.publish_user = request.user
            lost_item.school = get_user_school(request)  # 自动绑定学校
            lost_item.save()
            
            messages.success(request, '失物信息发布成功！')
            return redirect('lost_item_detail', pk=lost_item.pk)
    else:
        form = LostItemForm()
    
    context = {
        'form': form,
        'school': get_user_school(request),
    }
    return render(request, 'lostfound/lost_item_form.html', context)


@login_required
def lost_item_edit(request, pk):
    """
    编辑失物信息
    权限验证：只能编辑自己发布的失物
    学校隔离：验证失物所属学校
    """
    lost_item = get_object_or_404(LostItem, pk=pk)
    
    # 验证学校权限
    if not check_school_permission(request.user, lost_item):
        messages.error(request, '您没有权限编辑该失物信息（不属于您的学校）')
        return redirect('lost_item_list')
    
    # 验证所有者权限
    if not check_owner_permission(request.user, lost_item):
        messages.error(request, '您没有权限编辑该失物信息（不是您发布的）')
        return redirect('lost_item_detail', pk=pk)
    
    if request.method == 'POST':
        form = LostItemForm(request.POST, request.FILES, instance=lost_item)
        if form.is_valid():
            form.save()
            messages.success(request, '失物信息更新成功！')
            return redirect('lost_item_detail', pk=pk)
    else:
        form = LostItemForm(instance=lost_item)
    
    context = {
        'form': form,
        'lost_item': lost_item,
        'is_edit': True,
    }
    return render(request, 'lostfound/lost_item_form.html', context)


@login_required
def lost_item_delete(request, pk):
    """
    删除失物信息
    权限验证：普通用户只能删除自己的，管理员可以删除本校所有失物
    学校隔离：验证失物所属学校
    """
    lost_item = get_object_or_404(LostItem, pk=pk)
    
    # 验证学校权限
    if not check_school_permission(request.user, lost_item):
        messages.error(request, '您没有权限删除该失物信息（不属于您的学校）')
        return redirect('lost_item_list')
    
    # 验证删除权限：所有者或管理员
    is_owner = check_owner_permission(request.user, lost_item)
    is_admin = request.user.profile.role == 'admin'
    
    if not (is_owner or is_admin):
        messages.error(request, '您没有权限删除该失物信息')
        return redirect('lost_item_detail', pk=pk)
    
    if request.method == 'POST':
        lost_item.delete()
        messages.success(request, '失物信息已删除')
        return redirect('lost_item_list')
    
    context = {
        'lost_item': lost_item,
    }
    return render(request, 'lostfound/lost_item_confirm_delete.html', context)

# ==================== ================================
# ==================== 招领信息管理 ====================
# ==================== ================================

@login_required
def found_item_list(request):
    """
    招领信息列表
    学校隔离：普通用户只显示本校招领信息
    超级管理员：可以通过下拉菜单切换查看不同学校
    状态筛选：支持按待认领/已归还状态筛选
    """
    # 超级管理员可以切换学校查看
    if request.user.is_superuser:
        selected_school_id = request.GET.get('school', 'all')
        
        if selected_school_id == 'all':
            found_items = FoundItem.objects.all()
            current_school_name = '所有学校'
            current_school_id = 'all'
        else:
            try:
                selected_school = School.objects.get(id=selected_school_id)
                found_items = FoundItem.objects.filter(school=selected_school)
                current_school_name = selected_school.name
                current_school_id = selected_school_id
            except School.DoesNotExist:
                found_items = FoundItem.objects.all()
                current_school_name = '所有学校'
                current_school_id = 'all'
        
        # 获取所有学校列表供下拉选择
        schools = School.objects.all()
    else:
        # 普通用户只能看本校
        user_school = get_user_school(request)
        found_items = FoundItem.objects.filter(school=user_school)
        current_school_name = user_school.name
        current_school_id = None
        schools = None
    
    # 状态筛选
    status_filter = request.GET.get('status', 'all')
    if status_filter == 'unclaimed':
        found_items = found_items.filter(status='unclaimed')
    elif status_filter == 'returned':
        found_items = found_items.filter(status='returned')
    # 'all' 不需要额外筛选
    
    # 排序
    found_items = found_items.order_by('-create_time')
    
    is_admin = (request.user.is_superuser or
                (not request.user.is_superuser and
                 hasattr(request.user, 'profile') and
                 request.user.profile.role == 'admin'))

    context = {
        'found_items': found_items,
        'current_school_name': current_school_name,
        'current_school_id': current_school_id,
        'schools': schools,
        'is_superuser': request.user.is_superuser,
        'status_filter': status_filter,
        'is_admin': is_admin,
    }
    return render(request, 'lostfound/found_item_list.html', context)


@login_required
def found_item_detail(request, pk):
    """
    招领信息详情
    学校隔离：验证招领信息所属学校
    """
    found_item = get_object_or_404(FoundItem, pk=pk)
    
    # 验证学校权限
    if not check_school_permission(request.user, found_item):
        messages.error(request, '您没有权限查看该招领信息（不属于您的学校）')
        return redirect('found_item_list')
    
    context = {
        'found_item': found_item,
    }
    return render(request, 'lostfound/found_item_detail.html', context)


@login_required
def found_item_create(request):
    """
    发布招领信息
    学校隔离：自动绑定用户所属学校
    """
    if request.method == 'POST':
        form = FoundItemForm(request.POST, request.FILES)
        if form.is_valid():
            found_item = form.save(commit=False)
            # 强制绑定当前用户和学校
            found_item.publish_user = request.user
            found_item.school = get_user_school(request)  # 自动绑定学校
            found_item.save()
            
            messages.success(request, '招领信息发布成功！')
            return redirect('found_item_detail', pk=found_item.pk)
    else:
        form = FoundItemForm()
    
    context = {
        'form': form,
        'school': get_user_school(request),
    }
    return render(request, 'lostfound/found_item_form.html', context)


@login_required
def found_item_edit(request, pk):
    """
    编辑招领信息
    权限验证：只能编辑自己发布的招领信息
    学校隔离：验证招领信息所属学校
    """
    found_item = get_object_or_404(FoundItem, pk=pk)
    
    # 验证学校权限
    if not check_school_permission(request.user, found_item):
        messages.error(request, '您没有权限编辑该招领信息（不属于您的学校）')
        return redirect('found_item_list')
    
    # 验证所有者权限
    if not check_owner_permission(request.user, found_item):
        messages.error(request, '您没有权限编辑该招领信息（不是您发布的）')
        return redirect('found_item_detail', pk=pk)
    
    if request.method == 'POST':
        form = FoundItemForm(request.POST, request.FILES, instance=found_item)
        if form.is_valid():
            form.save()
            messages.success(request, '招领信息更新成功！')
            return redirect('found_item_detail', pk=pk)
    else:
        form = FoundItemForm(instance=found_item)
    
    context = {
        'form': form,
        'found_item': found_item,
        'is_edit': True,
    }
    return render(request, 'lostfound/found_item_form.html', context)


@login_required
def found_item_delete(request, pk):
    """
    删除招领信息
    权限验证：普通用户只能删除自己的，管理员可以删除本校所有招领
    学校隔离：验证招领信息所属学校
    """
    found_item = get_object_or_404(FoundItem, pk=pk)
    
    # 验证学校权限
    if not check_school_permission(request.user, found_item):
        messages.error(request, '您没有权限删除该招领信息（不属于您的学校）')
        return redirect('found_item_list')
    
    # 验证删除权限：所有者或管理员
    is_owner = check_owner_permission(request.user, found_item)
    is_admin = request.user.profile.role == 'admin'
    
    if not (is_owner or is_admin):
        messages.error(request, '您没有权限删除该招领信息')
        return redirect('found_item_detail', pk=pk)
    
    if request.method == 'POST':
        found_item.delete()
        messages.success(request, '招领信息已删除')
        return redirect('found_item_list')
    
    context = {
        'found_item': found_item,
    }
    return render(request, 'lostfound/found_item_confirm_delete.html', context)


@login_required
def found_item_admin_mark_status(request, pk):
    """
    管理员强制修改招领信息状态（待认领 / 已归还）
    权限：校级管理员（本校）和超级管理员
    """
    found_item = get_object_or_404(FoundItem, pk=pk)

    # 验证学校权限
    if not check_school_permission(request.user, found_item):
        messages.error(request, '您没有权限操作该招领信息（不属于您的学校）')
        return redirect('found_item_list')

    # 仅管理员或超级管理员可操作
    is_admin = not request.user.is_superuser and hasattr(request.user, 'profile') and request.user.profile.role == 'admin'
    if not (request.user.is_superuser or is_admin):
        messages.error(request, '您没有权限执行此操作')
        return redirect('found_item_list')

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ('unclaimed', 'returned'):
            found_item.status = new_status
            found_item.save()
            status_label = '待认领' if new_status == 'unclaimed' else '已归还'
            messages.success(request, f'招领信息「{found_item.title}」状态已更新为「{status_label}」')
        else:
            messages.error(request, '无效的状态值')

    # 保留原来的筛选参数跳回列表
    referer = request.META.get('HTTP_REFERER', '')
    if 'found-items' in referer:
        return redirect(referer)
    return redirect('found_item_list')


@login_required
def found_item_mark_returned(request, pk):
    """
    标记招领信息为已归还
    权限验证：只有发布者可以标记
    学校隔离：验证招领信息所属学校
    """
    found_item = get_object_or_404(FoundItem, pk=pk)
    
    # 验证学校权限
    if not check_school_permission(request.user, found_item):
        messages.error(request, '您没有权限操作该招领信息（不属于您的学校）')
        return redirect('found_item_list')
    
    # 验证所有者权限
    if not check_owner_permission(request.user, found_item):
        messages.error(request, '您没有权限操作该招领信息（不是您发布的）')
        return redirect('found_item_detail', pk=pk)
    
    # 验证当前状态
    if found_item.status == 'returned':
        messages.warning(request, '该招领信息已经标记为已归还')
        return redirect('found_item_detail', pk=pk)
    
    if request.method == 'POST':
        found_item.status = 'returned'
        found_item.save()
        messages.success(request, '已成功标记为已归还！')
        return redirect('found_item_list')
    
    return redirect('found_item_detail', pk=pk)

# ==================== ================================
# ==================== 认领申请管理 ====================
# ==================== ================================

@login_required
def claim_create(request, lost_item_id):
    """
    提交认领申请
    学校隔离：只能认领本校失物
    """
    lost_item = get_object_or_404(LostItem, pk=lost_item_id)
    
    # 验证学校权限：禁止跨校认领
    if not check_school_permission(request.user, lost_item):
        messages.error(request, '您不能认领其他学校的失物')
        return redirect('lost_item_list')
    
    # 验证失物状态
    if lost_item.status == 'claimed':
        messages.error(request, '该失物已被认领')
        return redirect('lost_item_detail', pk=lost_item_id)
    
    # 检查是否已经提交过认领申请
    existing_claim = Claim.objects.filter(
        lost_item=lost_item,
        claim_user=request.user,
        status='pending'
    ).first()
    
    if existing_claim:
        messages.warning(request, '您已经提交过认领申请，请等待审核')
        return redirect('lost_item_detail', pk=lost_item_id)
    
    if request.method == 'POST':
        form = ClaimForm(request.POST)
        if form.is_valid():
            claim = form.save(commit=False)
            claim.lost_item = lost_item
            claim.claim_user = request.user
            claim.save()
            
            messages.success(request, '认领申请已提交，请等待管理员审核')
            return redirect('lost_item_detail', pk=lost_item_id)
    else:
        form = ClaimForm()
    
    context = {
        'form': form,
        'lost_item': lost_item,
    }
    return render(request, 'lostfound/claim_form.html', context)


@login_required
def claim_list(request):
    """
    认领申请列表
    普通用户：查看自己的认领申请
    管理员：查看本校所有认领申请
    超级管理员：可以切换查看不同学校的认领申请
    """
    # 超级管理员可以切换学校查看
    if request.user.is_superuser:
        selected_school_id = request.GET.get('school', 'all')
        
        if selected_school_id == 'all':
            claims = Claim.objects.all().order_by('-create_time')
            current_school_name = '所有学校'
            current_school_id = 'all'
        else:
            try:
                selected_school = School.objects.get(id=selected_school_id)
                claims = Claim.objects.filter(lost_item__school=selected_school).order_by('-create_time')
                current_school_name = selected_school.name
                current_school_id = selected_school_id
            except School.DoesNotExist:
                claims = Claim.objects.all().order_by('-create_time')
                current_school_name = '所有学校'
                current_school_id = 'all'
        
        # 获取所有学校列表供下拉选择
        schools = School.objects.all()
    elif request.user.profile.role == 'admin':
        # 管理员：查看本校所有认领申请
        user_school = get_user_school(request)
        claims = Claim.objects.filter(
            lost_item__school=user_school
        ).order_by('-create_time')
        current_school_name = user_school.name
        current_school_id = None
        schools = None
    else:
        # 普通用户：只查看自己的认领申请
        claims = Claim.objects.filter(
            claim_user=request.user
        ).order_by('-create_time')
        current_school_name = None
        current_school_id = None
        schools = None
    
    context = {
        'claims': claims,
        'current_school_name': current_school_name,
        'current_school_id': current_school_id,
        'schools': schools,
        'is_admin': request.user.profile.role == 'admin' if not request.user.is_superuser else True,
        'is_superuser': request.user.is_superuser,
    }
    return render(request, 'lostfound/claim_list.html', context)


@login_required
def claim_detail(request, pk):
    """
    认领申请详情
    权限验证：申请人或管理员可查看
    """
    claim = get_object_or_404(Claim, pk=pk)
    
    # 验证权限：申请人或本校管理员
    is_claimant = claim.claim_user == request.user
    is_admin = (request.user.profile.role == 'admin' and 
                check_school_permission(request.user, claim))
    
    if not (is_claimant or is_admin):
        messages.error(request, '您没有权限查看该认领申请')
        return redirect('claim_list')
    
    context = {
        'claim': claim,
        'is_admin': request.user.profile.role == 'admin',
    }
    return render(request, 'lostfound/claim_detail.html', context)


@admin_required
def claim_review(request, pk):
    """
    审核认领申请
    权限验证：仅管理员可审核
    学校隔离：只能审核本校认领申请
    """
    claim = get_object_or_404(Claim, pk=pk)
    
    # 验证学校权限
    if not check_school_permission(request.user, claim):
        messages.error(request, '您没有权限审核该认领申请（不属于您的学校）')
        return redirect('claim_list')
    
    # 验证申请状态
    if claim.status != 'pending':
        messages.warning(request, '该认领申请已经被审核过了')
        return redirect('claim_detail', pk=pk)
    
    if request.method == 'POST':
        form = ClaimReviewForm(request.POST)
        if form.is_valid():
            status = form.cleaned_data['status']
            admin_note = form.cleaned_data.get('admin_note', '')
            
            # 更新认领申请状态
            claim.status = status
            claim.admin_note = admin_note
            claim.save()
            
            # 如果审核通过，更新失物状态
            if status == 'approved':
                claim.lost_item.status = 'claimed'
                claim.lost_item.save()
                messages.success(request, '认领申请已通过，失物状态已更新')
            else:
                messages.success(request, '认领申请已拒绝')
            
            return redirect('claim_detail', pk=pk)
    else:
        form = ClaimReviewForm()
    
    context = {
        'form': form,
        'claim': claim,
    }
    return render(request, 'lostfound/claim_review.html', context)

# ==================== ================================
# ==================== 公告管理 ====================
# ==================== ================================

@login_required
def notice_list(request):
    """
    公告列表
    学校隔离：普通用户显示本校公告 + 系统级公告
    超级管理员：可以切换查看不同学校的公告
    排序规则：系统级置顶 > 校级置顶 > 普通公告（按时间倒序）
    """
    # 超级管理员可以切换学校查看
    if request.user.is_superuser:
        selected_school_id = request.GET.get('school', 'all')
        
        if selected_school_id == 'all':
            notices = Notice.objects.all()
            current_school_name = '所有学校'
            current_school_id = 'all'
        elif selected_school_id == 'system':
            notices = Notice.objects.filter(school__isnull=True)
            current_school_name = '系统级公告'
            current_school_id = 'system'
        else:
            try:
                selected_school = School.objects.get(id=selected_school_id)
                notices = Notice.objects.filter(
                    Q(school=selected_school) | Q(school__isnull=True)
                )
                current_school_name = selected_school.name
                current_school_id = selected_school_id
            except School.DoesNotExist:
                notices = Notice.objects.all()
                current_school_name = '所有学校'
                current_school_id = 'all'
        
        # 获取所有学校列表供下拉选择
        schools = School.objects.all()
    else:
        # 普通用户看本校 + 系统级公告
        user_school = get_user_school(request)
        notices = Notice.objects.filter(
            Q(school=user_school) | Q(school__isnull=True)
        )
        current_school_name = user_school.name
        current_school_id = None
        schools = None
    
    # 自定义排序：系统级置顶 > 校级置顶 > 普通公告（按时间倒序）
    # 使用 Python 排序而不是数据库排序，以实现复杂的优先级规则
    notices_list = list(notices)
    notices_list.sort(key=lambda x: (
        0 if (x.school is None and x.is_pinned) else  # 系统级置顶（最高优先级）
        1 if (x.school is not None and x.is_pinned) else  # 校级置顶
        2,  # 普通公告
        -x.create_time.timestamp()  # 同级别内按时间倒序
    ))
    
    context = {
        'notices': notices_list,
        'current_school_name': current_school_name,
        'current_school_id': current_school_id,
        'schools': schools,
        'is_admin': request.user.profile.role == 'admin' if not request.user.is_superuser else True,
        'is_superuser': request.user.is_superuser,
    }
    return render(request, 'lostfound/notice_list.html', context)


@login_required
def notice_detail(request, pk):
    """
    公告详情
    学校隔离：验证公告可见性
    超级管理员：可以查看所有公告
    """
    notice = get_object_or_404(Notice, pk=pk)
    
    # 超级管理员可以查看所有公告
    if request.user.is_superuser:
        context = {
            'notice': notice,
        }
        return render(request, 'lostfound/notice_detail.html', context)
    
    # 普通用户验证权限
    user_school = get_user_school(request)
    
    # 验证权限：系统级公告或本校公告
    if notice.school is not None and notice.school != user_school:
        messages.error(request, '您没有权限查看该公告（不属于您的学校）')
        return redirect('notice_list')
    
    context = {
        'notice': notice,
    }
    return render(request, 'lostfound/notice_detail.html', context)


@admin_required
def notice_create(request):
    """
    发布公告
    权限验证：仅管理员可发布
    学校隔离：校级管理员发布的公告自动绑定本校
    超级管理员：可以选择发布系统级公告或校级公告，并可设置置顶
    """
    if request.method == 'POST':
        form = NoticeForm(request.POST)
        if form.is_valid():
            notice = form.save(commit=False)
            notice.publish_user = request.user
            
            # 超级管理员可以选择发布系统级公告
            if request.user.is_superuser:
                # 从表单获取是否发布系统级公告
                is_system_notice = request.POST.get('is_system_notice') == 'on'
                if is_system_notice:
                    notice.school = None  # 系统级公告
                else:
                    # 如果选择了学校，绑定到该学校
                    school_id = request.POST.get('school_select')
                    if school_id:
                        notice.school = School.objects.get(id=school_id)
                    else:
                        notice.school = None  # 默认系统级
                
                # 超级管理员可以设置置顶
                notice.is_pinned = request.POST.get('is_pinned') == 'on'
            else:
                # 校级管理员发布的公告自动绑定本校
                notice.school = get_user_school(request)
                # 校级管理员也可以设置置顶
                notice.is_pinned = request.POST.get('is_pinned') == 'on'
            
            notice.save()
            
            pin_status = '（已置顶）' if notice.is_pinned else ''
            if notice.school:
                messages.success(request, f'校级公告发布成功（{notice.school.name}）{pin_status}')
            else:
                messages.success(request, f'系统级公告发布成功（所有学校可见）{pin_status}')
            
            return redirect('notice_detail', pk=notice.pk)
    else:
        form = NoticeForm()
    
    # 超级管理员需要学校列表
    if request.user.is_superuser:
        schools = School.objects.all()
    else:
        schools = None
    
    context = {
        'form': form,
        'school': get_user_school(request) if not request.user.is_superuser else None,
        'schools': schools,
        'is_superuser': request.user.is_superuser,
    }
    return render(request, 'lostfound/notice_form.html', context)


@admin_required
def notice_edit(request, pk):
    """
    编辑公告
    权限验证：只能编辑本校公告
    超级管理员：可以编辑所有公告
    """
    notice = get_object_or_404(Notice, pk=pk)
    
    # 超级管理员可以编辑所有公告
    if not request.user.is_superuser:
        # 验证权限：只能编辑本校公告
        if notice.school != get_user_school(request):
            messages.error(request, '您没有权限编辑该公告（不属于您的学校）')
            return redirect('notice_list')
    
    if request.method == 'POST':
        form = NoticeForm(request.POST, instance=notice)
        if form.is_valid():
            notice = form.save(commit=False)
            
            # 更新置顶状态
            if request.user.is_superuser:
                # 超级管理员可以设置任何公告的置顶状态
                notice.is_pinned = request.POST.get('is_pinned') == 'on'
            else:
                # 校级管理员只能设置校级公告的置顶状态
                notice.is_pinned = request.POST.get('is_pinned') == 'on'
            
            notice.save()
            messages.success(request, '公告更新成功')
            return redirect('notice_detail', pk=pk)
    else:
        form = NoticeForm(instance=notice)
    
    # 超级管理员需要学校列表
    if request.user.is_superuser:
        schools = School.objects.all()
    else:
        schools = None
    
    context = {
        'form': form,
        'notice': notice,
        'is_edit': True,
        'schools': schools,
        'is_superuser': request.user.is_superuser,
    }
    return render(request, 'lostfound/notice_form.html', context)


@admin_required
def notice_delete(request, pk):
    """
    删除公告
    权限验证：只能删除本校公告
    超级管理员：可以删除所有公告
    """
    notice = get_object_or_404(Notice, pk=pk)
    
    # 超级管理员可以删除所有公告
    if not request.user.is_superuser:
        # 验证权限：只能删除本校公告
        if notice.school != get_user_school(request):
            messages.error(request, '您没有权限删除该公告（不属于您的学校）')
            return redirect('notice_list')
    
    if request.method == 'POST':
        notice.delete()
        messages.success(request, '公告已删除')
        return redirect('notice_list')
    
    context = {
        'notice': notice,
    }
    return render(request, 'lostfound/notice_confirm_delete.html', context)


@admin_required
def notice_toggle_pin(request, pk):
    """
    切换公告置顶状态
    权限验证：只能操作本校公告
    超级管理员：可以操作所有公告
    """
    notice = get_object_or_404(Notice, pk=pk)
    
    # 超级管理员可以操作所有公告
    if not request.user.is_superuser:
        # 验证权限：只能操作本校公告
        if notice.school != get_user_school(request):
            messages.error(request, '您没有权限操作该公告（不属于您的学校）')
            return redirect('notice_list')
    
    # 切换置顶状态
    notice.is_pinned = not notice.is_pinned
    notice.save()
    
    # 提示信息
    if notice.is_pinned:
        pin_type = "系统级" if notice.school is None else "校级"
        messages.success(request, f'公告已设置为{pin_type}置顶')
    else:
        messages.success(request, '公告已取消置顶')
    
    return redirect('notice_list')

# ==================== ================================
# ==================== 用户管理（仅超级管理员） ====================
# ==================== ================================

from .decorators import superuser_required
from django.core.paginator import Paginator

@superuser_required
def user_management_list(request):
    """
    用户列表视图（仅超级管理员）
    支持按用户名/姓名搜索，分页显示
    """
    search = request.GET.get('search', '').strip()
    users = User.objects.select_related('profile', 'profile__school').exclude(is_superuser=True).order_by('id')
    if search:
        users = users.filter(
            Q(username__icontains=search) | Q(first_name__icontains=search)
        )
    paginator = Paginator(users, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'lostfound/user_management_list.html', {
        'page_obj': page_obj,
        'search': search,
    })


@superuser_required
def user_toggle_role(request, user_id):
    """
    切换用户角色：普通用户 <-> 管理员（仅超级管理员）
    """
    if request.method != 'POST':
        return redirect('user_management_list')
    target_user = get_object_or_404(User, pk=user_id, is_superuser=False)
    profile = target_user.profile
    if profile.role == 'user':
        profile.role = 'admin'
        messages.success(request, f'已将用户 {target_user.username} 设为管理员')
    else:
        profile.role = 'user'
        messages.success(request, f'已将用户 {target_user.username} 设为普通用户')
    profile.save()
    return redirect(request.META.get('HTTP_REFERER', 'user_management_list'))
0

@superuser_required
def user_toggle_active(request, user_id):
    """
    启用/禁用用户账号（仅超级管理员）
    """
    if request.method != 'POST':
        return redirect('user_management_list')
    target_user = get_object_or_404(User, pk=user_id, is_superuser=False)
    target_user.is_active = not target_user.is_active
    target_user.save()
    status_text = '启用' if target_user.is_active else '禁用'
    messages.success(request, f'已{status_text}用户 {target_user.username}')
    return redirect(request.META.get('HTTP_REFERER', 'user_management_list'))


@superuser_required
def user_reset_password(request, user_id):
    """
    重置用户密码为 123456（仅超级管理员）
    """
    if request.method != 'POST':
        return redirect('user_management_list')
    target_user = get_object_or_404(User, pk=user_id, is_superuser=False)
    new_password = '123456'
    target_user.set_password(new_password)
    target_user.save()
    messages.success(request, f'用户 {target_user.username} 的密码已重置为：{new_password}，请通知该用户')
    return redirect(request.META.get('HTTP_REFERER', 'user_management_list'))


# ==================== 信息页面 ====================

def data_isolation_info(request):
    """
    数据隔离说明页面
    公开访问，无需登录
    """
    return render(request, 'lostfound/data_isolation_info.html')


def responsibility_info(request):
    """
    责任说明页面
    公开访问，无需登录
    """
    return render(request, 'lostfound/responsibility_info.html')


# ==================== 忘记密码功能 ====================

def forgot_password_step1(request):
    """
    忘记密码 - 步骤1：输入用户名，选择重置方式
    """
    if request.method == 'POST':
        form = ForgotPasswordStep1Form(request.POST)
        if form.is_valid():
            user = form.user
            # 将用户ID存入session
            request.session['reset_user_id'] = user.id
            
            # 跳转到选择重置方式页面
            return redirect('forgot_password_choose_method')
    else:
        form = ForgotPasswordStep1Form()
    
    return render(request, 'lostfound/forgot_password_step1.html', {'form': form})


def forgot_password_choose_method(request):
    """
    忘记密码 - 选择重置方式
    """
    user_id = request.session.get('reset_user_id')
    if not user_id:
        messages.error(request, '请先输入用户名')
        return redirect('forgot_password_step1')
    
    user = get_object_or_404(User, id=user_id)
    has_security = user.profile.has_security_question()
    
    context = {
        'user': user,
        'has_security': has_security,
    }
    return render(request, 'lostfound/forgot_password_choose_method.html', context)


def forgot_password_security(request):
    """
    忘记密码 - 安全问题验证并重置密码
    """
    user_id = request.session.get('reset_user_id')
    if not user_id:
        messages.error(request, '请先输入用户名')
        return redirect('forgot_password_step1')
    
    user = get_object_or_404(User, id=user_id)
    
    if not user.profile.has_security_question():
        messages.error(request, '您还未设置密保问题，请使用其他方式重置密码')
        return redirect('forgot_password_choose_method')
    
    if request.method == 'POST':
        form = ForgotPasswordSecurityForm(request.POST, user=user)
        if form.is_valid():
            # 重置密码
            new_password = form.cleaned_data['new_password']
            user.set_password(new_password)
            user.save()
            
            # 清除session
            del request.session['reset_user_id']
            
            messages.success(request, '密码重置成功！请使用新密码登录')
            return redirect('user_login')
    else:
        form = ForgotPasswordSecurityForm(user=user)
    
    context = {
        'form': form,
        'user': user,
        'security_question': user.profile.security_question,
    }
    return render(request, 'lostfound/forgot_password_security.html', context)


@login_required
def security_question_set(request):
    """
    设置密保问题
    """
    profile = request.user.profile
    
    if request.method == 'POST':
        form = SecurityQuestionForm(request.POST)
        if form.is_valid():
            profile.security_question = form.cleaned_data['security_question']
            profile.security_answer = form.cleaned_data['security_answer']
            profile.save()
            
            messages.success(request, '密保问题设置成功！')
            return redirect('profile_edit')
    else:
        # 如果已设置，显示当前密保问题
        initial = {}
        if profile.has_security_question():
            initial['security_question'] = profile.security_question
        form = SecurityQuestionForm(initial=initial)
    
    context = {
        'form': form,
        'profile': profile,
        'has_security': profile.has_security_question(),
    }
    return render(request, 'lostfound/security_question_set.html', context)




# ==================== User Management (Superuser Only) ====================

from .decorators import superuser_required
from django.core.paginator import Paginator

@superuser_required
def user_management_list(request):
    search = request.GET.get('search', '').strip()
    school_filter = request.GET.get('school', 'all')
    users = User.objects.select_related('profile', 'profile__school').exclude(is_superuser=True).order_by('id')
    if search:
        users = users.filter(
            Q(username__icontains=search) | Q(first_name__icontains=search)
        )
    if school_filter == 'none':
        users = users.filter(profile__school__isnull=True)
    elif school_filter != 'all':
        try:
            users = users.filter(profile__school__id=int(school_filter))
        except (ValueError, TypeError):
            pass
    paginator = Paginator(users, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    schools = School.objects.all().order_by('name')
    return render(request, 'lostfound/user_management_list.html', {
        'page_obj': page_obj,
        'search': search,
        'school_filter': school_filter,
        'schools': schools,
    })


@superuser_required
def user_toggle_role(request, user_id):
    if request.method != 'POST':
        return redirect('user_management_list')
    target_user = get_object_or_404(User, pk=user_id, is_superuser=False)
    profile = target_user.profile
    if profile.role == 'user':
        profile.role = 'admin'
        messages.success(request, f'已将用户 {target_user.username} 设为管理员')
    else:
        profile.role = 'user'
        messages.success(request, f'已将用户 {target_user.username} 设为普通用户')
    profile.save()
    return redirect(request.META.get('HTTP_REFERER', '/superadmin/users/'))


@superuser_required
def user_toggle_active(request, user_id):
    if request.method != 'POST':
        return redirect('user_management_list')
    target_user = get_object_or_404(User, pk=user_id, is_superuser=False)
    target_user.is_active = not target_user.is_active
    target_user.save()
    status_text = '已启用' if target_user.is_active else '已禁用'
    messages.success(request, f'{status_text}用户 {target_user.username}')
    return redirect(request.META.get('HTTP_REFERER', '/superadmin/users/'))


@superuser_required
def user_reset_password(request, user_id):
    if request.method != 'POST':
        return redirect('user_management_list')
    target_user = get_object_or_404(User, pk=user_id, is_superuser=False)
    new_password = '123456'
    target_user.set_password(new_password)
    target_user.save()
    messages.success(request, f'用户 {target_user.username} 的密码已重置为：{new_password}，请通知该用户')
    return redirect(request.META.get('HTTP_REFERER', '/superadmin/users/'))
