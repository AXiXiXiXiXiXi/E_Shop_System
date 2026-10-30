import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import '../styles/review.css';

function ReviewForm() {
  // 参数中的productId可能是订单项ID或变体ID，而不是实际的商品ID
  const { orderId, productId } = useParams();
  const [reviewData, setReviewData] = useState(null);
  const [finalProductId, setFinalProductId] = useState(null); // 添加最终确定的产品ID状态
  const [rating, setRating] = useState(5);
  const [content, setContent] = useState('');
  const [images, setImages] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isEditing, setIsEditing] = useState(false); // 标记是否为编辑状态
  const [existingReview, setExistingReview] = useState(null); // 存储已有的评价
  const navigate = useNavigate();
  
  // 在组件顶部添加显示纠正信息的逻辑
  useEffect(() => {
    // 检查登录状态
    const token = localStorage.getItem('access') || localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }
    
    console.log("ReviewForm 组件加载，开始获取商品信息...");
    
    // 获取商品信息
    fetchProductInfo();
  }, [navigate]);
  
  // 检查用户是否已经评价过该商品
  const checkExistingReview = async (pid) => {
    try {
      // 确保productId是有效的
      const productIdToCheck = pid || productId;
      if (!productIdToCheck || isNaN(parseInt(productIdToCheck))) {
        console.error("无效的商品ID:", productIdToCheck);
        return;
      }
      
      console.log(`检查商品ID ${productIdToCheck} 的评价状态...`);
      
      const token = localStorage.getItem('access') || localStorage.getItem('token');
      const response = await axios.get(`/api/review/reviews/user-product/${productIdToCheck}/`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.status === 200 && response.data) {
        // 用户已评价过该商品
        console.log(`找到商品 ${productIdToCheck} 的已有评价:`, response.data);
        setExistingReview(response.data);
        setIsEditing(true);
        setRating(parseFloat(response.data.rating));
        setContent(response.data.content);
        
        // 处理已有的图片
        if (response.data.images && response.data.images.length > 0) {
          // 这里只保存图片URL，不是文件对象
          setImages(response.data.images.map(url => ({ isExisting: true, url })));
        }
      }
    } catch (err) {
      // 处理404错误，检查是否有real_product_id信息
      if (err.response && err.response.status === 404) {
        console.log(`商品 ${pid || productId} 未找到已有评价，可以创建新评价`);
        
        // 检查错误响应中是否包含真实商品ID的映射
        const errorData = err.response.data;
        
        // 检查是否ID完全不存在（既不是产品ID也不是变体ID）
        if (errorData && errorData.id_not_found === true) {
          console.warn(`警告: ID ${pid || productId} 在系统中不存在，既不是产品ID也不是变体ID`);
          
          // 记录调试信息
          console.log(`当前URL参数:`, { pid, productId, orderId });
          console.log(`localStorage中的评论数据:`, localStorage.getItem('current_review_item'));
          console.log(`有效的主产品ID范围: 1-32`);
          console.log(`有效的变体ID范围: 1-71`);
          console.log(`建议使用有效的ID进行测试`);
          
          // 尝试通过商品名称找到正确的ID
          if (reviewData && reviewData.productName) {
            console.log(`尝试通过商品名称 "${reviewData.productName}" 查找正确的ID...`);
            
            try {
              // 调用后端API根据名称查找商品
              const searchResponse = await axios.get(`/api/product/products/?search=${encodeURIComponent(reviewData.productName)}&limit=1`);
              
              if (searchResponse.data && searchResponse.data.results && searchResponse.data.results.length > 0) {
                const correctProduct = searchResponse.data.results[0];
                console.log(`✓ 找到匹配的商品: ID=${correctProduct.id}, 名称=${correctProduct.name}`);
                
                // 自动更正ID
                const correctedData = {
                  ...reviewData,
                  productId: correctProduct.id,
                  originalProductId: reviewData.productId, // 保存错误的原始ID
                  idCorrected: true, // 标记ID已被纠正
                  correctionMessage: `ID从 ${reviewData.productId} 自动纠正为 ${correctProduct.id}`
                };
                
                setReviewData(correctedData);
                localStorage.setItem('current_review_item', JSON.stringify(correctedData));
                
                console.log(`✓ 已自动纠正商品ID: ${reviewData.productId} -> ${correctProduct.id}`);
                
                // 使用正确的ID重新检查评论
                checkExistingReview(correctProduct.id);
                return;
                
              } else {
                console.log(`未找到名称为 "${reviewData.productName}" 的商品`);
              }
            } catch (searchErr) {
              console.error(`通过名称搜索商品失败:`, searchErr);
            }
          }
          
          setError(`商品ID ${pid || productId} 无效。请检查：\n1. 是否从正确的商品页面进入\n2. 商品链接是否正确\n3. 建议返回商品列表重新选择`);
          return;
        }
        
        // 检查是否有API错误
        if (errorData && errorData.error === true) {
          console.warn(`API错误: ${errorData.message || "未知错误"}`);
          setError(`系统错误: ${errorData.message || "查询商品信息失败"}`);
          return;
        }
        
        // 检查是否有ID映射
        if (errorData && errorData.real_product_id && errorData.real_product_id !== parseInt(pid || productId)) {
          console.log(`检测到ID映射: 原始ID ${pid || productId} -> 真实商品ID ${errorData.real_product_id}`);
          console.log(`映射信息:`, errorData);
          
          // 强制更新当前商品ID为真实ID
          const realProductId = errorData.real_product_id;
          // 使用后端返回的正确商品名称，如果没有则使用原有名称或默认名称
          const realProductName = errorData.product_name || reviewData?.productName || "未知商品";
          
          console.log(`使用商品名称: ${realProductName}`);
          
          // 创建或更新reviewData
          const currentData = reviewData || {
            orderId: orderId,
            productId: pid || productId,
            productName: realProductName,  // 使用正确的商品名称
            productImage: '/images/Normal.jpg'
          };
          
          console.log(`更新reviewData: 将商品ID从 ${currentData.productId} 修改为 ${realProductId}`);
          console.log(`更新商品名称为: ${realProductName}`);
          
          // 创建新的reviewData对象，不直接修改原对象
          const updatedData = {
            ...currentData,
            productId: realProductId,
            productName: realProductName,  // 确保使用正确的商品名称
            originalProductId: currentData.productId, // 保存原始ID以供参考
            idMapped: true, // 标记已进行ID映射
            mappingMessage: errorData.mapping_message || `ID从 ${currentData.productId} 映射到 ${realProductId}`
          };
          
          // 更新状态
          setReviewData(updatedData);
          
          // 保存到localStorage
          localStorage.setItem('current_review_item', JSON.stringify(updatedData));
          console.log(`已更新localStorage中的商品ID为: ${realProductId}`);
          
          // 直接在这里重新查询正确ID的评论
          try {
            console.log(`立即使用真实商品ID ${realProductId} 重新查询评价...`);
            const token = localStorage.getItem('access') || localStorage.getItem('token');
            const retryResponse = await axios.get(`/api/review/reviews/user-product/${realProductId}/`, {
              headers: {
                'Authorization': `Bearer ${token}`
              }
            });
            
            if (retryResponse.status === 200 && retryResponse.data) {
              console.log(`成功: 使用ID ${realProductId} 找到评价:`, retryResponse.data);
              setExistingReview(retryResponse.data);
              setIsEditing(true);
              setRating(parseFloat(retryResponse.data.rating));
              setContent(retryResponse.data.content);
              
              // 处理已有的图片
              if (retryResponse.data.images && retryResponse.data.images.length > 0) {
                setImages(retryResponse.data.images.map(url => ({ isExisting: true, url })));
              }
              
              return; // 成功找到评价，直接返回
            }
          } catch (retryErr) {
            if (retryErr.response && retryErr.response.status === 404) {
              console.log(`使用真实商品ID ${realProductId} 确实没有找到评价，可以创建新评价`);
            } else {
              console.error(`使用真实商品ID ${realProductId} 重新查询失败:`, retryErr);
            }
          }
        }
      } else if (err.response && err.response.status !== 404) {
        console.error("检查评价状态失败:", err);
        setError(`检查评价状态失败: ${err.response?.data?.message || err.message || "未知错误"}`);
      }
    }
  };
  
  // 从API获取商品信息
  const fetchProductInfo = async () => {
    console.log("正在从localStorage和URL参数获取商品信息...");
    
    // 从localStorage获取数据
    const storedData = localStorage.getItem('current_review_item');
    if (storedData) {
      try {
        const parsedData = JSON.parse(storedData);
        console.log("从localStorage获取到的数据:", parsedData);
        
        // 验证数据完整性
        if (parsedData.productId && parsedData.productName) {
          setReviewData(parsedData);
          console.log(`使用localStorage中的商品ID: ${parsedData.productId}`);
          
          // 使用localStorage中的ID检查评论
          checkExistingReview(parsedData.productId);
          return;
        }
      } catch (e) {
        console.error("解析localStorage数据失败:", e);
      }
    }
    
    // 如果localStorage没有数据，使用URL参数
    const urlProductId = new URLSearchParams(window.location.search).get('productId');
    const urlOrderId = new URLSearchParams(window.location.search).get('orderId');
    
    if (urlProductId) {
      console.log(`从URL参数获取商品ID: ${urlProductId}`);
      
      // 创建基本的评价数据
      const basicData = {
        orderId: urlOrderId || orderId,
        productId: parseInt(urlProductId),
        productName: "加载中...",
        productImage: '/images/Normal.jpg'
      };
      
      setReviewData(basicData);
      localStorage.setItem('current_review_item', JSON.stringify(basicData));
      
      // 检查评论
      checkExistingReview(parseInt(urlProductId));
    } else {
      setError("无法获取商品信息，请从订单页面重新进入");
    }
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (content.trim() === '') {
      setError("请输入评价内容");
      return;
    }
    
    setUploading(true);
    setError('');
    
    try {
      const token = localStorage.getItem('access') || localStorage.getItem('token');
      
      // 如果有图片，先上传图片
      let imageUrls = [];
      if (images.length > 0) {
        // 处理新上传的图片和已有图片
        imageUrls = images.map(img => {
          // 如果是已有图片，直接使用URL
          if (img.isExisting) {
            return img.url;
          }
          // 如果是新上传的图片
          return URL.createObjectURL(img);
        });
      }
      
      // 确保获取正确的商品ID和名称
      if (!reviewData || !reviewData.productId) {
        setError("无法获取商品信息，请刷新页面重试");
        setUploading(false);
        return;
      }
      
      // 使用reviewData中的商品ID
      const productIdToUse = parseInt(reviewData.productId);
      
      // 验证商品ID是有效的数字
      if (isNaN(productIdToUse) || productIdToUse <= 0) {
        setError(`商品ID无效: ${reviewData.productId}`);
        setUploading(false);
        return;
      }
      
      console.log(`使用商品ID进行提交: ${productIdToUse}`);
      
      // 添加调试日志
      console.log("提交评价:", {
        isEditing,
        existingReviewId: existingReview?.id,
        product_id: productIdToUse,
        product_name: reviewData.productName || "未知商品",
        rating,
        content,
        images: imageUrls.length > 0 ? imageUrls : null
      });
      
      let submitResponse;
      
      if (isEditing && existingReview && existingReview.id) {
        // 更新现有评论
        console.log(`更新评论ID: ${existingReview.id}`);
        submitResponse = await axios.put(`/api/review/reviews/${existingReview.id}/`, {
          rating: rating,
          content: content,
          images: imageUrls.length > 0 ? imageUrls : null
        }, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
      } else {
        // 创建新评论
        console.log("创建新评论");
        submitResponse = await axios.post('/api/review/reviews/', {
          product_id: productIdToUse,
          product_name: reviewData.productName || "未知商品",
          rating: rating,
          content: content,
          images: imageUrls.length > 0 ? imageUrls : null
        }, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
      }
      
      console.log("评价提交成功:", submitResponse.data);
      setSuccess(isEditing ? "评价更新成功!" : "评价提交成功!");
      
      // 清除缓存的评价数据
      localStorage.removeItem('current_review_item');
      
      // 延迟返回会员中心
      setTimeout(() => {
        navigate('/member');
      }, 2000);
      
    } catch (err) {
      console.error("提交评价失败:", err.response?.data || err.message);
      if (err.response?.status === 400) {
        setError(`提交失败: ${err.response.data.error || '请检查输入数据'}`);
      } else if (err.response?.status === 404) {
        setError(`提交失败: 商品ID不存在或无效`);
      } else {
        setError("评价提交失败，请稍后重试");
      }
    } finally {
      setUploading(false);
    }
  };
  
  // 处理图片上传
  const handleImageUpload = (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
      // 计算已有图片数量（包括已有的和新上传的）
      const currentImagesCount = images.length;
      
      // 限制上传数量
      if (currentImagesCount + files.length > 5) {
        setError("最多只能上传5张图片");
        return;
      }
      
      // 检查文件大小和类型
      const validFiles = files.filter(file => {
        if (file.size > 5 * 1024 * 1024) {
          setError("图片大小不能超过5MB");
          return false;
        }
        
        if (!['image/jpeg', 'image/png', 'image/gif', 'image/webp'].includes(file.type)) {
          setError("只能上传JPG、PNG、GIF或WEBP格式的图片");
          return false;
        }
        
        return true;
      });
      
      if (validFiles.length > 0) {
        setImages(prev => [...prev, ...validFiles]);
        setError('');
      }
    }
  };
  
  // 移除已选择的图片
  const removeImage = (index) => {
    setImages(prev => prev.filter((_, i) => i !== index));
  };
  
  return (
    <div className="review-form-container">
      <div className="review-header">
        <h2>{isEditing ? '修改评价' : '商品评价'}</h2>
        <button className="back-button" onClick={() => navigate('/member')}>返回会员中心</button>
      </div>
      
      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}
      
      {reviewData && (
        <div className="product-info">
          <img 
            src={reviewData.productImage} 
            alt={reviewData.productName} 
            className="product-image"
            onError={(e) => {
              e.target.onerror = null;
              e.target.src = '/images/Normal.jpg';
            }}
          />
          <h3>{reviewData.productName}</h3>
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="review-form">
        <div className="rating-container">
          <label>评分:</label>
          <div className="stars">
            {[1, 2, 3, 4, 5].map((star) => (
              <span 
                key={star}
                className={star <= rating ? "star active" : "star"}
                onClick={() => setRating(star)}
              >
                ★
              </span>
            ))}
          </div>
          <span className="rating-text">{rating}分</span>
        </div>
        
        <div className="form-group">
          <label>评价内容:</label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="请输入您对商品的评价..."
            rows={5}
            required
          ></textarea>
        </div>
        
        <div className="form-group">
          <label>上传图片 (可选，最多5张):</label>
          <input 
            type="file" 
            multiple 
            accept="image/*" 
            onChange={handleImageUpload}
            disabled={images.length >= 5}
          />
          
          {images.length > 0 && (
            <div className="image-preview">
              {images.map((img, index) => (
                <div key={index} className="image-item">
                  <img src={img.isExisting ? img.url : URL.createObjectURL(img)} alt={`上传图片 ${index + 1}`} />
                  <button 
                    type="button" 
                    className="remove-btn"
                    onClick={() => removeImage(index)}
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
        
        <div className="form-actions">
          <button 
            type="submit" 
            className="submit-btn" 
            disabled={uploading}
          >
            {uploading ? '提交中...' : (isEditing ? '更新评价' : '提交评价')}
          </button>
        </div>
      </form>
    </div>
  );
}

export default ReviewForm; 