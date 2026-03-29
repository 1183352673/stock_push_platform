"""
报告生成模块 - 生成日报/周报
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import json
import os
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import seaborn as sns
from jinja2 import Template
import markdown

from config import Config, create_directories
from data_collector import DataCollector
from industry_analyzer import IndustryAnalyzer
from stock_recommender import StockRecommender

logger = logging.getLogger(__name__)

class ReportGenerator:
    """报告生成器"""
    
    def __init__(self):
        self.collector = DataCollector()
        self.industry_analyzer = IndustryAnalyzer()
        self.stock_recommender = StockRecommender()
        self.today = Config.CURRENT_DATE
        
        # 创建目录
        create_directories()
        
        # 设置matplotlib中文字体（如果需要）
        try:
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
        except:
            pass
    
    def generate_daily_report(self) -> Dict[str, Any]:
        """生成日报"""
        logger.info("开始生成日报...")
        
        report_data = {
            'report_date': self.today,
            'report_type': 'daily',
            'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'market_overview': {},
            'top_industries': [],
            'stock_recommendations': [],
            'risk_warnings': [],
            'summary': ''
        }
        
        try:
            # 1. 获取市场概览
            report_data['market_overview'] = self.collector.get_market_overview()
            
            # 2. 分析潜力行业（Top 5）
            top_industries = self.industry_analyzer.analyze_all_industries(
                top_n=Config.INDUSTRY_COUNT
            )
            report_data['top_industries'] = top_industries
            
            # 3. 为每个潜力行业推荐股票
            all_stock_recommendations = []
            for industry in top_industries:
                industry_code = industry['industry_code']
                industry_name = industry['industry_name']
                
                stocks = self.stock_recommender.recommend_stocks_for_industry(
                    industry_code, industry_name, top_n=Config.STOCKS_PER_INDUSTRY
                )
                
                for stock in stocks:
                    stock['industry_name'] = industry_name
                    stock['industry_score'] = industry['total_score']
                    all_stock_recommendations.append(stock)
            
            # 按总分排序
            all_stock_recommendations.sort(key=lambda x: x['total_score'], reverse=True)
            report_data['stock_recommendations'] = all_stock_recommendations[:15]  # 取前15只
            
            # 4. 生成风险提示
            report_data['risk_warnings'] = self._generate_risk_warnings(
                report_data['market_overview'], top_industries
            )
            
            # 5. 生成摘要
            report_data['summary'] = self._generate_summary(
                report_data['market_overview'], top_industries, all_stock_recommendations
            )
            
            # 6. 生成图表
            self._generate_charts(top_industries, all_stock_recommendations)
            
            # 7. 保存报告数据
            self._save_report_data(report_data, 'daily')
            
            # 8. 生成Markdown报告
            markdown_report = self._generate_markdown_report(report_data, 'daily')
            
            logger.info("日报生成完成")
            return report_data
            
        except Exception as e:
            logger.error(f"生成日报失败: {e}")
            raise
    
    def generate_weekly_report(self) -> Dict[str, Any]:
        """生成周报"""
        logger.info("开始生成周报...")
        
        # 获取本周日期范围
        today = datetime.now()
        start_of_week = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
        
        report_data = {
            'report_date': self.today,
            'week_start': start_of_week,
            'report_type': 'weekly',
            'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'market_summary': {},
            'industry_performance': [],
            'weekly_winners': [],
            'weekly_losers': [],
            'weekly_insights': [],
            'next_week_outlook': ''
        }
        
        try:
            # 1. 市场总结（需要历史数据，这里简化）
            report_data['market_summary'] = self._generate_market_summary()
            
            # 2. 行业表现排名
            industries = self.industry_analyzer.analyze_all_industries(top_n=10)
            report_data['industry_performance'] = industries
            
            # 3. 本周涨跌幅榜（需要历史数据，这里简化）
            report_data['weekly_winners'] = self._get_weekly_performers('winners')
            report_data['weekly_losers'] = self._get_weekly_performers('losers')
            
            # 4. 本周洞察
            report_data['weekly_insights'] = self._generate_weekly_insights(industries)
            
            # 5. 下周展望
            report_data['next_week_outlook'] = self._generate_next_week_outlook(industries)
            
            # 6. 保存报告数据
            self._save_report_data(report_data, 'weekly')
            
            # 7. 生成Markdown报告
            markdown_report = self._generate_markdown_report(report_data, 'weekly')
            
            logger.info("周报生成完成")
            return report_data
            
        except Exception as e:
            logger.error(f"生成周报失败: {e}")
            raise
    
    def _generate_market_summary(self) -> Dict:
        """生成市场总结（简化版）"""
        overview = self.collector.get_market_overview()
        
        summary = {
            'overview': overview,
            'comment': '',
            'key_events': []
        }
        
        # 简单判断市场状态
        if overview:
            # 检查主要指数涨跌
            up_count = 0
            total_count = 0
            
            for index_name, index_data in overview.items():
                if isinstance(index_data, dict) and 'pct_change' in index_data:
                    total_count += 1
                    if index_data['pct_change'] > 0:
                        up_count += 1
            
            if total_count > 0:
                up_ratio = up_count / total_count
                if up_ratio >= 0.7:
                    summary['comment'] = '市场整体强势，多数指数上涨'
                elif up_ratio >= 0.4:
                    summary['comment'] = '市场震荡分化，涨跌互现'
                else:
                    summary['comment'] = '市场整体偏弱，多数指数下跌'
        
        return summary
    
    def _get_weekly_performers(self, performer_type: str) -> List[Dict]:
        """获取周度表现最佳/最差股票（简化版）"""
        # 这里需要实际的历史数据，暂时返回示例数据
        if performer_type == 'winners':
            return [
                {'code': '示例1', 'name': '涨幅股1', 'change': 15.2, 'industry': '电子'},
                {'code': '示例2', 'name': '涨幅股2', 'change': 12.8, 'industry': '医药'},
                {'code': '示例3', 'name': '涨幅股3', 'change': 10.5, 'industry': '新能源'}
            ]
        else:
            return [
                {'code': '示例4', 'name': '跌幅股1', 'change': -8.3, 'industry': '房地产'},
                {'code': '示例5', 'name': '跌幅股2', 'change': -6.7, 'industry': '金融'},
                {'code': '示例6', 'name': '跌幅股3', 'change': -5.2, 'industry': '传统制造'}
            ]
    
    def _generate_weekly_insights(self, industries: List[Dict]) -> List[str]:
        """生成本周洞察"""
        insights = []
        
        if not industries:
            return insights
        
        # 分析行业轮动
        top_industry = industries[0] if industries else None
        if top_industry and top_industry['total_score'] > 0.7:
            insights.append(f"本周{top_industry['industry_name']}行业表现强势，资金关注度高")
        
        # 检查市场情绪
        avg_news_score = np.mean([ind.get('news_heat_score', 0.5) for ind in industries])
        if avg_news_score > 0.6:
            insights.append("市场情绪整体偏暖，新闻关注度提升")
        elif avg_news_score < 0.4:
            insights.append("市场情绪偏冷，新闻关注度下降")
        
        # 检查资金流向
        avg_capital_score = np.mean([ind.get('capital_flow_score', 0.5) for ind in industries])
        if avg_capital_score > 0.6:
            insights.append("整体资金呈流入态势，市场流动性改善")
        
        return insights
    
    def _generate_next_week_outlook(self, industries: List[Dict]) -> str:
        """生成下周展望"""
        if not industries:
            return "数据不足，无法提供下周展望"
        
        # 分析趋势
        up_trend_count = sum(1 for ind in industries 
                           if ind.get('trend_analysis', {}).get('direction') == 'up')
        total_count = len(industries)
        
        if up_trend_count / total_count >= 0.6:
            outlook = "下周市场有望延续强势，建议关注资金流入明显的行业"
        elif up_trend_count / total_count >= 0.4:
            outlook = "下周市场可能维持震荡，建议精选个股，注意仓位控制"
        else:
            outlook = "下周市场可能面临调整压力，建议谨慎操作，控制风险"
        
        # 推荐关注行业
        top_industries = [ind['industry_name'] for ind in industries[:3]]
        if top_industries:
            outlook += f"。可重点关注：{''.join(top_industries)}等行业"
        
        return outlook
    
    def _generate_risk_warnings(self, market_overview: Dict, industries: List[Dict]) -> List[str]:
        """生成风险提示"""
        warnings = []
        
        # 基础风险提示
        warnings.append("股市有风险，投资需谨慎。本报告仅供参考，不构成投资建议。")
        warnings.append("过往表现不代表未来收益，投资者应独立判断并承担风险。")
        
        # 市场风险
        if market_overview:
            # 检查市场波动
            indices = ['上证指数', '深证成指', '创业板指']
            volatile_count = 0
            
            for index in indices:
                if index in market_overview:
                    change = abs(market_overview[index].get('pct_change', 0))
                    if change > 2:  # 涨跌幅超过2%
                        volatile_count += 1
            
            if volatile_count >= 2:
                warnings.append("主要指数波动较大，请注意市场波动风险。")
        
        # 行业集中风险
        if industries:
            top_score = industries[0]['total_score'] if industries else 0
            if top_score > 0.8:
                warnings.append("部分行业评分过高，可能存在过热风险，建议谨慎追高。")
        
        # 数据风险
        warnings.append("本报告基于公开数据生成，数据可能存在延迟或不准确的情况。")
        
        return warnings
    
    def _generate_summary(self, market_overview: Dict, industries: List[Dict], 
                         stocks: List[Dict]) -> str:
        """生成报告摘要"""
        summary_parts = []
        
        # 市场状态
        if market_overview:
            sh_change = market_overview.get('上证指数', {}).get('pct_change', 0)
            if sh_change > 0:
                summary_parts.append(f"上证指数上涨{sh_change:.1f}%")
            elif sh_change < 0:
                summary_parts.append(f"上证指数下跌{abs(sh_change):.1f}%")
            else:
                summary_parts.append("上证指数持平")
        
        # 行业表现
        if industries:
            top_industry = industries[0]['industry_name'] if industries else ""
            if top_industry:
                summary_parts.append(f"{top_industry}行业表现最佳")
        
        # 股票推荐
        if stocks:
            top_stock = stocks[0]['stock_name'] if stocks else ""
            if top_stock:
                summary_parts.append(f"{top_stock}综合评分最高")
        
        if summary_parts:
            return "；".join(summary_parts) + "。"
        else:
            return "今日市场数据更新完成。"
    
    def _generate_charts(self, industries: List[Dict], stocks: List[Dict]):
        """生成图表"""
        try:
            # 1. 行业评分雷达图
            if len(industries) >= 3:
                self._create_industry_radar_chart(industries[:3])
            
            # 2. 股票评分分布图
            if stocks:
                self._create_stock_score_distribution(stocks)
            
            # 3. 行业趋势图
            if industries:
                self._create_industry_trend_chart(industries[:5])
                
        except Exception as e:
            logger.error(f"生成图表失败: {e}")
    
    def _create_industry_radar_chart(self, industries: List[Dict]):
        """创建行业评分雷达图"""
        try:
            if len(industries) < 2:
                return
            
            # 提取数据
            categories = ['资金', '价格', '新闻']
            angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
            
            fig, ax = plt.subplots(figsize=(8, 6), subplot_kw=dict(projection='polar'))
            
            colors = ['b', 'r', 'g']
            for idx, industry in enumerate(industries[:3]):
                values = [
                    industry['capital_flow_score'],
                    industry['price_momentum_score'],
                    industry['news_heat_score']
                ]
                
                # 闭合数据
                values += values[:1]
                angles_closed = angles + angles[:1]
                
                ax.plot(angles_closed, values, 'o-', linewidth=2, 
                       label=industry['industry_name'], color=colors[idx])
                ax.fill(angles_closed, values, alpha=0.1, color=colors[idx])
            
            ax.set_xticks(angles)
            ax.set_xticklabels(categories)
            ax.set_ylim(0, 1)
            ax.set_title('行业评分雷达图', size=14, y=1.1)
            ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
            
            # 保存图片
            chart_path = os.path.join(Config.IMAGE_DIR, f'industry_radar_{self.today}.png')
            plt.tight_layout()
            plt.savefig(chart_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            logger.info(f"雷达图已保存: {chart_path}")
            
        except Exception as e:
            logger.error(f"创建雷达图失败: {e}")
    
    def _create_stock_score_distribution(self, stocks: List[Dict]):
        """创建股票评分分布图"""
        try:
            if not stocks:
                return
            
            scores = [s['total_score'] for s in stocks]
            
            plt.figure(figsize=(10, 6))
            plt.hist(scores, bins=10, alpha=0.7, color='skyblue', edgecolor='black')
            plt.xlabel('综合评分')
            plt.ylabel('股票数量')
            plt.title('股票综合评分分布')
            plt.grid(True, alpha=0.3)
            
            # 添加平均线
            avg_score = np.mean(scores)
            plt.axvline(avg_score, color='red', linestyle='--', linewidth=2, 
                       label=f'平均分: {avg_score:.2f}')
            plt.legend()
            
            # 保存图片
            chart_path = os.path.join(Config.IMAGE_DIR, f'stock_distribution_{self.today}.png')
            plt.tight_layout()
            plt.savefig(chart_path, dpi=150)
            plt.close()
            
            logger.info(f"评分分布图已保存: {chart_path}")
            
        except Exception as e:
            logger.error(f"创建评分分布图失败: {e}")
    
    def _create_industry_trend_chart(self, industries: List[Dict]):
        """创建行业趋势图"""
        try:
            if not industries:
                return
            
            # 提取行业名称和总分
            industry_names = [ind['industry_name'] for ind in industries]
            total_scores = [ind['total_score'] for ind in industries]
            
            plt.figure(figsize=(12, 6))
            bars = plt.bar(industry_names, total_scores, color='lightcoral')
            
            # 添加数值标签
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                        f'{height:.2f}', ha='center', va='bottom', fontsize=10)
            
            plt.xlabel('行业')
            plt.ylabel('综合评分')
            plt.title('行业综合评分排行')
            plt.ylim(0, 1)
            plt.xticks(rotation=45, ha='right')
            plt.grid(True, alpha=0.3, axis='y')
            
            # 保存图片
            chart_path = os.path.join(Config.IMAGE_DIR, f'industry_trend_{self.today}.png')
            plt.tight_layout()
            plt.savefig(chart_path, dpi=150)
            plt.close()
            
            logger.info(f"行业趋势图已保存: {chart_path}")
            
        except Exception as e:
            logger.error(f"创建行业趋势图失败: {e}")
    
    def _save_report_data(self, report_data: Dict, report_type: str):
        """保存报告数据到JSON文件"""
        try:
            filename = f"{report_type}_report_{self.today}.json"
            filepath = os.path.join(Config.REPORT_DIR, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"报告数据已保存: {filepath}")
            
        except Exception as e:
            logger.error(f"保存报告数据失败: {e}")
    
    def _generate_markdown_report(self, report_data: Dict, report_type: str) -> str:
        """生成Markdown格式报告"""
        try:
            if report_type == 'daily':
                template = self._get_daily_report_template()
            else:
                template = self._get_weekly_report_template()
            
            # 使用Jinja2模板
            jinja_template = Template(template)
            markdown_content = jinja_template.render(**report_data)
            
            # 保存Markdown文件
            filename = f"{report_type}_report_{self.today}.md"
            filepath = os.path.join(Config.REPORT_DIR, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            logger.info(f"Markdown报告已保存: {filepath}")
            
            return markdown_content
            
        except Exception as e:
            logger.error(f"生成Markdown报告失败: {e}")
            return f"# 报告生成失败\n\n错误: {str(e)}"
    
    def _get_daily_report_template(self) -> str:
        """获取日报模板"""
        return """# 📈 股票信息日报 - {{ report_date }}

