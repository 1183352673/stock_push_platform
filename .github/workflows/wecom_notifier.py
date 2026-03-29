"""
企业微信推送模块 - 将报告推送到企业微信
"""

import requests
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

from config import Config, MessageTemplates

logger = logging.getLogger(__name__)

class WeComNotifier:
    """企业微信通知器"""
    
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url or Config.WECOM_WEBHOOK
        if not self.webhook_url:
            logger.warning("未设置企业微信Webhook URL，推送功能将不可用")
    
    def send_daily_report(self, report_data: Dict[str, Any]) -> bool:
        """发送日报摘要到企业微信"""
        if not self.webhook_url:
            logger.error("无法发送日报：未配置Webhook URL")
            return False
        
        try:
            # 生成消息内容
            message = self._format_daily_message(report_data)
            
            # 发送消息
            success = self._send_wecom_message(message)
            
            if success:
                logger.info("日报推送成功")
            else:
                logger.error("日报推送失败")
            
            return success
            
        except Exception as e:
            logger.error(f"发送日报失败: {e}")
            return False
    
    def send_weekly_report(self, report_data: Dict[str, Any]) -> bool:
        """发送周报摘要到企业微信"""
        if not self.webhook_url:
            logger.error("无法发送周报：未配置Webhook URL")
            return False
        
        try:
            # 生成消息内容
            message = self._format_weekly_message(report_data)
            
            # 发送消息
            success = self._send_wecom_message(message)
            
            if success:
                logger.info("周报推送成功")
            else:
                logger.error("周报推送失败")
            
            return success
            
        except Exception as e:
            logger.error(f"发送周报失败: {e}")
            return False
    
    def send_custom_message(self, title: str, content: str, report_url: str = None) -> bool:
        """发送自定义消息"""
        if not self.webhook_url:
            logger.error("无法发送消息：未配置Webhook URL")
            return False
        
        try:
            message = {
                "msgtype": "markdown",
                "markdown": {
                    "content": f"**{title}**\n\n{content}\n\n"
                }
            }
            
            if report_url:
                message["markdown"]["content"] += f"详细报告: {report_url}"
            
            success = self._send_wecom_message(message)
            
            if success:
                logger.info(f"自定义消息推送成功: {title}")
            else:
                logger.error(f"自定义消息推送失败: {title}")
            
            return success
            
        except Exception as e:
            logger.error(f"发送自定义消息失败: {e}")
            return False
    
    def _format_daily_message(self, report_data: Dict[str, Any]) -> Dict:
        """格式化日报消息"""
        report_date = report_data.get('report_date', Config.CURRENT_DATE)
        top_industries = report_data.get('top_industries', [])
        stock_recommendations = report_data.get('stock_recommendations', [])
        risk_warnings = report_data.get('risk_warnings', [])
        summary = report_data.get('summary', '')
        
        # 生成行业摘要
        industry_summary = ""
        for i, industry in enumerate(top_industries[:3], 1):  # 只显示前3个
            industry_summary += MessageTemplates.INDUSTRY_SUMMARY_ITEM.format(
                rank=i,
                industry_name=industry['industry_name'],
                score=industry['total_score'],
                reason=industry['recommendation_reason']
            ) + "\n"
        
        # 生成个股摘要
        stock_summary = ""
        for i, stock in enumerate(stock_recommendations[:5], 1):  # 只显示前5个
            stock_summary += MessageTemplates.STOCK_SUMMARY_ITEM.format(
                stock_name=stock['stock_name'],
                stock_code=stock['stock_code'],
                score=stock['total_score'],
                advice=stock['trading_advice']['action']
            ) + "\n"
        
        # 生成风险提示
        risk_text = "\n".join([f"• {warning}" for warning in risk_warnings[:3]])  # 只显示前3个
        
        # 报告URL
        report_url = f"{Config.GITHUB_PAGES_URL}/reports/daily_report_{report_date}.md"
        
        # 构建完整消息
        message_content = MessageTemplates.DAILY_MESSAGE.format(
            date=report_date,
            count=min(3, len(top_industries)),
            industry_summary=industry_summary,
            stock_summary=stock_summary,
            risk_warnings=risk_text,
            report_url=report_url
        )
        
        return {
            "msgtype": "markdown",
            "markdown": {
                "content": message_content
            }
        }
    
    def _format_weekly_message(self, report_data: Dict[str, Any]) -> Dict:
        """格式化周报消息"""
        report_date = report_data.get('report_date', Config.CURRENT_DATE)
        week_start = report_data.get('week_start', '')
        market_summary = report_data.get('market_summary', {})
        industry_performance = report_data.get('industry_performance', [])
        weekly_insights = report_data.get('weekly_insights', [])
        next_week_outlook = report_data.get('next_week_outlook', '')
        
        # 标题
        title = MessageTemplates.WEEKLY_TITLE.format(date=report_date)
        if week_start:
            title += f" ({week_start} - {report_date})"
        
        # 市场总结
        market_text = market_summary.get('comment', '')
        if not market_text:
            market_text = "本周市场数据总结"
        
        # 行业表现
        industry_text = ""
        for i, industry in enumerate(industry_performance[:3], 1):
            industry_text += f"{i}. **{industry['industry_name']}** - 评分: {industry['total_score']:.2f}\n"
        
        # 本周洞察
        insights_text = ""
        if weekly_insights:
            insights_text = "\n".join([f"• {insight}" for insight in weekly_insights])
        
        # 构建消息
        content = f"""**{title}**

**📈 市场总结**
{market_text}

**🏆 行业表现 Top 3**
{industry_text}

**💡 本周洞察**
{insights_text}

**🔮 下周展望**
{next_week_outlook}

**⚠️ 风险提示**
• 股市有风险，投资需谨慎
• 本报告仅供参考，不构成投资建议
• 过往表现不代表未来收益

详细周报请查看: {Config.GITHUB_PAGES_URL}/reports/weekly_report_{report_date}.md
"""
        
        return {
            "msgtype": "markdown",
            "markdown": {
                "content": content
            }
        }
    
    def _send_wecom_message(self, message: Dict) -> bool:
        """发送消息到企业微信"""
        if not self.webhook_url:
            logger.error("Webhook URL未设置")
            return False
        
        try:
            headers = {'Content-Type': 'application/json'}
            response = requests.post(
                self.webhook_url,
                data=json.dumps(message, ensure_ascii=False).encode('utf-8'),
                headers=headers,
                timeout=10
            )
            
            result = response.json()
            
            if response.status_code == 200 and result.get('errcode') == 0:
                logger.debug(f"消息发送成功: {result}")
                return True
            else:
                logger.error(f"消息发送失败: {result}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("发送消息超时")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"网络请求失败: {e}")
            return False
        except Exception as e:
            logger.error(f"发送消息异常: {e}")
            return False
    
    def test_connection(self) -> bool:
        """测试企业微信连接"""
        if not self.webhook_url:
            logger.error("未配置Webhook URL")
            return False
        
        try:
            test_message = {
                "msgtype": "markdown",
                "markdown": {
                    "content": "**连接测试**\n\n股票信息推送平台测试消息\n\n时间: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            }
            
            success = self._send_wecom_message(test_message)
            
            if success:
                logger.info("企业微信连接测试成功")
            else:
                logger.error("企业微信连接测试失败")
            
            return success
            
        except Exception as e:
            logger.error(f"连接测试失败: {e}")
            return False


if __name__ == "__main__":
    # 测试代码
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # 从环境变量获取Webhook URL
    webhook_url = os.getenv("WECOM_WEBHOOK", "")
    
    if not webhook_url:
        print("请设置环境变量 WECOM_WEBHOOK")
        print("示例: export WECOM_WEBHOOK='https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY'")
        exit(1)
    
    notifier = WeComNotifier(webhook_url)
    
    # 测试连接
    print("测试企业微信连接...")
    if notifier.test_connection():
        print("连接测试成功!")
        
        # 测试发送示例消息
        print("\n发送测试消息...")
        success = notifier.send_custom_message(
            title="测试消息",
            content="这是股票信息推送平台的测试消息。",
            report_url="https://example.com"
        )
        
        if success:
            print("测试消息发送成功!")
        else:
            print("测试消息发送失败!")
    else:
        print("连接测试失败，请检查Webhook URL是否正确")