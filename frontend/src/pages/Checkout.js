import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import '../styles/cart.css';  // 先复用购物车的样式
import '../styles/checkout.css';  // 结算页面专用样式

const Checkout = () => {
  const navigate = useNavigate();
  const [cartItems, setCartItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [totalPrice, setTotalPrice] = useState(0);
  const [shippingFee, setShippingFee] = useState(10);
  const [addresses, setAddresses] = useState([]);
  const [selectedAddress, setSelectedAddress] = useState(null);
  const [paymentMethod, setPaymentMethod] = useState('alipay');
  const [couponCode, setCouponCode] = useState('');
  const [couponDiscount, setCouponDiscount] = useState(0);
  const [orderRemark, setOrderRemark] = useState('');
  const [showNewAddressForm, setShowNewAddressForm] = useState(false);
  const [processingOrder, setProcessingOrder] = useState(false);
  const [couponError, setCouponError] = useState('');
  const [couponSuccess, setCouponSuccess] = useState('');
  const [availableCoupons, setAvailableCoupons] = useState([]);
  const [selectedCouponId, setSelectedCouponId] = useState(null);
  const [couponLoading, setCouponLoading] = useState(false);
  const [showCouponList, setShowCouponList] = useState(false);
  
  // 钱包相关状态
  const [walletBalance, setWalletBalance] = useState(0);
  const [loadingBalance, setLoadingBalance] = useState(false);
  const [showRechargeModal, setShowRechargeModal] = useState(false);
  const [rechargeAmount, setRechargeAmount] = useState('');
  const [rechargingWallet, setRechargingWallet] = useState(false);

  // 会员折扣相关状态
  const [memberDiscountInfo, setMemberDiscountInfo] = useState({
    member_level: '银卡会员',
    discount_rate: 1.00,
    discount_percentage: 0,
    points: 0,
    points_threshold: 0,
    description: '',
    icon: ''
  });
  const [memberDiscount, setMemberDiscount] = useState(0);

  // 新地址表单数据
  const [newAddress, setNewAddress] = useState({
    name: '',
    phone: '',
    province: '',
    city: '',
    district: '',
    detail: '',
    postal_code: '',
    is_default: false
  });

  useEffect(() => {
    // 检查用户是否登录
    const token = localStorage.getItem('access') || localStorage.getItem('token');
    if (!token) {
      navigate('/login', { state: { from: '/checkout' } });
      return;
    }

    // 获取购物车数据、用户地址和钱包余额
    fetchCartItems();
    fetchAddresses();
    fetchAvailableCoupons();
    fetchWalletBalance();
    fetchMemberDiscountInfo();
  }, [navigate]);

  // 当总价变化时重新计算会员折扣
  useEffect(() => {
    if (memberDiscountInfo && totalPrice > 0) {
      calculateMemberDiscount(memberDiscountInfo, totalPrice);
    }
  }, [totalPrice, memberDiscountInfo]);

  // 获取钱包余额
  const fetchWalletBalance = async () => {
    try {
      setLoadingBalance(true);
      const token = localStorage.getItem('access') || localStorage.getItem('token');
      
      const response = await axios.get('/api/member/members/current_member/', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      console.log('会员信息响应:', response.data);
      
      if (response.data && typeof response.data.balance !== 'undefined') {
        setWalletBalance(parseFloat(response.data.balance));
        console.log('钱包余额:', response.data.balance);
      } else {
        setWalletBalance(0);
      }
    } catch (err) {
      console.error('获取钱包余额失败:', err);
      setWalletBalance(0);
    } finally {
      setLoadingBalance(false);
    }
  };

  // 获取会员折扣信息
  const fetchMemberDiscountInfo = async () => {
    try {
      const token = localStorage.getItem('access') || localStorage.getItem('token');
      
      const response = await axios.get('/api/member/members/discount_info/', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      console.log('会员折扣信息:', response.data);
      setMemberDiscountInfo(response.data);
      
      // 计算会员折扣金额
      calculateMemberDiscount(response.data, totalPrice);
      
    } catch (err) {
      console.error('获取会员折扣信息失败:', err);
    }
  };

  // 计算会员折扣
  const calculateMemberDiscount = (discountInfo, subtotal) => {
    if (discountInfo && discountInfo.discount_rate < 1.00) {
      const discount = subtotal * (1 - discountInfo.discount_rate);
      setMemberDiscount(discount);
    } else {
      setMemberDiscount(0);
    }
  };

  // 钱包充值
  const handleWalletRecharge = async () => {
    if (!rechargeAmount || parseFloat(rechargeAmount) <= 0) {
      showNotification('请输入有效的充值金额', 'error');
      return;
    }

    try {
      setRechargingWallet(true);
      const token = localStorage.getItem('access') || localStorage.getItem('token');
      
      const response = await axios.post('/api/member/members/recharge/', {
        amount: parseFloat(rechargeAmount)
      }, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      console.log('充值响应:', response.data);
      
      if (response.data.success) {
        setWalletBalance(parseFloat(response.data.new_balance));
        setShowRechargeModal(false);
        setRechargeAmount('');
        showNotification(`充值成功！当前余额：¥${response.data.new_balance}`, 'success');
      } else {
        showNotification('充值失败，请稍后重试', 'error');
      }
    } catch (err) {
      console.error('充值失败:', err);
      showNotification(err.response?.data?.detail || '充值失败，请稍后重试', 'error');
    } finally {
      setRechargingWallet(false);
    }
  };

  // 检查钱包余额是否足够
  const checkWalletBalance = () => {
    const finalPrice = Math.max(0, totalPrice + shippingFee - couponDiscount - memberDiscount);
    return walletBalance >= finalPrice;
  };

  const fetchCartItems = async () => {
    try {
      const token = localStorage.getItem('access') || localStorage.getItem('token');
      
      const response = await axios.get('/api/cart/cart/', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      console.log('购物车数据:', response.data);
      
      if (response.data && response.data.items) {
        setCartItems(response.data.items);
        
        // 使用API返回的总价
        if (typeof response.data.total_price === 'number') {
          setTotalPrice(response.data.total_price);
        } else {
          // 如果API没有返回总价，自己计算
          const total = response.data.items.reduce((sum, item) => {
            const price = typeof item.unit_price === 'number' ? item.unit_price : 0;
            return sum + (price * item.quantity);
          }, 0);
          setTotalPrice(total);
        }
      } else {
        setCartItems([]);
        setTotalPrice(0);
      }
      
      setLoading(false);
    } catch (err) {
      console.error('获取购物车失败:', err);
      setError('获取购物车失败，请稍后再试');
      setLoading(false);
      
      if (err.response && err.response.status === 401) {
        navigate('/login', { state: { from: '/checkout' } });
      }
    }
  };

  const fetchAddresses = async () => {
    try {
      const token = localStorage.getItem('access') || localStorage.getItem('token');
      if (!token) {
        console.error('无法获取认证令牌');
        return;
      }
      
      const response = await axios.get('/api/member/addresses/', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      console.log('地址API响应:', response.data);
      
      if (Array.isArray(response.data) && response.data.length > 0) {
        setAddresses(response.data);
        
        // 设置默认选中地址
        const defaultAddress = response.data.find(addr => addr.is_default);
        if (defaultAddress) {
          setSelectedAddress(defaultAddress.id);
        } else {
          setSelectedAddress(response.data[0].id);
        }
      } else {
        setAddresses([]);
        setSelectedAddress(null);
        // 如果没有地址，显示添加地址表单
        setShowNewAddressForm(true);
      }
    } catch (err) {
      console.error('获取地址失败:', err);
      setAddresses([]);
      setSelectedAddress(null);
      // 如果获取地址失败，显示添加地址表单
      setShowNewAddressForm(true);
    }
  };

  const handleAddressChange = (addressId) => {
    setSelectedAddress(addressId);
  };

  const handleNewAddressInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setNewAddress({
      ...newAddress,
      [name]: type === 'checkbox' ? checked : value
    });
  };

  const handleAddNewAddress = async (e) => {
    e.preventDefault();
    
    // 验证表单
    if (!newAddress.name || !newAddress.phone || 
        !newAddress.province || !newAddress.city || 
        !newAddress.district || !newAddress.detail) {
      showNotification('请填写完整的地址信息', 'error');
      return;
    }
    
    try {
      const token = localStorage.getItem('access') || localStorage.getItem('token');
      if (!token) {
        showNotification('未授权，请重新登录', 'error');
        return;
      }
      
      // 调用API创建新地址
      const response = await axios.post(
        '/api/member/addresses/',
        newAddress,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      console.log('添加地址响应:', response.data);
      
      // 重新获取地址列表
      await fetchAddresses();
      
      // 选中新添加的地址
      if (response.data && response.data.id) {
        setSelectedAddress(response.data.id);
      }
      
      // 隐藏表单
      setShowNewAddressForm(false);
      
      // 重置表单
      setNewAddress({
        name: '',
        phone: '',
        province: '',
        city: '',
        district: '',
        detail: '',
        postal_code: '',
        is_default: false
      });
      
      showNotification('地址添加成功', 'success');
    } catch (err) {
      console.error('添加地址失败:', err);
      showNotification(err.response?.data?.detail || '添加地址失败，请稍后再试', 'error');
    }
  };

  // 获取可用的优惠券
  const fetchAvailableCoupons = async () => {
    try {
      const token = localStorage.getItem('access') || localStorage.getItem('token');
      if (!token) {
        console.error('无法获取认证令牌');
        return;
      }
      
      setCouponLoading(true);
      
      // 尝试获取会员优惠券
      const response = await axios.get('/api/coupon/member-coupons/', {
        headers: {
          'Authorization': `Bearer ${token}`
        },
        params: {
          status: 'available'  // 只获取可用的优惠券
        }
      });
      
      console.log('优惠券API响应:', response.data);
      
      let validCoupons = [];
      
      if (Array.isArray(response.data)) {
        // 直接返回数组格式
        validCoupons = response.data;
      } else if (response.data && response.data.results && Array.isArray(response.data.results)) {
        // 分页格式
        validCoupons = response.data.results;
      } else {
        validCoupons = [];
      }
      
      // 过滤和格式化优惠券
      const now = new Date();
      const formattedCoupons = validCoupons
        .filter(coupon => {
          // 确保优惠券未过期且状态为可用
          const endDate = new Date(
            coupon.coupon_detail.end_date || 
            coupon.coupon_detail.end_time || 
            coupon.expiry_date
          );
          return endDate > now && coupon.status === 'available';
        })
        .map(coupon => {
          // 标准化优惠券格式
          return {
            id: coupon.id,
            status: coupon.status,
            coupon_detail: {
              id: coupon.coupon_detail.id,
              name: coupon.coupon_detail.name,
              code: coupon.coupon_detail.code,
              type: coupon.coupon_detail.type,
              value: parseFloat(coupon.coupon_detail.value),
              min_amount: parseFloat(coupon.coupon_detail.min_amount || coupon.coupon_detail.min_purchase_amount || 0),
              max_discount: coupon.coupon_detail.max_discount ? parseFloat(coupon.coupon_detail.max_discount) : null,
              end_date: new Date(
                coupon.coupon_detail.end_date || 
                coupon.coupon_detail.end_time || 
                coupon.expiry_date
              )
            }
          };
        });
      
      console.log('格式化后的优惠券:', formattedCoupons);
      setAvailableCoupons(formattedCoupons);
    } catch (err) {
      console.error('获取优惠券失败:', err);
      console.error('错误详情:', err.response?.data);
      setAvailableCoupons([]);
    } finally {
      setCouponLoading(false);
    }
  };

  const handleApplyCoupon = async () => {
    if (!couponCode) {
      setCouponError('请输入优惠码');
      return;
    }
    
    try {
      setCouponLoading(true);
      const token = localStorage.getItem('access') || localStorage.getItem('token');
      
      // 调用验证优惠券API
      const response = await axios.post(`/api/coupon/coupons/1/validate/`, {
        code: couponCode,
        total_amount: totalPrice
      }, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      console.log('优惠券验证响应:', response.data);
      
      if (response.data && response.data.valid) {
        setCouponDiscount(response.data.discount_amount);
        setCouponError('');
        setCouponSuccess(`优惠券应用成功，已减免¥${response.data.discount_amount.toFixed(2)}`);
        setSelectedCouponId(response.data.coupon_id);
      } else {
        setCouponDiscount(0);
        setCouponError('优惠券验证失败');
        setCouponSuccess('');
      }
    } catch (err) {
      console.error('验证优惠券失败:', err);
      setCouponDiscount(0);
      setCouponSuccess('');
      
      if (err.response && err.response.data && err.response.data.error) {
        setCouponError(err.response.data.error);
      } else {
        setCouponError('验证优惠券失败，请稍后重试');
      }
    } finally {
      setCouponLoading(false);
    }
  };

  const handleSelectCoupon = (coupon) => {
    try {
      // 检查优惠券最低消费金额
      const minAmount = parseFloat(coupon.coupon_detail.min_amount);
      if (totalPrice < minAmount) {
        setCouponError(`订单金额不满足使用条件，最低需要¥${minAmount.toFixed(2)}`);
        return;
      }
      
      // 计算折扣金额
      let discountAmount = 0;
      let discountDescription = '';
      
      if (coupon.coupon_detail.type === 'fixed') {
        // 满减券
        discountAmount = parseFloat(coupon.coupon_detail.value);
        discountDescription = `满${minAmount}减${discountAmount}`;
      } else if (coupon.coupon_detail.type === 'discount') {
        // 折扣券
        const discountRate = parseFloat(coupon.coupon_detail.value);
        discountAmount = totalPrice * (1 - discountRate);
        
        // 如果有最大折扣限制
        if (coupon.coupon_detail.max_discount) {
          const maxDiscount = parseFloat(coupon.coupon_detail.max_discount);
          if (discountAmount > maxDiscount) {
            discountAmount = maxDiscount;
          }
        }
        
        discountDescription = `${discountRate * 10}折，优惠${discountAmount.toFixed(2)}元`;
      } else if (coupon.coupon_detail.type === 'free_shipping') {
        // 包邮券
        discountAmount = shippingFee;
        discountDescription = '包邮';
      }
      
      // 更新优惠券信息
      setCouponCode(coupon.coupon_detail.code);
      setCouponDiscount(discountAmount);
      setSelectedCouponId(coupon.id);
      setCouponError('');
      setCouponSuccess(`已选择优惠券：${coupon.coupon_detail.name}，${discountDescription}`);
      
      // 可选：关闭优惠券列表
      setShowCouponList(false);
      
      console.log('应用优惠券:', {
        id: coupon.id,
        code: coupon.coupon_detail.code,
        type: coupon.coupon_detail.type,
        discountAmount: discountAmount
      });
    } catch (err) {
      console.error('选择优惠券失败:', err);
      setCouponError('选择优惠券失败，请稍后重试');
    }
  };

  const getCouponTypeText = (type) => {
    switch(type) {
      case 'full_reduction':
      case 'fixed':
        return '满减券';
      case 'discount':
        return '折扣券';
      case 'free_shipping':
        return '包邮券';
      default:
        return '优惠券';
    }
  };

  const handleSubmitOrder = async () => {
    // 检查是否有选择的地址或者填写了新地址信息
    if (!selectedAddress && !showNewAddressForm) {
      showNotification('请选择收货地址', 'error');
      return;
    }
    
    // 如果显示新地址表单，验证表单是否完整填写
    if (showNewAddressForm && !selectedAddress) {
      if (!newAddress.name || !newAddress.phone || 
          !newAddress.province || !newAddress.city || 
          !newAddress.district || !newAddress.detail) {
        showNotification('请完整填写收货地址信息', 'error');
        return;
      }
    }
    
    if (cartItems.length === 0) {
      showNotification('购物车为空，无法提交订单', 'error');
      return;
    }
    
    // 计算最终价格
    const finalPrice = Math.max(0, totalPrice + shippingFee - couponDiscount - memberDiscount);
    
    // 如果选择钱包支付，检查余额是否足够
    if (paymentMethod === 'balance') {
      if (!checkWalletBalance()) {
        // 直接弹出充值模态框，不显示错误提示
        setShowRechargeModal(true);
        return;
      }
    }
    
    try {
      setProcessingOrder(true);
      
      const token = localStorage.getItem('access') || localStorage.getItem('token');
      
      // 获取选中的地址或使用新填写的地址
      let address;
      if (selectedAddress) {
        address = addresses.find(addr => addr.id === selectedAddress);
      } else if (showNewAddressForm) {
        // 使用新填写的地址信息
        address = {
          name: newAddress.name,
          phone: newAddress.phone,
          province: newAddress.province,
          city: newAddress.city,
          district: newAddress.district,
          detail: newAddress.detail,
          postal_code: newAddress.postal_code || ''
        };
      }
      
      // 确保地址信息存在
      if (!address) {
        showNotification('地址信息获取失败，请重新选择或填写地址', 'error');
        setProcessingOrder(false);
        return;
      }
      
      // 准备订单数据
      const orderItems = cartItems.map(item => {
        // 确保所有必需字段都存在
        const productId = item.product_info?.id || item.product_id;
        const productVariantId = item.variant_info?.id || item.product_info?.variant_id || 0;
        
        console.log("处理订单商品:", item);
        
        if (!productId) {
          console.error("商品ID缺失:", item);
          // 使用默认值而不是抛出错误
          return null;
        }
        
        const productName = item.product_info?.name || item.product_name || '未命名商品';
        const variantName = item.variant_info?.name || item.variant_name || '默认规格';
        const quantity = parseInt(item.quantity) || 1;
        const price = parseFloat(item.unit_price) || 0;
        
        // 扩展商品信息，包含更多详细数据
        return {
          product_id: parseInt(productId),
          product_variant_id: parseInt(productVariantId || 0),
          product_name: productName,
          variant_name: variantName,
          quantity: quantity,
          price: price,
          // 添加这些额外字段以便在订单详情中显示
          product_image: item.product_image || item.product_info?.image || '/images/Normal.jpg',
          product_sku: item.variant_info?.sku || item.product_info?.sku || `SKU-${productId}`,
          variant_info: item.variant_info || {},
          subtotal: price * quantity
        };
      }).filter(item => item !== null); // 过滤掉无效的订单项
      
      if (orderItems.length === 0) {
        showNotification('购物车中没有有效商品，无法提交订单', 'error');
        setProcessingOrder(false);
        return;
      }
      
      // 验证收货地址信息
      if (!address.name || !address.phone) {
        showNotification('收货人信息不完整', 'error');
        setProcessingOrder(false);
        return;
      }
      
      // 构建收货地址对象
      const shippingAddressObj = {
        province: address.province || '',
        city: address.city || '',
        district: address.district || '',
        detail: address.detail || '',
        full_address: `${address.province || ''} ${address.city || ''} ${address.district || ''} ${address.detail || ''}`.trim(),
        recipient_name: address.name,
        recipient_phone: address.phone
      };
      
      if (!shippingAddressObj.full_address) {
        showNotification('收货地址不能为空', 'error');
        setProcessingOrder(false);
        return;
      }
      
      // 构建订单数据
      const orderData = {
        items: orderItems,
        recipient_name: address.name,
        recipient_phone: address.phone,
        shipping_address: shippingAddressObj,
        payment_method: paymentMethod,
        coupon_code: couponCode || '',
        coupon_id: selectedCouponId,
        discount_amount: couponDiscount,
        remark: orderRemark || ''
      };
      
      console.log('提交订单数据:', orderData);
      
      // 发送创建订单请求
      const response = await axios.post('/api/order/create-order/', orderData, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      console.log('订单创建成功:', response.data);
      
      // 清空购物车
      try {
        await axios.delete('/api/cart/cart/clear/', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        console.log('购物车已清空');
      } catch (cartError) {
        console.error('清空购物车失败:', cartError);
        // 继续流程，不中断
      }
      
      // 显示成功提示
      showNotification('订单提交成功，即将跳转到支付页面', 'success');
      
      // 记录订单详情，方便调试
      console.log('订单创建成功，响应数据:', {
        id: response.data.order_id || response.data.id,
        number: response.data.order_number,
        total: response.data.total_price,
        status: response.data.status
      });
      
      // 跳转到订单详情页
      setTimeout(() => {
        let orderId = '';
        if (response.data && (response.data.order_id || response.data.id)) {
          orderId = response.data.order_id || response.data.id;
        } else if (response.data && response.data.order_number) {
          orderId = response.data.order_number;
        }
        
        if (orderId) {
          console.log(`跳转到订单详情页: /order/${orderId}`);
          // 使用本地存储暂存订单数据，以便在订单详情页使用
          localStorage.setItem('latest_order', JSON.stringify({
            id: orderId,
            order_number: response.data.order_number,
            total_price: response.data.total_price,
            status: response.data.status || 'pending',
            created_at: response.data.created_at || new Date().toISOString(),
            payment_method: paymentMethod,
            payment_method_display: paymentMethod === 'alipay' ? '支付宝' : 
                                   paymentMethod === 'wechat' ? '微信支付' : 
                                   paymentMethod === 'balance' ? '钱包支付' : 
                                   paymentMethod === 'cod' ? '货到付款' : '其他方式',
            items: orderItems.map(item => ({
              ...item,
              id: item.product_id,
              product_id: item.product_id,
              product_name: item.product_name,
              product_image: item.product_image,
              variant_info: item.variant_info,
              quantity: item.quantity,
              unit_price: item.price,
              total_price: item.subtotal
            })), // 保存完整且正确的商品信息
            shipping_address: shippingAddressObj, // 保存完整的地址信息
            recipient_name: address.name,
            recipient_phone: address.phone
          }));
          navigate(`/order/${orderId}`);
        } else {
          console.log('无法获取订单ID，跳转到订单列表');
          navigate('/orders');
        }
      }, 2000);
    } catch (err) {
      console.error('提交订单失败:', err);
      // 打印更详细的错误信息
      if (err.response) {
        console.error('响应错误:', err.message);
        console.error('错误状态码:', err.response.status);
        console.error('错误数据:', err.response.data);
        
        // 显示具体错误信息
        if (err.response.data && typeof err.response.data === 'object') {
          const errorMessages = [];
          
          // 处理嵌套错误
          for (const [key, value] of Object.entries(err.response.data)) {
            if (Array.isArray(value)) {
              errorMessages.push(`${key}: ${value.join(', ')}`);
            } else if (typeof value === 'object' && value !== null) {
              for (const [subKey, subValue] of Object.entries(value)) {
                if (Array.isArray(subValue)) {
                  errorMessages.push(`${key}.${subKey}: ${subValue.join(', ')}`);
                } else if (typeof subValue === 'object' && subValue !== null) {
                  for (const [subSubKey, subSubValue] of Object.entries(subValue)) {
                    errorMessages.push(`${key}.${subKey}.${subSubKey}: ${subSubValue}`);
                  }
                } else {
                  errorMessages.push(`${key}.${subKey}: ${subValue}`);
                }
              }
            } else {
              errorMessages.push(`${key}: ${value}`);
            }
          }
          
          if (errorMessages.length > 0) {
            showNotification(`提交订单失败: ${errorMessages.join('; ')}`, 'error');
          } else {
            showNotification('提交订单失败，请稍后再试', 'error');
          }
        } else {
          showNotification('提交订单失败，请稍后再试', 'error');
        }
      } else {
        showNotification('提交订单失败，请稍后再试', 'error');
      }
      
      setProcessingOrder(false);
    }
  };

  // 显示通知提示
  const showNotification = (message, type = 'success') => {
    const notification = document.createElement('div');
    notification.className = `cart-notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.classList.add('show');
    }, 10);
    
    setTimeout(() => {
      notification.classList.remove('show');
      setTimeout(() => {
        document.body.removeChild(notification);
      }, 300);
    }, 3000);
  };

  // 添加优惠券列表组件
  const CouponList = ({ coupons, onSelect, totalPrice }) => {
    if (coupons.length === 0) {
      return <div className="empty-coupons">暂无可用优惠券</div>;
    }
    
    return (
      <div className="coupon-list">
        {coupons.map(coupon => {
          const minAmount = parseFloat(coupon.coupon_detail.min_amount);
          const isAvailable = totalPrice >= minAmount;
          
          let couponTypeText = '';
          let valueText = '';
          
          if (coupon.coupon_detail.type === 'fixed') {
            couponTypeText = '满减券';
            valueText = `满${minAmount}减${coupon.coupon_detail.value}`;
          } else if (coupon.coupon_detail.type === 'discount') {
            couponTypeText = '折扣券';
            valueText = `${coupon.coupon_detail.value * 10}折`;
            if (coupon.coupon_detail.max_discount) {
              valueText += `，最高减${coupon.coupon_detail.max_discount}`;
            }
          } else if (coupon.coupon_detail.type === 'free_shipping') {
            couponTypeText = '包邮券';
            valueText = '包邮';
          }
          
          const expireDate = new Date(coupon.coupon_detail.end_date);
          
          return (
            <div 
              key={coupon.id} 
              className={`coupon-item ${isAvailable ? '' : 'disabled'}`}
              onClick={() => isAvailable && onSelect(coupon)}
            >
              <div className="coupon-value">{valueText}</div>
              <div className="coupon-info">
                <div className="coupon-name">{coupon.coupon_detail.name || couponTypeText}</div>
                <div className="coupon-limit">满 ¥{minAmount} 可用</div>
                <div className="coupon-expire">有效期至: {expireDate.toLocaleDateString()}</div>
              </div>
              {!isAvailable && <div className="coupon-unavailable">订单金额不满足条件</div>}
            </div>
          );
        })}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="loading-spinner"></div>
        <p>加载中...</p>
      </div>
    );
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  if (cartItems.length === 0) {
    return (
      <div className="cart-empty">
        <h2>购物车为空</h2>
        <p>您的购物车中没有商品，无法结算</p>
        <button className="continue-shopping" onClick={() => navigate('/products')}>
          继续购物
        </button>
      </div>
    );
  }

  // 计算最终价格
  const finalPrice = Math.max(0, totalPrice + shippingFee - couponDiscount - memberDiscount);

  return (
    <div className="checkout-container">
      <h1>订单结算</h1>
      
      {/* 会员等级信息 */}
      {memberDiscountInfo.discount_percentage > 0 && (
        <div className="member-info-bar">
          <div className="member-badge">
            <span className="member-level">{memberDiscountInfo.member_level}</span>
            <span className="member-benefit">享受 {memberDiscountInfo.discount_percentage}% 会员折扣</span>
          </div>
          <div className="member-points">
            当前积分: {memberDiscountInfo.points}
          </div>
        </div>
      )}
      
      <div className="checkout-layout">
        {/* 左侧：订单信息 */}
        <div className="checkout-left">
          {/* 收货地址 */}
          <div className="checkout-section">
            <h2>收货地址</h2>
            
            <div className="address-list">
              {addresses.map(address => (
                <div 
                  key={address.id}
                  className={`address-item ${selectedAddress === address.id ? 'selected' : ''}`}
                  onClick={() => handleAddressChange(address.id)}
                >
                  <div className="address-header">
                    <span className="recipient">{address.name}</span>
                    <span className="phone">{address.phone}</span>
                    {address.is_default && <span className="default-tag">默认</span>}
                  </div>
                  <div className="address-content">
                    {address.province} {address.city} {address.district} {address.detail}
                  </div>
                </div>
              ))}
              
              {!showNewAddressForm ? (
                <div className="add-address" onClick={() => setShowNewAddressForm(true)}>
                  <span>+ 添加新地址</span>
                </div>
              ) : (
                <div className="new-address-form">
                  <h3>添加新地址</h3>
                  <div className="address-form-tip">
                    <p>💡 提示：填写完地址信息后，您可以直接提交订单，无需先保存地址</p>
                  </div>
                  <form onSubmit={handleAddNewAddress}>
                    <div className="form-row">
                      <div className="form-group">
                        <label htmlFor="name">收货人</label>
                        <input
                          type="text"
                          id="name"
                          name="name"
                          value={newAddress.name}
                          onChange={handleNewAddressInputChange}
                          required
                        />
                      </div>
                      <div className="form-group">
                        <label htmlFor="phone">手机号码</label>
                        <input
                          type="tel"
                          id="phone"
                          name="phone"
                          value={newAddress.phone}
                          onChange={handleNewAddressInputChange}
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
                          value={newAddress.province}
                          onChange={handleNewAddressInputChange}
                          required
                        />
                      </div>
                      <div className="form-group">
                        <label htmlFor="city">城市</label>
                        <input
                          type="text"
                          id="city"
                          name="city"
                          value={newAddress.city}
                          onChange={handleNewAddressInputChange}
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
                          value={newAddress.district}
                          onChange={handleNewAddressInputChange}
                          required
                        />
                      </div>
                      <div className="form-group">
                        <label htmlFor="postal_code">邮政编码</label>
                        <input
                          type="text"
                          id="postal_code"
                          name="postal_code"
                          value={newAddress.postal_code}
                          onChange={handleNewAddressInputChange}
                        />
                      </div>
                    </div>
                    
                    <div className="form-group">
                      <label htmlFor="detail">详细地址</label>
                      <input
                        type="text"
                        id="detail"
                        name="detail"
                        value={newAddress.detail}
                        onChange={handleNewAddressInputChange}
                        required
                      />
                    </div>
                    
                    <div className="form-group checkbox">
                      <input
                        type="checkbox"
                        id="is_default"
                        name="is_default"
                        checked={newAddress.is_default}
                        onChange={handleNewAddressInputChange}
                      />
                      <label htmlFor="is_default">设为默认地址</label>
                    </div>
                    
                    <div className="form-actions">
                      <button type="button" onClick={() => {
                        setShowNewAddressForm(false);
                        // 重置表单
                        setNewAddress({
                          name: '',
                          phone: '',
                          province: '',
                          city: '',
                          district: '',
                          detail: '',
                          postal_code: '',
                          is_default: false
                        });
                      }}>取消</button>
                      <button type="submit">保存地址</button>
                    </div>
                  </form>
                </div>
              )}
            </div>
          </div>
          
          {/* 支付方式 */}
          <div className="checkout-section">
            <h2>支付方式</h2>
            
            <div className="payment-methods">
              <div 
                className={`payment-method ${paymentMethod === 'alipay' ? 'selected' : ''}`}
                onClick={() => setPaymentMethod('alipay')}
              >
                <div className="payment-icon alipay"></div>
                <span>支付宝</span>
              </div>
              
              <div 
                className={`payment-method ${paymentMethod === 'wechat' ? 'selected' : ''}`}
                onClick={() => setPaymentMethod('wechat')}
              >
                <div className="payment-icon wechat"></div>
                <span>微信支付</span>
              </div>
              
              <div 
                className={`payment-method ${paymentMethod === 'balance' ? 'selected' : ''}`}
                onClick={() => setPaymentMethod('balance')}
              >
                <div className="payment-icon wallet"></div>
                <div className="payment-info">
                  <span>钱包支付</span>
                  <div className="balance-info">
                    {loadingBalance ? (
                      <span className="loading-text">加载中...</span>
                    ) : (
                      <span className="balance-amount">余额: ¥{walletBalance.toFixed(2)}</span>
                    )}
                  </div>
                </div>
              </div>
              
              <div 
                className={`payment-method ${paymentMethod === 'cod' ? 'selected' : ''}`}
                onClick={() => setPaymentMethod('cod')}
              >
                <div className="payment-icon cod"></div>
                <span>货到付款</span>
              </div>
            </div>
          </div>
          
          {/* 优惠券 */}
          <div className="checkout-section">
            <h3>优惠券</h3>
            <div className="coupon-container">
              <div className="coupon-input">
              <input
                type="text"
                value={couponCode}
                onChange={(e) => setCouponCode(e.target.value)}
                  placeholder="输入优惠码"
                  disabled={couponLoading}
              />
              <button 
                onClick={handleApplyCoupon}
                  disabled={couponLoading || !couponCode}
                  className="apply-coupon-btn"
              >
                  {couponLoading ? '处理中...' : '应用'}
              </button>
            </div>
            
              {couponError && <div className="error-message">{couponError}</div>}
              {couponSuccess && <div className="success-message">{couponSuccess}</div>}
            
              <div className="available-coupons">
                <button 
                  className="toggle-coupon-list" 
                  onClick={() => setShowCouponList(!showCouponList)}
                >
                  {showCouponList ? '隐藏可用优惠券' : '查看可用优惠券'}
                </button>
                
                {couponLoading && <div className="loading">加载优惠券中...</div>}
                
                {showCouponList && !couponLoading && (
                  <CouponList 
                    coupons={availableCoupons} 
                    onSelect={handleSelectCoupon}
                    totalPrice={totalPrice}
                  />
                            )}
                          </div>
                            </div>
            
            {couponDiscount > 0 && (
              <div className="discount-summary">
                <span>优惠金额:</span>
                <span className="discount-amount">-¥{couponDiscount.toFixed(2)}</span>
              </div>
            )}
          </div>
          
          {/* 订单备注 */}
          <div className="checkout-section">
            <h2>订单备注</h2>
            
            <textarea
              placeholder="请输入订单备注（选填）"
              value={orderRemark}
              onChange={(e) => setOrderRemark(e.target.value)}
              maxLength={200}
            ></textarea>
            <div className="remark-counter">{orderRemark.length}/200</div>
          </div>
        </div>
        
        {/* 右侧：订单摘要 */}
        <div className="checkout-right">
          <div className="order-summary">
            <h2>订单摘要</h2>
            
            <div className="summary-items">
              {cartItems.map(item => (
                <div key={item.id} className="summary-item">
                  <div className="item-image">
                    <img 
                      src={item.product_info?.image || item.product_image || '/images/Normal.jpg'} 
                      alt={item.product_info?.name || '商品'} 
                      onError={(e) => { e.target.src = '/images/Normal.jpg'; }}
                    />
                  </div>
                  <div className="item-info">
                    <div className="item-name">{item.product_info?.name || '未命名商品'}</div>
                    {item.variant_info && (
                      <div className="item-variant">
                        {typeof item.variant_info === 'object' ? 
                          (item.variant_info.name || 
                            Object.entries(item.variant_info)
                              .filter(([key]) => key !== 'id' && key !== 'name')
                              .map(([key, value]) => `${key}: ${value}`)
                              .join(', ')
                          ) : 
                          item.variant_info}
                      </div>
                    )}
                    {item.product_info?.sku && (
                      <div className="item-sku">SKU: {item.product_info.sku}</div>
                    )}
                    <div className="item-price">¥{parseFloat(item.unit_price || 0).toFixed(2)} × {item.quantity}</div>
                  </div>
                  <div className="item-subtotal">¥{(parseFloat(item.unit_price || 0) * item.quantity).toFixed(2)}</div>
                </div>
              ))}
            </div>
            
            {/* 计算最终价格 */}
            <div className="summary-calculation">
              <div className="calc-row">
                <span>商品总价</span>
                <span>¥{parseFloat(totalPrice).toFixed(2)}</span>
              </div>
              <div className="calc-row">
                <span>运费</span>
                <span>¥{parseFloat(shippingFee).toFixed(2)}</span>
              </div>
              {couponDiscount > 0 && (
                <div className="calc-row discount">
                  <span>优惠券折扣</span>
                  <span>-¥{parseFloat(couponDiscount).toFixed(2)}</span>
                </div>
              )}
              {memberDiscount > 0 && (
                <div className="calc-row discount member-discount">
                  <span>会员折扣({memberDiscountInfo.member_level} {memberDiscountInfo.discount_percentage}%折)</span>
                  <span>-¥{parseFloat(memberDiscount).toFixed(2)}</span>
                </div>
              )}
              <div className="calc-row total">
                <span>应付总额</span>
                <span>¥{parseFloat(finalPrice).toFixed(2)}</span>
              </div>
            </div>
            
            <button 
              className="submit-order-btn" 
              onClick={handleSubmitOrder}
              disabled={processingOrder}
            >
              {processingOrder ? '处理中...' : '提交订单'}
            </button>
          </div>
        </div>
      </div>
      
      {/* 充值模态框 */}
      {showRechargeModal && (
        <div className="modal-overlay" onClick={() => setShowRechargeModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>钱包充值</h3>
              <button className="close-btn" onClick={() => setShowRechargeModal(false)}>×</button>
            </div>
            
            <div className="modal-body">
              <div className="balance-display">
                <p>当前余额: ¥{walletBalance.toFixed(2)}</p>
                <p>订单金额: ¥{Math.max(0, totalPrice + shippingFee - couponDiscount - memberDiscount).toFixed(2)}</p>
                <p className="insufficient-notice">余额不足，请充值后继续支付</p>
              </div>
              
              <div className="recharge-form">
                <div className="form-group">
                  <label htmlFor="recharge-amount">充值金额</label>
                  <input
                    type="number"
                    id="recharge-amount"
                    value={rechargeAmount}
                    onChange={(e) => setRechargeAmount(e.target.value)}
                    placeholder="请输入充值金额"
                    min="1"
                    step="1"
                  />
                </div>
                
                <div className="recharge-qr">
                  <img src="/images/PayQRcode.jpg" alt="充值二维码" />
                  <p>扫码充值</p>
                </div>
              </div>
            </div>
            
            <div className="modal-footer">
              <button 
                className="btn btn-primary" 
                onClick={handleWalletRecharge}
                disabled={rechargingWallet || !rechargeAmount}
              >
                {rechargingWallet ? '充值中...' : '确认充值'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Checkout; 