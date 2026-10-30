import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import '../styles/cart.css';
import { getProductDetailImage, processImageUrl } from '../utils/productUtils';

// 获取商品图片
const getProductImage = (product) => {
  // 记录商品数据以便调试
  console.log('尝试获取图片:', product?.product_info);
  
  // 优先使用商品详情页的第一张图片
  if (product?.product_info) {
    return getProductDetailImage(product.product_info);
  }
  
  // 首先尝试从product_image直接获取（新增字段）
  if (product?.product_image) {
    return product.product_image;
  }
  
  // 1. 从product_info.image获取
  if (product?.product_info?.image) {
    const processedUrl = processImageUrl(product.product_info.image);
    console.log('处理后的图片URL:', processedUrl);
    return processedUrl;
  }
  
  // 2. 从variant_info.image获取（如果有）
  if (product?.variant_info?.image) {
    const processedUrl = processImageUrl(product.variant_info.image);
    return processedUrl;
  }
  
  // 3. 使用默认图片
  console.log('使用默认图片');
  return '/images/Normal.jpg';
};

// 获取产品背景色
const getProductBackgroundColor = (product, index) => {
  const colors = [
    'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)', // 紫色
    'linear-gradient(135deg, #0ea5e9 0%, #10b981 100%)', // 蓝绿色
    'linear-gradient(135deg, #f97316 0%, #ef4444 100%)', // 橙红色
    'linear-gradient(135deg, #14b8a6 0%, #0d9488 100%)', // 青色
    'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)', // 深紫色
    'linear-gradient(135deg, #ec4899 0%, #db2777 100%)'  // 粉色
  ];
  
  // 根据产品ID或索引选择一个颜色
  const colorIndex = product && product.id ? product.id % colors.length : index % colors.length;
  return colors[colorIndex];
};

