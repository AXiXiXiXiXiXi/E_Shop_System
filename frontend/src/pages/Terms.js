import React from 'react';
import { Link } from 'react-router-dom';
import '../styles/legal.css';

function Terms() {
  return (
    <div className="legal-container">
      <div className="legal-header">
        <div className="container">
          <h1>武汉精品商城用户协议</h1>
          <p className="update-date">最后更新时间：2026年1月1日</p>
        </div>
      </div>
      
      <div className="legal-content">
        <div className="container">
          <div className="legal-nav">
            <Link to="/" className="back-link">← 返回首页</Link>
            <div className="nav-links">
            <Link to="/privacy" className="nav-link">隐私政策</Link>
              <Link to="/about" className="nav-link">关于我们</Link>
              <Link to="/help" className="nav-link">帮助中心</Link>
            </div>
          </div>
          
          <div className="terms-content">
            <section className="terms-section">
              <h2>1. 协议的接受</h2>
              <p>欢迎使用武汉精品商城（以下简称"本商城"）。本用户协议（以下简称"本协议"）是您与武汉精品商城之间关于使用本商城服务的法律协议。</p>
              <p>通过注册账户、访问或使用本商城的服务，您表示同意接受本协议的所有条款和条件。如果您不同意本协议的任何条款，请不要使用本商城的服务。</p>
            </section>

            <section className="terms-section">
              <h2>2. 服务描述</h2>
              <p>武汉精品商城是一个综合性电子商务平台，为用户提供以下服务：</p>
              <ul>
                <li>优质商品的在线浏览、搜索和购买服务</li>
                <li>安全便捷的支付和配送服务</li>
                <li>完善的售后服务和客户支持</li>
                <li>会员积分和优惠活动服务</li>
                <li>商品评价和社区交流功能</li>
              </ul>
            </section>

            <section className="terms-section">
              <h2>3. 用户注册与账户</h2>
              <h3>3.1 注册要求</h3>
              <ul>
                <li>用户必须年满18周岁，具有完全民事行为能力</li>
                <li>提供真实、准确、完整的个人信息</li>
                <li>确保注册信息的及时更新</li>
                <li>遵守相关法律法规和本协议条款</li>
              </ul>
              
              <h3>3.2 账户安全</h3>
              <ul>
                <li>用户有义务保护账户密码的安全性</li>
                <li>不得将账户转让、出借或授权他人使用</li>
                <li>发现账户异常应立即通知本商城</li>
                <li>用户对账户下的所有活动承担责任</li>
              </ul>
            </section>

            <section className="terms-section">
              <h2>4. 购物与交易</h2>
              <h3>4.1 商品信息</h3>
              <ul>
                <li>本商城努力确保商品信息的准确性，但不对信息错误承担责任</li>
                <li>商品价格可能随时调整，以下单时的价格为准</li>
                <li>商品库存信息仅供参考，实际库存以系统确认为准</li>
              </ul>
              
              <h3>4.2 订单处理</h3>
              <ul>
                <li>订单提交后，用户不可随意取消或修改</li>
                <li>本商城有权因库存不足等原因取消订单</li>
                <li>支付成功后，订单即告成立</li>
                <li>配送时间以实际发货时间为准</li>
              </ul>
            </section>

            <section className="terms-section">
              <h2>5. 支付与配送</h2>
              <h3>5.1 支付方式</h3>
              <ul>
                <li>支持多种安全的在线支付方式</li>
                <li>钱包余额、银行卡、第三方支付等</li>
                <li>支付过程受到银行级别的安全保护</li>
              </ul>
              
              <h3>5.2 配送服务</h3>
              <ul>
                <li>提供武汉市内快速配送服务</li>
                <li>支持全国范围的快递配送</li>
                <li>配送费用根据商品重量和距离计算</li>
                <li>部分商品支持免费配送</li>
              </ul>
            </section>

            <section className="terms-section">
              <h2>6. 退换货政策</h2>
              <h3>6.1 退货条件</h3>
              <ul>
                <li>商品质量问题：7天内无理由退货</li>
                <li>商品必须保持原包装和完好状态</li>
                <li>个人定制商品不支持退货</li>
                <li>易腐、易损商品按特殊规定处理</li>
              </ul>
              
              <h3>6.2 退款处理</h3>
              <ul>
                <li>退款将原路返回至用户付款账户</li>
                <li>处理时间为3-7个工作日</li>
                <li>运费承担按具体情况确定</li>
              </ul>
            </section>

            <section className="terms-section">
              <h2>7. 会员权益</h2>
              <h3>7.1 积分系统</h3>
              <ul>
                <li>购物消费可获得相应积分奖励</li>
                <li>积分可用于抵扣现金或兑换商品</li>
                <li>积分有效期为获得之日起12个月</li>
              </ul>
              
              <h3>7.2 会员等级</h3>
              <ul>
                <li>根据消费金额和积分划分会员等级</li>
                <li>不同等级享受不同的优惠和特权</li>
                <li>会员等级每月更新一次</li>
              </ul>
            </section>

            <section className="terms-section">
              <h2>8. 用户行为规范</h2>
              <p>用户在使用本商城服务时，不得从事以下行为：</p>
              <ul>
                <li>发布虚假信息或恶意评价</li>
                <li>恶意退换货或欺诈行为</li>
                <li>侵犯他人知识产权或隐私权</li>
                <li>传播违法、有害信息</li>
                <li>破坏商城系统安全</li>
                <li>批量注册账户或使用外挂软件</li>
                <li>其他违反法律法规的行为</li>
              </ul>
            </section>

            <section className="terms-section">
              <h2>9. 知识产权</h2>
              <ul>
                <li>本商城的商标、Logo、网站设计等知识产权归本商城所有</li>
                <li>用户不得擅自使用本商城的知识产权</li>
                <li>商品图片、描述等内容受著作权保护</li>
                <li>用户上传的内容应确保不侵犯他人权益</li>
              </ul>
            </section>

            <section className="terms-section">
              <h2>10. 免责声明</h2>
              <ul>
                <li>本商城对因不可抗力造成的损失不承担责任</li>
                <li>对于第三方支付、物流等服务商的行为不承担责任</li>
                <li>用户因违反本协议造成的损失由用户自行承担</li>
                <li>在法律允许范围内，本商城的责任以用户实际损失为限</li>
              </ul>
            </section>

            <section className="terms-section">
              <h2>11. 协议修改</h2>
              <p>本商城有权根据法律法规变化和业务发展需要修改本协议。修改后的协议将在网站上公布，并自公布之日起生效。</p>
              <p>用户继续使用本商城服务视为接受修改后的协议。如不同意修改内容，用户可以停止使用相关服务。</p>
            </section>

            <section className="terms-section">
              <h2>12. 争议解决</h2>
              <ul>
                <li>本协议适用中华人民共和国法律</li>
                <li>因本协议产生的争议，双方应友好协商解决</li>
                <li>协商不成的，提交武汉市有管辖权的人民法院处理</li>
              </ul>
            </section>

            <section className="terms-section">
              <h2>13. 联系方式</h2>
              <p>如对本协议有任何疑问，请通过以下方式联系我们：</p>
              <ul>
                <li>客服电话：15623826666</li>
                <li>客服邮箱：2819291673@qq.com</li>
                <li>在线客服：登录后使用售后聊天功能</li>
                <li>公司地址：湖北省武汉市江夏区武汉工厂科技学院</li>
              </ul>
            </section>

            <div className="terms-footer">
              <p>本协议自2026年1月1日起生效。</p>
              <p><strong>武汉精品商城保留本协议的最终解释权。</strong></p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Terms; 