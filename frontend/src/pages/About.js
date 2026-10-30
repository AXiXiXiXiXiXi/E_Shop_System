import React from 'react';
import { Link } from 'react-router-dom';
import '../styles/legal.css';

function About() {
  return (
    <div className="legal-container">
      <div className="legal-header">
        <div className="container">
          <h1>关于武汉精品商城</h1>
          <p className="header-subtitle">致力于为您提供优质商品和贴心服务</p>
        </div>
      </div>
      
      <div className="legal-content">
        <div className="container">
          <div className="legal-nav">
            <Link to="/" className="back-link">← 返回首页</Link>
            <div className="nav-links">
              <Link to="/terms" className="nav-link">用户协议</Link>
              <Link to="/privacy" className="nav-link">隐私政策</Link>
              <Link to="/help" className="nav-link">帮助中心</Link>
            </div>
          </div>
          
          <div className="about-content">
            <section className="company-intro">
              <div className="intro-card">
                <div className="card-icon">🏢</div>
                <h2>公司简介</h2>
                <p>武汉精品商城成立于2020年，是一家专注于为消费者提供优质商品和服务的综合性电子商务平台。我们始终坚持"品质第一，服务至上"的经营理念，致力于成为华中地区最受信赖的在线购物平台。</p>
                <p>我们的使命是通过技术创新和服务优化，为每一位用户创造愉快的购物体验，让优质生活触手可及。</p>
              </div>
            </section>

            <section className="company-values">
              <h2>核心价值观</h2>
              <div className="values-grid">
                <div className="value-item">
                  <div className="value-icon">🎯</div>
                  <h3>品质至上</h3>
                  <p>严格筛选每一件商品，确保为用户提供高品质的产品体验</p>
                </div>
                <div className="value-item">
                  <div className="value-icon">❤️</div>
                  <h3>用户为本</h3>
                  <p>以用户需求为导向，不断优化服务流程和购物体验</p>
                </div>
                <div className="value-item">
                  <div className="value-icon">⚡</div>
                  <h3>高效创新</h3>
                  <p>运用先进技术，持续创新服务模式，提升运营效率</p>
                </div>
                <div className="value-item">
                  <div className="value-icon">🤝</div>
                  <h3>诚信经营</h3>
                  <p>坚持诚信原则，建立透明、公正的商业环境</p>
                </div>
              </div>
            </section>

            <section className="terms-section company-history">
              <h2>发展历程</h2>
              <div className="timeline">
                <div className="timeline-item">
                  <div className="timeline-year">2020</div>
                  <div className="timeline-content">
                    <h3>创立之年</h3>
                    <p>武汉精品商城正式成立，开始在武汉本地提供优质商品服务</p>
                  </div>
                </div>
                <div className="timeline-item">
                  <div className="timeline-year">2021</div>
                  <div className="timeline-content">
                    <h3>快速发展</h3>
                    <p>用户量突破10万，商品品类扩展至8大类别，建立完善的物流体系</p>
                  </div>
                </div>
                <div className="timeline-item">
                  <div className="timeline-year">2022</div>
                  <div className="timeline-content">
                    <h3>服务升级</h3>
                    <p>推出会员积分系统，上线24小时客服服务，获得ISO质量认证</p>
                  </div>
                </div>
                <div className="timeline-item">
                  <div className="timeline-year">2023</div>
                  <div className="timeline-content">
                    <h3>技术创新</h3>
                    <p>引入智能推荐系统，上线售后聊天功能，用户满意度达98%</p>
                  </div>
                </div>
                <div className="timeline-item">
                  <div className="timeline-year">2024</div>
                  <div className="timeline-content">
                    <h3>技术创新</h3>
                    <p>引入人工智能推荐，推出直播带货功能，建立绿色配送体系</p>
                  </div>
                </div>
                <div className="timeline-item">
                  <div className="timeline-year">2025</div>
                  <div className="timeline-content">
                    <h3>智能升级</h3>
                    <p>升级智能算法，推出AR试用功能，开展跨境电商业务</p>
                  </div>
                </div>
                <div className="timeline-item">
                  <div className="timeline-year">2026</div>
                  <div className="timeline-content">
                    <h3>品牌升级</h3>
                    <p>全面升级用户界面，优化购物流程，向全国市场拓展</p>
                  </div>
                </div>
              </div>
            </section>

            <section className="terms-section business-scope">
              <h2>业务范围</h2>
              <div className="business-grid">
                <div className="business-item">
                  <div className="business-icon">📱</div>
                  <h3>电子数码</h3>
                  <p>手机、电脑、智能设备等高科技产品</p>
                </div>
                <div className="business-item">
                  <div className="business-icon">👕</div>
                  <h3>服装鞋帽</h3>
                  <p>时尚服饰、运动装备、精品配饰</p>
                </div>
                <div className="business-item">
                  <div className="business-icon">🏠</div>
                  <h3>家居用品</h3>
                  <p>家具、装饰、生活用品等居家必需品</p>
                </div>
                <div className="business-item">
                  <div className="business-icon">📚</div>
                  <h3>图书文娱</h3>
                  <p>图书、文具、音像制品等文化产品</p>
                </div>
                <div className="business-item">
                  <div className="business-icon">💄</div>
                  <h3>美妆护肤</h3>
                  <p>化妆品、护肤品、个人护理用品</p>
                </div>
                <div className="business-item">
                  <div className="business-icon">🎮</div>
                  <h3>娱乐休闲</h3>
                  <p>游戏设备、运动器材、户外用品</p>
                </div>
              </div>
            </section>

            <section className="team-intro">
              <h2>团队介绍</h2>
              <div className="team-stats">
                <div className="stat-item">
                  <div className="stat-number">50+</div>
                  <div className="stat-label">专业团队成员</div>
                </div>
                <div className="stat-item">
                  <div className="stat-number">5年</div>
                  <div className="stat-label">平均行业经验</div>
                </div>
                <div className="stat-item">
                  <div className="stat-number">100万+</div>
                  <div className="stat-label">服务用户数量</div>
                </div>
                <div className="stat-item">
                  <div className="stat-number">99.5%</div>
                  <div className="stat-label">用户满意度</div>
                </div>
              </div>
              <p className="team-description">
                我们拥有一支年轻而充满活力的专业团队，包括技术开发、产品运营、客户服务、物流配送等各个部门。
                团队成员均具备丰富的电商行业经验和专业技能，始终以用户需求为中心，为提供更好的服务而不断努力。
              </p>
            </section>

            <section className="service-advantages">
              <h2>服务优势</h2>
              <div className="advantages-grid">
                <div className="advantage-item">
                  <div className="advantage-icon">🚚</div>
                  <h3>快速配送</h3>
                  <p>武汉市内24小时达，全国3-5天配送到家</p>
                </div>
                <div className="advantage-item">
                  <div className="advantage-icon">🔒</div>
                  <h3>安全保障</h3>
                  <p>银行级安全加密，多重保护确保交易安全</p>
                </div>
                <div className="advantage-item">
                  <div className="advantage-icon">💎</div>
                  <h3>品质保证</h3>
                  <p>正品保障，7天无理由退换，品质问题包退包换</p>
                </div>
                <div className="advantage-item">
                  <div className="advantage-icon">🎧</div>
                  <h3>贴心服务</h3>
                  <p>24小时在线客服，售后聊天功能，问题及时响应</p>
                </div>
                <div className="advantage-item">
                  <div className="advantage-icon">🎁</div>
                  <h3>会员权益</h3>
                  <p>积分返现，专属优惠，会员等级越高优惠越多</p>
                </div>
                <div className="advantage-item">
                  <div className="advantage-icon">📱</div>
                  <h3>便捷体验</h3>
                  <p>响应式设计，手机电脑同步购物体验</p>
                </div>
              </div>
            </section>

            <section className="contact-info">
              <h2>联系我们</h2>
              <div className="contact-grid">
                <div className="contact-item">
                  <div className="contact-icon">📍</div>
                  <h3>公司地址</h3>
                  <p>湖北省武汉市江夏区武汉工厂科技学院</p>
                </div>
                <div className="contact-item">
                  <div className="contact-icon">📞</div>
                  <h3>联系电话</h3>
                  <p>客服热线：15623826666<br/>工作时间：9:00-18:00</p>
                </div>
                <div className="contact-item">
                  <div className="contact-icon">✉️</div>
                  <h3>邮箱地址</h3>
                  <p>客服邮箱：2819291673@qq.com<br/>商务合作：2819291673@qq.com</p>
                </div>
                <div className="contact-item">
                  <div className="contact-icon">🌐</div>
                  <h3>官方网站</h3>
                  <p>www.whjpsc.com<br/>关注我们获取最新优惠</p>
                </div>
              </div>
            </section>

            <section className="future-vision">
              <h2>未来展望</h2>
              <div className="vision-card">
                <p>
                  展望未来，武汉精品商城将继续秉承"品质第一，服务至上"的理念，
                  通过技术创新和服务升级，为用户提供更加便捷、安全、优质的购物体验。
                </p>
                <p>
                  我们计划在未来三年内，将服务范围扩展至全国主要城市，
                  建立更加完善的物流网络和服务体系，成为中国领先的综合性电商平台。
                </p>
                <p>
                  同时，我们将继续投入研发，运用人工智能、大数据等先进技术，
                  为每一位用户提供个性化的购物推荐和专属服务，让购物变得更加智能和便捷。
                </p>
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}

export default About; 