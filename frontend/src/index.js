import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import axios from 'axios';
import './styles/global.css';

// 配置axios全局默认值
// 开发环境默认指向本地后端，生产环境通过 .env.production 设为空字符串（同源相对路径）
axios.defaults.baseURL = process.env.REACT_APP_API_URL !== undefined
  ? process.env.REACT_APP_API_URL
  : 'http://127.0.0.1:8000';

// 页面关闭或刷新时的处理
const handleTabClose = () => {
  // 设置一个标记来识别这是刷新还是关闭
  sessionStorage.setItem('isRefreshing', 'true');
  
  // 设置一个关闭时间戳
  sessionStorage.setItem('closeTimestamp', Date.now().toString());
};

// 页面刷新时的处理
const handlePageLoad = () => {
  const isRefreshing = sessionStorage.getItem('isRefreshing') === 'true';
  const closeTimestamp = sessionStorage.getItem('closeTimestamp');
  
  // 清除刷新标记
  sessionStorage.removeItem('isRefreshing');
  
  if (closeTimestamp) {
    const timeDiff = Date.now() - parseInt(closeTimestamp, 10);
    sessionStorage.removeItem('closeTimestamp');
    
    // 如果时间间隔大于1秒，我们认为这可能是一个新的打开操作而不是刷新
    if (timeDiff > 1000 && !isRefreshing) {
      // 清除登录状态
      sessionStorage.removeItem('isLoggedIn');
      localStorage.removeItem('access');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      console.log('检测到页面重新打开，已清除登录状态');
    } else {
      console.log('检测到页面刷新，保持登录状态');
    }
  }
};

// 添加页面关闭事件监听
window.addEventListener('beforeunload', handleTabClose);

// 添加页面加载事件监听
window.addEventListener('load', handlePageLoad);

// 添加请求拦截器
axios.interceptors.request.use(function (config) {
  console.log('发送请求:', config.url, config.data);
  
  // 自动添加认证头，但对于公共API（如商品列表、分类列表）不添加
  const publicApiPaths = [
    '/api/product/products',
    '/api/product/categories',
    '/api/product/featured',
    '/api/product/latest',
    '/api/product/bestselling'
  ];
  
  // 检查是否是公共API
  const isPublicApi = publicApiPaths.some(path => config.url.includes(path));
  
  // 如果不是公共API，才添加认证头
  if (!isPublicApi) {
    // 从localStorage获取token
    const token = localStorage.getItem('access') || localStorage.getItem('token');
    if (token && !config.headers['Authorization']) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
  }
  
  return config;
}, function (error) {
  console.error('请求错误:', error);
  return Promise.reject(error);
});

// 添加响应拦截器
axios.interceptors.response.use(function (response) {
  console.log('响应成功:', response.status, response.data);
  return response;
}, function (error) {
  console.error('响应错误:', error.message);
  if (error.response) {
    console.error('错误状态码:', error.response.status);
    console.error('错误数据:', error.response.data);
    
    // 处理404错误，可能是API路径问题
    if (error.response.status === 404) {
      console.error('API路径不存在，请检查URL是否正确');
    }
    
    // 处理401未授权错误
    if (error.response.status === 401) {
      // 检查是否是公共API
      const publicApiPaths = [
        '/api/product/products',
        '/api/product/categories',
        '/api/product/featured',
        '/api/product/latest',
        '/api/product/bestselling'
      ];
      
      const isPublicApi = publicApiPaths.some(path => 
        error.config && error.config.url && error.config.url.includes(path)
      );
      
      // 如果不是公共API且不在登录页面，才提示登录
      if (!isPublicApi && !window.location.pathname.includes('/login')) {
        console.log('未授权，需要登录');
        // 可能会话已过期，清除会话标记
        sessionStorage.removeItem('isLoggedIn');
        // 这里可以添加跳转到登录页面的逻辑
        // window.location.href = '/login';
      }
    }
  }
  return Promise.reject(error);
});

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);