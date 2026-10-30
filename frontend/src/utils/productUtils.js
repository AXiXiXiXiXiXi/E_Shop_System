/**
 * 商品相关工具函数
 */

// 获取商品详情页的第一张图片
export const getProductDetailImage = (product) => {
  // 检查产品是否有图片URL
  if (product && product.image_url) {
    return product.image_url;
  }

  // 商品详情图片列表
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
  
  // 根据产品ID选择第一张图片
  if (product && product.id) {
    // 使用产品ID作为随机种子
    const productSeed = product.id % 100000;
    
    // 根据产品ID选择第一张图片的索引
    const imageIndex = productSeed % detailImages.length;
    return detailImages[imageIndex];
  }
  
  // 默认返回第一张图片
  return detailImages[0];
};

// 处理图片URL的辅助函数
export const processImageUrl = (imagePath) => {
  if (!imagePath) return null;
  
  // 完整的URL直接返回
  if (imagePath.startsWith('http://') || imagePath.startsWith('https://')) {
    return imagePath;
  }
  
  const baseUrl = process.env.REACT_APP_API_URL !== undefined
    ? process.env.REACT_APP_API_URL
    : 'http://127.0.0.1:8000';  // 后端服务器地址
  
  // 添加适当的前缀
  if (imagePath.startsWith('/media/')) {
    return `${baseUrl}${imagePath}`;
  } else if (imagePath.startsWith('/static/')) {
    return `${baseUrl}${imagePath}`;
  } else if (imagePath.startsWith('/')) {
    return `${baseUrl}${imagePath}`;
  } else {
    // 如果是相对路径，假设是在media目录下
    return `${baseUrl}/media/${imagePath}`;
  }
}; 