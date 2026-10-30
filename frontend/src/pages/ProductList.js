import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import '../styles/productList.css';

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

// 分类ID映射
const categoryIdMapping = {
  1: '电子产品',
  2: '服装鞋帽',
  3: '家居用品',
  4: '图书音像',
  5: '手机数码',
  6: '电脑办公',
  7: '男装',
  8: '女装'
};

// 使用分类图片作为默认图片
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
    const categoryName = categoryIdMapping[product.category];
    if (categoryName) {
      const categoryImage = categoryMapping[categoryName]?.image;
      if (categoryImage) {
        return categoryImage;
      }
    }
  }
  
  // 如果没有找到对应的分类图片，使用默认图片
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

const ProductList = () => {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [isFilterVisible, setIsFilterVisible] = useState(false);
  const [sortOption, setSortOption] = useState('default');
  const [addingToCart, setAddingToCart] = useState(null);
  const [categoryProductCounts, setCategoryProductCounts] = useState({});
  const [hoveredProduct, setHoveredProduct] = useState(null);

  const navigate = useNavigate();
  const location = useLocation();
  const searchParams = new URLSearchParams(location.search);
  const categoryParam = searchParams.get('category');
  const searchQuery = searchParams.get('search');
  const sortParam = searchParams.get('sort');

  // 获取每个分类的商品数量
  const fetchCategoryProductCounts = async () => {
    try {
      // 使用不带认证的请求
      const response = await axios.get('/api/product/products/?page_size=1000', {
        headers: { 'Authorization': '' } // 清除可能的认证头
      });
      const products = response.data.results || [];
      
      // 计算每个分类的商品数量
      const counts = {};
      products.forEach(product => {
        if (product.category) {
          counts[product.category] = (counts[product.category] || 0) + 1;
        }
      });
      
      setCategoryProductCounts(counts);
    } catch (err) {
      console.error('获取分类商品数量失败:', err);
      // 即使失败也不显示错误，继续显示商品列表
    }
  };

  useEffect(() => {
    // 获取分类列表
    const fetchCategories = async () => {
      try {
        // 获取第一页分类，使用不带认证的请求
        const response = await axios.get('/api/product/categories/', {
          headers: { 'Authorization': '' } // 清除可能的认证头
        });
        
        // 确保categories是一个数组
        if (Array.isArray(response.data)) {
          setCategories(response.data);
        } else if (response.data && Array.isArray(response.data.results)) {
          // 如果是分页数据，先设置第一页
          let allCategories = [...response.data.results];
          
          // 如果有多页，获取其他页面的数据
          if (response.data.next) {
            try {
              // 基于总数和每页数量计算总页数
              const totalPages = Math.ceil(response.data.count / response.data.results.length);
              
              // 获取剩余页面的数据
              for (let page = 2; page <= totalPages; page++) {
                const nextPageResponse = await axios.get(`/api/product/categories/?page=${page}`);
                if (nextPageResponse.data && Array.isArray(nextPageResponse.data.results)) {
                  allCategories = [...allCategories, ...nextPageResponse.data.results];
                }
              }
            } catch (err) {
              console.error('获取额外分类页面失败:', err);
            }
          }
          
          // 尝试修复可能损坏的分类名称
          allCategories = allCategories.map(category => {
            // 如果名称中全是问号，尝试使用一个友好的替代名称
            if (category.name && /^[?]+$/.test(category.name.replace(/\s/g, ''))) {
              return {
                ...category,
                name: `分类 ${category.id}`,
                fixedName: true
              };
            }
            return category;
          });
          
          // 处理重复的分类名称
          const nameMap = new Map();
          allCategories.forEach(category => {
            const name = category.name.trim();
            if (nameMap.has(name)) {
              // 如果已经存在相同名称的分类，保留ID较小的那个
              const existingCategory = nameMap.get(name);
              if (category.id < existingCategory.id) {
                nameMap.set(name, category);
              }
            } else {
              nameMap.set(name, category);
            }
          });
          
          // 过滤空名称的分类
          const filteredCategories = Array.from(nameMap.values()).filter(
            category => category.name && category.name.trim() !== ''
          );
          
          setCategories(filteredCategories);
        } else {
          console.error('分类数据不是数组格式:', response.data);
          setCategories([]);
        }
      } catch (err) {
        console.error('获取分类列表失败:', err);
        setCategories([]);
      }
    };

    fetchCategories();
    fetchCategoryProductCounts();
  }, []);

  useEffect(() => {
    // 设置当前选中的分类
    if (categoryParam) {
      setSelectedCategory(Number(categoryParam));
    }
    
    // 设置排序选项
    if (sortParam) {
      setSortOption(sortParam);
    }
  }, [categoryParam, sortParam]);

  useEffect(() => {
    // 获取商品列表
    const fetchProducts = async () => {
      setLoading(true);
      setError(null);

      try {
        // 构建URL参数
        const params = new URLSearchParams();
        params.append('page', page);
        
        if (selectedCategory) {
          params.append('category', selectedCategory);
        }
        
        if (searchQuery) {
          params.append('search', searchQuery);
        }
        
        if (sortOption && sortOption !== 'default') {
          params.append('sort', sortOption);
          console.log(`应用排序: ${sortOption}`);
        }

        const url = `/api/product/products/?${params.toString()}`;
        console.log("请求URL:", url);

        const response = await axios.get(url, {
          headers: { 'Authorization': '' } // 清除可能的认证头
        });
        console.log("API响应:", response.data);
        
        setProducts(response.data.results);
        
        // 计算实际页数
        const itemsPerPage = 12; // 固定每页显示12个商品
        
        // 获取当前页面实际商品数量和API返回的总商品数
        const currentPageItemCount = response.data.results.length;
        const totalCount = response.data.count || 0;
        
        // 检查是否是最后一页且不足12个商品
        const isLastPageWithFewItems = currentPageItemCount < itemsPerPage;
        
        // 计算实际总页数
        let calculatedTotalPages = Math.ceil(totalCount / itemsPerPage);
        
        // 如果当前页显示的商品数量小于每页应显示的数量，说明这是最后一页
        // 此时将总页数设置为当前页，防止出现多余的页码
        if (isLastPageWithFewItems && page > 1) {
          calculatedTotalPages = page;
        }
        
        console.log(`商品总数: ${totalCount}, 当前页商品数: ${currentPageItemCount}, 每页应显示: ${itemsPerPage}, 实际总页数: ${calculatedTotalPages}, 是否最后一页: ${isLastPageWithFewItems}`);
        
        // 确保页数不为0
        const actualTotalPages = calculatedTotalPages > 0 ? calculatedTotalPages : 1;
        setTotalPages(actualTotalPages);
        setLoading(false);
      } catch (err) {
        setError('获取商品列表失败，请稍后再试');
        setLoading(false);
        console.error('获取商品列表失败:', err);
      }
    };

    fetchProducts();
  }, [page, selectedCategory, searchQuery, sortOption]);

  const handleCategoryClick = (categoryId) => {
    setSelectedCategory(categoryId);
    setPage(1);
    navigate(`/products?category=${categoryId}`);
  };
  
  const handleSortChange = (e) => {
    const value = e.target.value;
    setSortOption(value);
    setPage(1);
    
    // 构建URL
    const params = new URLSearchParams();
    if (selectedCategory) {
      params.append('category', selectedCategory);
    }
    if (searchQuery) {
      params.append('search', searchQuery);
    }
    params.append('sort', value);
    
    // 输出日志
    console.log(`选择的排序选项: ${value}`);
    console.log(`跳转URL: /products?${params.toString()}`);
    
    navigate(`/products?${params.toString()}`);
  };

  const handleAddToCart = async (productId, variantId) => {
    try {
      // 设置正在添加的商品ID
      setAddingToCart(productId);
      
      // 检查用户是否登录（同时检查access和token）
      const token = localStorage.getItem('access') || localStorage.getItem('token');
      if (!token) {
        navigate('/login', { state: { from: location.pathname + location.search } });
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
      const productElement = document.getElementById(`product-${productId}`);
      if (productElement) {
        const notification = document.createElement('div');
        notification.className = 'add-success-notification';
        notification.textContent = '已添加到购物车';
        productElement.appendChild(notification);
        
        setTimeout(() => {
          notification.classList.add('show');
        }, 10);
        
        setTimeout(() => {
          notification.classList.remove('show');
          setTimeout(() => {
            productElement.removeChild(notification);
          }, 300);
        }, 2000);
      }
    } catch (err) {
      console.error('添加到购物车失败:', err);
      setAddingToCart(null);
      
      if (err.response && err.response.status === 401) {
        navigate('/login', { state: { from: location.pathname + location.search } });
      } else {
        alert(err.response?.data?.error || '添加到购物车失败，请稍后再试');
      }
    }
  };

  const renderPriceRange = (product) => {
    if (product.price_min === product.price_max) {
      return <span className="price">¥{product.price_min}</span>;
    }
    return <span className="price">¥{product.price_min} - ¥{product.price_max}</span>;
  };

  const toggleFilters = () => {
    setIsFilterVisible(!isFilterVisible);
  };

  // 过滤掉没有商品的分类
  const filteredCategories = categories.filter(category => {
    return categoryProductCounts[category.id] > 0;
  });

  if (loading && !products.length) {
    return (
      <div className="loading">
        <div className="loading-spinner"></div>
        <p>加载商品中...</p>
      </div>
    );
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  return (
    <div className="product-list-container">
      <button 
        className={`filter-toggle-btn ${isFilterVisible ? 'active' : ''}`}
        onClick={toggleFilters}
      >
        {isFilterVisible ? '隐藏筛选' : '显示筛选'}
      </button>
      
      <div className={`sidebar ${isFilterVisible ? 'visible' : ''}`}>
        <h3>商品分类</h3>
        <ul className="categories">
          <li 
            className={!selectedCategory ? 'active' : ''}
            onClick={() => {
              setSelectedCategory(null);
              navigate('/products');
            }}
          >
            所有分类
          </li>
          {filteredCategories.map(category => (
            <li 
              key={category.id}
              className={selectedCategory === category.id ? 'active' : ''}
              onClick={() => handleCategoryClick(category.id)}
            >
              {category.name}
              {categoryProductCounts[category.id] > 0 && (
                <span className="category-count">({categoryProductCounts[category.id]})</span>
              )}
            </li>
          ))}
        </ul>
      </div>
      <div className="main-content">
        <div className="header">
          <h2>{searchQuery ? `搜索结果: "${searchQuery}"` : '商品列表'}</h2>
          <div className="filters">
            <select value={sortOption} onChange={handleSortChange}>
              <option value="default">默认排序</option>
              <option value="price_asc">价格从低到高</option>
              <option value="price_desc">价格从高到低</option>
              <option value="newest">最新上架</option>
              <option value="rating">评分最高</option>
              <option value="bestselling">销量最高</option>
            </select>
          </div>
        </div>
        
        {products.length === 0 ? (
          <div className="no-products">
            <h3>没有找到符合条件的商品</h3>
            <p>请尝试更改筛选条件或浏览其他分类</p>
            <button 
              className="back-btn"
              onClick={() => {
                setSelectedCategory(null);
                navigate('/products');
              }}
            >
              查看所有商品
            </button>
          </div>
        ) : (
          <div className="products-grid">
            {products.map((product, index) => {
              const productImage = getProductImage(product);
              
              return (
                <div 
                  key={product.id} 
                  className="product-card" 
                  id={`product-${product.id}`}
                  style={{animationDelay: `${index * 0.05}s`}}
                >
                  <Link to={`/product/${product.id}`}>
                    <div className="product-image">
                      <img src={productImage} alt={product.name} />
                      {product.is_featured && <span className="product-badge featured">推荐</span>}
                      {product.discount > 0 && <span className="product-badge sale">特惠</span>}
                    </div>
                  </Link>
                  <div className="product-name">{product.name}</div>
                  <div className="product-meta">
                    {product.category_name && <span className="category">{product.category_name}</span>}
                    {product.brand && <span className="brand">{product.brand && ` · ${product.brand}`}</span>}
                  </div>
                  <div className="product-price">
                    {product.price_min === product.price_max 
                      ? `¥${typeof product.price_min === 'number' ? product.price_min.toFixed(2) : product.price_min}`
                      : `¥${typeof product.price_min === 'number' ? product.price_min.toFixed(2) : product.price_min} - ¥${typeof product.price_max === 'number' ? product.price_max.toFixed(2) : product.price_max}`
                    }
                  </div>
                  {product.rating > 0 && (
                    <div className="product-stats">
                      <span className="product-rating">★ {typeof product.rating === 'number' ? product.rating.toFixed(2) : product.rating}</span>
                      <span>销量 {product.sales_count}</span>
                    </div>
                  )}
                  <button 
                    className={`add-to-cart ${addingToCart === product.id ? 'adding' : ''}`}
                    onClick={() => {
                      // 如果没有提供变体ID，需要导航到产品详情页
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
              );
            })}
          </div>
        )}
        
        {totalPages > 0 && (
          <div className="pagination">
            {page > 1 && (
            <button 
                onClick={() => setPage(page - 1)}
              className="pagination-btn prev"
            >
              上一页
            </button>
            )}
            <div className="page-numbers">
              {/* 只显示实际存在的页码 */}
              {Array.from({ length: totalPages }, (_, i) => {
                // 页码从1开始
                const pageNum = i + 1;
                
                // 不显示超过实际页数的页码
                if (pageNum > totalPages) return null;
                
                // 显示逻辑（简化版）：
                // 如果总页数较少，全部显示
                // 否则只显示当前页附近的页码
                let shouldShow = false;
                
                if (totalPages <= 3) {
                  // 总页数小于等于3，显示所有页码
                  shouldShow = true;
                } else if (pageNum === 1 || pageNum === totalPages) {
                  // 始终显示第一页和最后一页
                  shouldShow = true;
                } else if (Math.abs(pageNum - page) <= 1) {
                  // 显示当前页及其相邻页
                  shouldShow = true;
                }
                
                return shouldShow ? (
                  <button
                    key={pageNum}
                    onClick={() => setPage(pageNum)}
                    className={`page-number ${page === pageNum ? 'active' : ''}`}
                  >
                    {pageNum}
                  </button>
                ) : pageNum === page - 2 || pageNum === page + 2 ? (
                  // 显示省略号
                  <span key={`ellipsis-${pageNum}`} className="page-ellipsis">...</span>
                ) : null;
              }).filter(Boolean)}
            </div>
            {page < totalPages && (
            <button 
                onClick={() => setPage(page + 1)}
              className="pagination-btn next"
            >
              下一页
            </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ProductList; 