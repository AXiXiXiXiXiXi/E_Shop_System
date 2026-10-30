import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import '../styles/auth.css';

function Login({ setIsLoggedIn, setUser }) {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    phone: '',
    password: ''
  });
  const [loginType, setLoginType] = useState('username'); // 默认使用用户名登录
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [passwordVisible, setPasswordVisible] = useState(false);
  const navigate = useNavigate();

  // 检查是否有保存的登录信息
  useEffect(() => {
    const savedUsername = localStorage.getItem('savedUsername');
    if (savedUsername) {
      setFormData(prev => ({ ...prev, username: savedUsername }));
      setRememberMe(true);
    }
  }, []);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    // 清除错误信息
    if (error) setError('');
  };

  const togglePasswordVisibility = () => {
    setPasswordVisible(!passwordVisible);
  };
  
  // 切换登录方式
  const switchLoginType = (type) => {
    setLoginType(type);
    setError(''); // 清除错误信息
  };

  // 获取当前登录方式的标识符
  const getIdentifier = () => {
    switch(loginType) {
      case 'username': return formData.username;
      case 'email': return formData.email;
      case 'phone': return formData.phone;
      default: return '';
    }
  };

  // 验证当前输入
  const validateInput = () => {
    const identifier = getIdentifier();
    if (!identifier) {
      switch(loginType) {
        case 'username': setError('请输入用户名'); break;
        case 'email': setError('请输入邮箱'); break;
        case 'phone': setError('请输入手机号'); break;
        default: setError('请输入登录信息');
      }
      return false;
    }
    
    if (!formData.password) {
      setError('请输入密码');
      return false;
    }
    
    // 邮箱格式验证
    if (loginType === 'email') {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(formData.email)) {
        setError('请输入有效的邮箱地址');
        return false;
      }
    }
    
    // 手机号格式验证
    if (loginType === 'phone') {
      const phoneRegex = /^\d{11}$/;
      if (!phoneRegex.test(formData.phone.replace(/\D/g, ''))) {
        setError('请输入有效的11位手机号');
        return false;
      }
    }
    
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateInput()) {
      return;
    }

    setLoading(true);
    setError('');

    try {
      // 准备请求数据
      const requestData = {
        password: formData.password,
        login_type: loginType
      };
      
      // 根据登录类型添加对应的字段
      if (loginType === 'username') {
        requestData.username = formData.username;
      } else if (loginType === 'email') {
        requestData.email = formData.email;
      } else if (loginType === 'phone') {
        requestData.phone = formData.phone;
      }
      
      // 调用后端登录API
      const response = await axios.post('/api/auth/login/', requestData);
      
      // 检查响应中是否包含所需数据
      if (!response.data.access || !response.data.user) {
        setError('登录成功但返回数据不完整');
        setLoading(false);
        return;
      }
      
      // 保存登录凭证到localStorage
      localStorage.setItem('access', response.data.access);
      localStorage.setItem('refresh_token', response.data.refresh);
      localStorage.setItem('user', JSON.stringify(response.data.user));
      
      // 在sessionStorage中设置登录标记，用于判断会话是否有效
      sessionStorage.setItem('isLoggedIn', 'true');
      
      // 清除可能存在的刷新或关闭标记
      sessionStorage.removeItem('isRefreshing');
      sessionStorage.removeItem('closeTimestamp');
      
      // 如果选择了"记住我"，保存用户名
      if (rememberMe) {
        if (loginType === 'username') {
          localStorage.setItem('savedUsername', formData.username);
        }
      } else {
        localStorage.removeItem('savedUsername');
      }
      
      setIsLoggedIn(true);
      setUser(response.data.user);
      
      // 显示成功消息
      showNotification('登录成功！欢迎回来', 'success');
      
      // 跳转到首页或之前的页面
      navigate('/');
    } catch (error) {
      // 处理登录错误
      if (error.response) {
        if (error.response.status === 401) {
        setError('登录信息或密码错误，请重试');
          // 添加表单抖动效果
          document.querySelector('.auth-card').classList.add('shake');
          setTimeout(() => {
            document.querySelector('.auth-card').classList.remove('shake');
          }, 500);
        } else if (error.response.status === 400) {
          // 尝试解析详细错误信息
          let errorMsg = '请求格式错误';
          if (error.response.data) {
            if (typeof error.response.data === 'object') {
              // 提取所有错误信息
              const errorDetails = Object.entries(error.response.data)
                .map(([key, value]) => {
                  if (Array.isArray(value)) {
                    return `${key}: ${value.join(', ')}`;
      } else {
                    return `${key}: ${value}`;
                  }
                })
                .join('; ');
              
              errorMsg = errorDetails || errorMsg;
            } else if (typeof error.response.data === 'string') {
              errorMsg = error.response.data;
            }
          }
          setError(errorMsg);
        } else {
          setError(`服务器错误 (${error.response.status}): ${JSON.stringify(error.response.data || '未知错误')}`);
        }
      } else if (error.request) {
        // 请求发出但没有收到响应
        setError('网络连接失败，服务器没有响应');
      } else {
        // 请求设置时出错
        setError('请求错误: ' + error.message);
      }
    } finally {
      setLoading(false);
    }
  };

  // 处理社交登录按钮点击
  const handleSocialLogin = (type) => {
    if (type === 'email') {
      switchLoginType('email');
    } else if (type === 'phone') {
      switchLoginType('phone');
    }
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

  // 定义商城特点数据
  const shopFeatures = [
    {
      icon: '🛒',
      title: '丰富商品',
      description: '数千种精选商品，满足您的各种需求'
    },
    {
      icon: '🚚',
      title: '快速配送',
      description: '极速物流配送，让您轻松购物无忧'
    },
    {
      icon: '💰',
      title: '优惠活动',
      description: '定期推出折扣优惠，让您享受实惠价格'
    },
    {
      icon: '🔒',
      title: '安全保障',
      description: '全程数据加密，保障您的账户和隐私安全'
    }
  ];

  // 获取当前登录方式的输入框标签
  const getInputLabel = () => {
    switch(loginType) {
      case 'username': return '用户名';
      case 'email': return '邮箱';
      case 'phone': return '手机号';
      default: return '账号';
    }
  };

  // 获取当前登录方式的输入框占位符
  const getInputPlaceholder = () => {
    switch(loginType) {
      case 'username': return '请输入用户名';
      case 'email': return '请输入邮箱';
      case 'phone': return '请输入手机号';
      default: return '请输入账号';
    }
  };

  // 获取当前登录方式的输入框值
  const getInputValue = () => {
    switch(loginType) {
      case 'username': return formData.username;
      case 'email': return formData.email;
      case 'phone': return formData.phone;
      default: return '';
    }
  };

  // 获取当前登录方式的输入框名称
  const getInputName = () => {
    switch(loginType) {
      case 'username': return 'username';
      case 'email': return 'email';
      case 'phone': return 'phone';
      default: return 'username';
    }
  };

  return (
    <div className="enhanced-auth-page fade-in">
      <div className="auth-container-enhanced">
        {/* 左侧介绍区域 */}
        <div className="auth-intro-panel">
          <div className="intro-content">
            <h1 className="intro-title">欢迎使用武汉精品商城</h1>
            <p className="intro-subtitle">您的一站式网上购物平台</p>
            
            <div className="intro-features">
              {shopFeatures.map((feature, index) => (
                <div className="feature-item" key={index}>
                  <div className="feature-icon">{feature.icon}</div>
                  <div className="feature-text">
                    <h3>{feature.title}</h3>
                    <p>{feature.description}</p>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="intro-decoration">
              <div className="floating-shape shape-1"></div>
              <div className="floating-shape shape-2"></div>
              <div className="floating-shape shape-3"></div>
            </div>
          </div>
        </div>

        {/* 右侧登录表单 */}
        <div className="auth-form-panel">
          <div className="auth-card">
            <div className="auth-header">
              <div className="auth-logo">
                <img 
                  src={process.env.PUBLIC_URL + '/images/Loging.jpg'} 
                  alt="Logo" 
                  style={{ 
                    width: '100%', 
                    height: '100%', 
                    borderRadius: '50%', 
                    objectFit: 'cover' 
                  }} 
                />
              </div>
              <h1 className="auth-title">欢迎回来</h1>
              <p className="auth-subtitle">登录您的账户以继续</p>
            </div>

            {/* 登录方式切换选项卡 */}
            <div className="login-tabs">
              <button 
                className={`login-tab ${loginType === 'username' ? 'active' : ''}`}
                onClick={() => switchLoginType('username')}
              >
                用户名登录
              </button>
              <button 
                className={`login-tab ${loginType === 'email' ? 'active' : ''}`}
                onClick={() => switchLoginType('email')}
              >
                邮箱登录
              </button>
              <button 
                className={`login-tab ${loginType === 'phone' ? 'active' : ''}`}
                onClick={() => switchLoginType('phone')}
              >
                手机号登录
              </button>
            </div>

            <form onSubmit={handleSubmit} className="auth-form">
              {error && (
                <div className="error-message">
                  <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" strokeWidth="2" fill="none">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="8" x2="12" y2="12"></line>
                    <line x1="12" y1="16" x2="12.01" y2="16"></line>
                  </svg>
                  {error}
                </div>
              )}

              <div className="form-group">
                <label htmlFor={getInputName()} className="form-label">
                  {getInputLabel()}
                </label>
                <div className="input-wrapper">
                <input
                  type={loginType === 'email' ? 'email' : 'text'}
                  id={getInputName()}
                  name={getInputName()}
                  value={getInputValue()}
                  onChange={handleChange}
                  className="form-input no-icon"
                  placeholder={getInputPlaceholder()}
                  autoComplete={loginType === 'email' ? 'email' : loginType === 'username' ? 'username' : 'tel'}
                  required
                />
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="password" className="form-label">
                  密码
                </label>
                <div className="input-wrapper">
                <input
                  type={passwordVisible ? "text" : "password"}
                  id="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  className="form-input no-icon"
                  placeholder="请输入密码"
                  autoComplete="current-password"
                  required
                />
                  <button 
                    type="button" 
                    className="password-toggle" 
                    onClick={togglePasswordVisibility}
                    aria-label={passwordVisible ? "隐藏密码" : "显示密码"}
                  >
                    {passwordVisible ? (
                      <svg viewBox="0 0 24 24" width="18" height="18" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M12 6.5C15.79 6.5 19.17 8.63 20.82 12C19.17 15.37 15.8 17.5 12 17.5C8.2 17.5 4.83 15.37 3.18 12C4.83 8.63 8.21 6.5 12 6.5ZM12 4.5C7 4.5 2.73 7.61 1 12C2.73 16.39 7 19.5 12 19.5C17 19.5 21.27 16.39 23 12C21.27 7.61 17 4.5 12 4.5ZM12 9.5C13.38 9.5 14.5 10.62 14.5 12C14.5 13.38 13.38 14.5 12 14.5C10.62 14.5 9.5 13.38 9.5 12C9.5 10.62 10.62 9.5 12 9.5ZM12 7.5C9.52 7.5 7.5 9.52 7.5 12C7.5 14.48 9.52 16.5 12 16.5C14.48 16.5 16.5 14.48 16.5 12C16.5 9.52 14.48 7.5 12 7.5Z" fill="#a0aec0"/>
                        <path d="M2 4L22 22" stroke="#a0aec0" strokeWidth="2" strokeLinecap="round"/>
                      </svg>
                    ) : (
                      <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" strokeWidth="2" fill="none">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                        <circle cx="12" cy="12" r="3"></circle>
                      </svg>
                    )}
                  </button>
                </div>
              </div>

              <div className="form-options">
                <label className="checkbox-label">
                  <input 
                    type="checkbox" 
                    className="checkbox" 
                    checked={rememberMe}
                    onChange={() => setRememberMe(!rememberMe)}
                  />
                  <span className="checkbox-text">记住我</span>
                </label>
                <Link to="/forgot-password" className="forgot-link">
                  忘记密码？
                </Link>
              </div>

              <button
                type="submit"
                className={`btn btn-primary auth-submit ${loading ? 'loading' : ''}`}
                disabled={loading}
              >
                {loading ? (
                  <>
                    <div className="spinner"></div>
                    <span>登录中...</span>
                  </>
                ) : (
                  '登录'
                )}
              </button>

            </form>

            <div className="auth-footer">
              <div className="auth-links">
                <Link to="/forgot-password" className="auth-link">
                  <span className="link-icon">🔐</span>
                  忘记密码？
                </Link>
              </div>
              <p className="auth-switch">
                还没有账户？
                <Link to="/register" className="auth-link">
                  立即注册
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>



      <div className="background-decoration">
        <div className="decoration-circle circle-1"></div>
        <div className="decoration-circle circle-2"></div>
        <div className="decoration-circle circle-3"></div>
        <div className="decoration-circle circle-4"></div>
        <div className="decoration-circle circle-5"></div>
      </div>
    </div>
  );
}

export default Login;