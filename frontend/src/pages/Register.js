import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import '../styles/auth.css';

function Register() {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    phone: '',
    agreeTerms: false
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    
    // 手机号字段特殊处理，只允许输入数字
    if (name === 'phone') {
      const numericValue = value.replace(/\D/g, '');
      // 限制最多11位数字
      const truncatedValue = numericValue.slice(0, 11);
      setFormData({
        ...formData,
        [name]: truncatedValue
      });
    } else {
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value
    });
    }
    
    // 清除对应字段的错误信息
    if (errors[name]) {
      setErrors({
        ...errors,
        [name]: ''
      });
    }
  };

  const validateForm = () => {
    const newErrors = {};

    // 用户名验证
    if (!formData.username) {
      newErrors.username = '请输入用户名';
    } else if (formData.username.length < 3) {
      newErrors.username = '用户名至少需要3个字符';
    }

    // 邮箱验证
    if (!formData.email) {
      newErrors.email = '请输入邮箱地址';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = '请输入有效的邮箱地址';
    }

    // 密码验证
    if (!formData.password) {
      newErrors.password = '请输入密码';
    } else if (formData.password.length < 6) {
      newErrors.password = '密码至少需要6个字符';
    }

    // 确认密码验证
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = '请确认密码';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = '两次输入的密码不一致';
    }

    // 手机号验证
    if (!formData.phone) {
      newErrors.phone = '请输入手机号';
    } else {
      // 移除所有非数字字符
      const cleanPhone = formData.phone.replace(/\D/g, '');
      if (cleanPhone.length !== 11) {
        newErrors.phone = '手机号必须为11位数字';
      }
    }

    // 协议验证
    if (!formData.agreeTerms) {
      newErrors.agreeTerms = '请同意用户协议和隐私政策';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      // 调用注册API，使用正确的URL并包含phone字段
      console.log('发送注册请求:', {
        username: formData.username,
        email: formData.email,
        password: formData.password,
        password_confirm: formData.confirmPassword,
        phone: formData.phone
      });
      
      // 确保手机号只包含数字并且是11位
      const phoneNumber = formData.phone.replace(/\D/g, '');
      
      const response = await axios.post(`${process.env.REACT_APP_API_URL !== undefined ? process.env.REACT_APP_API_URL : 'http://127.0.0.1:8000'}/api/auth/register/`, {
        username: formData.username,
        email: formData.email,
        password: formData.password,
        password_confirm: formData.confirmPassword,
        phone: phoneNumber  // 发送字符串类型的手机号
      });
      
      console.log('注册成功响应:', response.data);
      
      // 成功注册时，自动登录
      if (response.data.access && response.data.refresh) {
        // 保存token到localStorage
        localStorage.setItem('access', response.data.access);
        localStorage.setItem('refresh_token', response.data.refresh);
        localStorage.setItem('user', JSON.stringify(response.data.user));
      
      // 显示成功消息
        showNotification('注册成功！即将跳转到首页', 'success');
      
        // 跳转到首页
        setTimeout(() => {
          navigate('/');
        }, 1500);
      } else {
        // 如果没有返回token，则跳转到登录页面
        showNotification('注册成功！请登录您的账户', 'success');
        setTimeout(() => {
      navigate('/login');
        }, 1500);
      }
    } catch (error) {
      console.error('注册失败:', error);
      
      if (error.response) {
        console.log('错误响应数据:', error.response.data);
        console.log('错误状态码:', error.response.status);
        
        // 显示具体的错误信息
        let errorMessage = '注册失败';
        if (error.response.data) {
        if (typeof error.response.data === 'object') {
            // 将所有错误信息整合成一个字符串显示
            errorMessage = Object.entries(error.response.data)
              .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value}`)
              .join('\n');
        } else {
          errorMessage = error.response.data;
          }
        }
        showNotification(`注册失败: ${errorMessage}`, 'error');
      } else if (error.request) {
        // 请求发出但没有收到响应
        showNotification('网络连接失败，服务器没有响应', 'error');
      } else {
        // 请求设置时出错
        showNotification(`请求错误: ${error.message}`, 'error');
      }
    } finally {
      setLoading(false);
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

  return (
    <div className="auth-page fade-in">
      <div className="container">
        <div className="auth-container">
          <div className="auth-card register-card">
            <div className="auth-header">
              <div className="auth-icon">📝</div>
              <h1 className="auth-title">用户注册</h1>
              <p className="auth-subtitle">创建您的账户，开始购物之旅</p>
            </div>

            <form onSubmit={handleSubmit} className="auth-form">
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="username" className="form-label">
                    <span className="label-icon">👤</span>
                    用户名
                  </label>
                  <input
                    type="text"
                    id="username"
                    name="username"
                    value={formData.username}
                    onChange={handleChange}
                    className={`form-input ${errors.username ? 'error' : ''}`}
                    placeholder="请输入用户名"
                    required
                  />
                  {errors.username && (
                    <div className="field-error">{errors.username}</div>
                  )}
                </div>

                <div className="form-group">
                  <label htmlFor="email" className="form-label">
                    <span className="label-icon">📧</span>
                    邮箱地址
                  </label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    className={`form-input ${errors.email ? 'error' : ''}`}
                    placeholder="请输入邮箱地址"
                    required
                  />
                  {errors.email && (
                    <div className="field-error">{errors.email}</div>
                  )}
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="phone" className="form-label">
                  <span className="label-icon">📱</span>
                  手机号码
                </label>
                <input
                  type="tel"
                  id="phone"
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  className={`form-input ${errors.phone ? 'error' : ''}`}
                  placeholder="请输入手机号码"
                  required
                />
                {errors.phone && (
                  <div className="field-error">{errors.phone}</div>
                )}
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="password" className="form-label">
                    <span className="label-icon">🔒</span>
                    密码
                  </label>
                  <input
                    type="password"
                    id="password"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    className={`form-input ${errors.password ? 'error' : ''}`}
                    placeholder="请输入密码"
                    required
                  />
                  {errors.password && (
                    <div className="field-error">{errors.password}</div>
                  )}
                </div>

                <div className="form-group">
                  <label htmlFor="confirmPassword" className="form-label">
                    <span className="label-icon">🔐</span>
                    确认密码
                  </label>
                  <input
                    type="password"
                    id="confirmPassword"
                    name="confirmPassword"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    className={`form-input ${errors.confirmPassword ? 'error' : ''}`}
                    placeholder="请再次输入密码"
                    required
                  />
                  {errors.confirmPassword && (
                    <div className="field-error">{errors.confirmPassword}</div>
                  )}
                </div>
              </div>

              <div className="form-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    name="agreeTerms"
                    checked={formData.agreeTerms}
                    onChange={handleChange}
                    className="checkbox"
                  />
                  <span className="checkbox-text">
                    我已阅读并同意
                    <Link to="/terms" className="terms-link">《用户协议》</Link>
                    和
                    <Link to="/privacy" className="terms-link">《隐私政策》</Link>
                  </span>
                </label>
                {errors.agreeTerms && (
                  <div className="field-error">{errors.agreeTerms}</div>
                )}
              </div>

              <button
                type="submit"
                className={`btn btn-primary auth-submit ${loading ? 'loading' : ''}`}
                disabled={loading}
              >
                {loading ? (
                  <>
                    <div className="spinner small"></div>
                    注册中...
                  </>
                ) : (
                  '立即注册'
                )}
              </button>
            </form>

            <div className="auth-footer">
              <p className="auth-switch">
                已有账户？
                <Link to="/login" className="auth-link">
                  立即登录
                </Link>
              </p>
            </div>
          </div>

          <div className="auth-decoration">
            <div className="decoration-circle circle-1"></div>
            <div className="decoration-circle circle-2"></div>
            <div className="decoration-circle circle-3"></div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Register;