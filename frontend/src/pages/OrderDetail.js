import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import '../styles/orderDetail.css';

const OrderDetail = () => {
  const { id: orderId } = useParams(); // 修改参数名，与App.js中的路由参数匹配
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showRefundModal, setShowRefundModal] = useState(false);
  const [refundReason, setRefundReason] = useState('');
  const [refundAmount, setRefundAmount] = useState('');
  const [refundType, setRefundType] = useState('refund_only');
  const [notification, setNotification] = useState({ show: false, message: '', type: '' });
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [selectedPaymentMethod, setSelectedPaymentMethod] = useState('');
  const [paymentStatus, setPaymentStatus] = useState('waiting'); // waiting, success, failed
  const [showRefundForm, setShowRefundForm] = useState(false);
  const [refundImages, setRefundImages] = useState([]);
  const [refundError, setRefundError] = useState('');
  const [refundSuccess, setRefundSuccess] = useState('');
  const [isProcessingRefund, setIsProcessingRefund] = useState(false);
  // 钱包支付相关状态
  const [showWalletConfirm, setShowWalletConfirm] = useState(false);
  const [walletBalance, setWalletBalance] = useState(0);
  const [loadingBalance, setLoadingBalance] = useState(false);
  // 售后申请相关状态
  const [showAfterSaleModal, setShowAfterSaleModal] = useState(false);
  const [selectedOrderItem, setSelectedOrderItem] = useState(null);
  const [afterSaleReason, setAfterSaleReason] = useState('');

  useEffect(() => {
    fetchOrderDetail();
  }, [orderId]);

  // 获取钱包余额
  const fetchWalletBalance = async () => {
    try {
      setLoadingBalance(true);
      const token = localStorage.getItem('token') || localStorage.getItem('access');
      
      const response = await axios.get('/api/member/members/current_member/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        }
      });
      
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

  // 辅助函数：尝试多种API路径获取订单详情
  const fetchOrderDetailWithRetry = async (token) => {
    let response = null;
    let error = null;
    
    // 判断orderId是数字ID还是订单号
    const isOrderNumber = typeof orderId === 'string' && orderId.startsWith('ORD');
    console.log(`订单ID类型: ${isOrderNumber ? '订单号' : 'ID'}, 值: ${orderId}`);
    
    // 根据orderId类型构建API路径
    const apiPaths = [];
    
    if (isOrderNumber) {
      // 如果是订单号，优先使用order_number查询
      apiPaths.push(
        `/api/order/orders/by-number/${orderId}/`, // 新添加的专门用于订单号查询的API
        `/api/order/orders/?order_number=${orderId}`,
        `/api/order/orders/${orderId}/`, // 后端已添加通过订单号查询的支持
        `/api/orders/?order_number=${orderId}`
      );
    } else {
      // 如果是ID，优先使用ID路径
      apiPaths.push(
        `/api/order/orders/${orderId}/`,
        `/api/orders/${orderId}/`
      );
    }
    
    // 添加通用路径作为后备
    apiPaths.push(`/api/order/orders/`);
    
    // 依次尝试每个API路径
    for (const apiPath of apiPaths) {
      try {
        console.log(`尝试API路径: ${apiPath}`);
        response = await axios.get(apiPath, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          }
        });
        
        if (response.status === 200) {
          console.log(`成功从 ${apiPath} 获取订单数据:`, response.data);
          
          // 如果是订单列表API，提取匹配的订单
          if (apiPath.includes('?order_number=')) {
            if (Array.isArray(response.data) && response.data.length > 0) {
              // 直接返回数组中的第一个匹配订单
              return response.data[0];
            } else if (response.data && response.data.results && Array.isArray(response.data.results)) {
              // DRF分页响应格式，查找匹配的订单
              const matchedOrder = response.data.results.find(order => 
                order.order_number === orderId || order.id.toString() === orderId
              );
              if (matchedOrder) return matchedOrder;
            }
          }
          
          // 如果是订单列表没有查询参数，尝试在结果中查找匹配订单
          if (apiPath === '/api/order/orders/' || apiPath === '/api/orders/') {
            if (response.data && response.data.results && Array.isArray(response.data.results)) {
              const matchedOrder = response.data.results.find(order => 
                order.order_number === orderId || order.id.toString() === orderId
              );
              if (matchedOrder) {
                console.log('在列表中找到匹配订单:', matchedOrder);
                return matchedOrder;
              }
            }
          }
          
          return response.data;
        }
      } catch (err) {
        console.log(`API路径 ${apiPath} 失败:`, err.message);
        error = err;
      }
    }
    
    // 所有尝试都失败
    throw error || new Error('无法获取订单详情');
  };

  const fetchOrderDetail = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token') || localStorage.getItem('access');
      
      // 首先检查localStorage中是否有最近的订单数据
      const latestOrderStr = localStorage.getItem('latest_order');
      if (latestOrderStr) {
        try {
          const latestOrder = JSON.parse(latestOrderStr);
          if (latestOrder && (latestOrder.id === orderId || latestOrder.order_number === orderId)) {
            console.log('使用本地存储的订单数据:', latestOrder);
            
            // 构建展示所需的订单数据
            const displayOrder = {
              ...latestOrder,
              status_display: getStatusDisplayName(latestOrder.status),
              can_pay: latestOrder.status === 'pending',
              can_cancel: ['pending', 'paid'].includes(latestOrder.status),
              can_confirm_receipt: latestOrder.status === 'delivered',
              // 使用本地存储的地址信息，或者提供默认值
              shipping_address: latestOrder.shipping_address || {
                full_address: '暂无地址信息'
              },
              recipient_name: latestOrder.recipient_name || '暂无收件人',
              recipient_phone: latestOrder.recipient_phone || '暂无联系电话',
              // 确保支付方式信息被保留
              payment_method: latestOrder.payment_method || 'alipay',
              payment_method_display: latestOrder.payment_method_display || '支付宝',
              // 确保商品信息存在
              items: latestOrder.items || []
            };
            
            setOrder(displayOrder);
            setLoading(false);
            
            // 尝试从API获取更完整的信息
            fetchFromApi(token);
            return;
          }
        } catch (e) {
          console.error('解析本地存储的订单数据失败:', e);
          // 继续尝试API获取
        }
      }
      
      if (!token) {
        // 使用模拟数据
        const mockOrder = {
          id: orderId,
          order_number: `ORD${Date.now()}`,
          status: 'pending', // 修改为待支付状态，以便测试支付功能
          status_display: '待支付',
          total_price: '299.00',
          total_amount: '289.00',
          shipping_fee: '10.00',
          discount_amount: '0.00',
          coupon_discount: '0.00',
          payment_method: '',
          payment_method_display: '',
          recipient_name: '张三',
          recipient_phone: '13800138000',
          shipping_address: '北京市朝阳区xxx街道xxx号',
          remark: '请尽快发货',
          created_at: new Date().toISOString(),
          paid_at: null,
          can_cancel: true,
          can_pay: true,
          can_confirm_receipt: false,
          items: [
            {
              id: 1,
              product_id: 1,
              product_name: 'iPhone 15 Pro',
              product_image: 'https://via.placeholder.com/100x100',
              product_sku: 'IP15P-256-BLU',
              variant_info: { color: '蓝色', storage: '256GB' },
              quantity: 1,
              unit_price: '289.00',
              total_price: '289.00'
            }
          ],
          status_history: [
            {
              id: 1,
              from_status: '',
              to_status: 'pending',
              remark: '订单创建',
              operator_name: '张三',
              created_at: new Date().toISOString()
            }
          ]
        };
        setOrder(mockOrder);
        setLoading(false);
        return;
      }

      // 直接从API获取
      fetchFromApi(token);
    } catch (err) {
      console.error('获取订单详情失败:', err);
      setError('网络错误，请稍后重试');
      setLoading(false);
    }
  };
  
  // 从API获取订单详情
  const fetchFromApi = async (token) => {
    try {
      console.log(`尝试从API获取订单详情: orderId=${orderId}`);
      
      // 使用辅助函数获取订单详情
      let orderData = await fetchOrderDetailWithRetry(token);
      
      // 检查是否需要从分页结果中提取单个订单
      if (orderData && orderData.results && Array.isArray(orderData.results)) {
        // 查找匹配的订单
        const matchedOrder = orderData.results.find(order => 
          order.order_number === orderId || order.id.toString() === orderId
        );
        
        if (matchedOrder) {
          console.log('从结果列表中找到匹配订单:', matchedOrder);
          orderData = matchedOrder;
        } else {
          console.warn('没有找到匹配订单号的订单:', orderId);
        }
      }
      
      // 记录原始数据，便于调试
      console.log('获取到的订单数据:', JSON.stringify(orderData, null, 2));
      
      // 获取本地存储的订单信息，保留支付方式
      const localOrderData = JSON.parse(localStorage.getItem('latest_order') || '{}');
      
      // 确保订单项数据正确
      if (orderData && orderData.items) {
        // 处理订单项数据，确保每个订单项都有正确的信息
        const processedItems = orderData.items.map(item => {
          console.log('处理订单项:', item);
          
          // 从product_variant中获取更多信息
          const productVariant = item.product_variant || {};
          const product = productVariant.product || {};
          
          return {
            ...item,
            // 使用原始订单中存储的商品名称，确保显示正确
            product_name: item.product_name || '未知商品',
            // 确保有商品图片
            product_image: item.product_image || '/images/Normal.jpg',
            // 确保价格格式正确
            price: parseFloat(item.price || item.unit_price || 0),
            unit_price: parseFloat(item.unit_price || item.price || 0),
            total_price: parseFloat(item.total_price || item.subtotal || (item.unit_price * item.quantity) || (item.price * item.quantity) || 0),
            // 添加变体信息
            variant_info: item.variant_info || {}
          };
        });
        
        // 保留原始订单数据，添加处理后的订单项
        orderData.items = processedItems;
      }
      
      // 处理收货地址
      if (orderData && typeof orderData.shipping_address === 'string') {
        try {
          // 尝试解析地址字符串为对象
          orderData.shipping_address = JSON.parse(orderData.shipping_address);
        } catch (e) {
          console.warn('无法解析地址字符串:', e);
        }
      }
      
      // 处理收件人信息
      if (orderData && orderData.recipient_info) {
        orderData.recipient_name = orderData.recipient_info.name || orderData.recipient_name;
        orderData.recipient_phone = orderData.recipient_info.phone || orderData.recipient_phone;
      }
      
      // 增加状态显示，保留支付方式信息
      const enhancedOrder = {
        ...orderData,
        status_display: getStatusDisplayName(orderData.status),
        can_pay: orderData.status === 'pending',
        can_cancel: ['pending', 'paid'].includes(orderData.status),
        can_confirm_receipt: orderData.status === 'delivered',
        // 保留本地存储中的支付方式信息
        payment_method: orderData.payment_method || localOrderData.payment_method,
        payment_method_display: orderData.payment_method_display || localOrderData.payment_method_display,
        // 确保收货地址信息
        shipping_address: orderData.shipping_address || localOrderData.shipping_address || '暂无地址信息',
        // 确保收件人信息
        recipient_name: orderData.recipient_name || localOrderData.recipient_name || '暂无收件人',
        recipient_phone: orderData.recipient_phone || localOrderData.recipient_phone || '暂无联系电话',
        // 确保金额信息字段存在
        total_amount: orderData.total_amount || orderData.subtotal || 0,
        shipping_fee: orderData.shipping_fee || 0,
        discount_amount: orderData.discount_amount || 0,
        // 确保meta信息存在
        meta: orderData.meta || {}
      };
      
      // 如果没有meta信息但有优惠券折扣，添加基本的meta信息
      if (enhancedOrder.discount_amount > 0 && (!enhancedOrder.meta || Object.keys(enhancedOrder.meta).length === 0)) {
        enhancedOrder.meta = {
          coupon_type: 'unknown',
          coupon_used: true
      };
      }
      
      setOrder(enhancedOrder);
      setLoading(false);
    } catch (err) {
      console.error('从API获取订单详情失败:', err);
      // 继续使用本地数据，如果有的话
      if (!order) {
        setError('无法获取订单详情，请稍后再试');
        setLoading(false);
      }
    }
  };
  
  // 根据订单状态获取显示名称
  const getStatusDisplayName = (status) => {
    const statusMap = {
      'pending': '待支付',
      'paid': '已支付',
      'processing': '处理中',
      'shipped': '已发货',
      'delivered': '已送达',
      'completed': '已完成',
      'cancelled': '已取消',
      'refunding': '退款中',
      'refunded': '已退款'
    };
    return statusMap[status] || status;
  };

  const handleCancelOrder = async () => {
    if (!window.confirm('确定要取消这个订单吗？')) return;

    try {
      const token = localStorage.getItem('token') || localStorage.getItem('access');
      
      // 检查订单ID是否为订单号格式
      const isOrderNumber = typeof orderId === 'string' && orderId.startsWith('ORD');
      console.log(`取消订单 - ID类型: ${isOrderNumber ? '订单号' : 'ID'}, 值: ${orderId}`);
      
      let cancelUrl;
      if (isOrderNumber) {
        // 使用专门的订单号取消API
        cancelUrl = `/api/order/orders/by-number/${orderId}/cancel/`;
      } else {
        // 使用常规ID取消API
        cancelUrl = `/api/order/orders/${orderId}/cancel/`;
      }
      
      console.log(`尝试取消订单，API路径: ${cancelUrl}`);
      
      const response = await axios.post(cancelUrl, {
        reason: '用户主动取消'
      }, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        }
      });

      console.log('取消订单响应:', response.data);
      
      if (response.status === 200) {
        showNotification('订单已取消', 'success');
        fetchOrderDetail();
      } else {
        showNotification('取消订单失败', 'error');
      }
    } catch (err) {
      console.error('取消订单失败:', err.message);
      console.error('错误详情:', err.response?.data);
      
      // 如果第一次尝试失败，尝试备用API
      if (err.response?.status === 404) {
        try {
          console.log('首选API失败，尝试备用API');
          const token = localStorage.getItem('token') || localStorage.getItem('access');
          
          // 尝试备用API路径
          let backupUrl;
          if (typeof orderId === 'string' && orderId.startsWith('ORD')) {
            // 使用常规ID取消API，但传入状态参数
            backupUrl = `/api/order/orders/?order_number=${orderId}`;
            
            // 先获取订单ID
            const orderResponse = await axios.get(backupUrl, {
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
              }
            });
            
            if (orderResponse.data && orderResponse.data.results && orderResponse.data.results.length > 0) {
              const actualOrderId = orderResponse.data.results[0].id;
              console.log(`找到订单ID: ${actualOrderId}, 尝试取消`);
              
              // 使用实际ID取消
              const cancelResponse = await axios.post(`/api/order/orders/${actualOrderId}/cancel/`, {
                reason: '用户主动取消'
              }, {
                headers: {
                  'Authorization': `Bearer ${token}`,
                  'Content-Type': 'application/json',
                }
              });
              
              if (cancelResponse.status === 200) {
                showNotification('订单已取消', 'success');
                fetchOrderDetail();
                return;
              }
            }
          }
        } catch (backupErr) {
          console.error('备用取消方法也失败:', backupErr.message);
        }
      }
      
      showNotification('网络错误，请稍后重试', 'error');
    }
  };

  const handlePayOrder = (paymentMethod) => {
    // 检查订单是否已有指定的支付方式
    if (order.payment_method && paymentMethod !== order.payment_method) {
      showNotification(`请使用结算时选择的${order.payment_method_display}支付`, 'error');
      return;
    }

    // 如果是钱包支付，显示确认对话框
    if (paymentMethod === 'balance') {
      setSelectedPaymentMethod(paymentMethod);
      fetchWalletBalance(); // 获取最新余额
      setShowWalletConfirm(true);
      return;
    }

    setSelectedPaymentMethod(paymentMethod);
    setPaymentStatus('waiting');
    setShowPaymentModal(true);
  };

  const handleConfirmPayment = async () => {
    try {
      setPaymentStatus('processing');
      
      const token = localStorage.getItem('token') || localStorage.getItem('access');
      if (!token) {
        setPaymentStatus('failed');
        showNotification('未登录，请先登录', 'error');
        return;
      }
      
      const response = await axios.post(`/api/order/orders/${orderId}/pay/`, {
        payment_method: selectedPaymentMethod
      }, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        }
      });

      if (response.status === 200) {
        setPaymentStatus('success');
        setTimeout(() => {
          setShowPaymentModal(false);
          showNotification('支付成功', 'success');
          fetchOrderDetail();
        }, 2000);
      } else {
        console.error('支付失败:', response.data);
        setPaymentStatus('failed');
        showNotification('支付失败，请稍后重试', 'error');
      }
    } catch (err) {
      console.error('支付错误:', err);
      setPaymentStatus('failed');
      showNotification('网络错误，请稍后重试', 'error');
    }
  };

  // 处理钱包支付确认
  const handleWalletPaymentConfirm = async () => {
    try {
      const token = localStorage.getItem('token') || localStorage.getItem('access');
      if (!token) {
        showNotification('未登录，请先登录', 'error');
        return;
      }

      // 计算订单总金额
      const totalAmount = 
        parseFloat(order.total_amount || 0) + 
        parseFloat(order.shipping_fee || 0) - 
        parseFloat(order.discount_amount || 0);

      // 检查余额是否足够
      if (walletBalance < totalAmount) {
        showNotification(`钱包余额不足！当前余额：¥${walletBalance.toFixed(2)}，需要：¥${totalAmount.toFixed(2)}`, 'error');
        return;
      }

      setShowWalletConfirm(false);
      
      const response = await axios.post(`/api/order/orders/${orderId}/pay/`, {
        payment_method: 'balance'
      }, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        }
      });

      if (response.status === 200) {
        showNotification('钱包支付成功！', 'success');
        fetchOrderDetail();
        // 刷新余额
        fetchWalletBalance();
      } else {
        console.error('钱包支付失败:', response.data);
        showNotification(response.data.message || '钱包支付失败，请稍后重试', 'error');
      }
    } catch (err) {
      console.error('钱包支付错误:', err);
      const errorMessage = err.response?.data?.message || err.response?.data?.error || '网络错误，请稍后重试';
      showNotification(errorMessage, 'error');
    }
  };

  // 处理售后申请
  const handleAfterSaleRequest = (orderItem) => {
    setSelectedOrderItem(orderItem);
    setShowAfterSaleModal(true);
  };

  const submitAfterSaleRequest = async () => {
    if (!afterSaleReason.trim()) {
      showNotification('请填写申请原因', 'error');
      return;
    }

    try {
      const token = localStorage.getItem('token') || localStorage.getItem('access');
      const response = await axios.post('/api/review/after-sale-requests/submit/', {
        order_item_id: selectedOrderItem.id,
        reason: afterSaleReason
      }, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        }
      });

      if (response.status === 201) {
        showNotification('售后申请提交成功，请等待处理', 'success');
        setShowAfterSaleModal(false);
        setAfterSaleReason('');
        setSelectedOrderItem(null);
        fetchOrderDetail(); // 刷新订单详情
      }
    } catch (err) {
      console.error('售后申请失败:', err);
      showNotification(err.response?.data?.error || '售后申请失败', 'error');
    }
  };

  const handleConfirmReceipt = async () => {
    if (!window.confirm('确定已收到商品吗？')) return;

    try {
      const token = localStorage.getItem('token') || localStorage.getItem('access');
      
      // 判断orderId是数字ID还是订单号
      const isOrderNumber = typeof orderId === 'string' && orderId.startsWith('ORD');
      console.log(`确认收货 - ID类型: ${isOrderNumber ? '订单号' : 'ID'}, 值: ${orderId}`);
      
      // 根据ID类型构建API路径
      let confirmUrl;
      if (isOrderNumber) {
        // 使用订单号API
        confirmUrl = `/api/order/orders/by-number/${orderId}/confirm_receipt/`;
      } else {
        // 使用ID API
        confirmUrl = `/api/order/orders/${orderId}/confirm_receipt/`;
      }
      
      console.log(`发送请求: ${confirmUrl} {}`);
      
      const response = await axios.post(confirmUrl, {}, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        }
      });

      if (response.status === 200) {
        const data = response.data;
        
        // 基本确认收货成功消息
        let message = '确认收货成功';
        
        // 如果返回了积分信息，添加到消息中
        if (data.points_added && data.points_added > 0) {
          message += `，获得 ${data.points_added} 积分`;
          if (data.current_points) {
            message += `，当前积分：${data.current_points}`;
          }
        }
        
        // 如果有等级升级，添加升级信息
        if (data.level_upgraded && data.level_message) {
          message += `。${data.level_message}`;
        }
        
        showNotification(message, 'success');
        fetchOrderDetail();
      } else {
        showNotification('确认收货失败', 'error');
      }
    } catch (err) {
      console.error('确认收货错误:', err);
      console.log('错误状态码:', err.response?.status);
      console.log('错误数据:', err.response?.data);
      
      if (err.response?.status === 404) {
        console.log('API路径不存在，请检查URL是否正确');
      }
      
      showNotification('网络错误，请稍后重试', 'error');
    }
  };

  const handleApplyRefund = async (e) => {
    e.preventDefault();
    
    if (!refundReason) {
      setRefundError('请填写退款原因');
      return;
    }
    
    if (!refundAmount || parseFloat(refundAmount) <= 0) {
      setRefundError('请输入有效的退款金额');
      return;
    }
    
    const actualPaidAmount = 
      parseFloat(order.total_amount || 0) + 
      parseFloat(order.shipping_fee || 0) - 
      parseFloat(order.discount_amount || 0);
      
    if (parseFloat(refundAmount) > actualPaidAmount) {
      setRefundError('退款金额不能超过实付金额');
      return;
    }

    try {
      setIsProcessingRefund(true);
      setRefundError('');
      
      const token = localStorage.getItem('access') || localStorage.getItem('token');
      
      const response = await axios.post(
        '/api/order/refunds/apply_refund/',
        {
          order_id: order.id,
        type: refundType,
        reason: refundReason,
          refund_amount: refundAmount,
          evidence_images: refundImages
        },
        {
        headers: {
          'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        }
        }
      );
      
      console.log('退款申请响应:', response.data);
      
      setRefundSuccess('退款申请已提交，请等待商家处理');
      setShowRefundForm(false);
      
      // 刷新订单数据
      fetchOrderDetail();
      
    } catch (err) {
      console.error('申请退款失败:', err);
      setRefundError(err.response?.data?.error || '申请退款失败，请稍后再试');
    } finally {
      setIsProcessingRefund(false);
    }
  };

  const handleImageUpload = (e) => {
    // 这里简化处理，实际项目中应该上传到服务器
    const files = Array.from(e.target.files);
    const imageUrls = files.map(file => URL.createObjectURL(file));
    setRefundImages([...refundImages, ...imageUrls]);
  };

  const handleRemoveImage = (index) => {
    const newImages = [...refundImages];
    newImages.splice(index, 1);
    setRefundImages(newImages);
  };

  const showNotification = (message, type) => {
    setNotification({ show: true, message, type });
    setTimeout(() => {
      setNotification({ show: false, message: '', type: '' });
    }, 3000);
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: '#f39c12',
      paid: '#3498db',
      processing: '#9b59b6',
      shipped: '#2ecc71',
      delivered: '#27ae60',
      completed: '#16a085',
      cancelled: '#e74c3c',
      refunding: '#e67e22',
      refunded: '#95a5a6'
    };
    return colors[status] || '#7f8c8d';
  };

  const getPaymentMethodIcon = (method) => {
    switch(method) {
      case 'alipay':
        return '支付宝';
      case 'wechat':
        return '微信支付';
      case 'bank_card':
        return '银行卡';
      case 'balance':
        return '钱包支付';
      default:
        return '其他方式';
    }
  };

  // 添加一个函数来获取退款状态的显示文本
  const getRefundStatusDisplay = (refund) => {
    if (!refund) return null;
    
    let statusText = '';
    switch (refund.status) {
      case 'pending':
        statusText = '退款申请处理中';
        break;
      case 'approved':
        statusText = '退款申请已同意，处理中';
        break;
      case 'rejected':
        statusText = '退款申请已拒绝';
        break;
      case 'completed':
        statusText = '退款已完成';
        break;
      default:
        statusText = '处理中';
    }
    
    // 添加优惠券退还信息
    if (refund.coupon_returned) {
      statusText += `，优惠券已退还`;
    }
    
    return statusText;
  };
  
  // 添加一个函数来获取退还的优惠券信息
  const getReturnedCouponInfo = (refund) => {
    if (!refund || !refund.coupon_returned) return null;
    
    return (
      <div className="returned-coupon-info">
        <h4>已退还的优惠券</h4>
        <div className="coupon-card returned">
          <div className="coupon-left">
            <div className="coupon-value">
              {refund.coupon_type === 'discount' ? (
                <span>{refund.coupon_value}<small>%</small></span>
              ) : (
                <span>¥{parseFloat(refund.coupon_value).toFixed(2)}</span>
              )}
            </div>
            <div className="coupon-condition">
              满{parseFloat(refund.coupon_min_amount).toFixed(2)}元可用
            </div>
          </div>
          <div className="coupon-right">
            <div className="coupon-name">{refund.coupon_code}</div>
            <div className="coupon-time">已退还至您的账户</div>
            <div className="coupon-status">
              <span className="status-available">可再次使用</span>
            </div>
          </div>
          <div className="coupon-type-tag">
            {refund.coupon_type === 'discount' ? '折扣券' : '满减券'}
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="order-detail-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>加载中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="order-detail-container">
        <div className="error-message">
          <p>{error}</p>
          <button onClick={() => navigate('/orders')} className="btn btn-primary">
            返回订单列表
          </button>
        </div>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="order-detail-container">
        <div className="error-message">
          <p>订单不存在</p>
          <button onClick={() => navigate('/orders')} className="btn btn-primary">
            返回订单列表
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="order-detail-container">
      {/* 通知 */}
      {notification.show && (
        <div className={`notification ${notification.type}`}>
          {notification.message}
        </div>
      )}

      {/* 面包屑导航 */}
      <div className="breadcrumb">
        <Link to="/">首页</Link>
        <span>/</span>
        <Link to="/orders">我的订单</Link>
        <span>/</span>
        <span>订单详情</span>
      </div>

      {/* 订单基本信息 */}
      <div className="order-header">
        <div className="order-info">
          <h1>订单详情</h1>
          <div className="order-meta">
            <span className="order-number">订单号：{order.order_number}</span>
            <span 
              className="order-status"
              style={{ color: getStatusColor(order.status) }}
            >
              {order.status_display}
            </span>
          </div>
          <div className="order-time">
            下单时间：{new Date(order.created_at).toLocaleString()}
          </div>
        </div>
        
        <div className="order-actions">
          {order.can_cancel && (
            <button onClick={handleCancelOrder} className="btn btn-outline">
              取消订单
            </button>
          )}
          {order.can_pay && (
            <div className="payment-buttons">
              {(!order.payment_method || order.payment_method === 'alipay') && (
                <button 
                  onClick={() => handlePayOrder('alipay')} 
                  className="btn btn-primary"
                >
                  支付宝支付
                </button>
              )}
              {(!order.payment_method || order.payment_method === 'wechat') && (
                <button 
                  onClick={() => handlePayOrder('wechat')} 
                  className="btn btn-success"
                >
                  微信支付
                </button>
              )}
              {(!order.payment_method || order.payment_method === 'balance') && (
                <button 
                  onClick={() => handlePayOrder('balance')} 
                  className="btn btn-wallet"
                  style={{ backgroundColor: '#ff6b35', color: 'white' }}
                >
                  余额支付
                </button>
              )}
              {order.payment_method && !['alipay', 'wechat', 'balance'].includes(order.payment_method) && (
                <button 
                  onClick={() => handlePayOrder(order.payment_method)} 
                  className="btn btn-primary"
                >
                  {order.payment_method_display || '其他支付方式'}
                </button>
              )}
            </div>
          )}
          {order.can_confirm_receipt && (
            <button onClick={handleConfirmReceipt} className="btn btn-success">
              确认收货
            </button>
          )}
          {['paid', 'shipped', 'delivered', 'completed'].includes(order.status) && (
            <button 
              className="refund-btn"
              onClick={() => setShowRefundForm(true)}
            >
              申请退款
            </button>
          )}
        </div>
      </div>

      {/* 收货信息 */}
      <div className="order-section">
        <h3>收货信息</h3>
        <div className="shipping-info">
          <div className="info-item">
            <span className="label">收货人：</span>
            <span>{order.recipient_name || '暂无收件人'}</span>
          </div>
          <div className="info-item">
            <span className="label">联系电话：</span>
            <span>{order.recipient_phone || '暂无联系电话'}</span>
          </div>
          <div className="info-item">
            <span className="label">收货地址：</span>
            <span>
              {typeof order.shipping_address === 'object' 
                ? (order.shipping_address.full_address || 
                   `${order.shipping_address.province || ''} ${order.shipping_address.city || ''} ${order.shipping_address.district || ''} ${order.shipping_address.detail || ''}`.trim() ||
                   '暂无地址信息') 
                : (order.shipping_address || '暂无地址信息')}
            </span>
          </div>
          {order.remark && (
            <div className="info-item">
              <span className="label">订单备注：</span>
              <span>{order.remark}</span>
            </div>
          )}
        </div>
      </div>

      {/* 商品信息 */}
      <div className="order-section">
        <h3>商品信息</h3>
        <div className="order-items">
          {order.items && order.items.length > 0 ? (
            order.items.map((item, index) => (
              <div key={item.id || `item-${index}`} className="order-item">
                <img 
                  src={item.product_image || '/images/Normal.jpg'} 
                  alt={item.product_name || '商品图片'}
                  className="item-image"
                  onError={(e) => {
                    e.target.onerror = null; 
                    e.target.src = '/images/Normal.jpg';
                  }}
                />
                <div className="item-info">
                  <h4>{item.product_name || '未知商品'}</h4>
                  <div className="item-variant">
                    {item.variant_name && (
                      <span className="variant-tag">
                        {item.variant_name}
                      </span>
                    )}
                    {item.variant_info && typeof item.variant_info === 'object' && 
                     Object.keys(item.variant_info).length > 0 ? 
                      Object.entries(item.variant_info).map(([key, value]) => (
                        <span key={key} className="variant-tag">
                          {key}: {value}
                        </span>
                      )) : 
                      (!item.variant_name && <span className="variant-tag">标准版</span>)
                    }
                  </div>
                  <div className="item-sku">SKU: {item.product_sku || item.variant_sku || '无'}</div>
                </div>
                <div className="item-quantity">x{item.quantity || 1}</div>
                <div className="item-price">¥{item.unit_price || item.price || 0}</div>
                <div className="item-total">¥{item.total_price || item.subtotal || ((item.quantity || 1) * (item.unit_price || item.price || 0))}</div>
                <div className="item-actions">
                  {/* 显示售后申请状态或按钮 */}
                  {item.after_sale_requests && item.after_sale_requests.length > 0 ? (
                    <div className="after-sale-status">
                      {item.after_sale_requests.map(request => (
                        <span key={request.id} className={`status-tag status-${request.status}`}>
                          售后: {request.status === 'pending' ? '待处理' : 
                                request.status === 'approved' ? '已批准' : '已拒绝'}
                        </span>
                      ))}
                    </div>
                  ) : (
                    item.can_request_after_sale && (
                      <button 
                        onClick={() => handleAfterSaleRequest(item)}
                        className="btn btn-outline btn-sm"
                      >
                        申请售后
                      </button>
                    )
                  )}
                </div>
              </div>
            ))
          ) : (
            <div className="empty-items">
              <p>暂无商品信息</p>
            </div>
          )}
        </div>
      </div>

      {/* 价格明细 */}
      <div className="order-section">
        <h3>价格明细</h3>
        <div className="price-details">
          <div className="price-item">
            <span>商品小计：</span>
            <span>¥{parseFloat(order.subtotal || order.total_amount || 0).toFixed(2)}</span>
          </div>
          <div className="price-item">
            <span>运费：</span>
            <span>¥{parseFloat(order.shipping_fee || 0).toFixed(2)}</span>
          </div>
          {parseFloat(order.discount_amount || 0) > 0 && (
            <div className="price-item discount">
              <span>优惠券折扣：</span>
              <span>-¥{parseFloat(order.discount_amount || 0).toFixed(2)}</span>
            </div>
          )}
          {parseFloat(order.member_discount || 0) > 0 && (
            <div className="price-item discount member-discount">
              <span>会员折扣({order.member_level || '会员'})：</span>
              <span>-¥{parseFloat(order.member_discount || 0).toFixed(2)}</span>
            </div>
          )}
          <div className="price-item total">
            <span>订单总额：</span>
            <span>¥{(
              parseFloat(order.total_amount || 0) + 
              parseFloat(order.shipping_fee || 0) - 
              parseFloat(order.discount_amount || 0) -
              parseFloat(order.member_discount || 0)
            ).toFixed(2)}</span>
          </div>
        </div>
      </div>

      {/* 支付信息 */}
        <div className="order-section">
          <h3>支付信息</h3>
          <div className="payment-info">
            <div className="info-item">
              <span className="label">支付方式：</span>
              <span>{order.payment_method_display || '未支付'}</span>
            </div>
            {order.paid_at && (
              <div className="info-item">
                <span className="label">支付时间：</span>
                <span>{new Date(order.paid_at).toLocaleString()}</span>
              </div>
            )}
            {order.payment_transaction_id && (
              <div className="info-item">
                <span className="label">交易号：</span>
                <span>{order.payment_transaction_id}</span>
              </div>
            )}
          </div>
        </div>
      
      {/* 优惠券信息 */}
      {parseFloat(order.discount_amount || 0) > 0 && (
        <div className="order-section">
          <h3>优惠券信息</h3>
          <div className="coupon-info">
            <div className="info-item">
              <span className="label">优惠类型：</span>
              <span>
                {order.meta && order.meta.coupon_type === 'fixed' && '满减券'}
                {order.meta && order.meta.coupon_type === 'discount' && '折扣券'}
                {order.meta && order.meta.coupon_type === 'free_shipping' && '包邮券'}
                {(!order.meta || !order.meta.coupon_type) && '优惠券'}
              </span>
            </div>
            <div className="info-item">
              <span className="label">优惠金额：</span>
              <span className="discount-amount">¥{parseFloat(order.discount_amount || 0).toFixed(2)}</span>
            </div>
            {order.meta && order.meta.coupon_code && (
              <div className="info-item">
                <span className="label">优惠券码：</span>
                <span>{order.meta.coupon_code}</span>
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* 退款信息 */}
      {order.refund && (
        <div className="order-section refund-section">
          <h3>退款信息</h3>
          <div className="refund-info">
              <div className="info-item">
              <span className="label">退款状态：</span>
              <span className={`refund-status ${order.refund.status}`}>
                {getRefundStatusDisplay(order.refund)}
              </span>
            </div>
            <div className="info-item">
              <span className="label">退款类型：</span>
              <span>
                {order.refund.type === 'refund_only' ? '仅退款' : 
                 order.refund.type === 'return_refund' ? '退货退款' : '其他'}
              </span>
            </div>
            <div className="info-item">
              <span className="label">退款金额：</span>
              <span className="refund-amount">¥{parseFloat(order.refund.amount).toFixed(2)}</span>
            </div>
            <div className="info-item">
              <span className="label">退款原因：</span>
              <span>{order.refund.reason || '无'}</span>
            </div>
            <div className="info-item">
              <span className="label">申请时间：</span>
              <span>{order.refund.created_at ? new Date(order.refund.created_at).toLocaleString() : '未知'}</span>
            </div>
            {order.refund.status === 'completed' && order.refund.completed_at && (
              <div className="info-item">
                <span className="label">完成时间：</span>
                <span>{new Date(order.refund.completed_at).toLocaleString()}</span>
              </div>
            )}
            
            {/* 退还的优惠券信息 */}
            {order.refund.coupon_returned && getReturnedCouponInfo(order.refund)}
          </div>
        </div>
      )}

      {/* 金额信息 */}
      <div className="order-section">
        <h3>金额信息</h3>
        <div className="price-info">
          <div className="info-item">
            <span className="label">商品金额：</span>
            <span>¥{parseFloat(order.total_amount || 0).toFixed(2)}</span>
          </div>
          <div className="info-item">
            <span className="label">运费：</span>
            <span>¥{parseFloat(order.shipping_fee || 0).toFixed(2)}</span>
          </div>
          {parseFloat(order.discount_amount || 0) > 0 && (
            <div className="info-item discount">
              <span className="label">优惠券折扣：</span>
              <span>-¥{parseFloat(order.discount_amount || 0).toFixed(2)}</span>
            </div>
          )}
          <div className="info-item total">
            <span className="label">实付金额：</span>
            <span className="total-price">¥{(
              parseFloat(order.total_amount || 0) + 
              parseFloat(order.shipping_fee || 0) - 
              parseFloat(order.discount_amount || 0)
            ).toFixed(2)}</span>
          </div>
        </div>
      </div>

      {/* 订单状态历史 */}
      {order.status_history && order.status_history.length > 0 && (
        <div className="order-section">
          <h3>订单状态</h3>
          <div className="status-timeline">
            {order.status_history.map(history => (
              <div key={history.id} className="timeline-item">
                <div className="timeline-dot"></div>
                <div className="timeline-content">
                  <div className="timeline-time">
                    {new Date(history.created_at).toLocaleString()}
                  </div>
                  <div className="timeline-text">{history.remark}</div>
                  {history.operator_name && (
                    <div className="timeline-operator">
                      操作人：{history.operator_name}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 退款表单 */}
      {showRefundForm && (
        <div className="refund-form-overlay">
          <div className="refund-form">
              <h3>申请退款</h3>
            
            <div className="form-group">
              <label>退款类型</label>
              <div className="refund-type-options">
                <label>
                  <input
                    type="radio"
                    name="refundType"
                    value="return_refund"
                    checked={refundType === 'return_refund'}
                    onChange={() => setRefundType('return_refund')}
                  />
                  退货退款 (退货后退款，将返还使用的优惠券)
                </label>
                <label>
                  <input
                    type="radio"
                    name="refundType"
                    value="refund_only"
                    checked={refundType === 'refund_only'}
                    onChange={() => setRefundType('refund_only')}
                  />
                  仅退款 (无需退货，将返还使用的优惠券)
                </label>
            </div>
            </div>
            
              <div className="form-group">
              <label>退款原因</label>
              <textarea
                value={refundReason}
                onChange={(e) => setRefundReason(e.target.value)}
                placeholder="请详细描述退款原因..."
                rows="3"
              ></textarea>
              </div>
            
              <div className="form-group">
              <label>退款金额</label>
                <input
                  type="number"
                  value={refundAmount}
                  onChange={(e) => setRefundAmount(e.target.value)}
                placeholder="请输入退款金额"
                min="0.01"
                  max={
                    parseFloat(order.total_amount || 0) + 
                    parseFloat(order.shipping_fee || 0) - 
                    parseFloat(order.discount_amount || 0)
                  }
                  step="0.01"
                />
              <div className="amount-hint">最大可退金额: ¥{(
                parseFloat(order.total_amount || 0) + 
                parseFloat(order.shipping_fee || 0) - 
                parseFloat(order.discount_amount || 0)
              ).toFixed(2)}</div>
              </div>
            
              <div className="form-group">
              <label>上传凭证 (选填)</label>
              <input
                type="file"
                accept="image/*"
                multiple
                onChange={handleImageUpload}
              />
              
              {refundImages.length > 0 && (
                <div className="uploaded-images">
                  {refundImages.map((image, index) => (
                    <div key={index} className="image-preview">
                      <img src={image} alt={`凭证 ${index + 1}`} />
                      <button type="button" onClick={() => handleRemoveImage(index)}>×</button>
              </div>
                  ))}
            </div>
              )}
            </div>
            
            {refundError && <div className="error-message">{refundError}</div>}
            
            <div className="form-actions">
              <button 
                type="button" 
                className="cancel-btn"
                onClick={() => setShowRefundForm(false)}
              >
                取消
              </button>
              <button 
                type="button" 
                className="submit-btn"
                onClick={handleApplyRefund}
                disabled={isProcessingRefund}
              >
                {isProcessingRefund ? '提交中...' : '提交申请'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 退款成功提示 */}
      {refundSuccess && (
        <div className="success-message">
          {refundSuccess}
        </div>
      )}

      {/* 支付二维码模态框 */}
      {showPaymentModal && (
        <div className="modal-overlay">
          <div className="modal payment-modal">
            <div className="modal-header">
              <h3>{getPaymentMethodIcon(selectedPaymentMethod)}付款</h3>
              <button 
                onClick={() => setShowPaymentModal(false)}
                className="modal-close"
              >
                ×
              </button>
            </div>
            <div className="modal-body payment-modal-body">
              {paymentStatus === 'waiting' && (
                <>
                  <div className="payment-amount">
                    <div className="amount-label">支付金额</div>
                    <div className="amount-value">¥{(
                      parseFloat(order?.total_amount || 0) + 
                      parseFloat(order?.shipping_fee || 0) - 
                      parseFloat(order?.discount_amount || 0)
                    ).toFixed(2)}</div>
                  </div>
                  <div className="payment-qrcode">
                    <img 
                      src="/images/PayQRcode.jpg" 
                      alt="支付二维码" 
                      style={{
                        maxWidth: '250px', 
                        margin: '0 auto', 
                        display: 'block',
                        border: '1px solid #eee',
                        borderRadius: '4px',
                        padding: '10px'
                      }}
                    />
                    <p style={{textAlign: 'center', marginTop: '10px'}}>
                      请使用{getPaymentMethodIcon(selectedPaymentMethod)}扫描二维码完成支付
                    </p>
                  </div>
                  <div className="payment-tips">
                    <p>二维码有效期为5分钟，请尽快完成支付</p>
                    <p>支付完成后，请点击"我已支付"按钮</p>
                  </div>
                </>
              )}
              
              {paymentStatus === 'processing' && (
                <div className="payment-processing">
                  <div className="loading-spinner">
                    <div className="spinner"></div>
                  </div>
                  <p>正在验证支付结果，请稍候...</p>
                </div>
              )}
              
              {paymentStatus === 'success' && (
                <div className="payment-success">
                  <div className="success-icon">✓</div>
                  <p>支付成功！</p>
                  <p>订单状态已更新</p>
                </div>
              )}
              
              {paymentStatus === 'failed' && (
                <div className="payment-failed">
                  <div className="failed-icon">✗</div>
                  <p>支付失败！</p>
                  <p>请重新尝试支付</p>
                </div>
              )}
            </div>
            <div className="modal-footer">
              {paymentStatus === 'waiting' && (
                <>
                  <button 
                    onClick={() => setShowPaymentModal(false)}
                    className="btn btn-outline"
                  >
                    取消支付
                  </button>
                  <button 
                    onClick={handleConfirmPayment}
                    className="btn btn-primary"
                  >
                    我已支付
                  </button>
                </>
              )}
              
              {paymentStatus === 'failed' && (
                <>
                  <button 
                    onClick={() => setShowPaymentModal(false)}
                    className="btn btn-outline"
                  >
                    取消
                  </button>
                  <button 
                    onClick={() => setPaymentStatus('waiting')}
                    className="btn btn-primary"
                  >
                    重新支付
                  </button>
                </>
              )}
              
              {paymentStatus === 'success' && (
                <button 
                  onClick={() => setShowPaymentModal(false)}
                  className="btn btn-primary"
                >
                  确定
                </button>
              )}
            </div>
          </div>
        </div>
              )}

      {/* 售后申请模态框 */}
      {showAfterSaleModal && (
        <div className="modal-overlay">
          <div className="modal after-sale-modal">
            <div className="modal-header">
              <h3>申请售后</h3>
              <button 
                onClick={() => setShowAfterSaleModal(false)}
                className="modal-close"
              >
                ×
              </button>
            </div>
            <div className="modal-body">
              <div className="after-sale-content">
                {selectedOrderItem && (
                  <div className="selected-item">
                    <h4>申请商品</h4>
                    <div className="item-info">
                      <span className="item-name">{selectedOrderItem.product_name}</span>
                      {selectedOrderItem.variant_name && (
                        <span className="item-variant">({selectedOrderItem.variant_name})</span>
                      )}
                      <span className="item-quantity">数量: {selectedOrderItem.quantity}</span>
                    </div>
                  </div>
                )}
                <div className="reason-section">
                  <label htmlFor="afterSaleReason">申请原因 *</label>
                  <textarea
                    id="afterSaleReason"
                    value={afterSaleReason}
                    onChange={(e) => setAfterSaleReason(e.target.value)}
                    placeholder="请详细描述申请售后的原因..."
                    rows="4"
                    className="form-textarea"
                  />
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button 
                onClick={() => setShowAfterSaleModal(false)}
                className="btn btn-outline"
              >
                取消
              </button>
              <button 
                onClick={submitAfterSaleRequest}
                className="btn btn-primary"
                disabled={!afterSaleReason.trim()}
              >
                提交申请
              </button>
            </div>
          </div>
        </div>
              )}

      {/* 钱包支付确认模态框 */}
      {showWalletConfirm && (
        <div className="modal-overlay">
          <div className="modal wallet-confirm-modal">
            <div className="modal-header">
              <h3>钱包支付确认</h3>
              <button 
                onClick={() => setShowWalletConfirm(false)}
                className="modal-close"
              >
                ×
              </button>
            </div>
            <div className="modal-body">
              <div className="wallet-confirm-content">
                <p>您选择使用钱包支付，请确认以下信息：</p>
                <div className="payment-summary">
                  <div className="summary-item">
                    <span>订单总额：</span>
                    <span className="amount">¥{(
                      parseFloat(order.total_amount || 0) + 
                      parseFloat(order.shipping_fee || 0) - 
                      parseFloat(order.discount_amount || 0) -
                      parseFloat(order.member_discount || 0)
                    ).toFixed(2)}</span>
                  </div>
                  <div className="summary-item">
                    <span>当前钱包余额：</span>
                    <span className={`amount ${walletBalance >= (
                      parseFloat(order.total_amount || 0) + 
                      parseFloat(order.shipping_fee || 0) - 
                      parseFloat(order.discount_amount || 0)
                    ) ? 'sufficient' : 'insufficient'}`}>
                      ¥{walletBalance.toFixed(2)}
                    </span>
                  </div>
                </div>
                <p className="confirm-question">是否确认使用钱包支付？</p>
              </div>
            </div>
            <div className="modal-footer">
              <button 
                onClick={() => setShowWalletConfirm(false)}
                className="btn btn-outline"
              >
                取消支付
              </button>
              <button 
                onClick={handleWalletPaymentConfirm}
                className="btn btn-primary"
                disabled={walletBalance < (
                  parseFloat(order.total_amount || 0) + 
                  parseFloat(order.shipping_fee || 0) - 
                  parseFloat(order.discount_amount || 0)
                )}
              >
                确认支付
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default OrderDetail;