import React, { useState, useEffect } from 'react';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import Home from './pages/Home';
import Cart from './pages/Cart';
import Checkout from './pages/Checkout';
import MemberCenter from './pages/MemberCenter';
import Login from './pages/Login';
import Register from './pages/Register';
import ForgotPassword from './pages/ForgotPassword';
import OrderList from './pages/OrderList';
import OrderDetail from './pages/OrderDetail';
import ProductList from './pages/ProductList';
import ProductDetail from './pages/ProductDetail';
import ReviewForm from './pages/ReviewForm'; // 导入评价表单组件
import Terms from './pages/Terms'; // 导入用户协议页面
import Privacy from './pages/Privacy'; // 导入隐私政策页面
import About from './pages/About'; // 导入关于我们页面
import Help from './pages/Help'; // 导入帮助中心页面
import './styles/global.css';
import './styles/checkout.css';

function App() {
  const [cartCount, setCartCount] = useState(0);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState(null);
  const [loginCheckKey, setLoginCheckKey] = useState(0); // 添加一个状态用于触发登录状态检查
  const navigate = useNavigate();
  const location = useLocation(); // 获取当前路径

  // 处理导航点击
  const handleNavClick = (path, event) => {
    event.preventDefault();
    event.stopPropagation();
    setTimeout(() => {
      navigate(path);
    }, 50); // 添加小延迟确保状态更新
  };

  // 检查是否为活跃链接
  const isActiveLink = (path) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  // 配置API基础路径，方便后续统一调整
  useEffect(() => {
    // 设置axios全局默认值
    if (window.axios) {
      window.axios.defaults.baseURL = '/api';
    }
  }, []);

  // 监听存储变化事件，当localStorage变化时重新检查登录状态
  useEffect(() => {
    const handleStorageChange = () => {
      // 触发登录状态检查
      setLoginCheckKey(prev => prev + 1);
    };
    
    // 添加事件监听器
    window.addEventListener('storage', handleStorageChange);
    
    // 创建一个自定义事件用于组件间通信
    window.addEventListener('logoutEvent', handleStorageChange);
    
    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('logoutEvent', handleStorageChange);
    };
  }, []);

  // 初始化登录状态
  useEffect(() => {
    // 首先检查sessionStorage中是否有登录标记
    const hasLoginFlag = sessionStorage.getItem('isLoggedIn');
    
    // 如果有登录标记，则从localStorage中获取token和用户信息
    if (hasLoginFlag) {
      const token = localStorage.getItem('access') || localStorage.getItem('token');
      const userData = localStorage.getItem('user');
      
      console.log('检查登录状态, token存在:', !!token);
      
      if (token && userData) {
        setIsLoggedIn(true);
        try {
          const parsedUser = JSON.parse(userData);
          setUser(parsedUser);
          console.log('用户已登录:', parsedUser.username);
        } catch (error) {
          console.error('解析用户数据失败:', error);
          localStorage.removeItem('user');
          sessionStorage.removeItem('isLoggedIn');
          setIsLoggedIn(false);
          setUser(null);
        }
      } else {
        console.log('用户未登录');
        sessionStorage.removeItem('isLoggedIn');
        setIsLoggedIn(false);
        setUser(null);
      }
    } else {
      console.log('会话已结束，用户需要重新登录');
      // 确保清除所有登录相关数据
      localStorage.removeItem('token');
      localStorage.removeItem('access');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      setIsLoggedIn(false);
      setUser(null);
    }
  }, [loginCheckKey]); // 当loginCheckKey变化时重新检查登录状态

  // 退出登录
  const handleLogout = () => {
    // 清除所有登录相关的localStorage数据
    localStorage.removeItem('token');
    localStorage.removeItem('access');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    
    // 清除会话标记
    sessionStorage.removeItem('isLoggedIn');
    
    // 更新状态
    setIsLoggedIn(false);
    setUser(null);
    setCartCount(0);
    
    // 触发自定义事件，确保所有组件都知道用户已退出
    window.dispatchEvent(new Event('logoutEvent'));
    
    // 显示退出成功提示
    showNotification('已退出登录', 'success');
    
    // 重定向到首页
    window.location.href = '/';
  };

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

  return (
    <div className="App">
      <nav className="navbar">
        <div className="container nav-container">
          <a href="/" className="logo" onClick={(e) => handleNavClick('/', e)}>
            🛒 武汉精品商城
          </a>
          <ul className="nav-menu">
            <li>
              <a href="/" className={`nav-link ${isActiveLink('/') ? 'active' : ''}`} onClick={(e) => handleNavClick('/', e)}>
                🏠 首页
              </a>
            </li>
            <li>
              <a href="/products" className={`nav-link ${isActiveLink('/products') ? 'active' : ''}`} onClick={(e) => handleNavClick('/products', e)}>
                🛍️ 商品列表
              </a>
            </li>
            <li>
              <a href="/cart" className={`nav-link ${isActiveLink('/cart') ? 'active' : ''}`} onClick={(e) => handleNavClick('/cart', e)}>
                🛒 购物车 {cartCount > 0 && <span className="cart-badge">{cartCount}</span>}
              </a>
            </li>
            {isLoggedIn ? (
              <>
                <li>
                  <a href="/member" className={`nav-link ${isActiveLink('/member') ? 'active' : ''}`} onClick={(e) => handleNavClick('/member', e)}>
                    👤 会员中心
                  </a>
                </li>
                <li>
                  <button 
                    onClick={handleLogout} 
                    className="nav-link logout-btn"
                  >
                    🚪 退出
                  </button>
                </li>
              </>
            ) : (
              <>
                <li>
                  <a href="/login" className={`nav-link ${isActiveLink('/login') ? 'active' : ''}`} onClick={(e) => handleNavClick('/login', e)}>
                    🔑 登录
                  </a>
                </li>
                <li>
                  <a href="/register" className={`nav-link ${isActiveLink('/register') ? 'active' : ''}`} onClick={(e) => handleNavClick('/register', e)}>
                    📝 注册
                  </a>
                </li>
              </>
            )}
          </ul>
        </div>
      </nav>
      
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/products" element={<ProductList />} />
          <Route path="/product/:id" element={<ProductDetail />} />
          <Route path="/cart" element={<Cart cartCount={cartCount} setCartCount={setCartCount} />} />
          <Route path="/checkout" element={<Checkout />} />
          <Route path="/member" element={<MemberCenter />} />
          <Route path="/orders" element={<OrderList />} />
          <Route path="/order/:id" element={<OrderDetail />} />
          <Route path="/login" element={<Login setIsLoggedIn={setIsLoggedIn} setUser={setUser} />} />
          <Route path="/register" element={<Register />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/review/:orderId/:productId" element={<ReviewForm />} />
          <Route path="/terms" element={<Terms />} />
          <Route path="/privacy" element={<Privacy />} />
          <Route path="/about" element={<About />} />
          <Route path="/help" element={<Help />} />
        </Routes>
      </main>
      
      <footer className="footer">
        <div className="container">
          <div className="footer-content">
            <div className="footer-links">
              <a href="/about" onClick={(e) => handleNavClick('/about', e)}>关于我们</a>
              <span className="separator">|</span>
              <a href="/terms" onClick={(e) => handleNavClick('/terms', e)}>使用条款</a>
              <span className="separator">|</span>
              <a href="/privacy" onClick={(e) => handleNavClick('/privacy', e)}>隐私政策</a>
              <span className="separator">|</span>
              <a href="/help" onClick={(e) => handleNavClick('/help', e)}>帮助中心</a>
            </div>
            <p>&copy; 2026 武汉精品商城. 所有权利保留.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;