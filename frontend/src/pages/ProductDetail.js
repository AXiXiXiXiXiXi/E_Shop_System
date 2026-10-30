import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import '../styles/productDetail.css';

// 使用本地图片作为默认图片
const getProductImage = (product) => {
  // 检查产品是否有图片URL
  if (product && product.image_url) {
    return product.image_url;
  }
  
  // 根据产品ID选择一个默认图片
  const placeholderImages = [
    '/images/User.jpg',
    '/images/Normal.jpg',
    '/images/Loging.jpg'
  ];
  
  // 如果有产品ID，使用ID来选择占位图，否则随机选择一个
  if (product && product.id) {
    return placeholderImages[product.id % placeholderImages.length];
  }
  
  // 默认返回第一个占位图
  return placeholderImages[0];
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

// 生成商品图片数组
const generateRandomImages = (product, count = 5) => {
  // 商品详情图片列表 (16张)
  const detailImages = [
    '/Product_Detail_Images/IMG_8934.JPG',
    '/Product_Detail_Images/IMG_8935.JPG',
    '/Product_Detail_Images/IMG_8936.JPG',
    '/Product_Detail_Images/IMG_8937.JPG',
    '/Product_Detail_Images/IMG_8938.JPG',
    '/Product_Detail_Images/IMG_8939.JPG',
    '/Product_Detail_Images/IMG_8940.JPG',
    '/Product_Detail_Images/IMG_8941.JPG',
    '/Product_Detail_Images/IMG_8942.JPG',
    '/Product_Detail_Images/IMG_8943.JPG',
    '/Product_Detail_Images/IMG_8944.JPG',
    '/Product_Detail_Images/IMG_8945.JPG',
    '/Product_Detail_Images/IMG_8946.JPG',
    '/Product_Detail_Images/IMG_8947.JPG',
    '/Product_Detail_Images/IMG_8948.JPG',
    '/Product_Detail_Images/IMG_8949.JPG'
  ];
  
  // 确保所有图片都能被使用，根据产品ID进行分组选择
  const result = [];
  if (product && product.id) {
    // 使用产品ID作为随机种子
    const productSeed = product.id % 100000;
    
    // 将16张图片均匀分成多个组，每个产品从一个特定组开始选择
    const startIndex = productSeed % 16;
    
    // 计算步长，确保每个产品选择的图片分布较为均匀
    const step = Math.max(1, Math.floor(16 / count));
    
    // 选择图片
    for (let i = 0; i < count; i++) {
      // 计算当前要选择的图片索引
      const index = (startIndex + i * step) % 16;
      result.push(detailImages[index]);
    }
    
    // 额外的随机性：有25%的几率替换一张图片为完全随机选择的图片
    if (productSeed % 4 === 0) {
      const randomIndex = Math.floor(productSeed / 4) % count;
      const randomImageIndex = (productSeed * 13) % 16;
      result[randomIndex] = detailImages[randomImageIndex];
    }
  } else {
    // 如果没有产品ID，则完全随机选择
    const shuffled = [...detailImages];
    // 随机打乱
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    // 选择前5张
    return shuffled.slice(0, count);
  }
  
  return result;
};

const ProductDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedVariant, setSelectedVariant] = useState(null);
  const [quantity, setQuantity] = useState(1);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [productImages, setProductImages] = useState([]);
  
  // 新增评论相关状态
  const [reviews, setReviews] = useState([]);
  const [reviewsLoading, setReviewsLoading] = useState(true);
  const [reviewsError, setReviewsError] = useState(null);
  const [reviewStats, setReviewStats] = useState({
    total: 0,
    average_rating: 0,
    rating_counts: { "5": 0, "4": 0, "3": 0, "2": 0, "1": 0 }
  });

  useEffect(() => {
    const fetchProductDetail = async () => {
      try {
        // 使用不带认证的请求获取商品详情
        const response = await axios.get(`/api/product/products/${id}/`, {
          headers: { 'Authorization': '' } // 清除可能的认证头
        });
        const productData = response.data;
        
        setProduct(productData);

        // 生成或设置商品图片 - 每个商品显示5张图片
        const images = generateRandomImages(productData, 5);
        setProductImages(images);

        // 如果商品有变体，默认选择第一个变体
        if (productData.variants && productData.variants.length > 0) {
          setSelectedVariant(productData.variants[0]);
        }

        setLoading(false);
      } catch (err) {
        console.error('获取商品详情失败:', err);
        setError('获取商品详情失败，请稍后再试');
        setLoading(false);
      }
    };

    fetchProductDetail();
  }, [id]);

  // 添加获取评论的useEffect
  useEffect(() => {
    const fetchProductReviews = async () => {
      try {
        setReviewsLoading(true);
        console.log(`获取商品ID: ${id} 的评论数据...`);
        const response = await axios.get(`/api/review/reviews/product/${id}/`);
        
        // 添加调试代码，查看评论数据
        console.log("获取到的评论数据:", response.data);
        
        // 检查是否ID完全不存在
        if (response.data && response.data.id_not_found === true) {
          console.error(`错误: ID ${id} 既不是有效的产品ID，也不是有效的变体ID`);
          setReviewsError(`商品ID ${id} 无效，无法获取评论`);
          setReviewsLoading(false);
          return;
        }
        
        // 检查是否有API错误
        if (response.data && response.data.api_error === true) {
          console.error(`API错误: ${response.data.error || "未知错误"}`);
          setReviewsError(`系统错误: ${response.data.error || "获取评论失败"}`);
          setReviewsLoading(false);
          return;
        }
        
        // 如果返回了不同的商品ID映射，记录下来
        if (response.data && response.data.original_id && response.data.product_id && 
            parseInt(response.data.original_id) !== parseInt(response.data.product_id)) {
          console.log(`注意: 商品ID映射 ${response.data.original_id} -> ${response.data.product_id}`);
        }
        
        // 检查是否有变体ID相关信息
        if (response.data && response.data.variant_ids && response.data.variant_ids.length > 0) {
          console.log(`该产品相关的变体IDs: ${response.data.variant_ids.join(', ')}`);
        }
        
        // 确保总数据正确
        const reviewData = response.data || {};
        const totalCount = reviewData.total || 0;
        const reviewsList = reviewData.reviews || [];
        
        console.log(`共找到 ${totalCount} 条评论, 数组长度: ${reviewsList.length}`);
        
        // 检查每条评论的内容
        if (reviewsList.length > 0) {
          reviewsList.forEach((review, index) => {
            console.log(`评论 #${index+1}:`);
            console.log(`  ID: ${review.id}`);
            console.log(`  用户: ${review.username}`);
            console.log(`  内容: ${review.content ? `'${review.content}'` : '无内容'}`);
            console.log(`  商品ID: ${review.product_id}`);
            
            // 检查评论的商品ID与当前页面ID的关系
            const matchesCurrentId = review.product_id == id;
            const matchesRealProductId = review.product_id == (response.data.product_id || id);
            const isVariantId = response.data.variant_ids && response.data.variant_ids.includes(review.product_id);
            
            if (!matchesCurrentId && !matchesRealProductId && !isVariantId) {
              console.warn(`  警告: 该评论的商品ID ${review.product_id} 与当前商品ID ${id} 不匹配`);
              if (response.data.product_id) {
                console.warn(`  但与映射后的ID ${response.data.product_id} 比较: ${matchesRealProductId ? '匹配' : '不匹配'}`);
              }
              if (isVariantId) {
                console.log(`  该评论关联到产品的变体ID: ${review.product_id}`);
              }
            }
          });
        }
        
        // 设置评论列表
        setReviews(reviewsList);
        
        // 设置评论统计信息
        setReviewStats({
          total: totalCount,
          average_rating: reviewData.average_rating || 0,
          rating_counts: reviewData.rating_counts || { "1": 0, "2": 0, "3": 0, "4": 0, "5": 0 }
        });
        
        setReviewsLoading(false);
      } catch (err) {
        console.error('获取商品评论失败:', err);
        
        // 检查错误响应中是否包含特定错误信息
        if (err.response && err.response.status === 404) {
          if (err.response.data && err.response.data.id_not_found) {
            setReviewsError(`商品ID ${id} 不存在，无法获取评论`);
          } else {
            setReviewsError('未找到该商品的评论数据');
          }
        } else if (err.response && err.response.status === 500) {
          setReviewsError(`服务器错误: ${err.response.data?.error || '获取评论失败'}`);
        } else {
        setReviewsError('获取评论失败，请稍后再试');
        }
        
        setReviewsLoading(false);
      }
    };

    if (id) {
      fetchProductReviews();
    }
  }, [id]);
  
  // 删除不再需要的fetchUserDetails函数

  const handleVariantSelect = (variant) => {
    setSelectedVariant(variant);
    // 更新数量为1，避免超过新选中变体的库存
    setQuantity(1);
  };

  const handleQuantityChange = (e) => {
    const value = parseInt(e.target.value);
    
    // 确保数量大于0且不超过库存
    if (value > 0 && (!selectedVariant || value <= selectedVariant.stock)) {
      setQuantity(value);
    }
  };

  const handleAddToCart = async () => {
    if (!selectedVariant) {
      alert('请选择商品规格');
      return;
    }

    try {
      // 检查用户是否登录（同时检查access和token）
      const token = localStorage.getItem('access') || localStorage.getItem('token');
      if (!token) {
        navigate('/login', { state: { from: `/product/${id}` } });
        return;
      }

      // 添加到购物车，发送product_id和variant_id
      const response = await axios.post(
        '/api/cart/cart/add_item/',
        {
          product_id: product.id,
          product_variant_id: selectedVariant.id,
          quantity: quantity
        },
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      alert('商品已添加到购物车');
    } catch (err) {
      console.error('添加到购物车失败:', err);
      if (err.response && err.response.status === 401) {
        navigate('/login', { state: { from: `/product/${id}` } });
      } else {
        alert(err.response?.data?.error || '添加到购物车失败，请稍后再试');
      }
    }
  };

  const handleBuyNow = () => {
    if (!selectedVariant) {
      alert('请选择商品规格');
      return;
    }

    // 添加到购物车然后跳转到购物车页面
    handleAddToCart().then(() => {
      navigate('/cart');
    });
  };

  const handleThumbnailClick = (index) => {
    setCurrentImageIndex(index);
  };

  // 渲染星星评分
  const renderStars = (rating) => {
    const fullStars = Math.floor(rating);
    const halfStar = rating % 1 >= 0.5;
    const emptyStars = 5 - fullStars - (halfStar ? 1 : 0);
    
    return (
      <div className="review-stars">
        {'★'.repeat(fullStars)}
        {halfStar ? '½' : ''}
        {'☆'.repeat(emptyStars)}
      </div>
    );
  };

  if (loading) {
    return <div className="loading">加载商品详情中...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  if (!product) {
    return <div className="error">商品不存在</div>;
  }

  return (
    <div className="product-detail-container">
      <div className="product-detail">
        <div className="product-gallery">
          <div className="main-image">
            <img 
              src={productImages[currentImageIndex]} 
              alt={product.name} 
              loading="eager"
              onError={(e) => {
                // 如果图片加载失败，使用默认图片
                console.error('图片加载失败:', e.target.src);
                e.target.src = '/images/Normal.jpg';
              }}
            />
          </div>
          {productImages.length > 1 && (
            <div className="thumbnails">
              {productImages.map((image, index) => (
                <div 
                  key={index} 
                  className={`thumbnail ${index === currentImageIndex ? 'active' : ''}`}
                  onClick={() => handleThumbnailClick(index)}
                >
                  <img 
                    src={image} 
                    alt={`${product.name} - ${index + 1}`}
                    loading={index < 2 ? "eager" : "lazy"} 
                    onError={(e) => {
                      // 如果缩略图加载失败，使用默认图片
                      console.error('缩略图加载失败:', e.target.src);
                      e.target.src = '/images/Normal.jpg';
                    }}
                  />
                </div>
              ))}
            </div>
          )}
        </div>
        
        <div className="product-info">
          <h1>{product.name}</h1>
          <div className="meta">
            <span className="category">{product.category_name}</span>
            {product.brand && <span className="brand">{product.brand}</span>}
            {product.rating > 0 && (
              <div className="rating">
                <span>★</span> {typeof product.rating === 'number' ? product.rating.toFixed(1) : product.rating}
              </div>
            )}
            <span className="sales">销量: {product.sales_count}</span>
          </div>
          
          {selectedVariant && (
            <div className="price-info">
              <div className="current-price">
                ¥{typeof selectedVariant.price === 'number' ? selectedVariant.price.toFixed(2) : selectedVariant.price}
              </div>
              {selectedVariant.original_price && selectedVariant.original_price > selectedVariant.price && (
                <div className="original-price">
                  ¥{typeof selectedVariant.original_price === 'number' ? selectedVariant.original_price.toFixed(2) : selectedVariant.original_price}
                </div>
              )}
              {selectedVariant.is_on_sale && (
                <div className="discount">
                  {typeof selectedVariant.discount_percentage === 'number' ? selectedVariant.discount_percentage : 0}% OFF
                </div>
              )}
            </div>
          )}
          
          <div className="variants">
            <h3>规格</h3>
            <div className="variant-options">
              {product.variants.map(variant => (
                <button
                  key={variant.id}
                  className={`variant-option ${selectedVariant && selectedVariant.id === variant.id ? 'active' : ''} ${variant.stock <= 0 ? 'disabled' : ''}`}
                  onClick={() => variant.stock > 0 && handleVariantSelect(variant)}
                  disabled={variant.stock <= 0}
                >
                  {variant.name}
                  {variant.stock <= 0 && <span className="out-of-stock">已售罄</span>}
                </button>
              ))}
            </div>
          </div>
          
          <div className="quantity">
            <h3>数量</h3>
            <div className="quantity-control">
              <button
                onClick={() => quantity > 1 && setQuantity(quantity - 1)}
                disabled={quantity <= 1}
              >
                -
              </button>
              <input
                type="number"
                value={quantity}
                onChange={handleQuantityChange}
                min="1"
                max={selectedVariant ? selectedVariant.stock : 1}
              />
              <button
                onClick={() => quantity < (selectedVariant ? selectedVariant.stock : 1) && setQuantity(quantity + 1)}
                disabled={!selectedVariant || quantity >= selectedVariant.stock}
              >
                +
              </button>
              {selectedVariant && (
                <span className="stock">库存: {selectedVariant.stock}</span>
              )}
            </div>
          </div>
          
          <div className="actions">
            <button className="add-to-cart" onClick={handleAddToCart}>
              加入购物车
            </button>
            <button className="buy-now" onClick={handleBuyNow}>
              立即购买
            </button>
          </div>
        </div>
      </div>
      
      {/* 评论部分 */}
      <div className="product-reviews">
        <h2>商品评价 ({reviewStats.total})</h2>
        
        <div className="review-summary">
          <div className="review-average">
            <div className="big-rating">{reviewStats.average_rating.toFixed(1)}</div>
            <div className="big-stars">{renderStars(reviewStats.average_rating)}</div>
          </div>
          <div className="rating-bars">
            {[5, 4, 3, 2, 1].map(star => (
              <div className="rating-bar" key={star}>
                <div className="star-label">{star}星</div>
                <div className="bar-container">
                  <div 
                    className="bar-fill" 
                    style={{ 
                      width: reviewStats.total ? `${(reviewStats.rating_counts[star] / reviewStats.total) * 100}%` : '0%' 
                    }}
                  ></div>
                </div>
                <div className="count-label">{reviewStats.rating_counts[star]}</div>
              </div>
            ))}
          </div>
        </div>
        
        {reviewsLoading ? (
          <div className="reviews-loading">加载评论中...</div>
        ) : reviewsError ? (
          <div className="reviews-error">{reviewsError}</div>
        ) : reviews.length === 0 ? (
          <div className="no-reviews">暂无评价</div>
        ) : (
          <div className="review-list">
            {reviews.map(review => (
              <div className="review-item" key={review.id}>
                <div className="review-header">
                  <div className="review-user">
                    <div className="user-avatar">
                      {review.username ? review.username.substring(0, 1).toUpperCase() : '?'}
                    </div>
                    <div className="user-name">{review.username || `用户${review.user_id}`}</div>
                  </div>
                  <div className="review-rating">
                    {renderStars(review.rating)}
                    <span className="rating-value">{review.rating}</span>
                  </div>
                </div>
                {review.content ? (
                  <div className="review-content">
                    {review.content}
                  </div>
                ) : (
                  <div className="review-content empty">暂无评论内容</div>
                )}
                {review.images && review.images.length > 0 && (
                  <div className="review-images">
                    {review.images.map((image, index) => (
                      <div className="review-image" key={index}>
                        <img src={image} alt={`评价图片 ${index + 1}`} />
                      </div>
                    ))}
                  </div>
                )}
                <div className="review-date">
                  {new Date(review.created_at).toLocaleDateString('zh-CN', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                  })}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      
      <div className="product-description">
        <h2>商品详情</h2>
        <div className="description-content">
          {product.description || '暂无详细描述'}
        </div>
      </div>
    </div>
  );
};

export default ProductDetail; 