**生成时间:** {{ generated_at }}

---

## 📊 市场概览

{% if market_overview %}
{% for index_name, index_data in market_overview.items() if index_data is mapping %}
- **{{ index_name }}**: {{ index_data.get('close', 0) | round(2) }} 
  ({{ "上涨" if index_data.get('pct_change', 0) > 0 else "下跌" if index_data.get('pct_change', 0) < 0 else "持平" }} 
  {{ index_data.get('pct_change', 0) | abs | round(2) }}%)
{% endfor %}
{% else %}
市场数据暂不可用
{% endif %}

---

## 🎯 今日潜力行业 Top {{ top_industries|length }}

{% for industry in top_industries %}
### {{ loop.index }}. {{ industry.industry_name }}

- **综合评分:** {{ industry.total_score | round(2) }}
- **资金得分:** {{ industry.capital_flow_score | round(2) }}
- **价格得分:** {{ industry.price_momentum_score | round(2) }}
- **新闻得分:** {{ industry.news_heat_score | round(2) }}
- **趋势分析:** 
  - 短期: {{ industry.trend_analysis.short_term }}
  - 中期: {{ industry.trend_analysis.mid_term }}
  - 长期: {{ industry.trend_analysis.long_term }}
- **推荐理由:** {{ industry.recommendation_reason }}
- **新闻数量:** {{ industry.news_count }}

