import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import '../styles/orderList.css';
import axios from 'axios'; // 导入 axios

const OrderList = () => {
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('all');
  const [notification, setNotification] = useState({ show: false, message: '', type: '' });
  const [statusTabs, setStatusTabs] = useState([
    { key: 'all', label: '全部订单', count: 0 },
    { key: 'pending', label: '待支付', count: 0 },
    { key: 'paid', label: '待发货', count: 0 },
    { key: 'shipped', label: '待收货', count: 0 },
    { key: 'delivered', label: '已送达', count: 0 },
    { key: 'completed', label: '已完成', count: 0 },
    { key: 'cancelled', label: '已取消', count: 0 },
  ]);
  
  // 添加删除中状态
  const [deletingOrderId, setDeletingOrderId] = useState(null);
  
  // 存储已评价商品的ID
  const [reviewedProducts, setReviewedProducts] = useState({});

  useEffect(() => {
    fetchOrders();
  }, [activeTab]);

  const fetchOrders = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token') || localStorage.getItem('access');
      
      if (!token) {
        // 未登录时重定向到登录页面
        navigate('/login', { state: { from: '/orders' } });
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

      // 构建API URL
      let url = '/api/order/orders/';
      if (activeTab !== 'all') {
        url = `/api/order/orders/?status=${activeTab}`;
      }
      
      console.log('获取订单列表:', url);
        
      const response = await axios.get(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      console.log('订单API响应:', response.data);

      // 处理API返回的订单数据
      if (response.status === 200) {
        let orderData = [];
        
        // 处理不同响应格式
        if (Array.isArray(response.data)) {
          orderData = response.data;
        } else if (response.data && response.data.results && Array.isArray(response.data.results)) {
          orderData = response.data.results;
        } else if (response.data && typeof response.data === 'object') {
          orderData = [response.data];
        }
        
        // 过滤掉已删除的订单
        orderData = orderData.filter(order => 
          !deletedOrders.includes(order.id) && 
          !deletedOrders.includes(order.order_number)
        );
        
        // 处理每个订单的状态显示和字段格式
        const formattedOrders = orderData.map(order => ({
          id: order.id,
          order_number: order.order_number,
          status: order.status,
          status_display: order.status_display || getStatusDisplayName(order.status),
          total_price: parseFloat(order.total_price || order.total_amount || 0),
          created_at: order.created_at,
          can_cancel: order.can_cancel !== undefined ? order.can_cancel : ['pending', 'paid'].includes(order.status),
          can_pay: order.can_pay !== undefined ? order.can_pay : order.status === 'pending',
          can_confirm_receipt: order.can_confirm_receipt !== undefined ? order.can_confirm_receipt : order.status === 'delivered',
          tracking_number: order.tracking_number,
          shipping_company: order.shipping_company,
          items: Array.isArray(order.items) ? order.items.map(item => ({
            id: item.id,
            product_id: item.product_id || item.product_variant?.product?.id,
            product_name: item.product_name,
            product_image: item.product_image || '/images/Normal.jpg',
            quantity: parseInt(item.quantity) || 1,
            unit_price: parseFloat(item.price || item.unit_price || 0)
          })) : []
        }));
        
        // 根据当前标签过滤订单
        const filteredOrders = activeTab === 'all' 
          ? formattedOrders 
          : formattedOrders.filter(order => order.status === activeTab);
        
        setOrders(filteredOrders);
        
        // 更新标签计数
        updateTabCounts(formattedOrders);
        
        // 检查已完成订单中的商品是否已经被评价
        checkReviewedProducts(filteredOrders.filter(order => order.status === 'completed'));
      } else if (response.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('access');
        navigate('/login');
      } else {
        setError('获取订单列表失败');
      }
    } catch (err) {
      console.error('获取订单失败:', err);
      setError('网络错误，请稍后重试');
    } finally {
      setLoading(false);
    }
  };
  
  // 检查已完成订单中的商品是否已被评价
  const checkReviewedProducts = async (completedOrders) => {
    if (completedOrders.length === 0) return;
    
    try {
      const token = localStorage.getItem('token') || localStorage.getItem('access');
      if (!token) return;
      
      // 获取用户所有评价
      const response = await axios.get('/api/review/reviews/user-reviews/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        }
      });
      
      if (response.status === 200 && Array.isArray(response.data)) {
        // 创建已评价商品的映射
        const reviewedMap = {};
        
        response.data.forEach(review => {
          reviewedMap[review.product_id] = true;
        });
        
        setReviewedProducts(reviewedMap);
      }
    } catch (err) {
      console.error('获取用户评价失败:', err);
    }
  };
  
  // 检查商品是否已被评价
  const isProductReviewed = (productId) => {
    return reviewedProducts[productId] === true;
  };
  
  // 更新标签计数
  const updateTabCounts = (orders) => {
    const counts = {
      all: orders.length,
      pending: 0,
      paid: 0,
      shipped: 0,
      delivered: 0,
      completed: 0,
      cancelled: 0
    };
    
    // 计算每个状态的订单数量
    orders.forEach(order => {
      if (counts[order.status] !== undefined) {
        counts[order.status]++;
      }
    });
    
    // 更新标签状态
    setStatusTabs(prev => prev.map(tab => ({
      ...tab,
      count: counts[tab.key] || 0
    })));
  };

  const handleCancelOrder = async (orderId) => {
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
        },
      });
      
      console.log('取消订单响应:', response.data);

      if (response.status === 200) {
        showNotification('订单已取消', 'success');
        fetchOrders();
      } else {
        showNotification('取消订单失败', 'error');
      }
    } catch (err) {
      console.error('取消订单错误:', err);
      console.log('错误详情:', err.message);
      console.log('响应状态:', err.response?.status);
      console.log('响应数据:', err.response?.data);
      
      // 如果第一次尝试失败，尝试备用API
      if (err.response?.status === 404) {
        try {
          console.log('首选API失败，尝试备用API');
          const token = localStorage.getItem('token') || localStorage.getItem('access');
          
          // 尝试备用API路径
          let backupUrl;
          if (typeof orderId === 'string' && orderId.startsWith('ORD')) {
            // 使用查询参数获取订单ID
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
                fetchOrders();
                return;
              }
            }
          }
        } catch (backupErr) {
          console.error('备用取消方法也失败:', backupErr.message);
        }
      }
      
      showNotification('取消订单失败，请稍后重试', 'error');
    }
  };

  const handlePayOrder = async (orderId, paymentMethod) => {
    try {
      const token = localStorage.getItem('token') || localStorage.getItem('access');
      const response = await axios.post(`/api/order/orders/${orderId}/pay/`, { payment_method: paymentMethod }, { // 修正API路径
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.status === 200) {
        showNotification('支付成功', 'success');
        fetchOrders();
      } else {
        showNotification('支付失败', 'error');
      }
    } catch (err) {
      console.error('支付订单错误:', err);
      showNotification('支付失败，请稍后重试', 'error');
    }
  };

  const handleConfirmReceipt = async (orderId) => {
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
      
      console.log(`发送请求: ${confirmUrl}`);
      
      const response = await axios.post(confirmUrl, {}, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
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
        fetchOrders();
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
      
      showNotification('确认收货失败，请稍后重试', 'error');
    }
  };

  const handleDeleteOrder = async (orderId) => {
    if (!window.confirm('确定要删除这个订单吗？删除后将无法恢复。')) {
      return;
    }

    try {
      setDeletingOrderId(orderId);
      
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
      
      // 尝试调用API删除订单（如果有）
      const token = localStorage.getItem('token') || localStorage.getItem('access');
      if (token) {
        try {
          await axios.delete(`/api/order/orders/${orderId}/`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            }
          });
          console.log(`订单 ${orderId} 已从服务器删除`);
        } catch (apiError) {
          console.log(`API删除失败，仅在本地标记为已删除: ${apiError.message}`);
          // 即使API删除失败，我们仍然在前端标记为已删除
        }
      }
      
      // 更新标签计数
      updateTabCounts(orders.filter(order => order.id !== orderId));
      
      showNotification('订单已成功删除', 'success');
    } catch (error) {
      console.error('删除订单错误:', error);
      showNotification('删除订单失败，请稍后重试', 'error');
    } finally {
      setDeletingOrderId(null);
    }
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

  const getStatusDisplayName = (status) => {
    const displayNames = {
      pending: '待支付',
      paid: '待发货',
      shipped: '待收货',
      delivered: '已送达',
      completed: '已完成',
      cancelled: '已取消',
      refunding: '退款中',
      refunded: '已退款',
      processing: '处理中'
    };
    return displayNames[status] || status;
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) {
      return '今天 ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    } else if (diffDays === 2) {
      return '昨天 ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    } else if (diffDays <= 7) {
      return `${diffDays - 1}天前`;
    } else {
      return date.toLocaleDateString('zh-CN');
    }
  };

  if (loading) {
    return (
      <div className="order-list-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>加载中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="order-list-container">
      {/* 通知 */}
      {notification.show && (
        <div className={`notification ${notification.type}`}>
          {notification.message}
        </div>
      )}

      {/* 页面标题 */}
      <div className="page-header">
        <h1>我的订单</h1>
        <div className="breadcrumb">
          <Link to="/">首页</Link>
          <span>/</span>
          <span>我的订单</span>
        </div>
      </div>

      {/* 订单状态标签 */}
      <div className="order-tabs">
        {statusTabs.map(tab => (
          <button
            key={tab.key}
            className={`tab-button ${activeTab === tab.key ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
            {tab.count > 0 && <span className="tab-count">({tab.count})</span>}
          </button>
        ))}
      </div>

      {/* 订单列表 */}
      <div className="order-list">
        {error ? (
          <div className="error-message">
            <p>{error}</p>
            <button onClick={fetchOrders} className="btn btn-primary">
              重新加载
            </button>
          </div>
        ) : orders.length === 0 ? (
          <div className="empty-orders">
            <div className="empty-icon">📦</div>
            <h3>暂无订单</h3>
            <p>您还没有任何订单，去逛逛吧！</p>
            <Link to="/products" className="btn btn-primary">
              去购物
            </Link>
          </div>
        ) : (
          orders.map(order => (
            <div key={order.id} className="order-card">
              {/* 订单头部 */}
              <div className="order-header">
                <div className="order-info">
                  <span className="order-number">订单号：{order.order_number}</span>
                  <span className="order-time">{formatDate(order.created_at)}</span>
                </div>
                <div className="order-status">
                  <span 
                    className="status-badge"
                    style={{ backgroundColor: getStatusColor(order.status) }}
                  >
                    {order.status_display}
                  </span>
                </div>
              </div>

              {/* 订单商品 */}
              <div className="order-items">
                {order.items.map(item => (
                  <div key={item.id} className="order-item">
                    <img 
                      src={item.product_image || 'https://via.placeholder.com/80x80'} 
                      alt={item.product_name}
                      className="item-image"
                    />
                    <div className="item-info">
                      <h4>{item.product_name}</h4>
                      {item.variant_info && (
                        <div className="item-variant">
                          {Object.entries(item.variant_info).map(([key, value]) => (
                            <span key={key} className="variant-tag">
                              {key}: {value}
                            </span>
                          ))}
                        </div>
                      )}
                      {/* 显示售后申请状态 */}
                      {item.after_sale_requests && item.after_sale_requests.length > 0 && (
                        <div className="after-sale-status">
                          {item.after_sale_requests.map(request => (
                            <span key={request.id} className={`status-tag status-${request.status}`}>
                              售后: {request.status === 'pending' ? '待处理' : 
                                    request.status === 'approved' ? '已批准' : '已拒绝'}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    <div className="item-quantity">x{item.quantity}</div>
                    <div className="item-price">¥{item.unit_price}</div>
                  </div>
                ))}
              </div>

              {/* 物流信息 */}
              {order.tracking_number && (
                <div className="shipping-info">
                  <span className="shipping-company">{order.shipping_company}</span>
                  <span className="tracking-number">运单号：{order.tracking_number}</span>
                </div>
              )}

              {/* 订单底部 */}
              <div className="order-footer">
                <div className="order-total">
                  <span>共{order.items.reduce((sum, item) => sum + item.quantity, 0)}件商品</span>
                  <span className="total-price">合计：¥{order.total_price}</span>
                </div>
                <div className="order-actions">
                  <Link 
                    to={`/order/${order.id}`} 
                    className="btn btn-outline"
                    onClick={() => {
                      // 将完整订单数据存储到localStorage，以便订单详情页使用
                      localStorage.setItem('latest_order', JSON.stringify({
                        ...order,
                        items: order.items.map(item => ({
                          ...item,
                          id: item.id,
                          product_id: item.product_id || item.id,
                          product_name: item.product_name,
                          product_image: item.product_image,
                          unit_price: item.unit_price,
                          total_price: item.unit_price * item.quantity,
                        }))
                      }));
                    }}
                  >
                    查看详情
                  </Link>
                  
                  {order.can_cancel && (
                    <button 
                      onClick={() => handleCancelOrder(order.id)}
                      className="btn btn-outline"
                    >
                      取消订单
                    </button>
                  )}
                  
                  {order.can_pay && (
                    <div className="payment-actions">
                      <Link
                        to={`/order/${order.id}`}
                        className="btn btn-primary"
                        onClick={() => {
                          // 将完整订单数据存储到localStorage，并设置为可支付状态
                          localStorage.setItem('latest_order', JSON.stringify({
                            ...order,
                            can_pay: true,
                            items: order.items.map(item => ({
                              ...item,
                              id: item.id,
                              product_id: item.product_id || item.id,
                              product_name: item.product_name,
                              product_image: item.product_image,
                              unit_price: item.unit_price,
                              total_price: item.unit_price * item.quantity,
                            }))
                          }));
                        }}
                      >
                        立即支付
                      </Link>
                    </div>
                  )}
                  
                  {order.can_confirm_receipt && (
                    <button 
                      onClick={() => handleConfirmReceipt(order.id)}
                      className="btn btn-success"
                    >
                      确认收货
                    </button>
                  )}
                  
                  {order.tracking_number && (
                    <Link 
                      to={`/orders/${order.id}/tracking`}
                      className="btn btn-outline"
                    >
                      查看物流
                    </Link>
                  )}
                  
                  {['completed'].includes(order.status) && order.items[0]?.product_id && (
                    <Link 
                      to={`/products/${order.items[0]?.product_id}/review`}
                      className="btn btn-outline"
                    >
                      {isProductReviewed(order.items[0]?.product_id) ? '查看/修改评价' : '评价商品'}
                    </Link>
                  )}
                  
                  {/* 删除按钮 - 所有订单都可以删除 */}
                  <button 
                    onClick={() => handleDeleteOrder(order.id)}
                    className="btn btn-danger"
                    disabled={deletingOrderId === order.id}
                  >
                    {deletingOrderId === order.id ? '删除中...' : '删除订单'}
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* 分页 */}
      {orders.length > 0 && (
        <div className="pagination">
          <button className="btn btn-outline" disabled>
            上一页
          </button>
          <span className="page-info">第 1 页，共 1 页</span>
          <button className="btn btn-outline" disabled>
            下一页
          </button>
        </div>
      )}
    </div>
  );
};

export default OrderList;