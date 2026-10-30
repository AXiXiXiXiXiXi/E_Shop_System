import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import '../styles/home.css';

// 根据商品名称和分类获取适合的默认图片
const getProductImage = (product) => {
  // 检查产品是否有图片URL
  if (product && product.image_url) {
    return product.image_url;
  }
  
  // 根据产品分类选择对应的图片
  if (product && product.category_name) {
    const categoryImage = categoryMapping[product.category_name]?.image;
    if (categoryImage) {
      return categoryImage;
    }
  }
  
  // 根据产品分类ID选择对应的图片
  if (product && product.category) {
    const categoryName = mainCategories.find(c => c.id === product.category)?.name;
    if (categoryName) {
      const categoryImage = categoryMapping[categoryName]?.image;
      if (categoryImage) {
        return categoryImage;
      }
    }
  }
  
  // 默认返回用户图片
  return '/images/User.jpg';
};

// 分类映射
const categoryMapping = {
  '电子产品': { en: 'Electronic_Products', image: '/Product_Images/Electronic_Products.JPG' },
  '服装鞋帽': { en: 'Clothing_Shoes', image: '/Product_Images/Clothing_Shoes.JPG' },
  '家居用品': { en: 'Home_Goods', image: '/Product_Images/Home_Goods.JPG' },
  '图书音像': { en: 'Books_Media', image: '/Product_Images/Books_Media.JPG' },
  '手机数码': { en: 'Mobile_Digital', image: '/Product_Images/Mobile_Digital.JPG' },
  '电脑办公': { en: 'Computer_Office_Supplies', image: '/Product_Images/Computer_Office_Supplies.JPG' },
  '男装': { en: 'Mens_Clothing', image: '/Product_Images/Mens_Clothing.JPG' },
  '女装': { en: 'Womens_Clothing', image: '/Product_Images/Womens_Clothing.JPG' }
};

// 主要分类列表（用于展示）
const mainCategories = [
  { name: '电子产品', id: 1 },
  { name: '服装鞋帽', id: 2 },
  { name: '家居用品', id: 3 },
  { name: '图书音像', id: 4 },
  { name: '手机数码', id: 5 },
  { name: '电脑办公', id: 6 },
  { name: '男装', id: 7 },
  { name: '女装', id: 8 }
];