{% endfor %}

---

## 📈 个股推荐

{% for stock in stock_recommendations %}
### {{ loop.index }}. {{ stock.stock_name }} ({{ stock.stock_code }})

**行业:** {{ stock.industry_name }} (行业评分: {{ stock.industry_score | round(2) }})

**综合评分:** {{ stock.total_score | round(2) }}
- 基本面: {{ stock.fundamental_score | round(2) }}
- 技术面: {{ stock.technical_score | round(2) }}
- 资金面: {{ stock.capital_score | round(2) }}
- 情绪面: {{ stock.sentiment_score | round(2) }}

**价格信息:**
- 当前价: {{ stock.current_price | round(2) }}
{% if stock.price_change.1d %}  - 1日涨跌: {{ stock.price_change.1d | round(1) }}%{% endif %}
{% if stock.price_change.5d %}  - 5日涨跌: {{ stock.price_change.5d | round(1) }}%{% endif %}

**操作建议:**
- **操作:** {{ stock.trading_advice.action }}
- **买入参考:** {{ stock.trading_advice.buy_price }}
- **止损位:** {{ stock.trading_advice.stop_loss }}
- **目标位:** {{ stock.trading_advice.target_price }}
- **信心度:** {{ stock.trading_advice.confidence | round(2) }}
- **理由:** {{ stock.trading_advice.reason }}

