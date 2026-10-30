import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import '../styles/legal.css';

function Help() {
  const [activeCategory, setActiveCategory] = useState('shopping');
  const [expandedFAQ, setExpandedFAQ] = useState(null);

  const categories = {
    shopping: '购物指南',
    payment: '支付帮助',
    delivery: '配送服务',
    aftersale: '售后服务',
    account: '账户管理',
    others: '其他问题'
  };

  const faqData = {
    shopping: [
      {
        question: '如何注册成为会员？',
        answer: '点击页面右上角"注册"按钮，填写手机号码、邮箱地址和密码即可快速注册。注册后即可享受会员专属优惠和积分奖励。'
      },
      {
        question: '如何搜索商品？',
        answer: '您可以在首页搜索框中输入商品名称、品牌或关键词进行搜索。也可以通过商品分类浏览您需要的商品。'
      },
      {
        question: '如何添加商品到购物车？',
        answer: '在商品详情页选择规格和数量后，点击"加入购物车"按钮。您也可以直接点击"立即购买"进行快速下单。'
      },
      {
        question: '如何查看购物车？',
        answer: '点击页面右上角的购物车图标即可查看已添加的商品。在购物车页面可以修改数量、删除商品或结算订单。'
      },
      {
        question: '商品价格会变动吗？',
        answer: '商品价格可能因促销活动、成本变化等因素有所调整，以您下单时的价格为准。建议及时下单以锁定优惠价格。'
      }
    ],
    payment: [
      {
        question: '支持哪些支付方式？',
        answer: '我们支持多种支付方式：钱包余额、银行卡支付、微信支付、支付宝、京东支付等。所有支付过程均采用银行级别的安全加密。'
      },
      {
        question: '支付失败怎么办？',
        answer: '请检查网络连接、银行卡余额或支付密码是否正确。如仍有问题，请联系客服或尝试更换支付方式。'
      },
      {
        question: '如何充值钱包余额？',
        answer: '登录会员中心，进入"我的钱包"页面，选择充值金额和支付方式即可快速充值。充值金额实时到账。'
      },
      {
        question: '支付安全吗？',
        answer: '我们采用SSL加密技术和多重安全验证，确保您的支付信息安全。同时与银行和第三方支付机构建立了安全合作关系。'
      },
      {
        question: '可以开发票吗？',
        answer: '可以开具电子发票和纸质发票。在下单时选择"需要发票"并填写发票信息，电子发票将发送到您的邮箱。'
      }
    ],
    delivery: [
      {
        question: '配送范围和时间？',
        answer: '武汉市内当日达或次日达，其他城市2-5个工作日送达。具体配送时间以商品页面显示为准。'
      },
      {
        question: '配送费用如何计算？',
        answer: '配送费根据商品重量、体积和配送距离计算。单笔订单满99元免配送费，部分商品支持包邮。'
      },
      {
        question: '可以指定配送时间吗？',
        answer: '支持预约配送，您可以在下单时选择希望的配送时间段。我们会尽量按您的要求安排配送。'
      },
      {
        question: '如何修改收货地址？',
        answer: '订单未发货前，可以联系客服修改收货地址。订单已发货后，需要联系快递公司进行地址变更。'
      },
      {
        question: '没有人收货怎么办？',
        answer: '配送员会电话联系您确认收货时间。如无人接收，商品会暂存在快递柜或快递点，请及时取件。'
      }
    ],
    aftersale: [
      {
        question: '什么情况可以退货？',
        answer: '商品收到后7天内，保持商品完好且未使用，可以申请无理由退货。质量问题商品支持15天内退换货。'
      },
      {
        question: '如何申请退货？',
        answer: '登录会员中心，在"我的订单"中找到相应订单，点击"申请退货"并填写退货原因即可。'
      },
      {
        question: '退款多久到账？',
        answer: '退货商品收到并验收通过后，退款将在3-7个工作日内原路返回到您的付款账户。'
      },
      {
        question: '哪些商品不支持退货？',
        answer: '个人定制商品、生鲜易腐商品、贴身用品、软件下载类商品等不支持无理由退货，具体以商品页面说明为准。'
      },
      {
        question: '如何联系售后客服？',
        answer: '您可以通过在线客服、客服电话15623826666、客服邮箱或微信客服联系我们，我们7×24小时为您服务。'
      }
    ],
    account: [
      {
        question: '忘记密码怎么办？',
        answer: '在登录页面点击"忘记密码"，输入注册手机号或邮箱，按提示重置密码即可。'
      },
      {
        question: '如何修改个人信息？',
        answer: '登录会员中心，进入"个人资料"页面即可修改姓名、手机号、邮箱、收货地址等信息。'
      },
      {
        question: '积分如何获得和使用？',
        answer: '购物消费、完成任务、参与活动可获得积分。积分可用于抵扣现金、兑换商品或参与积分活动。'
      },
      {
        question: '会员等级有什么好处？',
        answer: '不同等级享受不同折扣、专属活动、优先客服等特权。会员等级根据消费金额和积分自动升级。'
      },
      {
        question: '如何注销账户？',
        answer: '如需注销账户，请联系客服处理。注销前请确保没有未完成的订单，余额和积分将按规定处理。'
      }
    ],
    others: [
      {
        question: '商品是正品吗？',
        answer: '我们承诺所有商品均为正品，与品牌方或授权经销商直接合作。假一赔十，让您放心购买。'
      },
      {
        question: '有实体店吗？',
        answer: '目前我们主要专注于线上服务，暂无实体店。但我们在武汉设有仓储中心和客服中心，确保优质服务。'
      },
      {
        question: '如何成为商家？',
        answer: '如果您是品牌商或经销商，想入驻我们平台，请发送邮件到2819291673@qq.com或致电商务合作热线。'
      },
      {
        question: '有优惠券吗？',
        answer: '我们定期推出各种优惠券活动，新用户注册即送优惠券。关注官方微信或下载APP可获得更多专属优惠。'
      },
      {
        question: '如何获取最新活动信息？',
        answer: '关注我们的官方微信"武汉精品商城"、官方微博或下载手机APP，第一时间获取促销活动和新品上架信息。'
      }
    ]
  };

  const toggleFAQ = (index) => {
    setExpandedFAQ(expandedFAQ === index ? null : index);
  };

  return (
    <div className="legal-container">
      <div className="legal-header">
        <div className="container">
          <h1>帮助中心</h1>
          <p className="update-date">为您提供全面的购物帮助和服务支持</p>
        </div>
      </div>
      
      <div className="legal-content">
        <div className="container">
          <div className="legal-nav">
            <Link to="/" className="back-link">← 返回首页</Link>
            <div className="nav-links">
              <Link to="/terms" className="nav-link">用户协议</Link>
              <Link to="/privacy" className="nav-link">隐私政策</Link>
              <Link to="/about" className="nav-link">关于我们</Link>
            </div>
          </div>
          
          <div className="help-container">
            <div className="help-sidebar">
              <h3>帮助分类</h3>
              <ul className="category-list">
                {Object.entries(categories).map(([key, name]) => (
                  <li key={key}>
                    <button
                      className={`category-btn ${activeCategory === key ? 'active' : ''}`}
                      onClick={() => setActiveCategory(key)}
                    >
                      {name}
                    </button>
                  </li>
                ))}
              </ul>
              
              <div className="contact-info">
                <h4>联系客服</h4>
                <p>📞 15623826666</p>
                <p>📧 2819291673@qq.com</p>
                <p>⏰ 7×24小时服务</p>
              </div>
            </div>
            
            <div className="help-content">
              <div className="terms-content">
                <section className="terms-section">
                  <h2>{categories[activeCategory]}</h2>
                  <div className="faq-list">
                    {faqData[activeCategory].map((faq, index) => (
                      <div key={index} className="faq-item">
                        <button
                          className={`faq-question ${expandedFAQ === index ? 'expanded' : ''}`}
                          onClick={() => toggleFAQ(index)}
                        >
                          <span>❓ {faq.question}</span>
                          <span className="faq-toggle">{expandedFAQ === index ? '−' : '+'}</span>
                        </button>
                        {expandedFAQ === index && (
                          <div className="faq-answer">
                            <p>{faq.answer}</p>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </section>

                {activeCategory === 'shopping' && (
                  <section className="terms-section">
                    <h2>购物流程</h2>
                    <div className="process-steps">
                      <div className="step">
                        <div className="step-number">1</div>
                        <div className="step-content">
                          <h4>注册登录</h4>
                          <p>使用手机号或邮箱快速注册，已有账户请直接登录</p>
                        </div>
                      </div>
                      <div className="step">
                        <div className="step-number">2</div>
                        <div className="step-content">
                          <h4>选择商品</h4>
                          <p>浏览商品分类或搜索找到心仪商品，查看详情和评价</p>
                        </div>
                      </div>
                      <div className="step">
                        <div className="step-number">3</div>
                        <div className="step-content">
                          <h4>加入购物车</h4>
                          <p>选择规格数量后加入购物车，可继续购物或直接结算</p>
                        </div>
                      </div>
                      <div className="step">
                        <div className="step-number">4</div>
                        <div className="step-content">
                          <h4>确认订单</h4>
                          <p>核对商品信息、收货地址，选择配送方式和支付方式</p>
                        </div>
                      </div>
                      <div className="step">
                        <div className="step-number">5</div>
                        <div className="step-content">
                          <h4>支付下单</h4>
                          <p>完成支付后订单生成，等待商家发货</p>
                        </div>
                      </div>
                      <div className="step">
                        <div className="step-number">6</div>
                        <div className="step-content">
                          <h4>收货评价</h4>
                          <p>收到商品后确认收货，可对商品和服务进行评价</p>
                        </div>
                      </div>
                    </div>
                  </section>
                )}

                <section className="terms-section">
                  <h2>常用功能</h2>
                  <div className="feature-grid">
                    <div className="feature-item">
                      <h4>🔍 商品搜索</h4>
                      <p>支持关键词搜索，筛选排序，快速找到想要的商品</p>
                    </div>
                    <div className="feature-item">
                      <h4>🛒 购物车</h4>
                      <p>临时保存商品，随时查看修改，支持批量结算</p>
                    </div>
                    <div className="feature-item">
                      <h4>❤️ 收藏夹</h4>
                      <p>收藏感兴趣的商品，方便下次购买</p>
                    </div>
                    <div className="feature-item">
                      <h4>📦 订单追踪</h4>
                      <p>实时查看订单状态，跟踪配送进度</p>
                    </div>
                    <div className="feature-item">
                      <h4>💰 钱包充值</h4>
                      <p>预充值享受更便捷的支付体验</p>
                    </div>
                    <div className="feature-item">
                      <h4>🎁 优惠券</h4>
                      <p>领取使用各种优惠券，享受更多优惠</p>
                    </div>
                  </div>
                </section>

                <section className="terms-section">
                  <h2>联系我们</h2>
                  <div className="contact-methods">
                    <div className="contact-method">
                      <h4>📞 客服热线</h4>
                      <p>15623826666</p>
                      <span>7×24小时人工服务</span>
                    </div>
                    <div className="contact-method">
                      <h4>💬 在线客服</h4>
                      <p>登录后使用售后聊天功能</p>
                      <span>即时响应，专业解答</span>
                    </div>
                    <div className="contact-method">
                      <h4>📧 邮件支持</h4>
                      <p>2819291673@qq.com</p>
                      <span>24小时内回复</span>
                    </div>
                    <div className="contact-method">
                      <h4>🏢 公司地址</h4>
                      <p>湖北省武汉市江夏区武汉工厂科技学院</p>
                      <span>欢迎实地考察</span>
                    </div>
                  </div>
                </section>

                <div className="terms-footer">
                  <p>还有其他问题？</p>
                  <p><strong>欢迎随时联系我们的客服团队，我们将竭诚为您服务！</strong></p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Help; 