function Home() {
  const [loading, setLoading] = useState(false);
  const [currentSlide, setCurrentSlide] = useState(0);
  const [featuredProducts, setFeaturedProducts] = useState([]);
  const [newProducts, setNewProducts] = useState([]);
  const [bestSellingProducts, setBestSellingProducts] = useState([]);
  const [productsLoading, setProductsLoading] = useState(true);
  const [hoveredProduct, setHoveredProduct] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [productsPerPage] = useState(12);
  const [showScrollTop, setShowScrollTop] = useState(false);
  const [addingToCart, setAddingToCart] = useState(null);
  const [categories, setCategories] = useState([]);
  
  const navigate = useNavigate();

  // 更现代化的轮播图数据
  const bannerImages = [
    {
      id: 1,
      title: '春季新品上市',
      subtitle: '精选好物，品质保证',
      color: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)'
    },
    {
      id: 2,
      title: '夏日特惠',
      subtitle: '精选商品优惠',
      color: 'linear-gradient(135deg, #ff7a45 0%, #ff4d4f 100%)'
    },
    {
      id: 3,
      title: '会员专享福利',
      subtitle: '注册即享专属优惠',
      color: 'linear-gradient(135deg, #f97316 0%, #ef4444 100%)'
    }
  ];

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

  // 监听滚动事件，显示/隐藏回到顶部按钮
  useEffect(() => {
    const handleScroll = () => {
      if (window.pageYOffset > 300) {
        setShowScrollTop(true);
      } else {
        setShowScrollTop(false);
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // 回到顶部功能
  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  };

  useEffect(() => {
    // 轮播图自动切换
    const interval = setInterval(() => {
      setCurrentSlide(prev => (prev + 1) % bannerImages.length);
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  // 获取推荐商品
  useEffect(() => {
    const fetchProducts = async () => {
      setProductsLoading(true);
      try {
        // 获取推荐商品
        const featuredResponse = await axios.get('/api/product/products/featured/');
        setFeaturedProducts(featuredResponse.data);

        // 获取最新商品
        const newResponse = await axios.get('/api/product/products/latest/');
        setNewProducts(newResponse.data);

        // 获取畅销商品
        const bestSellingResponse = await axios.get('/api/product/products/bestselling/');
        setBestSellingProducts(bestSellingResponse.data);

        setProductsLoading(false);
      } catch (error) {
        console.error('获取商品列表失败:', error);
        setProductsLoading(false);
      }
    };

    fetchProducts();
    
    // 设置Intersection Observer for 滚动动画
    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.style.animationPlayState = 'running';
          entry.target.classList.add('animate-in');
        }
      });
    }, observerOptions);
    
    // 延迟观察，确保DOM已渲染
    setTimeout(() => {
      const animatedElements = document.querySelectorAll('.product-section, .categories-section');
      animatedElements.forEach((el) => {
        el.style.animationPlayState = 'paused';
        observer.observe(el);
      });
    }, 100);
    
    return () => observer.disconnect();
  }, []);

  // 分页处理
  const handlePageChange = (pageNumber) => {
    setCurrentPage(pageNumber);
    // 滚动到产品区域顶部
    document.querySelector('.product-section').scrollIntoView({ behavior: 'smooth' });
  };

  // 分页显示商品
  const paginateProducts = (products) => {
    const startIndex = (currentPage - 1) * productsPerPage;
    const endIndex = startIndex + productsPerPage;
    return products.slice(startIndex, endIndex);
  };

  // 计算总页数
  const calculateTotalPages = (totalItems) => {
    return Math.ceil(totalItems / productsPerPage);
  };

  // 渲染商品卡片
  const renderProductCard = (product, index) => {
    const isHovered = hoveredProduct === product.id;
    const productImage = getProductImage(product);
    
    return (
      <div 
        key={product.id} 
        className="product-card"
        onMouseEnter={() => setHoveredProduct(product.id)}
        onMouseLeave={() => setHoveredProduct(null)}
        style={{ 
          '--card-index': index,
          animationDelay: `${index * 0.1}s` 
        }}
      >
        <Link to={`/product/${product.id}`} className="img-wrap">
          <img src={productImage} alt={product.name} />
          {product.is_featured && <span className="product-badge featured">推荐</span>}
        </Link>
        <div className="info">
          <Link to={`/product/${product.id}`}><h3 title={product.name}>{product.name}</h3></Link>
          <div className="tags">
            {product.category_name && <span>{product.category_name}</span>}
            {product.brand && <span>{product.brand}</span>}
            {product.discount > 0 && <span className="discount">特惠</span>}
          </div>
          <div className="price">¥{typeof product.price_min === 'number' ? product.price_min.toFixed(2) : product.price_min}</div>
          {product.rating > 0 && (
            <div className="rating">
              <div className="stars">{'★'.repeat(Math.floor(product.rating))}</div>
              <div className="count">({product.sales_count})</div>
            </div>
          )}
          <div className="actions">
            <button 
              className={`btn-cart ${addingToCart === product.id ? 'loading' : ''}`}
              onClick={(e) => {
                e.preventDefault();
                if (!product.default_variant_id) {
                  navigate(`/product/${product.id}`);
                } else {
                  handleAddToCart(product.id, product.default_variant_id);
                }
              }}
              disabled={addingToCart === product.id}
            >
              {addingToCart === product.id ? '添加中...' : '加入购物车'}
            </button>
          </div>
        </div>
      </div>
    );
  };

  // 添加到购物车
  const handleAddToCart = async (productId, variantId) => {
    try {
      // 设置正在添加的商品ID
      setAddingToCart(productId);
      
      // 检查用户是否登录（同时检查access和token）
      const token = localStorage.getItem('access') || localStorage.getItem('token');
      if (!token) {
        navigate('/login', { state: { from: location.pathname } });
        return;
      }

      // 添加到购物车
      await axios.post(
        '/api/cart/cart/add_item/',
        {
          product_id: productId,
          variant_id: variantId || null, // 如果没有提供变体ID，则使用null
          quantity: 1
        },
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      // 显示添加成功的动画效果
      setTimeout(() => {
        setAddingToCart(null);
      }, 1000);
      
      // 显示添加成功的提示
      alert('成功添加到购物车!');
    } catch (err) {
      console.error('添加到购物车失败:', err);
      setAddingToCart(null);
      
      if (err.response && err.response.status === 401) {
        navigate('/login', { state: { from: location.pathname } });
      } else {
        alert(err.response?.data?.error || '添加到购物车失败，请稍后再试');
      }
    }
  };

  return (
    <div className="home fade-in">
      {/* 轮播图区域 */}
      <section className="hero-section">
        <div className="carousel">
          {bannerImages.map((banner, index) => (
            <div
              key={banner.id}
              className={`carousel-slide ${index === currentSlide ? 'active' : ''}`}
              style={{ background: banner.color }}
            >
              <div className="banner-overlay"></div>
              <div className="container">
                <div className="hero-content">
                  <div className="hero-text">
                    <h1 className="hero-title">{banner.title}</h1>
                    <p className="hero-subtitle">{banner.subtitle}</p>
                    <Link to="/products" className="btn btn-primary">
                      浏览商品
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          ))}
          <div className="carousel-indicators">
            {bannerImages.map((_, index) => (
              <button
                key={index}
                className={`indicator ${index === currentSlide ? 'active' : ''}`}
                onClick={() => setCurrentSlide(index)}
              />
            ))}
          </div>
          <button className="carousel-control prev" onClick={() => setCurrentSlide((currentSlide - 1 + bannerImages.length) % bannerImages.length)}>
            &lsaquo;
          </button>
          <button className="carousel-control next" onClick={() => setCurrentSlide((currentSlide + 1) % bannerImages.length)}>
            &rsaquo;
          </button>
        </div>
      </section>

      {/* 分类导航区域 */}
      <section className="categories-section">
        <div className="container">
          <div className="section-title-container">
            <h2 className="section-title">商品分类</h2>
            <div className="section-title-line"></div>
          </div>
          <div className="categories-grid">
            {mainCategories.map((category) => (
              <Link 
                to={`/products?category=${category.id}`} 
                key={category.id} 
                className="category-card"
              >
                <div className="category-image">
                  <img 
                    src={categoryMapping[category.name]?.image || '/images/Normal.jpg'} 
                    alt={category.name} 
                    onError={(e) => { e.target.src = '/images/Normal.jpg' }}
                  />
                </div>
                <div className="category-name">{category.name}</div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* 特色功能区域 */}
      <section className="features-section">
        <div className="container">
          <div className="section-title-container">
            <h2 className="section-title">我们的优势</h2>
            <div className="section-title-line"></div>
          </div>
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">🚚</div>
              <h3>免费配送</h3>
              <p>满99元免费配送到家</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🔒</div>
              <h3>安全支付</h3>
              <p>多重加密保障支付安全</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🎁</div>
              <h3>会员特权</h3>
              <p>专享折扣和积分奖励</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">📞</div>
              <h3>24小时客服</h3>
              <p>随时为您解答疑问</p>
            </div>
          </div>
        </div>
      </section>

      {/* 推荐商品区域 */}
      <section className="product-section">
        <div className="container">
          <div className="section-header">
            <div className="section-title-container">
              <h2 className="section-title">精选推荐</h2>
              <div className="section-title-line"></div>
            </div>
            <Link to="/products?featured=true" className="view-all">查看全部 →</Link>
          </div>
          
          <div className="products-container">
            {productsLoading ? (
              <div className="loading-products">
                <div className="loading-spinner"></div>
                <p>加载中...</p>
              </div>
            ) : featuredProducts.length > 0 ? (
              <div className="products-grid">
                {paginateProducts(featuredProducts).map((product, index) => renderProductCard(product, index))}
              </div>
            ) : (
              <div className="no-products">暂无推荐商品</div>
            )}

            {featuredProducts.length > productsPerPage && (
              <div className="pagination">
                {Array.from({ length: calculateTotalPages(featuredProducts.length) }, (_, i) => (
                  <button
                    key={i + 1}
                    className={`page-btn ${currentPage === i + 1 ? 'active' : ''}`}
                    onClick={() => handlePageChange(i + 1)}
                  >
                    {i + 1}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </section>

      {/* 新品上市区域 */}
      <section className="product-section">
        <div className="container">
          <div className="section-header">
            <div className="section-title-container">
              <h2 className="section-title">新品上市</h2>
              <div className="section-title-line"></div>
            </div>
            <Link to="/products?sort=newest" className="view-all">查看全部 →</Link>
          </div>
          
          <div className="products-container">
            {productsLoading ? (
              <div className="loading-products">
                <div className="loading-spinner"></div>
                <p>加载中...</p>
              </div>
            ) : newProducts.length > 0 ? (
              <div className="products-grid">
                {paginateProducts(newProducts).map((product, index) => renderProductCard(product, index))}
              </div>
            ) : (
              <div className="no-products">暂无新品</div>
            )}

            {newProducts.length > productsPerPage && (
              <div className="pagination">
                {Array.from({ length: calculateTotalPages(newProducts.length) }, (_, i) => (
                  <button
                    key={i + 1}
                    className={`page-btn ${currentPage === i + 1 ? 'active' : ''}`}
                    onClick={() => handlePageChange(i + 1)}
                  >
                    {i + 1}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </section>

      {/* 热卖商品区域 */}
      <section className="product-section">
        <div className="container">
          <div className="section-header">
            <div className="section-title-container">
              <h2 className="section-title">热卖商品</h2>
              <div className="section-title-line"></div>
            </div>
            <Link to="/products?sort=bestselling" className="view-all">查看全部 →</Link>
          </div>
          
          <div className="products-container">
            {productsLoading ? (
              <div className="loading-products">
                <div className="loading-spinner"></div>
                <p>加载中...</p>
              </div>
            ) : bestSellingProducts.length > 0 ? (
              <div className="products-grid">
                {paginateProducts(bestSellingProducts).map((product, index) => renderProductCard(product, index))}
              </div>
            ) : (
              <div className="no-products">暂无热卖商品</div>
            )}

            {bestSellingProducts.length > productsPerPage && (
              <div className="pagination">
                {Array.from({ length: calculateTotalPages(bestSellingProducts.length) }, (_, i) => (
                  <button
                    key={i + 1}
                    className={`page-btn ${currentPage === i + 1 ? 'active' : ''}`}
                    onClick={() => handlePageChange(i + 1)}
                  >
                    {i + 1}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </section>
      
      {/* 品牌展示区域 */}
      <section className="brands-section">
        <div className="container">
          <div className="section-title-container">
            <h2 className="section-title">合作品牌</h2>
            <div className="section-title-line"></div>
          </div>
          <div className="brands-grid">
            <div className="brand-item">
              <div className="brand-logo">A</div>
              <div className="brand-name">Apple</div>
            </div>
           
            <div className="brand-item">
              <div className="brand-logo">X</div>
              <div className="brand-name">Xiaomi</div>
            </div>
            <div className="brand-item">
              <div className="brand-logo">H</div>
              <div className="brand-name">Huawei</div>
            </div>
            <div className="brand-item">
              <div className="brand-logo">D</div>
              <div className="brand-name">Dell</div>
            </div>
            <div className="brand-item">
              <div className="brand-logo">S</div>
              <div className="brand-name">Samsung</div>
            </div>
          </div>
        </div>
      </section>

      {/* 回到顶部按钮 */}
      {showScrollTop && (
        <button className="scroll-to-top" onClick={scrollToTop}>
          ↑
        </button>
      )}
    </div>
  );
}

export default Home;