**推荐理由:** {{ stock.recommendation_reason }}

---
{% endfor %}

## ⚠️ 风险提示

{% for warning in risk_warnings %}
- {{ warning }}
{% endfor %}

---

## 📝 报告摘要

{{ summary }}

---

*报告生成时间: {{ generated_at }}*  
*数据来源: 公开市场数据*  
*风险提示: 本报告仅供参考，不构成投资建议。股市有风险，投资需谨慎。*
"""
    
    def _get_weekly_report_template(self) -> str:
        """获取周报模板"""
        return """# 📊 股票信息周报 - {{ report_date }}

**统计周期:** {{ week_start }} 至 {{ report_date }}  
**生成时间:** {{ generated_at }}

---

## 📈 本周市场总结

{{ market_summary.comment }}

{% if market_summary.key_events %}
**本周关键事件:**
{% for event in market_summary.key_events %}
- {{ event }}
{% endfor %}
{% endif %}

---

## 🏆 行业表现排行

{% for industry in industry_performance %}
### {{ loop.index }}. {{ industry.industry_name }}

- **综合评分:** {{ industry.total_score | round(2) }}
- **资金得分:** {{ industry.capital_flow_score | round(2) }}
- **价格得分:** {{ industry.price_momentum_score | round(2) }}
- **新闻得分:** {{ industry.news_heat_score | round(2) }}
- **趋势方向:** {{ industry.trend_analysis.direction }}
- **趋势强度:** {{ industry.trend_analysis.strength_desc }}

