import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import '../styles/auth.css';

function ForgotPassword() {
  const [formData, setFormData] = useState({
    username: '',
    phone: '',
    email: '',
    first_name: '',
    last_name: '',
    reason: '',
    new_password: '',
    confirm_password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [passwordVisible, setPasswordVisible] = useState(false);
  const [confirmPasswordVisible, setConfirmPasswordVisible] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    // 清除错误和成功信息
    if (error) setError('');
    if (success) setSuccess('');
  };

  const togglePasswordVisibility = () => {
    setPasswordVisible(!passwordVisible);
  };

  const toggleConfirmPasswordVisibility = () => {
    setConfirmPasswordVisible(!confirmPasswordVisible);
  };

  const validateForm = () => {
    // 验证必填字段
    const requiredFields = ['username', 'phone', 'email', 'first_name', 'last_name', 'reason', 'new_password'];
    for (let field of requiredFields) {
      if (!formData[field]) {
        setError(`请填写${getFieldLabel(field)}`);
        return false;
      }
    }

    // 验证邮箱格式
    if (!/\S+@\S+\.\S+/.test(formData.email)) {
      setError('请输入有效的邮箱地址');
      return false;
    }

    // 验证手机号格式
    if (!/^1[3-9]\d{9}$/.test(formData.phone)) {
      setError('请输入有效的手机号码');
      return false;
    }

    // 验证密码强度
    if (formData.new_password.length < 6) {
      setError('密码至少需要6个字符');
      return false;
    }

    if (formData.new_password.length > 20) {
      setError('密码不能超过20个字符');
      return false;
    }

    // 验证密码确认
    if (formData.new_password !== formData.confirm_password) {
      setError('两次输入的密码不一致');
      return false;
    }

    return true;
  };

  const getFieldLabel = (field) => {
    const labels = {
      username: '用户名',
      phone: '手机号',
      email: '邮箱',
      first_name: '姓',
      last_name: '名',
      reason: '忘记密码的理由',
      new_password: '新密码'
    };
    return labels[field] || field;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    try {
      // 提取需要发送的数据（不包含确认密码）
      const { confirm_password, ...submitData } = formData;
      
      const response = await axios.post('/api/password-reset/submit/', submitData);

      setSuccess(response.data.message);
      setError('');
      
      showNotification('密码重置请求已提交', 'success');
      
      // 3秒后跳转到登录页面
      setTimeout(() => {
        navigate('/login');
      }, 3000);
      
    } catch (error) {
      console.error('提交密码重置请求失败:', error);
      
      if (error.response?.data?.details) {
        // 处理字段验证错误
        const details = error.response.data.details;
        const errorMessages = [];
        
        Object.keys(details).forEach(field => {
          const fieldLabel = getFieldLabel(field);
          const messages = details[field];
          if (Array.isArray(messages)) {
            messages.forEach(msg => errorMessages.push(`${fieldLabel}: ${msg}`));
          } else {
            errorMessages.push(`${fieldLabel}: ${messages}`);
          }
        });
        
        setError(errorMessages.join('; '));
      } else if (error.response?.data?.error) {
        setError(error.response.data.error);
      } else {
        setError('提交失败，请稍后重试');
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

  // 定义商城特点数据
  const shopFeatures = [
    {
      icon: '🔐',
      title: '账户安全',
      description: '严格的身份验证，确保账户安全'
    },
    {
      icon: '👥',
      title: '人工审核',
      description: '专业管理员审核，保障账户安全'
    },
    {
      icon: '⚡',
      title: '快速处理',
      description: '高效处理流程，尽快恢复账户'
    }
  ];

  return (
    <div className="enhanced-auth-page fade-in">
      <div className="auth-container-enhanced">
        {/* 左侧介绍区域 */}
        <div className="auth-intro-panel">
          <div className="intro-content">
            <h1 className="intro-title">密码重置申请</h1>
            <p className="intro-subtitle">
              请填写完整信息，管理员将审核您的申请
            </p>
            
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

        {/* 右侧申请表单 */}
        <div className="auth-form-panel">
          <div className="auth-card">
            <div className="auth-header">
              <div className="auth-logo">
                <div className="logo-placeholder">🔐</div>
              </div>
              <h1 className="auth-title">密码重置申请</h1>
              <p className="auth-subtitle">
                请填写以下信息，管理员将审核您的身份后重置密码
              </p>
            </div>

            <form className="auth-form" onSubmit={handleSubmit}>
              {/* 基本身份信息 */}
              <div className="form-section">
                <h3 className="section-title">身份信息</h3>
                
                <div className="form-row">
                  <div className="form-group half">
                    <label className="form-label">用户名 *</label>
                    <div className="input-wrapper">
                      <input
                        type="text"
                        name="username"
                        value={formData.username}
                        onChange={handleChange}
                        className="form-input no-icon"
                        placeholder="请输入用户名"
                        required
                      />
                    </div>
                  </div>
                  
                  <div className="form-group half">
                    <label className="form-label">手机号 *</label>
                    <div className="input-wrapper">
                      <input
                        type="tel"
                        name="phone"
                        value={formData.phone}
                        onChange={handleChange}
                        className="form-input no-icon"
                        placeholder="请输入手机号"
                        required
                      />
                    </div>
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">邮箱 *</label>
                  <div className="input-wrapper">
                    <input
                      type="email"
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      className="form-input no-icon"
                      placeholder="请输入邮箱地址"
                      required
                    />
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-group half">
                    <label className="form-label">姓 *</label>
                    <div className="input-wrapper">
                      <input
                        type="text"
                        name="first_name"
                        value={formData.first_name}
                        onChange={handleChange}
                        className="form-input no-icon"
                        placeholder="请输入您的姓"
                        required
                      />
                    </div>
                  </div>
                  
                  <div className="form-group half">
                    <label className="form-label">名 *</label>
                    <div className="input-wrapper">
                      <input
                        type="text"
                        name="last_name"
                        value={formData.last_name}
                        onChange={handleChange}
                        className="form-input no-icon"
                        placeholder="请输入您的名"
                        required
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* 申请说明 */}
              <div className="form-section">
                <h3 className="section-title">申请说明</h3>
                
                <div className="form-group">
                  <label className="form-label">忘记密码的理由 *</label>
                  <div className="input-wrapper">
                    <textarea
                      name="reason"
                      value={formData.reason}
                      onChange={handleChange}
                      className="form-textarea"
                      placeholder="请详细说明您忘记密码的原因，以便管理员验证您的身份"
                      rows="4"
                      required
                    />
                  </div>
                </div>
              </div>

              {/* 新密码设置 */}
              <div className="form-section">
                <h3 className="section-title">新密码设置</h3>
                
                <div className="form-group">
                  <label className="form-label">新密码 *</label>
                  <div className="input-wrapper">
                    <input
                      type={passwordVisible ? "text" : "password"}
                      name="new_password"
                      value={formData.new_password}
                      onChange={handleChange}
                      className="form-input"
                      placeholder="请输入新密码（6-20个字符）"
                      required
                    />
                    <button
                      type="button"
                      className="password-toggle"
                      onClick={togglePasswordVisibility}
                    >
                      {passwordVisible ? '🙈' : '👁️'}
                    </button>
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">确认新密码 *</label>
                  <div className="input-wrapper">
                    <input
                      type={confirmPasswordVisible ? "text" : "password"}
                      name="confirm_password"
                      value={formData.confirm_password}
                      onChange={handleChange}
                      className="form-input"
                      placeholder="请再次输入新密码"
                      required
                    />
                    <button
                      type="button"
                      className="password-toggle"
                      onClick={toggleConfirmPasswordVisibility}
                    >
                      {confirmPasswordVisible ? '🙈' : '👁️'}
                    </button>
                  </div>
                </div>
              </div>

              {error && <div className="error-message">{error}</div>}
              {success && <div className="success-message">{success}</div>}

              <button 
                type="submit" 
                className="auth-btn primary-btn"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <span className="btn-spinner"></span>
                    提交申请中...
                  </>
                ) : (
                  '提交重置申请'
                )}
              </button>
            </form>

            <div className="auth-footer">
              <div className="auth-links">
                <Link to="/login" className="auth-link">
                  <span className="link-icon">🔙</span>
                  返回登录
                </Link>
                <Link to="/register" className="auth-link">
                  <span className="link-icon">📝</span>
                  创建新账户
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ForgotPassword; 