const Cart = () => {
  const [cartItems, setCartItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [totalPrice, setTotalPrice] = useState(0);
  const [updatingItem, setUpdatingItem] = useState(null);
  const [removingItem, setRemovingItem] = useState(null);
  const [fadeOutItems, setFadeOutItems] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    fetchCartItems();
  }, []);

  const fetchCartItems = async () => {
    try {
      const token = localStorage.getItem('access') || localStorage.getItem('token');
      
      if (!token) {
        navigate('/login', { state: { from: '/cart' } });
        return;
      }

      console.log('发送请求: /api/cart/cart/', token);
      const response = await axios.get('/api/cart/cart/', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      console.log('购物车数据:', response.data);
      
      if (response.data && response.data.items) {
        // 详细打印每个商品的信息，特别是图片路径
        response.data.items.forEach((item, index) => {
          console.log(`商品 ${index + 1} 详情:`, {
            id: item.id,
            name: item.product_info?.name,
            image: item.product_info?.image,
            price: item.unit_price
          });
        });
        
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
        navigate('/login', { state: { from: '/cart' } });
      }
    }
  };

  const handleUpdateQuantity = async (itemId, newQuantity) => {
    if (newQuantity < 1) return;
    
    try {
      setUpdatingItem(itemId);
      const token = localStorage.getItem('access') || localStorage.getItem('token');
      
      // 添加详细的调试日志
      const apiUrl = '/api/cart/cart/update_item/';
      const requestData = {
        cart_item_id: itemId,
        quantity: newQuantity
      };
      console.log('发送购物车更新请求:', apiUrl);
      console.log('请求数据:', requestData);
      console.log('Token信息:', token ? '已设置' : '未设置');
      
      await axios.post(apiUrl, requestData, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      // 更新本地状态
      const updatedItems = cartItems.map(item => {
        if (item.id === itemId) {
          const price = typeof item.unit_price === 'number' ? item.unit_price : 0;
          return {
            ...item,
            quantity: newQuantity,
            subtotal: price * newQuantity
          };
        }
        return item;
      });
      
      setCartItems(updatedItems);
      
      // 重新计算总价
      const total = updatedItems.reduce((sum, item) => {
        const price = typeof item.unit_price === 'number' ? item.unit_price : 0;
        return sum + (price * item.quantity);
      }, 0);
      
      setTotalPrice(total);
      
      // 清除更新状态
      setTimeout(() => {
        setUpdatingItem(null);
      }, 500);
    } catch (err) {
      // 详细的错误日志
      console.error('更新购物车失败:', err);
      console.log('错误详情:', err.message);
      console.log('响应错误:', err.response);
      console.log('错误状态码:', err.response?.status);
      console.log('错误数据:', err.response?.data);
      
      if (err.response?.status === 404) {
        console.log('API路径不存在，请检查URL是否正确');
      } else if (err.response?.status === 401) {
        console.log('认证失败，请检查Token是否正确');
      } else if (err.response?.status === 400) {
        console.log('请求参数错误:', err.response?.data);
      } else if (err.response?.status >= 500) {
        console.log('服务器内部错误');
      }
      
      setUpdatingItem(null);
      
      // 显示错误提示
      const errorMessage = err.response?.data?.error || '更新购物车失败，请稍后再试';
      showNotification(errorMessage, 'error');
    }
  };

  const handleRemoveItem = async (itemId) => {
    try {
      // 设置正在删除的商品
      setRemovingItem(itemId);
      setFadeOutItems([...fadeOutItems, itemId]);
      
      const token = localStorage.getItem('access') || localStorage.getItem('token');
      
      // 等待动画完成
      setTimeout(async () => {
        await axios.post('/api/cart/cart/remove_item/', {
          cart_item_id: itemId
        }, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        // 从本地状态移除
        const updatedItems = cartItems.filter(item => item.id !== itemId);
        setCartItems(updatedItems);
        
        // 重新计算总价
        const total = updatedItems.reduce((sum, item) => {
          const price = typeof item.unit_price === 'number' ? item.unit_price : 0;
          return sum + (price * item.quantity);
        }, 0);
        
        setTotalPrice(total);
        setRemovingItem(null);
        setFadeOutItems(fadeOutItems.filter(id => id !== itemId));
        
        // 显示成功提示
        showNotification('商品已从购物车中移除', 'success');
      }, 300);
    } catch (err) {
      console.error('移除商品失败:', err);
      setRemovingItem(null);
      setFadeOutItems(fadeOutItems.filter(id => id !== itemId));
      
      // 显示错误提示
      const errorMessage = err.response?.data?.error || '移除商品失败，请稍后再试';
      showNotification(errorMessage, 'error');
    }
  };

  const handleClearCart = async () => {
    if (!window.confirm('确定要清空购物车吗？')) return;
    
    try {
      const token = localStorage.getItem('access') || localStorage.getItem('token');
      
      // 设置所有商品为淡出状态
      setFadeOutItems(cartItems.map(item => item.id));
      
      // 等待动画完成
      setTimeout(async () => {
        await axios.delete('/api/cart/cart/clear/', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        setCartItems([]);
        setTotalPrice(0);
        setFadeOutItems([]);
        
        // 显示成功提示
        showNotification('购物车已清空', 'success');
      }, 300);
    } catch (err) {
      console.error('清空购物车失败:', err);
      setFadeOutItems([]);
      
      // 显示错误提示
      const errorMessage = err.response?.data?.error || '清空购物车失败，请稍后再试';
      showNotification(errorMessage, 'error');
    }
  };

  const handleCheckout = () => {
    if (cartItems.length === 0) {
      showNotification('购物车为空，无法结算', 'error');
      return;
    }
    navigate('/checkout');
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

  if (loading) {
    return (
      <div className="loading">
        <div className="loading-spinner"></div>
        <p>加载购物车中...</p>
      </div>
    );
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  if (cartItems.length === 0) {
    return (
      <div className="cart-container">
      <div className="cart-empty">
          <div className="empty-icon">
            <div className="cart-animation">
              🛒
              <div className="sparkles">
                <span className="sparkle">✨</span>
                <span className="sparkle">✨</span>
                <span className="sparkle">✨</span>
              </div>
            </div>
          </div>
          <h2>购物车空空如也</h2>
          <p>还没有挑选到心仪的商品？<br/>快去发现更多精彩好物吧！</p>
          <div className="empty-actions">
            <Link to="/products" className="continue-shopping-btn">
              <span className="btn-icon">🛍️</span>
              开始购物
              <span className="btn-arrow">→</span>
        </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="cart-container">
      <h1>购物车</h1>
      <div className="cart-actions">
        <button className="clear-cart" onClick={handleClearCart}>
          清空购物车
        </button>
        <Link to="/products" className="continue-shopping">
          继续购物
        </Link>
      </div>
      
      <div className="cart-items">
        <div className="cart-header">
          <div className="cart-header-product">商品</div>
          <div className="cart-header-price">单价</div>
          <div className="cart-header-quantity">数量</div>
          <div className="cart-header-subtotal">小计</div>
          <div className="cart-header-actions"></div>
        </div>
        
        {cartItems.map((item, index) => {
          const productImage = getProductImage(item);
          
          return (
            <div 
              key={item.id} 
              className={`cart-item ${fadeOutItems.includes(item.id) ? 'fade-out' : ''}`}
              style={{ '--item-index': index }}
            >
              <div className="cart-item-product">
                <div className="cart-item-image">
                  <img 
                    src={productImage} 
                    alt={item.product_info?.name || '商品'} 
                    loading="eager"
                    onError={(e) => {
                      console.log('图片加载失败，尝试使用商品详情图片');
                      
                      // 如果有product_info，尝试使用详情页图片
                      if (item.product_info) {
                        const detailImage = getProductDetailImage(item.product_info);
                        if (e.target.src !== detailImage) {
                          e.target.src = detailImage;
                          return;
                        }
                      }
                      
                      // 使用默认图片
                      e.target.src = '/images/Normal.jpg';
                    }}
                  />
                </div>
                <div className="cart-item-details">
                  <div className="cart-item-name">{item.product_info?.name || '未命名商品'}</div>
                  {item.variant_info && (
                    <div className="cart-item-variant">
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
                    <div className="cart-item-sku">SKU: {item.product_info.sku}</div>
                  )}
                </div>
              </div>
              <div className="cart-item-price">¥{parseFloat(item.unit_price || 0).toFixed(2)}</div>
              <div className="cart-item-quantity">
                <div className={`quantity-control ${updatingItem === item.id ? 'updating' : ''}`}>
                  <button 
                    onClick={() => handleUpdateQuantity(item.id, Math.max(1, item.quantity - 1))}
                    disabled={item.quantity <= 1 || updatingItem === item.id}
                  >
                    -
                  </button>
                  <span>{item.quantity}</span>
                  <button 
                    onClick={() => handleUpdateQuantity(item.id, item.quantity + 1)}
                    disabled={updatingItem === item.id}
                  >
                    +
                  </button>
                </div>
              </div>
              <div className="cart-item-subtotal">
                ¥{(parseFloat(item.unit_price || 0) * item.quantity).toFixed(2)}
              </div>
              
              {/* 隐藏原来的操作区，但保留元素以维持表格结构 */}
              <div className="cart-item-actions"></div>
              
              {/* 新的删除按钮位置 */}
              <div className="delete-btn-wrapper">
                <button 
                  className={`remove-btn ${removingItem === item.id ? 'removing' : ''}`}
                  onClick={() => handleRemoveItem(item.id)}
                  disabled={removingItem === item.id}
                >
                  {removingItem === item.id ? '...' : '×'}
                </button>
              </div>
            </div>
          );
        })}
      </div>
      
      <div className="cart-summary">
        <div className="summary-row">
          <span>商品总数:</span>
          <span>{cartItems.reduce((sum, item) => sum + item.quantity, 0)} 件</span>
        </div>
        <div className="summary-row total">
          <span>总计:</span>
          <span>¥{parseFloat(totalPrice || 0).toFixed(2)}</span>
        </div>
        <button className="checkout-btn" onClick={handleCheckout}>
          去结算
        </button>
      </div>
    </div>
  );
};

export default Cart;