{% endfor %}

---

## 📊 本周股票表现

### 🎉 涨幅榜
{% for stock in weekly_winners %}
{{ loop.index }}. {{ stock.name }} ({{ stock.code }}) - 涨幅: {{ stock.change | round(1) }}% ({{ stock.industry }})
{% endfor %}

### 📉 跌幅榜  
{% for stock in weekly_losers %}
{{ loop.index }}. {{ stock.name }} ({{ stock.code }}) - 跌幅: {{ stock.change | abs | round(1) }}% ({{ stock.industry }})
{% endfor %}

---

## 💡 本周洞察

{% for insight in weekly_insights %}
- {{ insight }}
{% endfor %}

---

## 🔮 下周展望

{{ next_week_outlook }}

---

## ⚠️ 风险提示

- 股市有风险，投资需谨慎。本报告仅供参考，不构成投资建议。
- 市场可能受到宏观经济、政策变化、国际形势等多种因素影响。
- 过往表现不代表未来收益，投资者应独立判断并承担风险。
- 建议投资者根据自身风险承受能力，合理配置资产。

---

*报告生成时间: {{ generated_at }}*  
*数据来源: 公开市场数据*  
*统计周期: {{ week_start }} 至 {{ report_date }}*
"""


if __name__ == "__main__":
    # 测试代码
    import logging
    logging.basicConfig(level=logging.INFO)
    
    generator = ReportGenerator()
    
    # 测试生成日报
    print("正在生成日报...")
    daily_report = generator.generate_daily_report()
    print(f"日报生成完成，包含 {len(daily_report.get('top_industries', []))} 个行业分析")
    print(f"包含 {len(daily_report.get('stock_recommendations', []))} 只股票推荐")
    
    # 测试生成周报
    print("\n正在生成周报...")
    weekly_report = generator.generate_weekly_report()
    print(f"周报生成完成，包含 {len(weekly_report.get('industry_performance', []))} 个行业分析")