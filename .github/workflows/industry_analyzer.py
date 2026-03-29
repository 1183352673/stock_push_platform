"""
行业分析模块 - 分析行业趋势并评分
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

from config import Config, IndustryWeights, SentimentConfig
from data_collector import DataCollector

logger = logging.getLogger(__name__)

class IndustryAnalyzer:
    """行业分析器"""
    
    def __init__(self):
        self.collector = DataCollector()
        self.today = Config.CURRENT_DATE
        
    def analyze_all_industries(self, top_n: int = None) -> List[Dict]:
        """
        分析所有行业，返回评分排序
        Args:
            top_n: 返回前N个行业，None表示返回所有
        Returns:
            List of industry dicts with scores and analysis
        """
        logger.info("开始分析所有行业...")
        
        # 获取行业列表
        industries_df = self.collector.get_industry_list()
        if industries_df.empty:
            logger.error("无法获取行业列表")
            return []
        
        # 分析每个行业
        industry_results = []
        for _, industry_row in industries_df.iterrows():
            industry_code = industry_row['industry_code']
            industry_name = industry_row['industry_name']
            
            logger.info(f"分析行业: {industry_name} ({industry_code})")
            
            try:
                result = self.analyze_single_industry(industry_code, industry_name)
                if result:
                    industry_results.append(result)
            except Exception as e:
                logger.error(f"分析行业 {industry_name} 失败: {e}")
                continue
        
        # 按总分排序
        industry_results.sort(key=lambda x: x['total_score'], reverse=True)
        
        # 限制返回数量
        if top_n is not None:
            industry_results = industry_results[:top_n]
        
        logger.info(f"分析完成，共分析 {len(industry_results)} 个行业")
        return industry_results
    
    def analyze_single_industry(self, industry_code: str, industry_name: str) -> Dict:
        """
        分析单个行业
        Returns:
            Dict with analysis results
        """
        # 收集数据
        quote_df = self.collector.get_industry_quote(industry_code, days=Config.LONG_TERM_DAYS)
        capital_flow_df = self.collector.get_industry_capital_flow(industry_code, days=5)
        news_list = self.collector.get_industry_news(industry_name, days=1)
        
        # 计算各项得分
        capital_flow_score = self._calculate_capital_flow_score(capital_flow_df)
        price_momentum_score = self._calculate_price_momentum_score(quote_df)
        news_heat_score = self._calculate_news_heat_score(news_list)
        
        # 计算总分（加权）
        total_score = (
            capital_flow_score * IndustryWeights.CAPITAL_FLOW_WEIGHT +
            price_momentum_score * IndustryWeights.PRICE_MOMENTUM_WEIGHT +
            news_heat_score * IndustryWeights.NEWS_HEAT_WEIGHT
        )
        
        # 趋势分析
        trend_analysis = self._analyze_industry_trend(quote_df)
        
        # 生成推荐理由
        recommendation_reason = self._generate_recommendation_reason(
            capital_flow_score, price_momentum_score, news_heat_score, trend_analysis
        )
        
        # 返回结果
        result = {
            'industry_code': industry_code,
            'industry_name': industry_name,
            'capital_flow_score': capital_flow_score,
            'price_momentum_score': price_momentum_score,
            'news_heat_score': news_heat_score,
            'total_score': total_score,
            'trend_analysis': trend_analysis,
            'recommendation_reason': recommendation_reason,
            'news_count': len(news_list),
            'data_points': {
                'quote_count': len(quote_df),
                'capital_flow_count': len(capital_flow_df),
                'latest_close': quote_df['close'].iloc[-1] if not quote_df.empty else 0,
                'latest_change': quote_df['close'].pct_change().iloc[-1] * 100 if len(quote_df) > 1 else 0
            }
        }
        
        return result
    
    def _calculate_capital_flow_score(self, capital_flow_df: pd.DataFrame) -> float:
        """计算资金流入得分"""
        if capital_flow_df.empty:
            return 0.5  # 中性得分
        
        try:
            # 如果有主力净流入数据
            if 'main_net_inflow' in capital_flow_df.columns:
                inflows = capital_flow_df['main_net_inflow'].tail(5)  # 最近5天
                total_inflow = inflows.sum()
                
                # 标准化到0-1范围（示例逻辑，实际需要调整）
                if total_inflow > 0:
                    # 正流入，得分在0.5-1.0之间
                    score = 0.5 + min(0.5, total_inflow / 1e8)  # 假设1亿为上限
                else:
                    # 负流入，得分在0-0.5之间
                    score = 0.5 - min(0.5, abs(total_inflow) / 1e8)
                
                return max(0, min(1, score))
            
            return 0.5
        except Exception as e:
            logger.error(f"计算资金流入得分失败: {e}")
            return 0.5
    
    def _calculate_price_momentum_score(self, quote_df: pd.DataFrame) -> float:
        """计算价格动量得分"""
        if quote_df.empty or len(quote_df) < 20:
            return 0.5
        
        try:
            closes = quote_df['close'].tail(20)  # 最近20天
            
            # 计算20日收益率
            if len(closes) >= 2:
                returns = (closes.iloc[-1] - closes.iloc[0]) / closes.iloc[0]
                
                # 计算短期动量（5日）
                short_returns = 0
                if len(closes) >= 5:
                    short_returns = (closes.iloc[-1] - closes.iloc[-5]) / closes.iloc[-5]
                
                # 计算动量得分（综合长短期）
                momentum_score = 0.6 * returns + 0.4 * short_returns
                
                # 转换为0-1得分：假设±10%为上下限
                score = 0.5 + momentum_score / 0.2  # 20%的变化对应1.0分
                return max(0, min(1, score))
            
            return 0.5
        except Exception as e:
            logger.error(f"计算价格动量得分失败: {e}")
            return 0.5
    
    def _calculate_news_heat_score(self, news_list: List[Dict]) -> float:
        """计算新闻热度得分"""
        if not news_list:
            return 0.3  # 无新闻，得分较低
        
        try:
            total_news = len(news_list)
            
            # 分析新闻情感
            positive_count = 0
            negative_count = 0
            
            for news in news_list:
                title = news.get('title', '')
                content = news.get('content', '')
                text = title + ' ' + content
                
                # 简单关键词匹配
                positive_words = sum(1 for word in SentimentConfig.POSITIVE_WORDS if word in text)
                negative_words = sum(1 for word in SentimentConfig.NEGATIVE_WORDS if word in text)
                
                if positive_words > negative_words:
                    positive_count += 1
                elif negative_words > positive_words:
                    negative_count += 1
            
            # 计算情感得分
            if total_news > 0:
                sentiment_score = positive_count / total_news - negative_count / total_news
                # 从-1到1映射到0到1
                sentiment_normalized = (sentiment_score + 1) / 2
            else:
                sentiment_normalized = 0.5
            
            # 新闻数量得分（0-0.5之间）
            count_score = min(0.5, total_news / 20)  # 20条新闻得0.5分
            
            # 综合得分：情感得分 + 数量得分
            total_score = 0.6 * sentiment_normalized + 0.4 * count_score
            
            return max(0, min(1, total_score))
        except Exception as e:
            logger.error(f"计算新闻热度得分失败: {e}")
            return 0.5
    
    def _analyze_industry_trend(self, quote_df: pd.DataFrame) -> Dict[str, Any]:
        """分析行业趋势（短/中/长期）"""
        if quote_df.empty:
            return {
                'short_term': '数据不足',
                'mid_term': '数据不足',
                'long_term': '数据不足',
                'trend_strength': 0,
                'direction': 'neutral'
            }
        
        try:
            closes = quote_df['close']
            
            # 短期趋势（20日）
            short_trend = 'neutral'
            short_strength = 0
            if len(closes) >= Config.SHORT_TERM_DAYS:
                short_closes = closes.tail(Config.SHORT_TERM_DAYS)
                if len(short_closes) >= 5:
                    # 计算短期移动平均
                    ma_short = short_closes.rolling(window=5).mean()
                    ma_medium = short_closes.rolling(window=10).mean()
                    
                    # 判断趋势
                    if ma_short.iloc[-1] > ma_medium.iloc[-1] and short_closes.iloc[-1] > ma_short.iloc[-1]:
                        short_trend = 'up'
                        short_strength = min(1.0, (short_closes.iloc[-1] - ma_medium.iloc[-1]) / ma_medium.iloc[-1] * 10)
                    elif ma_short.iloc[-1] < ma_medium.iloc[-1] and short_closes.iloc[-1] < ma_short.iloc[-1]:
                        short_trend = 'down'
                        short_strength = min(1.0, (ma_medium.iloc[-1] - short_closes.iloc[-1]) / ma_medium.iloc[-1] * 10)
            
            # 中期趋势（120日）
            mid_trend = 'neutral'
            mid_strength = 0
            if len(closes) >= Config.MID_TERM_DAYS:
                mid_closes = closes.tail(Config.MID_TERM_DAYS)
                if len(mid_closes) >= 20:
                    # 计算中期移动平均
                    ma_short = mid_closes.rolling(window=20).mean()
                    ma_long = mid_closes.rolling(window=60).mean()
                    
                    if ma_short.iloc[-1] > ma_long.iloc[-1]:
                        mid_trend = 'up'
                        mid_strength = min(1.0, (ma_short.iloc[-1] - ma_long.iloc[-1]) / ma_long.iloc[-1] * 5)
                    elif ma_short.iloc[-1] < ma_long.iloc[-1]:
                        mid_trend = 'down'
                        mid_strength = min(1.0, (ma_long.iloc[-1] - ma_short.iloc[-1]) / ma_long.iloc[-1] * 5)
            
            # 长期趋势（750日）
            long_trend = 'neutral'
            long_strength = 0
            if len(closes) >= Config.LONG_TERM_DAYS:
                long_closes = closes.tail(Config.LONG_TERM_DAYS)
                if len(long_closes) >= 120:
                    # 计算长期移动平均
                    ma_medium = long_closes.rolling(window=120).mean()
                    ma_long = long_closes.rolling(window=250).mean()
                    
                    if ma_medium.iloc[-1] > ma_long.iloc[-1]:
                        long_trend = 'up'
                        long_strength = min(1.0, (ma_medium.iloc[-1] - ma_long.iloc[-1]) / ma_long.iloc[-1] * 3)
                    elif ma_medium.iloc[-1] < ma_long.iloc[-1]:
                        long_trend = 'down'
                        long_strength = min(1.0, (ma_long.iloc[-1] - ma_medium.iloc[-1]) / ma_long.iloc[-1] * 3)
            
            # 综合趋势判断
            trends = [short_trend, mid_trend, long_trend]
            up_count = trends.count('up')
            down_count = trends.count('down')
            
            if up_count >= 2:
                overall_trend = 'up'
                trend_strength = (short_strength + mid_strength + long_strength) / 3
            elif down_count >= 2:
                overall_trend = 'down'
                trend_strength = (short_strength + mid_strength + long_strength) / 3
            else:
                overall_trend = 'neutral'
                trend_strength = 0
            
            # 趋势强度描述
            if trend_strength > 0.7:
                trend_desc = '强'
            elif trend_strength > 0.3:
                trend_desc = '中等'
            else:
                trend_desc = '弱'
            
            return {
                'short_term': f'{short_trend}_{trend_desc}' if short_trend != 'neutral' else 'neutral',
                'mid_term': f'{mid_trend}_{trend_desc}' if mid_trend != 'neutral' else 'neutral',
                'long_term': f'{long_trend}_{trend_desc}' if long_trend != 'neutral' else 'neutral',
                'trend_strength': trend_strength,
                'direction': overall_trend,
                'strength_desc': trend_desc
            }
        except Exception as e:
            logger.error(f"分析行业趋势失败: {e}")
            return {
                'short_term': '分析失败',
                'mid_term': '分析失败',
                'long_term': '分析失败',
                'trend_strength': 0,
                'direction': 'neutral'
            }
    
    def _generate_recommendation_reason(self, capital_score: float, price_score: float, 
                                      news_score: float, trend_analysis: Dict) -> str:
        """生成推荐理由"""
        reasons = []
        
        # 资金面理由
        if capital_score > 0.7:
            reasons.append("资金大幅流入")
        elif capital_score > 0.6:
            reasons.append("资金小幅流入")
        elif capital_score < 0.4:
            reasons.append("资金流出")
        
        # 价格动量理由
        if price_score > 0.7:
            reasons.append("价格强势上涨")
        elif price_score > 0.6:
            reasons.append("价格温和上涨")
        elif price_score < 0.4:
            reasons.append("价格走弱")
        
        # 新闻热度理由
        if news_score > 0.7:
            reasons.append("市场关注度高")
        elif news_score > 0.6:
            reasons.append("有一定关注度")
        elif news_score < 0.4:
            reasons.append("关注度较低")
        
        # 趋势理由
        trend_direction = trend_analysis.get('direction', 'neutral')
        trend_strength = trend_analysis.get('strength_desc', '弱')
        
        if trend_direction == 'up':
            reasons.append(f"趋势向上({trend_strength})")
        elif trend_direction == 'down':
            reasons.append(f"趋势向下({trend_strength})")
        
        if not reasons:
            reasons.append("各项指标中性")
        
        return "，".join(reasons)


if __name__ == "__main__":
    # 测试代码
    import logging
    logging.basicConfig(level=logging.INFO)
    
    analyzer = IndustryAnalyzer()
    
    # 测试分析前5个行业
    results = analyzer.analyze_all_industries(top_n=5)
    
    print(f"分析完成，共 {len(results)} 个行业")
    for i, industry in enumerate(results, 1):
        print(f"{i}. {industry['industry_name']} - 总分: {industry['total_score']:.2f}")
        print(f"   资金: {industry['capital_flow_score']:.2f}, "
              f"价格: {industry['price_momentum_score']:.2f}, "
              f"新闻: {industry['news_heat_score']:.2f}")
        print(f"   趋势: {industry['trend_analysis']}")
        print(f"   理由: {industry['recommendation_reason']}")
        print()
