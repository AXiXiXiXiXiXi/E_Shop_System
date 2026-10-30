import React from 'react';
import { Link } from 'react-router-dom';
import '../styles/legal.css';

function Privacy() {
  return (
    <div className="legal-container">
      <div className="legal-header">
        <div className="container">
          <h1>武汉精品商城隐私政策</h1>
          <p className="update-date">最后更新时间：2026年1月1日</p>
        </div>
      </div>
      
      <div className="legal-content">
        <div className="container">
          <div className="legal-nav">
            <Link to="/" className="back-link">← 返回首页</Link>
            <div className="nav-links">
            <Link to="/terms" className="nav-link">用户协议</Link>
              <Link to="/about" className="nav-link">关于我们</Link>
              <Link to="/help" className="nav-link">帮助中心</Link>
            </div>
          </div>
          
          <div className="privacy-content">
            <section className="privacy-section">
              <h2>引言</h2>
              <p>武汉精品商城（以下简称"我们"、"本商城"）深知个人信息对您的重要性，我们将按照法律法规要求，采用相应的安全保护措施，保护您的个人信息安全可控。</p>
              <p>本隐私政策将帮助您了解：我们收集哪些信息、为什么收集这些信息、我们如何使用收集的信息，以及如何访问和更新这些信息。</p>
              <p><strong>请您仔细阅读本隐私政策，确保充分理解和同意后再使用我们的服务。</strong></p>
            </section>

            <section className="privacy-section">
              <h2>1. 我们收集的信息</h2>
              <h3>1.1 您主动提供的信息</h3>
              <ul>
                <li><strong>注册信息：</strong>用户名、邮箱地址、手机号码、密码</li>
                <li><strong>个人资料：</strong>姓名、性别、生日、收货地址</li>
                <li><strong>支付信息：</strong>银行卡信息、支付密码（经过加密处理）</li>
                <li><strong>联系信息：</strong>客服沟通记录、售后申请信息</li>
                <li><strong>用户生成内容：</strong>商品评价、反馈意见、上传的图片</li>
              </ul>

              <h3>1.2 我们自动收集的信息</h3>
              <ul>
                <li><strong>设备信息：</strong>设备型号、操作系统、浏览器类型</li>
                <li><strong>网络信息：</strong>IP地址、网络类型、运营商信息</li>
                <li><strong>使用信息：</strong>访问时间、浏览页面、搜索记录、购买历史</li>
                <li><strong>位置信息：</strong>基于IP的大概位置（用于配送服务）</li>
                <li><strong>Cookies信息：</strong>登录状态、购物车内容、个性化推荐</li>
              </ul>

              <h3>1.3 第三方提供的信息</h3>
              <ul>
                <li><strong>支付机构：</strong>支付结果、交易状态信息</li>
                <li><strong>物流公司：</strong>配送状态、签收信息</li>
                <li><strong>授权登录：</strong>第三方平台的公开信息（如微信、QQ）</li>
              </ul>
            </section>

            <section className="privacy-section">
              <h2>2. 我们如何使用您的信息</h2>
              <h3>2.1 基础服务功能</h3>
              <ul>
                <li>创建和管理您的账户</li>
                <li>处理您的订单和支付</li>
                <li>安排商品配送和售后服务</li>
                <li>验证您的身份和账户安全</li>
                <li>提供客户服务和技术支持</li>
              </ul>

              <h3>2.2 增值服务功能</h3>
              <ul>
                <li>为您推荐感兴趣的商品和活动</li>
                <li>发送优惠信息和促销活动通知</li>
                <li>分析用户行为以改进我们的服务</li>
                <li>开展市场调研和用户满意度调查</li>
                <li>预防欺诈和保护平台安全</li>
              </ul>

              <h3>2.3 法律合规要求</h3>
              <ul>
                <li>遵守法律法规的强制性要求</li>
                <li>配合政府部门的合法调查</li>
                <li>维护社会公共利益</li>
                <li>保护用户和他人的合法权益</li>
              </ul>
            </section>

            <section className="privacy-section">
              <h2>3. 信息共享、转让和公开披露</h2>
              <h3>3.1 信息共享</h3>
              <p>我们不会向第三方出售、出租或交换您的个人信息。但在以下情况下，我们可能会共享您的信息：</p>
              <ul>
                <li><strong>获得您的明确同意：</strong>在获得您的明确同意后分享您指定的信息</li>
                <li><strong>业务合作伙伴：</strong>与支付机构、物流公司等合作伙伴共享必要信息</li>
                <li><strong>关联公司：</strong>与我们的关联公司共享信息以提供一致的服务</li>
                <li><strong>法律要求：</strong>根据法律法规、法律程序或政府要求</li>
              </ul>

              <h3>3.2 信息转让</h3>
              <p>除非获得您的明确同意，我们不会将您的个人信息转让给任何公司、组织或个人。但在以下情况下可能发生转让：</p>
              <ul>
                <li>涉及合并、收购或破产清算时</li>
                <li>其他涉及合并、收购或资产转让的情况</li>
              </ul>

              <h3>3.3 公开披露</h3>
              <p>我们仅会在以下情况下公开披露您的个人信息：</p>
              <ul>
                <li>获得您的明确同意后</li>
                <li>基于法律规定：在法律、法律程序、诉讼或政府主管部门强制性要求下</li>
              </ul>
            </section>

            <section className="privacy-section">
              <h2>4. 我们如何保护您的信息</h2>
              <h3>4.1 技术保护措施</h3>
              <ul>
                <li><strong>数据加密：</strong>采用HTTPS协议和SSL加密技术保护数据传输</li>
                <li><strong>数据存储：</strong>使用加密存储技术保护静态数据安全</li>
                <li><strong>访问控制：</strong>严格限制有权访问个人信息的人员</li>
                <li><strong>安全审计：</strong>定期进行安全检查和漏洞修复</li>
                <li><strong>防火墙：</strong>部署多层防火墙保护系统安全</li>
              </ul>

              <h3>4.2 管理保护措施</h3>
              <ul>
                <li>建立专门的信息安全团队</li>
                <li>制定严格的数据访问权限管理制度</li>
                <li>对员工进行定期的隐私保护培训</li>
                <li>签署保密协议和隐私保护承诺</li>
                <li>建立数据安全事件应急响应机制</li>
              </ul>

              <h3>4.3 数据保留期限</h3>
              <ul>
                <li>账户信息：账户注销后6个月内删除</li>
                <li>交易记录：保留7年（符合会计法要求）</li>
                <li>日志信息：保留12个月后自动删除</li>
                <li>客服记录：保留2年后删除</li>
              </ul>
            </section>

            <section className="privacy-section">
              <h2>5. 您的权利</h2>
              <h3>5.1 访问权</h3>
              <p>您有权访问您的个人信息，了解我们处理您个人信息的情况。您可以通过以下方式访问：</p>
              <ul>
                <li>登录账户查看个人资料</li>
                <li>在会员中心查看订单和交易记录</li>
                <li>联系客服获取其他个人信息</li>
              </ul>

              <h3>5.2 更正权</h3>
              <p>如发现我们处理的您的个人信息有错误，您有权要求我们更正。您可以：</p>
              <ul>
                <li>在个人中心直接修改个人资料</li>
                <li>联系客服协助修改</li>
                <li>通过邮件申请更正</li>
              </ul>

              <h3>5.3 删除权</h3>
              <p>在以下情况下，您可以要求我们删除个人信息：</p>
              <ul>
                <li>处理目的已实现、无法实现或为实现处理目的不再必要</li>
                <li>我们停止提供产品或服务，或保存期限已届满</li>
                <li>您撤回同意</li>
                <li>我们违法处理您的个人信息</li>
              </ul>

              <h3>5.4 撤回同意权</h3>
              <p>您可以通过以下方式撤回您的同意：</p>
              <ul>
                <li>关闭设备功能：关闭位置、摄像头、通讯录等权限</li>
                <li>软件设置：在隐私设置中关闭相应功能</li>
                <li>注销账户：彻底停止我们收集您的个人信息</li>
              </ul>
            </section>

            <section className="privacy-section">
              <h2>6. 未成年人信息保护</h2>
              <ul>
                <li>我们非常重视未成年人个人信息的保护</li>
                <li>如您为未成年人，建议请您的监护人仔细阅读本隐私政策</li>
                <li>我们只会在监护人同意、法律法规授权或保护未成年人所必需的情况下收集未成年人信息</li>
                <li>如发现在未获得监护人同意的情况下收集了未成年人信息，我们会尽快删除</li>
                <li>如您是未成年人的监护人，当您对您所监护的未成年人信息有疑问时，请联系我们</li>
              </ul>
            </section>

            <section className="privacy-section">
              <h2>7. Cookie和类似技术</h2>
              <h3>7.1 Cookie的使用</h3>
              <p>为了提供更好的服务体验，我们可能会使用Cookie和类似技术来收集和使用您的信息：</p>
              <ul>
                <li><strong>会话Cookie：</strong>保持您的登录状态</li>
                <li><strong>偏好Cookie：</strong>记住您的设置和偏好</li>
                <li><strong>安全Cookie：</strong>识别异常登录和保护账户安全</li>
                <li><strong>分析Cookie：</strong>了解您如何使用我们的服务</li>
              </ul>

              <h3>7.2 您的选择</h3>
              <p>您可以通过浏览器设置来控制Cookie：</p>
              <ul>
                <li>删除计算机上保存的所有Cookie</li>
                <li>阻止或允许所有Cookie</li>
                <li>每次Cookie保存时收到通知</li>
              </ul>
              <p>注意：如果禁用Cookie，您可能无法使用依赖于Cookie的服务功能。</p>
            </section>

            <section className="privacy-section">
              <h2>8. 本政策的更新</h2>
              <ul>
                <li>我们可能会适时修订本隐私政策</li>
                <li>重大变更时，我们会在网站显著位置发布通知</li>
                <li>继续使用我们的服务表示您同意更新后的隐私政策</li>
                <li>如不同意更新内容，您可以停止使用我们的服务</li>
                <li>我们建议您定期查看本隐私政策以了解最新信息</li>
              </ul>
            </section>

            <section className="privacy-section">
              <h2>9. 如何联系我们</h2>
              <p>如果您对本隐私政策有任何疑问、意见或建议，或需要行使相关权利，请通过以下方式联系我们：</p>
              <ul>
                <li><strong>客服电话：</strong>15623826666（工作时间：9:00-18:00）</li>
                <li><strong>客服邮箱：</strong>2819291673@qq.com</li>
                <li><strong>在线客服：</strong>登录后使用售后聊天功能</li>
                <li><strong>邮寄地址：</strong>湖北省武汉市江夏区武汉工厂科技学院 隐私保护部收</li>
                <li><strong>微信客服：</strong>关注"武汉精品商城"公众号</li>
              </ul>
              <p>我们将在收到您的请求后，在合理期限内给予回复。</p>
            </section>

            <div className="privacy-footer">
              <p>本隐私政策自2026年1月1日起生效。</p>
              <p><strong>感谢您对武汉精品商城的信任！我们将持续努力保护您的个人信息安全。</strong></p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Privacy; 