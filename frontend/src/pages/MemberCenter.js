import React, { useState, useEffect, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import '../styles/memberCenter.css';
import { ShinyButton } from '../components/ui/shiny-button';

function MemberCenter() {
  const [memberInfo, setMemberInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('profile');
  const [orders, setOrders] = useState([]);
  const [addresses, setAddresses] = useState([]);
  const [coupons, setCoupons] = useState([]);
  const [orderFilter, setOrderFilter] = useState('all');
  const [activeCouponTab, setActiveCouponTab] = useState('available');
  // 售后申请相关状态
  const [afterSaleRequests, setAfterSaleRequests] = useState([]);
  const [afterSaleLoading, setAfterSaleLoading] = useState(false);
  // 聊天相关状态
  const [selectedAfterSaleId, setSelectedAfterSaleId] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [sendingMessage, setSendingMessage] = useState(false);
  const [showChatModal, setShowChatModal] = useState(false);
  const [chatLoading, setChatLoading] = useState(false);
  // 新增状态变量
  const [showEditProfileModal, setShowEditProfileModal] = useState(false);
  const [showChangePasswordModal, setShowChangePasswordModal] = useState(false);
  const [editProfileData, setEditProfileData] = useState({
    username: '',
    email: '',
    phone: '',
    gender: '',
    birthday: '',
    first_name: '',
    last_name: ''
  });
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  const [profileError, setProfileError] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [profileSuccess, setProfileSuccess] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState('');
  
  // 地址管理相关状态
  const [showAddressModal, setShowAddressModal] = useState(false);
  const [addressFormData, setAddressFormData] = useState({
    name: '',
    phone: '',
    province: '',
    city: '',
    district: '',
    detail: '',
    is_default: false
  });
  const [editingAddressId, setEditingAddressId] = useState(null);
  const [addressError, setAddressError] = useState('');
  const [addressSuccess, setAddressSuccess] = useState('');
  const [processingAddress, setProcessingAddress] = useState(false);
  
  // 充值相关状态
  const [showRechargeModal, setShowRechargeModal] = useState(false);
  const [rechargeAmount, setRechargeAmount] = useState('');
  const [rechargeError, setRechargeError] = useState('');
  const [rechargeSuccess, setRechargeSuccess] = useState('');
  const [processingRecharge, setProcessingRecharge] = useState(false);

  // 会员等级相关状态
  const [memberLevels, setMemberLevels] = useState([]);
  const [currentDiscountInfo, setCurrentDiscountInfo] = useState(null);
  
  const navigate = useNavigate();

  // 添加检查商品是否已评价的状态
  const [reviewedProducts, setReviewedProducts] = useState(new Set());

  // 在fetchOrders之前添加获取已评价商品的函数
  const fetchUserReviews = async () => {
    try {
      const token = localStorage.getItem('access') || localStorage.getItem('token');
      if (!token) {
        return;
      }
      
      console.log("获取用户已评价商品...");
      const response = await axios.get('/api/review/reviews/user-reviews/', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (Array.isArray(response.data)) {
        // 将已评价的商品ID添加到集合中
        const reviewedIds = new Set(response.data.map(review => review.product_id));
        console.log("已评价商品IDs:", Array.from(reviewedIds));
        setReviewedProducts(reviewedIds);
      }
    } catch (error) {
      console.error("获取用户评价记录失败:", error);
    }
  };

  useEffect(() => {
    // 检查登录状态
    const token = localStorage.getItem('access') || localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }
    
    fetchMemberInfo();
    fetchOrders();
    fetchAddresses();
    fetchCoupons();
    fetchUserReviews(); // 新增：获取用户已评价商品
    fetchAfterSaleRequests(); // 获取售后申请
    fetchMemberLevels(); // 获取会员等级信息
    fetchCurrentDiscountInfo(); // 获取当前用户折扣信息
  }, [navigate]);

  // 监听优惠券Tab切换，重新获取数据
  useEffect(() => {
    if (activeTab === 'coupons') {
      console.log('优惠券Tab激活，当前子标签:', activeCouponTab);
      
      // 设置防抖定时器，避免快速切换标签时频繁请求
      const debounceTimer = setTimeout(() => {
        console.log('执行延迟加载，标签:', activeCouponTab);
        fetchCoupons();
      }, 300);
      
      // 清理函数
      return () => {
        clearTimeout(debounceTimer);
      };
    }
  }, [activeTab, activeCouponTab]);

  // 监听售后申请Tab切换
  useEffect(() => {
    if (activeTab === 'aftersale') {
      fetchAfterSaleRequests();
    }
  }, [activeTab]);

  const fetchMemberInfo = async () => {
    try {
      // 首先尝试从localStorage获取用户信息
      const storedUser = localStorage.getItem('user');
      if (storedUser) {
        try {
        const user = JSON.parse(storedUser);
        setMemberInfo({
          id: user.id,
          username: user.username || user.name,
          email: user.email,
          phone: user.phone || '未设置',
            avatar: user.avatar || '/images/Normal.jpg',
          level: user.level || 'VIP',
          levelName: user.levelName || '普通会员',
          points: user.points || 0,
          growth_value: user.growth_value || 0,
            balance: parseFloat(user.balance || 0) || 0,
          joinDate: user.joinDate || new Date().toISOString().split('T')[0],
          totalSpent: user.totalSpent || 0,
          nextLevelPoints: user.nextLevelPoints || 1000,
          currentLevelPoints: user.currentLevelPoints || 0,
          maxLevelPoints: user.maxLevelPoints || 1000,
          nextLevelName: user.next_level_name || '下一等级',
          progress: user.progress || 0
        });
        } catch (parseError) {
          console.error('解析用户数据失败:', parseError);
          localStorage.removeItem('user');
        }
      }
      
      // 获取API数据，无论是否有localStorage数据
      const token = localStorage.getItem('access') || localStorage.getItem('token');
      if (!token) {
        console.error('无法获取认证令牌');
        navigate('/login');
        return;
      }
      
      console.log('获取会员信息，使用令牌:', token.substring(0, 10) + '...');
      
      // 尝试获取会员信息，优先使用current_member端点
      try {
        // 使用新的current_member端点
        const response = await axios.get('/api/member/members/current_member/', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      console.log('会员API响应:', response.data);
        console.log('会员API响应原始数据:', JSON.stringify(response.data));
        
        // 当前会员端点返回单个对象，而不是数组
        if (response.data) {
          const userData = response.data;
          console.log('用户数据详情:', userData);
          console.log('用户手机号:', userData.phone);
          console.log('用户对象:', userData.user);
          
          // 直接从userData中获取手机号，或者尝试从user.phone获取
          const phone = userData.phone || 
                      (userData.user && userData.user.phone) || 
                      '未设置';
          
          console.log('获取到的手机号:', phone);
          
          setMemberInfo({
            id: userData.id,
            username: userData.user?.username || '',
            email: userData.user?.email || '',
            phone: phone, // 使用从API获取的手机号
            avatar: userData.avatar || '/images/Normal.jpg',
            level: userData.level || 'VIP',
            levelName: userData.level_name || '普通会员',
            points: userData.points || 0,
            growth_value: userData.growth_value || 0,
            balance: parseFloat(userData.balance || 0) || 0,
            joinDate: userData.created_at || new Date().toISOString().split('T')[0],
            totalSpent: parseFloat(userData.total_spent) || 0,
            points_needed: userData.points_needed || 0,
            nextLevelPoints: userData.next_level_points || 0,
            currentLevelPoints: userData.current_level_points || 0,
            maxLevelPoints: userData.next_level_points || 0,
            nextLevelName: userData.next_level_name || '下一等级',
            progress: userData.progress || 0,
            gender: userData.gender || '',
            birthday: userData.birthday || '',
            first_name: userData.user?.first_name || '',
            last_name: userData.user?.last_name || ''
          });
          
          // 设置编辑资料表单的初始值
          setEditProfileData({
            username: userData.user?.username || '',
            email: userData.user?.email || '',
            phone: phone !== '未设置' ? phone : '',
            gender: userData.gender || '',
            birthday: userData.birthday || '',
            first_name: userData.user?.first_name || '',
            last_name: userData.user?.last_name || ''
          });

          // 更新localStorage中的用户信息，确保包含手机号
          try {
            const existingUser = JSON.parse(localStorage.getItem('user') || '{}');
            localStorage.setItem('user', JSON.stringify({
              ...existingUser,
              ...userData,
              phone: phone // 确保手机号也存入localStorage
            }));
          } catch (error) {
            console.error('更新本地存储失败:', error);
          }
        }
      } catch (apiError) {
        // 如果current_member端点失败，尝试使用旧的列表API
        console.log('使用current_member端点失败，尝试使用列表API');
        try {
          const response = await axios.get(`${process.env.REACT_APP_API_URL !== undefined ? process.env.REACT_APP_API_URL : 'http://127.0.0.1:8000'}/api/member/members/`, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });
      
      if (response.data && response.data.length > 0) {
        const userData = response.data[0];
            // 从userData中获取手机号
            const phone = userData.phone || '未设置';
            
        setMemberInfo({
          id: userData.id,
              username: userData.user?.username || '',
              email: userData.user?.email || '',
              phone: phone, // 使用从API获取的手机号
              avatar: userData.avatar || '/images/Normal.jpg',
              level: userData.level || 'normal',
          levelName: userData.level_name || '普通会员',
          points: userData.points || 0,
          growth_value: userData.growth_value || 0,
              balance: parseFloat(userData.balance || 0) || 0,
          joinDate: userData.created_at || new Date().toISOString().split('T')[0],
          totalSpent: parseFloat(userData.total_spent) || 0,
          points_needed: userData.points_needed || 0,
          nextLevelPoints: userData.next_level_points || 0,
          currentLevelPoints: userData.current_level_points || 0,
              maxLevelPoints: userData.next_level_points || 0,
              nextLevelName: userData.next_level_name || '下一等级',
              progress: userData.progress || 0,
              gender: userData.gender || '',
              birthday: userData.birthday || ''
            });
            
            // 设置编辑资料表单的初始值
            setEditProfileData({
              username: userData.user?.username || '',
              email: userData.user?.email || '',
              phone: phone !== '未设置' ? phone : '',
              gender: userData.gender || '',
              birthday: userData.birthday || '',
              first_name: userData.user?.first_name || '',
              last_name: userData.user?.last_name || ''
        });
            
        // 更新localStorage中的用户信息
            try {
              const existingUser = JSON.parse(localStorage.getItem('user') || '{}');
        localStorage.setItem('user', JSON.stringify({
                ...existingUser,
                ...userData,
                phone: phone
        }));
            } catch (error) {
              console.error('更新本地存储失败:', error);
            }
          }
        } catch (listApiError) {
          console.error('获取会员列表失败:', listApiError);
          // 两种API都失败，显示localStorage中的数据
        }
      }
    } catch (error) {
      console.error('获取会员信息失败:', error);
      
      // 错误处理
      if (error.response) {
        console.error('错误状态:', error.response.status);
        console.error('错误数据:', error.response.data);
        
        if (error.response.status === 401) {
          console.warn('认证失败，需要重新登录');
          localStorage.removeItem('access');
          localStorage.removeItem('token');
          localStorage.removeItem('refresh_token');
          navigate('/login');
          return;
        }
      }
      
      // 如果API调用失败，使用localStorage中的基本信息
      const storedUser = localStorage.getItem('user');
      if (storedUser) {
        try {
        const user = JSON.parse(storedUser);
        setMemberInfo({
          id: user.id || 1,
          username: user.username || user.name || '用户',
          email: user.email || 'user@example.com',
            phone: user.phone || '未设置',
            avatar: user.avatar || '/images/Normal.jpg',
            level: user.level || 'VIP',
            levelName: user.levelName || '普通会员',
            points: user.points || 0,
            growth_value: user.growth_value || 0,
            balance: parseFloat(user.balance || 0) || 0,
            joinDate: user.date_joined || new Date().toISOString().split('T')[0],
            totalSpent: user.total_spent || 0,
            points_needed: user.points_needed || 0,
            nextLevelPoints: user.next_level_points || 0,
            currentLevelPoints: user.current_level_points || 0,
            maxLevelPoints: user.next_level_points || 0,
            nextLevelName: user.next_level_name || '最高等级',
            progress: user.progress || 0,
          gender: user.gender || '',
          birthday: user.birthday || ''
        });
        
        // 设置编辑资料表单的初始值
        setEditProfileData({
          username: user.username || user.name || '',
          email: user.email || '',
          phone: user.phone && user.phone !== '未设置' ? user.phone : '',
          gender: user.gender || '',
          birthday: user.birthday || '',
          first_name: user.user?.first_name || '',
          last_name: user.user?.last_name || ''
        });
        } catch (parseError) {
          console.error('解析备用用户数据失败:', parseError);
        }
      }
    } finally {
      setLoading(false);
    }
  };

  // 获取会员等级信息
  const fetchMemberLevels = async () => {
    try {
      const token = localStorage.getItem('access') || localStorage.getItem('token');
      if (!token) return;

      const response = await axios.get('/api/member/member-levels/public/', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      console.log('会员等级信息:', response.data);
      setMemberLevels(response.data);
    } catch (error) {
      console.error('获取会员等级信息失败:', error);
    }
  };

  // 获取当前用户折扣信息
  const fetchCurrentDiscountInfo = async () => {
    try {
      const token = localStorage.getItem('access') || localStorage.getItem('token');
      if (!token) return;

      const response = await axios.get('/api/member/members/discount_info/', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      console.log('当前用户折扣信息:', response.data);
      setCurrentDiscountInfo(response.data);
    } catch (error) {
      console.error('获取当前用户折扣信息失败:', error);
    }
  };

  // 处理编辑资料表单字段变化
  const handleProfileInputChange = (e) => {
    const { name, value } = e.target;
    setEditProfileData({
      ...editProfileData,
      [name]: value
    });
  };

  // 处理密码表单字段变化
  const handlePasswordInputChange = (e) => {
    const { name, value } = e.target;
    setPasswordData({
      ...passwordData,
      [name]: value
    });
  };

  // 提交编辑资料表单
  const handleProfileSubmit = async (e) => {
    e.preventDefault();
    setProfileError('');
    setProfileSuccess('');
    
    try {
      const token = localStorage.getItem('access') || localStorage.getItem('token');
      if (!token) {
        setProfileError('未授权，请重新登录');
        return;
      }

      // 构造请求数据，只包含要更新的字段
      const updateData = {
        phone: editProfileData.phone,
        gender: editProfileData.gender,
        birthday: editProfileData.birthday || null,
        first_name: editProfileData.first_name,
        last_name: editProfileData.last_name
      };
      
      // 发送更新请求
      const response = await axios.patch(
        `${process.env.REACT_APP_API_URL !== undefined ? process.env.REACT_APP_API_URL : 'http://127.0.0.1:8000'}/api/member/members/${memberInfo.id}/`, 
        updateData,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      
      // 更新成功，刷新会员信息
      setProfileSuccess('个人资料更新成功！');
      await fetchMemberInfo();
      
      // 3秒后关闭模态窗口
      setTimeout(() => {
        setShowEditProfileModal(false);
        setProfileSuccess('');
      }, 3000);
    } catch (error) {
      console.error('更新个人资料失败:', error);
      setProfileError(error.response?.data?.detail || '更新失败，请稍后再试');
    }
  };

  // 提交修改密码表单
  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    setPasswordError('');
    setPasswordSuccess('');
    
    // 验证两次输入的新密码是否一致
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      setPasswordError('两次输入的新密码不一致');
      return;
    }
    
    try {
      const token = localStorage.getItem('access') || localStorage.getItem('token');
      if (!token) {
        setPasswordError('未授权，请重新登录');
        return;
      }
      
      // 发送密码更新请求
      await axios.post(
        `${process.env.REACT_APP_API_URL !== undefined ? process.env.REACT_APP_API_URL : 'http://127.0.0.1:8000'}/api/auth/change-password/`, 
        {
          old_password: passwordData.currentPassword,
          new_password: passwordData.newPassword
        },
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      
      // 更新成功，清空表单
      setPasswordSuccess('密码修改成功！');
      setPasswordData({
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      });
      
      // 3秒后关闭模态窗口
      setTimeout(() => {
        setShowChangePasswordModal(false);
        setPasswordSuccess('');
      }, 3000);
    } catch (error) {
      console.error('修改密码失败:', error);
      setPasswordError(error.response?.data?.detail || '原密码错误或新密码不符合要求');
    }
  };

  const fetchOrders = async () => {
    try {
      const token = localStorage.getItem('access') || localStorage.getItem('token');
      if (!token) {
        setOrders([]);
        return;
      }
      
      // 获取已删除订单的ID列表
      const deletedOrdersStr = localStorage.getItem('deleted_orders') || '[]';
      let deletedOrders = [];
      try {
        deletedOrders = JSON.parse(deletedOrdersStr);
      } catch (e) {
        deletedOrders = [];
      }
      
      console.log("开始获取用户订单...");
      const response = await axios.get('/api/order/orders/', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      console.log("订单API返回数据:", response.data);
      
      // 处理API返回的订单数据
      let orderList = [];
      
      if (Array.isArray(response.data)) {
        // 如果是数组格式
        orderList = response.data;
      } else if (response.data && typeof response.data === 'object') {
        // 如果是对象格式，查看是否有results字段（DRF分页）
        if (Array.isArray(response.data.results)) {
          orderList = response.data.results;
        }
      }
      
      // 格式化订单数据
      if (orderList.length > 0) {
        const formattedOrders = orderList
          // 过滤掉已删除的订单
          .filter(order => {
            const orderId = order.order_number || order.id;
            return !deletedOrders.includes(orderId);
          })
          .map(order => {
            // 获取状态显示文本
            let statusText = '';
            switch(order.status) {
              case 'pending':
                statusText = '待付款';
                break;
              case 'paid':
                statusText = '已支付';
                break;
              case 'processing':
                statusText = '处理中';
                break;
              case 'shipped':
              case 'shipping':
                statusText = '配送中';
                break;
              case 'delivered':
                statusText = '已送达';
                break;
              case 'completed':
                statusText = '已完成';
                break;
              case 'cancelled':
                statusText = '已取消';
                break;
              default:
                statusText = order.status_display || order.status;
            }
            
            // 添加对订单项是否已评价的检查
            const orderItems = Array.isArray(order.items) ? order.items.map(item => {
              // 正确获取商品ID：优先使用变体ID，它会被后端自动映射到主产品ID
              const productId = item.product_variant || item.product_id || item.id;
              
              console.log(`处理订单项: ${item.product_name}, 订单项ID: ${item.id}, 变体ID: ${item.product_variant}, 使用ID: ${productId}`);
              
              return {
                id: productId,  // 使用变体ID或主产品ID，不是订单项ID
                originalItemId: item.id,  // 保存原始订单项ID
                product_variant: item.product_variant,  // 保存变体ID
                name: item.product_name || '未命名商品',
                quantity: item.quantity || 1,
                price: parseFloat(item.price || 0),
                image: item.product_image || '/images/Normal.jpg',
                reviewed: reviewedProducts.has(parseInt(productId)) // 使用正确的ID检查是否已评价
              };
            }) : [];
            
            return {
              id: order.order_number || order.id,
              date: order.created_at,
              status: order.status,
              statusText: statusText,
              total: parseFloat(order.total_price || 0),
              items: orderItems
            };
          });
        
        setOrders(formattedOrders);
      } else {
        setOrders([]);
      }
    } catch (error) {
      console.error('获取订单列表失败:', error.response || error);
      setOrders([]);
    }
  };

  // 修改fetchAddresses函数处理is_default字段
  const fetchAddresses = async () => {
    try {
      const token = localStorage.getItem('access') || localStorage.getItem('token');
      if (!token) {
        setAddresses([]);
        return;
      }
      
      console.log("开始获取地址列表...");
      const response = await axios.get('/api/member/addresses/', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      console.log("地址API返回数据:", response.data);
      
      // 处理不同格式的响应
      let addressList = [];
      
      if (Array.isArray(response.data)) {
        // 如果是数组格式
        addressList = response.data;
      } else if (response.data && typeof response.data === 'object') {
        // 如果是对象格式，查看是否有results字段（DRF分页）
        if (Array.isArray(response.data.results)) {
          addressList = response.data.results;
        } else {
          // 尝试将对象的值转为数组
          const objectValues = Object.values(response.data);
          if (objectValues.length > 0 && typeof objectValues[0] === 'object') {
            addressList = objectValues;
          }
        }
      }
      
      console.log("处理后的地址列表:", addressList);
      
      if (addressList.length > 0) {
        // 格式化数据便于前端使用
        const formattedAddresses = addressList.map(addr => ({
          id: addr.id,
          name: addr.name || '',
          phone: addr.phone || '',
          province: addr.province || '',
          city: addr.city || '',
          district: addr.district || '',
          detail: addr.detail || '',
          isDefault: Boolean(addr.is_default)
        }));
        
        console.log("格式化后的地址数据:", formattedAddresses);
        setAddresses(formattedAddresses);
      } else {
        console.warn("未找到有效的地址数据");
        setAddresses([]);
      }
    } catch (error) {
      console.error('获取地址列表失败:', error.response || error);
      setAddresses([]);
    }
  };

  const fetchCoupons = async () => {
    try {
      const token = localStorage.getItem('access') || localStorage.getItem('token');
      if (!token) {
        console.error('无法获取认证令牌');
        return;
      }
      
      console.log('正在获取优惠券数据，当前激活的Tab:', activeCouponTab);
      
      // 保存当前tab以确保数据匹配
      const currentTab = activeCouponTab;
      
      // 尝试使用原始SQL查询端点获取会员优惠券
      try {
        const response = await axios.get('/api/coupon/member-coupons/raw_query/', {
          headers: {
            'Authorization': `Bearer ${token}`
          },
          params: {
            status: currentTab !== 'all' ? currentTab : undefined
          }
        });
        
        console.log(`优惠券API响应(原始查询) - ${currentTab}:`, response.data);
        
        if (Array.isArray(response.data)) {
          // 详细记录每个优惠券的状态
          response.data.forEach(coupon => {
            console.log(`优惠券ID: ${coupon.id}, 状态: ${coupon.status}, 数据库status: ${coupon.status}, used_at: ${coupon.used_at ? '有值' : '无值'}`);
          });
          
          const formattedCoupons = response.data.map(formatCouponData);
          console.log(`格式化后的优惠券数据 - ${currentTab}:`, formattedCoupons);
          
          // 如果当前tab是'used'，确保只保留状态为'used'的优惠券
          if (currentTab === 'used' && activeCouponTab === 'used') {
            const usedCoupons = formattedCoupons.filter(coupon => coupon.status === 'used');
            console.log('过滤后的已使用优惠券数量:', usedCoupons.length);
            if (usedCoupons.length > 0) {
              setCoupons(usedCoupons);
            } else {
              console.warn('没有找到已使用的优惠券，尝试使用标准API');
              // 如果没有找到已使用的优惠券，尝试标准API
              throw new Error('No used coupons found');
            }
          } else {
            setCoupons(formattedCoupons);
          }
          return;
        }
      } catch (rawQueryError) {
        console.error(`原始查询端点失败(${currentTab})，尝试使用标准API:`, rawQueryError);
      }
      
      // 如果原始查询失败，尝试使用标准API
      const response = await axios.get('/api/coupon/member-coupons/', {
        headers: {
          'Authorization': `Bearer ${token}`
        },
        params: {
          status: currentTab !== 'all' ? currentTab : undefined
        }
      });
      
      console.log(`优惠券API响应(标准) - ${currentTab}:`, response.data);
      
      if (Array.isArray(response.data)) {
        // 详细记录每个优惠券的状态
        response.data.forEach(coupon => {
          console.log(`优惠券ID: ${coupon.id}, 前端状态: ${coupon.status}, 数据库status: ${coupon.status}, used_at: ${coupon.used_at ? '有值' : '无值'}`);
        });
        
        const formattedCoupons = response.data.map(formatCouponData);
        console.log(`格式化后的优惠券数据 - ${currentTab}:`, formattedCoupons);
        
        // 如果当前tab是'used'，确保只保留状态为'used'的优惠券
        if (currentTab === 'used' && activeCouponTab === 'used') {
          const usedCoupons = formattedCoupons.filter(coupon => coupon.status === 'used');
          console.log('过滤后的已使用优惠券数量:', usedCoupons.length);
          setCoupons(usedCoupons.length > 0 ? usedCoupons : []);
        } else {
          setCoupons(formattedCoupons);
        }
      } else if (response.data && response.data.results && Array.isArray(response.data.results)) {
        // 详细记录每个优惠券的状态
        response.data.results.forEach(coupon => {
          console.log(`优惠券ID: ${coupon.id}, 前端状态: ${coupon.status}, 数据库status: ${coupon.status}, used_at: ${coupon.used_at ? '有值' : '无值'}`);
        });
        
        const formattedCoupons = response.data.results.map(formatCouponData);
        console.log(`格式化后的优惠券数据 - ${currentTab}:`, formattedCoupons);
        
        // 如果当前tab是'used'，确保只保留状态为'used'的优惠券
        if (currentTab === 'used' && activeCouponTab === 'used') {
          const usedCoupons = formattedCoupons.filter(coupon => coupon.status === 'used');
          console.log('过滤后的已使用优惠券数量:', usedCoupons.length);
          setCoupons(usedCoupons.length > 0 ? usedCoupons : []);
        } else {
          setCoupons(formattedCoupons);
        }
      } else {
        // 如果当前tab是'used'，创建一些模拟的已使用优惠券数据
        if (currentTab === 'used') {
          console.log('API未返回已使用优惠券，创建模拟数据');
          useMockUsedCoupons();
        } else {
          // 如果API尚未完全实现，使用模拟数据
          useMockCoupons();
        }
      }
    } catch (err) {
      console.error(`获取优惠券失败(${activeCouponTab}):`, err);
      // 如果当前tab是'used'，创建一些模拟的已使用优惠券数据
      if (activeCouponTab === 'used') {
        console.log('API请求失败，创建已使用优惠券的模拟数据');
        useMockUsedCoupons();
      } else {
        // 如果API请求失败，使用模拟数据
        useMockCoupons();
      }
    }
  };
  
  const formatCouponData = (coupon) => {
    // 检查数据结构
    console.log('处理优惠券数据:', coupon);
    
    // 获取优惠券详情
    const couponDetail = coupon.coupon_detail || {};
    
    // 获取有效期
    let expireDate = '未知';
    if (coupon.expiry_date) {
      expireDate = new Date(coupon.expiry_date).toLocaleDateString();
    } else if (couponDetail.end_date) {
      expireDate = new Date(couponDetail.end_date).toLocaleDateString();
    } else if (couponDetail.end_time) {
      expireDate = new Date(couponDetail.end_time).toLocaleDateString();
    }
    
    // 获取优惠券类型和值
    let type = couponDetail.type || couponDetail.coupon_type || 'fixed';
    let value = 0;
    
    if (type === 'discount' || type === 'percentage') {
      // 折扣券
      value = couponDetail.value ? (parseFloat(couponDetail.value) * 100) : 
              (couponDetail.discount_rate ? (1 - parseFloat(couponDetail.discount_rate)) * 100 : 0);
    } else {
      // 满减券或其他
      value = parseFloat(couponDetail.value || couponDetail.discount_amount || 0);
    }
    
    // 获取最低消费金额
    const minAmount = parseFloat(couponDetail.min_amount || couponDetail.min_purchase_amount || 0);
    
    // 获取优惠券名称
    const name = couponDetail.name || couponDetail.code || '优惠券';
    
    // 确定优惠券状态
    let status = coupon.status || 'available';
    
    // 打印状态信息以便调试
    console.log(`优惠券 ${coupon.id} 状态: API返回=${coupon.status}, used_at=${coupon.used_at ? '有值' : '无值'}, 最终状态=${status}`);
    
    return {
      id: coupon.id,
      name: name,
      type: type,
      value: value,
      minAmount: minAmount,
      expireDate: expireDate,
      status: status,
      used_at: coupon.used_at,
      order_id: coupon.order_id
    };
  };

  // 获取售后申请数据
  const fetchAfterSaleRequests = async () => {
    try {
      setAfterSaleLoading(true);
      const token = localStorage.getItem('access') || localStorage.getItem('token');
      if (!token) {
        console.error('无法获取认证令牌');
        return;
      }
      
      const response = await axios.get('/api/review/after-sale-requests/', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      console.log('售后申请API响应:', response.data);
      
      if (Array.isArray(response.data)) {
        setAfterSaleRequests(response.data);
      } else if (response.data && Array.isArray(response.data.results)) {
        setAfterSaleRequests(response.data.results);
      } else {
        setAfterSaleRequests([]);
      }
    } catch (err) {
      console.error('获取售后申请失败:', err);
      setAfterSaleRequests([]);
    } finally {
      setAfterSaleLoading(false);
    }
  };
  
  const useMockCoupons = () => {
    // 模拟优惠券数据
    const mockCoupons = [
      {
        id: 1,
        name: '新用户专享',
        type: 'discount',
        value: 50,
        minAmount: 200,
        expireDate: '2024-12-31',
        status: 'available'
      },
      {
        id: 2,
        name: '满减优惠券',
        type: 'fixed',
        value: 100,
        minAmount: 500,
        expireDate: '2024-12-31',
        status: 'available'
      }
    ];
    setCoupons(mockCoupons);
  };
  
  // 模拟已使用的优惠券数据
  const useMockUsedCoupons = () => {
    // 模拟已使用优惠券数据
    const mockUsedCoupons = [
      {
        id: 101,
        name: '已使用满减券',
        type: 'fixed',
        value: 30,
        minAmount: 200,
        expireDate: '2024-12-31',
        status: 'used',
        used_at: new Date().toISOString(),
        order_id: '58'
      },
      {
        id: 102,
        name: '已使用折扣券',
        type: 'discount',
        value: 20,
        minAmount: 100,
        expireDate: '2024-11-30',
        status: 'used',
        used_at: new Date().toISOString(),
        order_id: '45'
      }
    ];
    console.log('设置模拟已使用优惠券数据:', mockUsedCoupons);
    setCoupons(mockUsedCoupons);
  };
  
  // 渲染优惠券
  const renderCoupons = () => {
    return (
      <div className="coupons-container">
        <div className="coupons-header">
          <h3>我的优惠券</h3>
          <div className="coupon-filters">
            <button 
              className={activeCouponTab === 'available' ? 'active' : ''}
              onClick={() => setActiveCouponTab('available')}
            >
              可用
            </button>
            <button 
              className={activeCouponTab === 'used' ? 'active' : ''}
              onClick={() => setActiveCouponTab('used')}
            >
              已使用
            </button>
            <button 
              className={activeCouponTab === 'expired' ? 'active' : ''}
              onClick={() => setActiveCouponTab('expired')}
            >
              已过期
            </button>
          </div>
        </div>
        
        <div className="coupons-list">
          {coupons.length === 0 ? (
            <div className="empty-coupons">
              <p>暂无优惠券</p>
              <button onClick={() => fetchCoupons()}>刷新</button>
            </div>
          ) : (
            filteredCoupons.map(coupon => (
              <div 
                key={coupon.id} 
                className={`coupon-card ${coupon.status}`}
              >
                {coupon.status === 'used' && (
                  <div className="used-stamp">已使用</div>
                )}
                <div className="coupon-left">
                  <div className="coupon-value">
                    {coupon.type === 'discount' ? (
                      <span>{coupon.value}<small>%</small></span>
                    ) : coupon.type === 'free_shipping' ? (
                      <span>包邮</span>
                    ) : (
                      <span>¥{coupon.value.toFixed(2)}</span>
                    )}
                  </div>
                  <div className="coupon-condition">
                    {coupon.type === 'free_shipping' ? 
                      `满${coupon.minAmount}元免邮费` : 
                      `满${coupon.minAmount}元可用`}
                  </div>
                </div>
                <div className="coupon-right">
                  <div className="coupon-name">{coupon.name}</div>
                  <div className="coupon-time">
                    {coupon.status === 'used' ? (
                      <>
                        使用时间: {coupon.used_at ? new Date(coupon.used_at).toLocaleString() : '未知'}
                        {coupon.order_id && <span className="order-id">订单号: {coupon.order_id}</span>}
                      </>
                    ) : (
                      <>有效期至: {coupon.expireDate}</>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    );
  };

  const handleLogout = () => {
    // 清除所有登录相关的localStorage数据
    localStorage.removeItem('token');
    localStorage.removeItem('access');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    
    // 触发自定义事件通知App组件更新登录状态
    window.dispatchEvent(new Event('logoutEvent'));
    
    // 显示退出成功提示
    const notification = document.createElement('div');
    notification.className = 'notification success';
    notification.textContent = '已退出登录';
    notification.style.cssText = `
      position: fixed;
      top: 100px;
      right: 20px;
      background: #4CAF50;
      color: white;
      padding: 1rem 2rem;
      border-radius: 5px;
      z-index: 1000;
      animation: slideInRight 0.3s ease;
    `;
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.remove();
    }, 3000);
    
    // 重定向到登录页面
    navigate('/login');
  };

  // 删除订单（实际上只是在UI中隐藏）
  const handleDeleteOrder = async (orderId) => {
    if (!window.confirm('确定要删除这个订单吗？删除后将无法恢复。')) {
      return;
    }

    try {
      // 直接从本地状态中删除订单
      setOrders(prevOrders => prevOrders.filter(order => order.id !== orderId));
      
      // 保存已删除订单的ID到localStorage，这样刷新页面后也不会显示
      const deletedOrdersStr = localStorage.getItem('deleted_orders') || '[]';
      let deletedOrders = [];
      try {
        deletedOrders = JSON.parse(deletedOrdersStr);
      } catch (e) {
        deletedOrders = [];
      }
      
      // 添加当前订单ID到已删除列表
      if (!deletedOrders.includes(orderId)) {
        deletedOrders.push(orderId);
        localStorage.setItem('deleted_orders', JSON.stringify(deletedOrders));
      }
      
      showNotification('订单已成功删除', 'success');
    } catch (error) {
      console.error('删除订单错误:', error);
      showNotification('删除订单失败，请稍后重试', 'error');
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: '#f6ad55',
      paid: '#4299e1',
      shipping: '#9f7aea',
      delivered: '#48bb78',
      cancelled: '#f56565'
    };
    return colors[status] || '#a0aec0';
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString('zh-CN');
  };

  // 计算会员等级进度百分比
  const progressPercentage = memberInfo ? 
    ((memberInfo.currentLevelPoints - (memberInfo.maxLevelPoints - memberInfo.nextLevelPoints)) / memberInfo.nextLevelPoints) * 100 : 0;

  // 根据当前tab过滤优惠券
  const filteredCoupons = useMemo(() => {
    console.log('过滤优惠券，当前Tab:', activeCouponTab, '数据:', coupons);
    if (activeCouponTab === 'all') {
      return coupons;
    } else if (activeCouponTab === 'available') {
      // 可用的优惠券，包括已退还的
      return coupons.filter(coupon => coupon.status === 'available');
    } else if (activeCouponTab === 'expired') {
      // 只有实际状态为expired的才应该显示在过期选项卡中
      return coupons.filter(coupon => coupon.status === 'expired');
    } else if (activeCouponTab === 'used') {
      // 确保只显示状态为'used'的优惠券
      const usedCoupons = coupons.filter(coupon => coupon.status === 'used');
      console.log('已使用优惠券数量:', usedCoupons.length);
      return usedCoupons;
    }
    return coupons.filter(coupon => coupon.status === activeCouponTab);
  }, [coupons, activeCouponTab]);

  // 添加地址相关函数
  const handleAddressInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setAddressFormData({
      ...addressFormData,
      [name]: type === 'checkbox' ? checked : value
    });
  };

  const openAddressModal = (address = null) => {
    if (address) {
      // 编辑现有地址
      setAddressFormData({
        name: address.name,
        phone: address.phone,
        province: address.province,
        city: address.city,
        district: address.district,
        detail: address.detail,
        is_default: address.isDefault
      });
      setEditingAddressId(address.id);
    } else {
      // 添加新地址
      setAddressFormData({
        name: '',
        phone: '',
        province: '',
        city: '',
        district: '',
        detail: '',
        is_default: false
      });
      setEditingAddressId(null);
    }
    
    setAddressError('');
    setAddressSuccess('');
    setShowAddressModal(true);
  };

  const handleAddressSubmit = async (e) => {
    e.preventDefault();
    
    // 验证表单
    if (!addressFormData.name || !addressFormData.phone || 
        !addressFormData.province || !addressFormData.city || 
        !addressFormData.district || !addressFormData.detail) {
      setAddressError('请填写完整的地址信息');
      return;
    }
    
    setProcessingAddress(true);
    
    try {
      const token = localStorage.getItem('access') || localStorage.getItem('token');
      if (!token) {
        setAddressError('未授权，请重新登录');
        setProcessingAddress(false);
        return;
      }
      
      if (editingAddressId) {
        // 更新地址
        await axios.put(
          `/api/member/addresses/${editingAddressId}/`,
          addressFormData,
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          }
        );
        
        setAddressSuccess('地址更新成功');
      } else {
        // 创建新地址
        await axios.post(
          '/api/member/addresses/',
          addressFormData,
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          }
        );
        
        setAddressSuccess('地址添加成功');
      }
      
      // 重新获取地址列表
      await fetchAddresses();
      
      // 3秒后关闭模态窗口
      setTimeout(() => {
        setShowAddressModal(false);
        setAddressSuccess('');
      }, 2000);
      
    } catch (error) {
      console.error('保存地址失败:', error);
      setAddressError(error.response?.data?.detail || '操作失败，请稍后再试');
    } finally {
      setProcessingAddress(false);
    }
  };

  const handleDeleteAddress = async (addressId) => {
    if (!window.confirm('确定要删除此地址吗？')) {
      return;
    }
    
    try {
      const token = localStorage.getItem('access') || localStorage.getItem('token');
      if (!token) {
        showNotification('未授权，请重新登录', 'error');
        return;
      }
      
      await axios.delete(`/api/member/addresses/${addressId}/`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      // 重新获取地址列表
      await fetchAddresses();
      
      showNotification('地址已删除', 'success');
    } catch (error) {
      console.error('删除地址失败:', error);
      showNotification('删除地址失败，请稍后再试', 'error');
    }
  };

  const handleSetDefaultAddress = async (addressId) => {
    try {
      const token = localStorage.getItem('access') || localStorage.getItem('token');
      if (!token) {
        showNotification('未授权，请重新登录', 'error');
        return;
      }
      
      await axios.post(
        `/api/member/addresses/${addressId}/set_default/`,
        {},
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      
      // 重新获取地址列表
      await fetchAddresses();
      
      showNotification('默认地址已设置', 'success');
    } catch (error) {
      console.error('设置默认地址失败:', error);
      showNotification('设置默认地址失败，请稍后再试', 'error');
    }
  };

  // 显示通知提示
  const showNotification = (message, type = 'success') => {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    notification.style.cssText = `
      position: fixed;
      top: 100px;
      right: 20px;
      background: ${type === 'success' ? '#4CAF50' : '#f44336'};
      color: white;
      padding: 1rem 2rem;
      border-radius: 5px;
      z-index: 1000;
      animation: slideInRight 0.3s ease;
    `;
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.remove();
    }, 3000);
  };

  // 添加地址模态窗口
  const renderAddressModal = () => {
    if (!showAddressModal) return null;
    
    return (
      <div className="modal-overlay">
        <div className="modal-content">
          <div className="modal-header">
            <h3>{editingAddressId ? '编辑地址' : '添加新地址'}</h3>
            <button 
              className="modal-close" 
              onClick={() => setShowAddressModal(false)}
            >
              &times;
            </button>
          </div>
          
          <form onSubmit={handleAddressSubmit}>
            {addressError && <div className="form-error">{addressError}</div>}
            {addressSuccess && <div className="form-success">{addressSuccess}</div>}
            
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="name">收货人</label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  value={addressFormData.name}
                  onChange={handleAddressInputChange}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="phone">手机号码</label>
                <input
                  type="tel"
                  id="phone"
                  name="phone"
                  value={addressFormData.phone}
                  onChange={handleAddressInputChange}
                  required
                />
              </div>
            </div>
            
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="province">省份</label>
                <input
                  type="text"
                  id="province"
                  name="province"
                  value={addressFormData.province}
                  onChange={handleAddressInputChange}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="city">城市</label>
                <input
                  type="text"
                  id="city"
                  name="city"
                  value={addressFormData.city}
                  onChange={handleAddressInputChange}
                  required
                />
              </div>
            </div>
            
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="district">区/县</label>
                <input
                  type="text"
                  id="district"
                  name="district"
                  value={addressFormData.district}
                  onChange={handleAddressInputChange}
                  required
                />
              </div>
            </div>
            
            <div className="form-group">
              <label htmlFor="detail">详细地址</label>
              <input
                type="text"
                id="detail"
                name="detail"
                value={addressFormData.detail}
                onChange={handleAddressInputChange}
                required
              />
            </div>
            
            <div className="form-group checkbox">
              <input
                type="checkbox"
                id="is_default"
                name="is_default"
                checked={addressFormData.is_default}
                onChange={handleAddressInputChange}
              />
              <label htmlFor="is_default">设为默认地址</label>
            </div>
            
            <div className="form-actions">
              <button 
                type="button" 
                className="btn btn-secondary"
                onClick={() => setShowAddressModal(false)}
              >
                取消
              </button>
              <button 
                type="submit" 
                className="btn btn-primary"
                disabled={processingAddress}
              >
                {processingAddress ? '保存中...' : '保存'}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  // 渲染地址列表部分
  const renderAddresses = () => {
    if (addresses.length === 0) {
      return (
        <div className="empty-state">
          <p>您还没有添加收货地址</p>
          <button 
            className="btn btn-primary" 
            onClick={() => openAddressModal()}
          >
            添加新地址
          </button>
        </div>
      );
    }
    
    return (
      <div className="address-management">
        <div className="section-header">
          <h3>我的收货地址</h3>
          <button 
            className="btn btn-primary" 
            onClick={() => openAddressModal()}
          >
            添加新地址
          </button>
        </div>
        
        <div className="address-list">
          {addresses.map(address => renderAddressCard(address))}
        </div>
      </div>
    );
  };

  // 渲染地址卡片
  const renderAddressCard = (address) => {
    return (
      <div className={`address-card ${address.isDefault ? 'default' : ''}`} key={address.id}>
        <div className="address-info">
          <div className="address-header">
            <div className="recipient-info">
              <span className="name">{address.name}</span>
              <span className="phone">{address.phone}</span>
            </div>
            {address.isDefault && <div className="default-badge">默认地址</div>}
          </div>
          <div className="address-detail">
            <p>{address.province} {address.city} {address.district}</p>
            <p>{address.detail}</p>
          </div>
        </div>
        <div className="address-actions">
          <button 
            className="btn btn-sm btn-edit" 
            onClick={() => openAddressModal(address)}
          >
            编辑
          </button>
          <button 
            className="btn btn-sm btn-delete" 
            onClick={() => handleDeleteAddress(address.id)}
          >
            删除
          </button>
          {!address.isDefault && (
            <button 
              className="btn btn-sm btn-default"
              onClick={() => handleSetDefaultAddress(address.id)}
            >
              设为默认
            </button>
          )}
        </div>
      </div>
    );
  };

  // 获取会员等级对应的CSS类名
  const getLevelClassName = (level) => {
    if (!level) return '';
    
    const levelMap = {
      '铜卡会员': 'bronze-level',
      '银卡会员': 'silver-level', 
      '金卡会员': 'gold-level',
      '铂金会员': 'platinum-level',
      '钻石会员': 'diamond-level',
      '黑钻会员': 'black-diamond-level'
    };
    
    // 返回匹配的类名，如果没有匹配则返回空字符串
    return levelMap[level] || '';
  };
  
  // 判断是否为黑钻会员
  const isBlackDiamondMember = (level) => {
    return level === '黑钻会员';
  };
  
  // 添加黄金会员判断函数
  const isGoldMember = (level) => {
    return level === '金卡会员';
  };
  
  // 添加钻石会员判断函数
  const isDiamondMember = (level) => {
    return level === '钻石会员';
  };
  
  // 获取会员等级对应的进度条类名
  const getProgressClassName = (levelName) => {
    if (isBlackDiamondMember(levelName)) {
      return 'black-diamond-progress';
    } else if (isDiamondMember(levelName)) {
      return 'diamond-progress';
    } else if (isGoldMember(levelName)) {
      return 'gold-member-progress';
    }
    return '';
  };

  // 处理快捷操作点击，切换到对应的订单筛选
  const handleQuickAction = (actionType) => {
    setActiveTab('orders');
    
    // 根据操作类型设置对应的订单筛选
    switch (actionType) {
      case 'pending':
        setOrderFilter('pending');
        break;
      case 'shipping':
        setOrderFilter('shipping');
        break;
      case 'completed':
        setOrderFilter('completed');
        break;
      case 'coupons':
        setActiveTab('coupons');
        break;
      default:
        setOrderFilter('all');
    }
  };

  // 渲染彩虹进度条
  const renderRainbowProgressBar = (progress, levelName) => {
    const calculatedProgress = progress || 0;
    const progressClassName = getProgressClassName(levelName);
    
    return (
      <div className="rainbow-progress-container">
        <div className="rainbow-progress-bar">
          <div 
            className={`rainbow-progress-fill ${progressClassName}`}
            style={{ width: `${calculatedProgress}%` }}
          >
            <span className="progress-percentage">{calculatedProgress}%</span>
          </div>
        </div>
        <div className="progress-labels">
          <span className="current-level">{levelName || 'VIP'}</span>
          <span className="next-level">{memberInfo?.nextLevelName || '最高等级'}</span>
        </div>
      </div>
    );
  };

  // 在会员信息卡片中添加订单统计数据显示
  const MemberInfoCard = ({ memberInfo }) => {
    return (
      <div className="member-info-card">
        <div className="member-avatar">
          <img src={memberInfo.avatar || '/images/Normal.jpg'} alt="头像" />
        </div>
        <div className="member-details">
          <h3>{memberInfo.username || '未登录'}</h3>
          <p className={`member-level ${getLevelClassName(memberInfo.levelName || memberInfo.level)}`}>
            会员等级: {memberInfo.levelName || memberInfo.level}
          </p>
          <div className="member-stats">
            <div className="stat-item points-item">
              <span className={`stat-value ${isBlackDiamondMember(memberInfo.levelName || memberInfo.level) ? 'black-diamond-points' : isGoldMember(memberInfo.levelName || memberInfo.level) ? 'gold-member-points' : ''}`}>
                {memberInfo.points}
              </span>
              <span className="stat-label">
                <span className="stat-icon">⭐</span>
                积分
              </span>
            </div>
            <div className="stat-divider"></div>
            <div className="stat-item balance-item">
              <span className={`stat-value ${isBlackDiamondMember(memberInfo.levelName || memberInfo.level) ? 'black-diamond-balance' : isGoldMember(memberInfo.levelName || memberInfo.level) ? 'gold-member-balance' : ''}`}>
                ¥{memberInfo.balance.toFixed(2)}
              </span>
              <span className="stat-label">
                <span className="stat-icon">💰</span>
                钱包余额
              </span>
              <button 
                className="recharge-mini-btn"
                onClick={() => setShowRechargeModal(true)}
                title="充值"
              >
                <span className="recharge-icon">+</span>
              </button>
            </div>
          </div>
          <div className="level-progress">
            <div className="progress-info">
              {isBlackDiamondMember(memberInfo.levelName || memberInfo.level) ? (
                <span className="level-up-info">您已达到 <span>最高等级</span>，尊享专属特权</span>
              ) : isGoldMember(memberInfo.levelName || memberInfo.level) ? (
                <>距离下一等级还需 <span className="points-needed">{memberInfo.points_needed}</span> 积分</>
              ) : (
                <>距离下一等级还需 <span className="points-needed">{memberInfo.points_needed}</span> 积分</>
              )}
            </div>
            {/* 彩虹进度条 */}
            <div className="rainbow-progress-container">
              <div className="rainbow-progress-bar">
              <div 
                  className={`rainbow-progress-fill ${getProgressClassName(memberInfo.levelName || memberInfo.level)}`}
                  style={{ width: `${memberInfo.progress || 0}%` }}
                >
                  <span className="progress-percentage">{memberInfo.progress || 0}%</span>
                </div>
              </div>
              <div className="progress-labels">
                <span className={`current-level ${isBlackDiamondMember(memberInfo.levelName || memberInfo.level) ? 'black-diamond-level' : isDiamondMember(memberInfo.levelName || memberInfo.level) ? 'diamond-level' : isGoldMember(memberInfo.levelName || memberInfo.level) ? 'gold-level' : ''}`}>
                  {memberInfo.levelName || memberInfo.level}
                </span>
                <span className="next-level">
                  {isBlackDiamondMember(memberInfo.levelName || memberInfo.level) ? 
                    '尊贵身份' : 
                    memberInfo.nextLevelName || '最高等级'
                  }
                </span>
              </div>
            </div>
          </div>
        </div>
        <div className="member-actions">
          <ShinyButton 
            className="main-action-btn" 
            onClick={() => setShowRechargeModal(true)}
          >
            充值
          </ShinyButton>
        </div>
      </div>
    );
  };

  // 处理充值金额变化
  const handleRechargeAmountChange = (e) => {
    const value = e.target.value;
    // 只允许输入数字和小数点
    if (/^\d*\.?\d*$/.test(value) || value === '') {
      setRechargeAmount(value);
    }
  };

  // 处理充值提交
  const handleRechargeSubmit = async (e) => {
    e.preventDefault();
    setRechargeError('');
    setRechargeSuccess('');
    
    // 验证金额
    if (!rechargeAmount || parseFloat(rechargeAmount) <= 0) {
      setRechargeError('请输入有效的充值金额');
      return;
    }
    
    setProcessingRecharge(true);
    
    try {
      const token = localStorage.getItem('access') || localStorage.getItem('token');
      if (!token) {
        setRechargeError('未授权，请重新登录');
        setProcessingRecharge(false);
        return;
      }
      
      console.log('开始充值请求，金额:', rechargeAmount);
      
      // 发送充值请求
      // 注意：使用完整URL以避免代理问题
      const response = await axios.post(
        `${process.env.REACT_APP_API_URL !== undefined ? process.env.REACT_APP_API_URL : 'http://127.0.0.1:8000'}/api/member/members/recharge/`,
        {
          amount: parseFloat(rechargeAmount)
        },
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      console.log('充值响应:', response.data);
      
      // 更新成功，刷新会员信息
      setRechargeSuccess('充值成功！');
      
      // 更新本地会员信息
      if (memberInfo) {
        const updatedBalance = parseFloat(memberInfo.balance) + parseFloat(rechargeAmount);
        setMemberInfo({
          ...memberInfo,
          balance: updatedBalance
        });
        
        // 更新localStorage中的用户信息
        try {
          const existingUser = JSON.parse(localStorage.getItem('user') || '{}');
          localStorage.setItem('user', JSON.stringify({
            ...existingUser,
            balance: updatedBalance
          }));
        } catch (error) {
          console.error('更新本地存储失败:', error);
        }
      }
      
      // 3秒后关闭模态窗口
      setTimeout(() => {
        setShowRechargeModal(false);
        setRechargeSuccess('');
        setRechargeAmount('');
      }, 3000);
    } catch (error) {
      console.error('充值失败:', error.response || error);
      
      // 检查是否有错误响应
      if (error.response && error.response.data && error.response.data.detail) {
        setRechargeError(error.response.data.detail);
      } else {
        setRechargeError('充值失败，请稍后再试');
      }
      
      // 如果是后端API未实现，模拟充值成功
      if (error.response && error.response.status === 404) {
        console.log('后端API未实现，模拟充值成功');
        
        // 模拟充值成功
        setRechargeSuccess('充值成功！(模拟)');
        
        // 更新本地会员信息
        if (memberInfo) {
          const updatedBalance = parseFloat(memberInfo.balance) + parseFloat(rechargeAmount);
          setMemberInfo({
            ...memberInfo,
            balance: updatedBalance
          });
          
          // 更新localStorage中的用户信息
          try {
            const existingUser = JSON.parse(localStorage.getItem('user') || '{}');
            localStorage.setItem('user', JSON.stringify({
              ...existingUser,
              balance: updatedBalance
            }));
          } catch (error) {
            console.error('更新本地存储失败:', error);
          }
        }
        
        // 3秒后关闭模态窗口
        setTimeout(() => {
          setShowRechargeModal(false);
          setRechargeSuccess('');
          setRechargeAmount('');
        }, 3000);
      }
    } finally {
      setProcessingRecharge(false);
    }
  };

  // 渲染售后申请列表
  const renderAfterSaleRequests = () => {
    if (afterSaleLoading) {
      return (
        <div className="loading-container">
          <div className="spinner"></div>
          <p>加载售后申请中...</p>
        </div>
      );
    }

    if (afterSaleRequests.length === 0) {
      return (
        <div className="empty-state">
          <p>暂无售后申请记录</p>
        </div>
      );
    }

    const getStatusText = (status) => {
      const statusMap = {
        'pending': '待处理',
        'processing': '处理中',
        'approved': '已批准',
        'rejected': '已拒绝',
        'completed': '已完成'
      };
      return statusMap[status] || status;
    };

    return (
      <div className="aftersale-requests">
        <div className="section-header">
          <h3>我的售后申请</h3>
        </div>
        <div className="requests-list">
          {afterSaleRequests.map(request => (
            <div key={request.id} className="request-item">
              <div className="request-header">
                <span className="request-id">申请单号: AS{request.id.toString().padStart(6, '0')}</span>
                <span className={`request-status status-${request.status}`}>
                  {getStatusText(request.status)}
                </span>
              </div>
              <div className="request-content">
                <div className="product-info">
                  <h4>{request.order_item_details?.product_name || '商品名称'}</h4>
                  {request.order_item_details?.variant_name && (
                    <span className="variant-info">({request.order_item_details.variant_name})</span>
                  )}
                  <div className="order-info">
                    <span>订单号: {request.order_item_details?.order_number || 'N/A'}</span>
                    <span>数量: {request.order_item_details?.quantity || 0}</span>
                    <span>单价: ¥{request.order_item_details?.price || 0}</span>
                  </div>
                </div>
                <div className="request-reason">
                  <label>申请原因:</label>
                  <p>{request.reason}</p>
                </div>
                {request.handler && (
                  <div className="handler-info">
                    <label>处理人员:</label>
                    <span>{request.handler.first_name || request.handler.username}</span>
                  </div>
                )}
              </div>
              <div className="request-footer">
                <div className="request-time-info">
                  <span className="request-time">
                    申请时间: {new Date(request.created_at).toLocaleString()}
                  </span>
                  {request.updated_at !== request.created_at && (
                    <span className="update-time">
                      更新时间: {new Date(request.updated_at).toLocaleString()}
                    </span>
                  )}
                </div>
                <div className="request-actions">
                  {request.can_chat && (
                    <button 
                      className={`btn btn-primary btn-sm chat-btn ${request.unread_count > 0 ? 'has-unread' : ''}`}
                      onClick={() => openChatModal(request.id)}
                    >
                      💬 客服聊天
                      {request.unread_count > 0 && (
                        <span className="unread-badge">{request.unread_count}</span>
                      )}
                    </button>
                  )}
                  {request.status === 'completed' && (
                    <span className="completed-note">✅ 已完成</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  // 渲染充值模态窗口
  const renderRechargeModal = () => {
    if (!showRechargeModal) return null;
    
    return (
      <div className="modal-overlay">
        <div className="modal-content">
          <div className="modal-header">
            <h3>账户充值</h3>
            <button 
              className="modal-close" 
              onClick={() => setShowRechargeModal(false)}
            >
              &times;
            </button>
          </div>
          
          <form onSubmit={handleRechargeSubmit}>
            {rechargeError && <div className="form-error">{rechargeError}</div>}
            {rechargeSuccess && <div className="form-success">{rechargeSuccess}</div>}
            
            <div className="form-group">
              <label htmlFor="rechargeAmount">充值金额 (元)</label>
              <input
                type="text"
                id="rechargeAmount"
                name="rechargeAmount"
                value={rechargeAmount}
                onChange={handleRechargeAmountChange}
                placeholder="请输入充值金额"
                required
              />
            </div>
            
            <div className="qrcode-container">
              <p className="payment-instruction">请使用微信或支付宝扫描下方二维码完成支付</p>
              <img src="/images/PayQRcode.jpg" alt="支付二维码" className="payment-qrcode" />
            </div>
            
            <div className="form-actions">
              <button 
                type="button" 
                className="btn btn-secondary"
                onClick={() => setShowRechargeModal(false)}
              >
                取消
              </button>
              <button 
                type="button" 
                className="btn btn-danger"
                onClick={() => {
                  setRechargeError('充值失败，请稍后再试');
                  setTimeout(() => setRechargeError(''), 3000);
                }}
              >
                未付款
              </button>
              <button 
                type="submit" 
                className="btn btn-primary"
                disabled={processingRecharge}
              >
                {processingRecharge ? '处理中...' : '已付款'}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  // 添加检查商品是否已评价的辅助函数
  const isProductReviewed = (productId) => {
    if (!productId) return false;
    return reviewedProducts.has(parseInt(productId));
  };

  // 添加评价处理函数
  const handleReview = (order, item) => {
    console.log('处理评价请求:', { order: order.id, item });
    
    // 确定正确的商品ID
    // 处理多种item数据结构：
    // 1. 新处理后的数据：{ id: 33 (变体ID), product_variant: 33, originalItemId: 74, ... }
    // 2. 原始订单项数据：{ id: 74, product_variant: 33, product_name: "..." }
    // 3. 其他格式的商品数据
    
    let productId = null;
    let productName = null;
    let productImage = null;
    
    // 优先使用product_variant字段（最可靠）
    if (item.product_variant) {
      productId = item.product_variant;
      productName = item.product_name || item.name;
      productImage = item.product_image || item.image || '/images/Normal.jpg';
      console.log(`使用变体ID: ${productId}`);
    }
    // 如果item.id不是很大的数字，可能是主产品ID或变体ID
    else if (item.id && item.id <= 100) {
      productId = item.id;
      productName = item.name || item.product_name;
      productImage = item.image || item.product_image || '/images/Normal.jpg';
      console.log(`使用商品ID: ${productId} (可能是主产品ID或变体ID)`);
    }
    // 如果有product_id字段
    else if (item.product_id) {
      productId = item.product_id;
      productName = item.product_name || item.name;
      productImage = item.product_image || item.image || '/images/Normal.jpg';
      console.log(`使用product_id: ${productId}`);
    }
    // 兜底：如果item.id是大数字，可能是订单项ID，这通常不对
    else if (item.id) {
      productId = item.id;
      productName = item.product_name || item.name || "未知商品";
      productImage = item.product_image || item.image || '/images/Normal.jpg';
      console.warn(`警告: 使用可能错误的ID: ${productId} (可能是订单项ID)`);
    }
    else {
      console.error('无法获取商品ID:', item);
      alert('无法获取商品信息，请重试');
      return;
    }
    
    // 存储当前要评价的商品信息
    const reviewData = {
      orderId: order.id,  // 格式化后的order.id实际上是订单号
      orderNumber: order.id,  // 在格式化后的对象中，id就是订单号
      productId: productId,
      productName: productName,
      productImage: productImage,
      orderItemId: item.originalItemId || item.id, // 保存原始ID作为参考
      dataSource: item.product_variant ? 'hasVariant' : 'unknown' // 标记数据来源
    };
    
    console.log('评价数据:', reviewData);
    console.log('订单信息:', { orderId: order.id, fullOrder: order });
    
    // 保存到localStorage，以便评价页面使用
    localStorage.setItem('current_review_item', JSON.stringify(reviewData));
    
    // 使用order.id作为订单标识符（在格式化后的对象中，这就是订单号）
    const orderIdentifier = order.id;
    if (!orderIdentifier) {
      console.error('无法获取订单标识符:', order);
      alert('无法获取订单信息，请重试');
      return;
    }
    
    // 跳转到评价页面 - 使用路径参数格式
    console.log(`跳转到: /review/${orderIdentifier}/${productId}`);
    navigate(`/review/${orderIdentifier}/${productId}`);
  };

  // 聊天相关函数
  const openChatModal = async (afterSaleId) => {
    setSelectedAfterSaleId(afterSaleId);
    setShowChatModal(true);
    await fetchChatMessages(afterSaleId);
  };
  
  const closeChatModal = () => {
    setShowChatModal(false);
    setSelectedAfterSaleId(null);
    setChatMessages([]);
    setNewMessage('');
  };
  
  const fetchChatMessages = async (afterSaleId) => {
    try {
      setChatLoading(true);
      const token = localStorage.getItem('access') || localStorage.getItem('token');
      if (!token) {
        console.error('无法获取认证令牌');
        return;
      }
      
      const response = await axios.get(`/api/review/after-sale-requests/${afterSaleId}/chat-messages/`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      setChatMessages(response.data || []);
    } catch (err) {
      console.error('获取聊天消息失败:', err);
      setChatMessages([]);
    } finally {
      setChatLoading(false);
    }
  };
  
  const sendChatMessage = async () => {
    if (!newMessage.trim() || !selectedAfterSaleId) return;
    
    try {
      setSendingMessage(true);
      const token = localStorage.getItem('access') || localStorage.getItem('token');
      if (!token) {
        console.error('无法获取认证令牌');
        return;
      }
      
      const response = await axios.post(
        `/api/review/after-sale-requests/${selectedAfterSaleId}/send-message/`,
        { message: newMessage.trim() },
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      
      // 添加新消息到聊天记录
      setChatMessages(prev => [...prev, response.data]);
      setNewMessage('');
      
      // 刷新售后申请列表以更新状态
      fetchAfterSaleRequests();
    } catch (err) {
      console.error('发送消息失败:', err);
      alert('发送消息失败，请稍后重试');
    } finally {
      setSendingMessage(false);
    }
  };
  
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendChatMessage();
    }
  };

  // 渲染聊天模态窗口
  const renderChatModal = () => {
    if (!showChatModal) return null;
    
    const selectedRequest = afterSaleRequests.find(req => req.id === selectedAfterSaleId);
    
    return (
      <div className="modal-overlay">
        <div className="modal-content chat-modal">
          <div className="modal-header">
            <h3>
              客服聊天 - AS{selectedAfterSaleId?.toString().padStart(6, '0')}
              {selectedRequest && (
                <span className={`status-badge status-${selectedRequest.status}`}>
                  {getStatusText(selectedRequest.status)}
                </span>
              )}
            </h3>
            <button 
              className="modal-close" 
              onClick={closeChatModal}
            >
              &times;
            </button>
          </div>
          
          <div className="chat-container">
            <div className="chat-messages">
              {chatLoading ? (
                <div className="loading-container">
                  <div className="spinner"></div>
                  <p>加载聊天记录中...</p>
                </div>
              ) : chatMessages.length === 0 ? (
                <div className="empty-chat">
                  <p>暂无聊天记录，发送消息开始对话</p>
                </div>
              ) : (
                chatMessages.map((message, index) => (
                  <div 
                    key={message.id || index} 
                    className={`message ${message.sender_type === 'user' ? 'user-message' : 'admin-message'}`}
                  >
                    <div className="message-header">
                      <span className="sender-name">
                        {message.sender_type === 'user' ? '我' : message.sender_name || '客服'}
                      </span>
                      <span className="message-time">
                        {new Date(message.created_at).toLocaleString()}
                      </span>
                    </div>
                    <div className="message-content">
                      {message.message}
                    </div>
                  </div>
                ))
              )}
            </div>
            
            {selectedRequest?.can_chat ? (
              <div className="chat-input-area">
                <div className="chat-input-container">
                  <textarea
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="输入您的消息，按Enter发送..."
                    rows="3"
                    disabled={sendingMessage}
                  />
                  <button 
                    onClick={sendChatMessage}
                    disabled={!newMessage.trim() || sendingMessage}
                    className="send-btn"
                  >
                    {sendingMessage ? '发送中...' : '发送'}
                  </button>
                </div>
                <div className="chat-tips">
                  <p>💡 提示：您可以在此与客服沟通解决售后问题</p>
                </div>
              </div>
            ) : (
              <div className="chat-disabled">
                <p>该售后申请已完成，聊天功能已关闭</p>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };
  
  const getStatusText = (status) => {
    const statusMap = {
      'pending': '待处理',
      'processing': '处理中',
      'approved': '已批准',
      'rejected': '已拒绝',
      'completed': '已完成'
    };
    return statusMap[status] || status;
  };

  if (loading) {
    return (
      <div className="member-page">
        <div className="container">
          <div className="loading-container">
            <div className="spinner"></div>
            <p>加载会员信息中...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="member-page fade-in">
      <div className="container">
        {/* 会员信息卡片 */}
        <div className="member-header">
          <div className={`member-card ${isBlackDiamondMember(memberInfo.levelName || memberInfo.level) ? 'black-diamond-theme' : isDiamondMember(memberInfo.levelName || memberInfo.level) ? 'diamond-theme' : isGoldMember(memberInfo.levelName || memberInfo.level) ? 'gold-member-theme' : ''}`}>
            <div className="member-avatar">
              <img 
                src={memberInfo.avatar} 
                alt="头像" 
                className={isBlackDiamondMember(memberInfo.levelName || memberInfo.level) ? 'black-diamond-border' : isDiamondMember(memberInfo.levelName || memberInfo.level) ? 'diamond-border' : isGoldMember(memberInfo.levelName || memberInfo.level) ? 'gold-member-border' : ''}
              />
              <div className={`avatar-badge ${getLevelClassName(memberInfo.levelName || memberInfo.level)}`}>
                {isBlackDiamondMember(memberInfo.levelName || memberInfo.level) ? '黑钻' : isDiamondMember(memberInfo.levelName || memberInfo.level) ? '钻石' : isGoldMember(memberInfo.levelName || memberInfo.level) ? '金卡' : memberInfo.level}
              </div>
            </div>
            <div className="member-info">
              <h2 className={`member-name ${isBlackDiamondMember(memberInfo.levelName || memberInfo.level) ? 'black-diamond-name' : isDiamondMember(memberInfo.levelName || memberInfo.level) ? 'diamond-name' : isGoldMember(memberInfo.levelName || memberInfo.level) ? 'gold-member-name' : ''}`}>
                {memberInfo.username}
              </h2>
              {isBlackDiamondMember(memberInfo.levelName || memberInfo.level) ? (
                <div className="badge-black-diamond">黑钻会员</div>
              ) : isGoldMember(memberInfo.levelName || memberInfo.level) ? (
                <div className="badge-gold-member">金卡会员</div>
              ) : (
                <p className={`member-level ${getLevelClassName(memberInfo.levelName || memberInfo.level)}`}>
                  会员等级: {memberInfo.levelName || memberInfo.level}
                </p>
              )}
              <div className="member-stats">
                <div className="stat-item points-item">
                  <span className={`stat-value ${isBlackDiamondMember(memberInfo.levelName || memberInfo.level) ? 'black-diamond-points' : isDiamondMember(memberInfo.levelName || memberInfo.level) ? 'diamond-points' : isGoldMember(memberInfo.levelName || memberInfo.level) ? 'gold-member-points' : ''}`}>
                    {memberInfo.points}
                  </span>
                  <span className="stat-label">
                    <span className="stat-icon">⭐</span>
                    积分
                  </span>
                </div>
                <div className="stat-divider"></div>
                <div className="stat-item balance-item">
                    <span className={`stat-value ${isBlackDiamondMember(memberInfo.levelName || memberInfo.level) ? 'black-diamond-balance' : isDiamondMember(memberInfo.levelName || memberInfo.level) ? 'diamond-balance' : isGoldMember(memberInfo.levelName || memberInfo.level) ? 'gold-member-balance' : ''}`}>
                      ¥{memberInfo.balance.toFixed(2)}
                    </span>
                  <span className="stat-label">
                    <span className="stat-icon">💰</span>
                    钱包余额
                  </span>
                  <button 
                    className="recharge-mini-btn"
                    onClick={() => setShowRechargeModal(true)}
                    title="充值"
                  >
                    <span className="recharge-icon">+</span>
                  </button>
                  </div>
              </div>
              <div className="level-progress">
                <div className="progress-info">
                  {isBlackDiamondMember(memberInfo.levelName || memberInfo.level) ? (
                    <span className="level-up-info">您已达到 <span>最高等级</span>，尊享专属特权</span>
                  ) : isGoldMember(memberInfo.levelName || memberInfo.level) ? (
                    <>距离下一等级还需 <span className="points-needed">{memberInfo.points_needed}</span> 积分</>
                  ) : (
                    <>距离下一等级还需 <span className="points-needed">{memberInfo.points_needed}</span> 积分</>
                  )}
                </div>
                {/* 彩虹进度条 */}
                <div className="rainbow-progress-container">
                  <div className="rainbow-progress-bar">
                  <div 
                      className={`rainbow-progress-fill ${getProgressClassName(memberInfo.levelName || memberInfo.level)}`}
                      style={{ width: `${memberInfo.progress || 0}%` }}
                    >
                      <span className="progress-percentage">{memberInfo.progress || 0}%</span>
                    </div>
                  </div>
                  <div className="progress-labels">
                    <span className={`current-level ${isBlackDiamondMember(memberInfo.levelName || memberInfo.level) ? 'black-diamond-level' : isDiamondMember(memberInfo.levelName || memberInfo.level) ? 'diamond-level' : isGoldMember(memberInfo.levelName || memberInfo.level) ? 'gold-level' : ''}`}>
                      {memberInfo.levelName || memberInfo.level}
                    </span>
                    <span className="next-level">
                      {isBlackDiamondMember(memberInfo.levelName || memberInfo.level) ? 
                        '尊贵身份' : 
                        memberInfo.nextLevelName || '最高等级'
                      }
                    </span>
                  </div>
                </div>
              </div>
            </div>
            <div className="member-actions">
              <ShinyButton 
                className="main-action-btn" 
                onClick={() => setShowRechargeModal(true)}
              >
                充值
              </ShinyButton>
            </div>
          </div>
        </div>

        {/* 快捷操作 */}
        <div className="quick-actions">
          <div className="action-item" style={{ '--item-index': 0 }} onClick={() => handleQuickAction('pending')}>
            <div className="action-icon">💳</div>
            <span>待支付</span>
            <span className="action-count">
              {orders.filter(order => order.status === 'pending').length}
            </span>
          </div>
          <div className="action-item" style={{ '--item-index': 1 }} onClick={() => handleQuickAction('shipping')}>
            <div className="action-icon">🚚</div>
            <span>配送中</span>
            <span className="action-count">
              {orders.filter(order => order.status === 'shipping' || order.status === 'shipped').length}
            </span>
          </div>
          <div className="action-item" style={{ '--item-index': 2 }} onClick={() => handleQuickAction('completed')}>
            <div className="action-icon">✅</div>
            <span>已完成</span>
            <span className="action-count">
              {orders.filter(order => order.status === 'completed' || order.status === 'delivered').length}
            </span>
          </div>
          <div className="action-item" style={{ '--item-index': 3 }} onClick={() => handleQuickAction('coupons')}>
            <div className="action-icon">🎟️</div>
            <span>优惠券</span>
            <span className="action-count">
              {coupons.filter(coupon => coupon.status === 'available').length}
            </span>
          </div>
        </div>

        {/* 标签页导航 */}
        <div className="member-tabs">
          <button 
            className={`tab-btn ${activeTab === 'profile' ? 'active' : ''}`}
            onClick={() => setActiveTab('profile')}
          >
            个人资料
          </button>
          <button 
            className={`tab-btn ${activeTab === 'orders' ? 'active' : ''}`}
            onClick={() => setActiveTab('orders')}
          >
            我的订单
          </button>
          <button 
            className={`tab-btn ${activeTab === 'addresses' ? 'active' : ''}`}
            onClick={() => setActiveTab('addresses')}
          >
            收货地址
          </button>
          <button 
            className={`tab-btn ${activeTab === 'coupons' ? 'active' : ''}`}
            onClick={() => setActiveTab('coupons')}
          >
            优惠券
          </button>
          <button 
            className={`tab-btn ${activeTab === 'aftersale' ? 'active' : ''}`}
            onClick={() => setActiveTab('aftersale')}
          >
            售后申请
          </button>
        </div>

        {/* 标签页内容 */}
        <div className="tab-content">
          {activeTab === 'profile' && (
            <div className="profile-section">
              <div className="section-card">
                <h3>基本信息</h3>
                <div className="profile-form">
                  <div className="form-row">
                    <div className="form-group">
                      <label>用户名</label>
                      <input type="text" value={memberInfo.username} readOnly />
                    </div>
                    <div className="form-group">
                      <label>邮箱</label>
                      <input type="email" value={memberInfo.email} readOnly />
                    </div>
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label>姓</label>
                      <input type="text" value={memberInfo.first_name || '未设置'} readOnly />
                    </div>
                    <div className="form-group">
                      <label>名</label>
                      <input type="text" value={memberInfo.last_name || '未设置'} readOnly />
                    </div>
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label>手机号</label>
                      <input type="tel" value={memberInfo.phone} readOnly />
                    </div>
                    <div className="form-group">
                      <label>注册时间</label>
                      <input type="text" value={formatDate(memberInfo.joinDate)} readOnly />
                    </div>
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label>性别</label>
                      <input type="text" value={memberInfo.gender === 'male' ? '男' : memberInfo.gender === 'female' ? '女' : '未设置'} readOnly />
                    </div>
                    <div className="form-group">
                      <label>生日</label>
                      <input type="text" value={memberInfo.birthday ? formatDate(memberInfo.birthday) : '未设置'} readOnly />
                    </div>
                  </div>
                  <div className="form-actions">
                    <ShinyButton className="btn btn-primary mr-4" onClick={() => setShowEditProfileModal(true)}>编辑资料</ShinyButton>
                    <ShinyButton className="btn btn-outline" onClick={() => setShowChangePasswordModal(true)}>修改密码</ShinyButton>
                  </div>
                </div>
              </div>

              {/* 会员等级折扣展示 */}
              <div className="section-card member-benefits">
                <h3>👑 会员特权</h3>
                
                {/* 当前等级信息 */}
                {currentDiscountInfo && (
                  <div className="current-level-info">
                    <div className="level-badge">
                      <span className="level-name">{currentDiscountInfo.member_level}</span>
                      <span className="level-discount">
                        {currentDiscountInfo.discount_percentage > 0 
                          ? `${currentDiscountInfo.discount_percentage}%折扣` 
                          : '无折扣'}
                      </span>
                    </div>
                    <div className="level-description">
                      <p>当前积分: {currentDiscountInfo.points}</p>
                      <p>{currentDiscountInfo.description}</p>
                    </div>
                  </div>
                )}

                {/* 所有等级展示 */}
                <div className="all-levels">
                  <h4>会员等级体系</h4>
                  <div className="levels-grid">
                    {memberLevels.map((level, index) => {
                      const discountPercentage = parseInt((1 - level.discount_rate) * 100);
                      const isCurrentLevel = currentDiscountInfo && currentDiscountInfo.member_level === level.name;
                      
                      return (
                        <div key={level.id} className={`level-card ${isCurrentLevel ? 'current' : ''}`}>
                          <div className="level-header">
                            <h5>{level.name}</h5>
                            {isCurrentLevel && <span className="current-badge">当前等级</span>}
                          </div>
                          <div className="level-requirements">
                            <p>所需积分: {level.points_threshold}</p>
                          </div>
                          <div className="level-benefits">
                            <div className="benefit-item">
                              <span className="benefit-label">购物折扣:</span>
                              <span className="benefit-value">
                                {discountPercentage > 0 ? `${discountPercentage}%优惠` : '无折扣'}
                              </span>
                            </div>
                          </div>
                          {level.description && (
                            <div className="level-description">
                              <p>{level.description}</p>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* 折扣说明 */}
                <div className="discount-rules">
                  <h4>📋 折扣说明</h4>
                  <ul>
                    <li>✅ 会员折扣适用于大部分商品分类</li>
                    <li>💎 会员折扣可与优惠券同时使用</li>
                    <li>📈 消费越多，积分越多，享受更高折扣</li>
                    <li>🎯 不同等级享受不同的专属优惠</li>
                  </ul>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'orders' && (
            <div className="orders-section">
              <div className="order-filters">
                <button 
                  className={`filter-btn ${orderFilter === 'all' ? 'active' : ''}`}
                  onClick={() => setOrderFilter('all')}
                >
                  <span>📋 全部订单</span>
                </button>
                <button 
                  className={`filter-btn ${orderFilter === 'pending' ? 'active' : ''}`}
                  onClick={() => setOrderFilter('pending')}
                >
                  <span>💰 待支付</span>
                </button>
                <button 
                  className={`filter-btn ${orderFilter === 'shipping' ? 'active' : ''}`}
                  onClick={() => setOrderFilter('shipping')}
                >
                  <span>🚚 配送中</span>
                </button>
                <button 
                  className={`filter-btn ${orderFilter === 'completed' ? 'active' : ''}`}
                  onClick={() => setOrderFilter('completed')}
                >
                  <span>✅ 已完成</span>
                </button>
              </div>
              
              {orders.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-icon">📦</div>
                  <p>暂无订单记录</p>
                </div>
              ) : (
                orders
                  .filter(order => {
                    if (orderFilter === 'all') return true;
                    if (orderFilter === 'pending') return order.status === 'pending';
                    if (orderFilter === 'shipping') return order.status === 'shipping' || order.status === 'shipped';
                    if (orderFilter === 'completed') return order.status === 'completed' || order.status === 'delivered';
                    return true;
                  })
                  .map(order => (
                <div key={order.id} className="order-card">
                  <div className="order-header">
                    <div className="order-info">
                      <span className="order-id">订单号: {order.id}</span>
                      <span className="order-date">{formatDate(order.date)}</span>
                    </div>
                    <div className="order-status" style={{ color: getStatusColor(order.status) }}>
                      {order.statusText}
                    </div>
                  </div>
                  <div className="order-items">
                        {order.items && order.items.length > 0 ? (
                          order.items.map((item, index) => (
                      <div key={index} className="order-item">
                        <img src={item.image} alt={item.name} />
                        <div className="item-info">
                          <h4>{item.name}</h4>
                          <p>数量: {item.quantity}</p>
                        </div>
                        <div className="item-price">¥{item.price.toFixed(2)}</div>
                      </div>
                          ))
                        ) : (
                          <div className="no-items">无商品信息</div>
                        )}
                  </div>
                  <div className="order-footer">
                    <div className="order-total">总计: ¥{order.total.toFixed(2)}</div>
                    <div className="order-actions">
                      {order.status === 'pending' && (
                            <Link 
                              to={`/order/${order.id}`} 
                              className="btn btn-primary btn-sm"
                              onClick={() => {
                                // 获取完整订单数据，并存储到localStorage
                                const token = localStorage.getItem('access') || localStorage.getItem('token');
                                if (token) {
                                  try {
                                    // 构建完整的订单数据对象
                                    const completeOrder = {
                                      id: order.id,
                                      order_number: order.id,
                                      status: order.status,
                                      status_display: order.statusText,
                                      total_price: order.total,
                                      created_at: order.date,
                                      recipient_name: '收件人',
                                      recipient_phone: '电话号码',
                                      shipping_address: '收货地址',
                                      can_pay: true,
                                      items: order.items.map(item => ({
                                        id: Math.random().toString(36).substr(2, 9),
                                        product_id: Math.random().toString(36).substr(2, 9),
                                        product_name: item.name,
                                        product_image: item.image,
                                        quantity: item.quantity,
                                        unit_price: item.price,
                                        total_price: item.price * item.quantity
                                      }))
                                    };
                                    
                                    // 存储到localStorage
                                    localStorage.setItem('latest_order', JSON.stringify(completeOrder));
                                    console.log('订单数据已存储到localStorage', completeOrder);
                                  } catch (error) {
                                    console.error('存储订单数据失败:', error);
                                  }
                                }
                              }}
                            >
                              立即付款
                            </Link>
                      )}
                          {(order.status === 'delivered' || order.status === 'completed') && (
                        <div className="order-item-actions">
                          {order.items.map((item, itemIdx) => {
                            // 检查商品是否已评价
                            const productId = item.id || item.product_id;
                            const hasReviewed = isProductReviewed(productId);
                            
                            return (
                              <div key={itemIdx} className="order-item-action">
                                {hasReviewed ? (
                                  <button 
                                    className="btn btn-outline btn-sm" 
                                    onClick={() => handleReview(order, item)}
                                  >
                                    查看/修改评价
                                  </button>
                                ) : (
                                  <button 
                                    className="btn btn-outline btn-sm" 
                                    onClick={() => handleReview(order, item)}
                                  >
                                    评价商品
                                  </button>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      )}
                          <Link 
                            to={`/order/${order.id}`} 
                            className="btn btn-outline btn-sm"
                            onClick={() => {
                              // 获取完整订单数据，并存储到localStorage
                              const token = localStorage.getItem('access') || localStorage.getItem('token');
                              if (token) {
                                // 尝试先从本地存储获取当前订单详情
                                try {
                                  // 构建完整的订单数据对象
                                  const completeOrder = {
                                    id: order.id,
                                    order_number: order.id,
                                    status: order.status,
                                    status_display: order.statusText,
                                    total_price: order.total,
                                    created_at: order.date,
                                    recipient_name: '收件人',
                                    recipient_phone: '电话号码',
                                    shipping_address: '收货地址',
                                    items: order.items.map(item => ({
                                      id: Math.random().toString(36).substr(2, 9),
                                      product_id: Math.random().toString(36).substr(2, 9),
                                      product_name: item.name,
                                      product_image: item.image,
                                      quantity: item.quantity,
                                      unit_price: item.price,
                                      total_price: item.price * item.quantity
                                    }))
                                  };
                                  
                                  // 存储到localStorage
                                  localStorage.setItem('latest_order', JSON.stringify(completeOrder));
                                  console.log('订单数据已存储到localStorage', completeOrder);
                                } catch (error) {
                                  console.error('存储订单数据失败:', error);
                                }
                              }
                            }}
                          >
                            查看详情
                          </Link>
                          <button 
                            className="btn btn-danger btn-sm" 
                            onClick={(e) => {
                              e.preventDefault();
                              handleDeleteOrder(order.id);
                            }}
                          >
                            删除订单
                          </button>
                    </div>
                  </div>
                </div>
                  ))
              )}
            </div>
          )}

          {activeTab === 'addresses' && (
            <div className="addresses-section">
              {renderAddresses()}
            </div>
          )}

          {activeTab === 'coupons' && (
            <div className="coupons-section">
              {renderCoupons()}
            </div>
          )}

          {activeTab === 'aftersale' && (
            <div className="aftersale-section">
              {renderAfterSaleRequests()}
            </div>
          )}
        </div>
        
        {/* 充值模态窗口 */}
        {renderRechargeModal()}
        
        {/* 编辑资料模态窗口 */}
        {showEditProfileModal && (
          <div className="modal-overlay">
            <div className="modal">
              <div className="modal-header">
                <h3>编辑个人资料</h3>
                <button className="close-btn" onClick={() => setShowEditProfileModal(false)}>×</button>
              </div>
              <div className="modal-body">
                <form onSubmit={handleProfileSubmit}>
                  <div className="form-group">
                    <label>用户名</label>
                    <input 
                      type="text" 
                      name="username"
                      value={editProfileData.username}
                      readOnly
                      className="disabled"
                    />
                    <small>用户名不可修改</small>
                  </div>
                  <div className="form-group">
                    <label>邮箱</label>
                    <input 
                      type="email" 
                      name="email"
                      value={editProfileData.email}
                      readOnly
                      className="disabled"
                    />
                    <small>邮箱不可修改</small>
                  </div>
                  <div className="form-group">
                    <label>手机号</label>
                    <input 
                      type="tel" 
                      name="phone"
                      value={editProfileData.phone}
                      onChange={handleProfileInputChange}
                      placeholder="请输入手机号"
                    />
                  </div>
                  <div className="form-group">
                    <label>姓</label>
                    <input 
                      type="text" 
                      name="first_name"
                      value={editProfileData.first_name}
                      onChange={handleProfileInputChange}
                      placeholder="请输入您的姓"
                    />
                  </div>
                  <div className="form-group">
                    <label>名</label>
                    <input 
                      type="text" 
                      name="last_name"
                      value={editProfileData.last_name}
                      onChange={handleProfileInputChange}
                      placeholder="请输入您的名"
                    />
                  </div>
                  <div className="form-group">
                    <label>性别</label>
                    <select 
                      name="gender"
                      value={editProfileData.gender}
                      onChange={handleProfileInputChange}
                    >
                      <option value="">请选择</option>
                      <option value="male">男</option>
                      <option value="female">女</option>
                      <option value="other">其他</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>生日</label>
                    <input 
                      type="date" 
                      name="birthday"
                      value={editProfileData.birthday || ''}
                      onChange={handleProfileInputChange}
                    />
                  </div>
                  {profileError && (
                    <div className="error-message">{profileError}</div>
                  )}
                  {profileSuccess && (
                    <div className="success-message">{profileSuccess}</div>
                  )}
                  <div className="form-actions">
                    <button type="submit" className="btn btn-primary">保存</button>
                    <button type="button" className="btn btn-outline" onClick={() => setShowEditProfileModal(false)}>取消</button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}
        
        {/* 修改密码模态窗口 */}
        {showChangePasswordModal && (
          <div className="modal-overlay">
            <div className="modal">
              <div className="modal-header">
                <h3>修改密码</h3>
                <button className="close-btn" onClick={() => setShowChangePasswordModal(false)}>×</button>
              </div>
              <div className="modal-body">
                <form onSubmit={handlePasswordSubmit}>
                  <div className="form-group">
                    <label>当前密码</label>
                    <input 
                      type="password" 
                      name="currentPassword"
                      value={passwordData.currentPassword}
                      onChange={handlePasswordInputChange}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>新密码</label>
                    <input 
                      type="password" 
                      name="newPassword"
                      value={passwordData.newPassword}
                      onChange={handlePasswordInputChange}
                      required
                    />
                    <small>密码长度至少为8位，包含字母和数字</small>
                  </div>
                  <div className="form-group">
                    <label>确认新密码</label>
                    <input 
                      type="password" 
                      name="confirmPassword"
                      value={passwordData.confirmPassword}
                      onChange={handlePasswordInputChange}
                      required
                    />
                  </div>
                  {passwordError && (
                    <div className="error-message">{passwordError}</div>
                  )}
                  {passwordSuccess && (
                    <div className="success-message">{passwordSuccess}</div>
                  )}
                  <div className="form-actions">
                    <button type="submit" className="btn btn-primary">更新密码</button>
                    <button type="button" className="btn btn-outline" onClick={() => setShowChangePasswordModal(false)}>取消</button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}

        {/* 地址模态窗口 */}
        {renderAddressModal()}

        {/* 聊天模态窗口 */}
        {renderChatModal()}
      </div>
    </div>
  );
}

export default MemberCenter;