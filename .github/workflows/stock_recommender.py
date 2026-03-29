"""
个股推荐模块 - 分析并推荐行业内的优质股票
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

from config import Config, StockWeights, TechnicalConfig, SentimentConfig
from data_collector import DataCollector

logger = logging.getLogger(__name__)

class StockRecommender:
    """个股推荐器"""
    
    def __init__(self):
        self.collector = DataCollector()
        self.today = Config.CURRENT_DATE
    
    def recommend_stocks_for_industry(self, industry_code: str, industry_name: str, 
                                     top_n: int = None) -> List[Dict]:
        """
        为指定行业推荐股票
        Args:
            industry_code: 行业代码
            industry_name: 行业名称
            top_n: 返回前N只股票，None表示使用配置默认值
        Returns:
            List of stock recommendation dicts
        """
        if top_n is None:
            top_n = Config.STOCKS_PER_INDUSTRY
        
        logger.info(f"为行业 {industry_name} 推荐股票...")
        
        # 获取行业内的股票列表
        stocks_df = self.collector.get_stocks_by_industry(industry_code)
        if stocks_df.empty:
            logger.warning(f"行业 {industry_name} 无股票数据")
            return []
        
        logger.info(f"行业 {industry_name} 共有 {len(stocks_df)} 只股票，开始分析...")
        
        # 分析每只股票
        stock_results = []
        analyzed_count = 0
        
        for _, stock_row in stocks_df.iterrows():
            stock_code = stock_row.get('code', '')
            stock_name = stock_row.get('name', '')
            
            if not stock_code:
                continue
            
            # 只分析前30只股票（避免API限制）
            if analyzed_count >= 30:
                break
            
            try:
                logger.info(f"分析股票: {stock_name} ({stock_code}) [{analyzed_count+1}/{min(30, len(stocks_df))}]")
                result = self.analyze_single_stock(stock_code, stock_name, industry_name)
                if result:
                    stock_results.append(result)
                    analyzed_count += 1
            except Exception as e:
                logger.error(f"分析股票 {stock_name} 失败: {e}")
                continue
        
        # 按总分排序
        stock_results.sort(key=lambda x: x['total_score'], reverse=True)
        
        # 限制返回数量
        stock_results = stock_results[:top_n]
        
        logger.info(f"行业 {industry_name} 股票推荐完成，推荐 {len(stock_results)} 只")
        return stock_results
    
    def analyze_single_stock(self, stock_code: str, stock_name: str, industry_name: str) -> Dict:
        """
        分析单只股票
        Returns:
            Dict with analysis results
        """
        # 收集数据
        quote_df = self.collector.get_stock_quote(stock_code, days=250)
        fundamental = self.collector.get_stock_fundamental(stock_code)
        news_list = self.collector.get_stock_news(stock_code, days=3)
        
        # 计算各项得分
        fundamental_score = self._calculate_fundamental_score(fundamental, quote_df)
        technical_score = self._calculate_technical_score(quote_df)
        capital_score = self._calculate_capital_score(quote_df)
        sentiment_score = self._calculate_sentiment_score(news_list)
        
        # 计算总分（加权）
        total_score = (
            fundamental_score * StockWeights.FUNDAMENTAL_WEIGHT +
            technical_score * StockWeights.TECHNICAL_WEIGHT +
            capital_score * StockWeights.CAPITAL_WEIGHT +
            sentiment_score * StockWeights.SENTIMENT_WEIGHT
        )
        
        # 生成买卖建议
        trading_advice = self._generate_trading_advice(quote_df, technical_score, total_score)
        
        # 生成推荐理由
        recommendation_reason = self._generate_recommendation_reason(
            fundamental_score, technical_score, capital_score, sentiment_score
        )
        
        # 返回结果
        result = {
            'stock_code': stock_code,
            'stock_name': stock_name,
            'industry': industry_name,
            'fundamental_score': fundamental_score,
            'technical_score': technical_score,
            'capital_score': capital_score,
            'sentiment_score': sentiment_score,
            'total_score': total_score,
            'trading_advice': trading_advice,
            'recommendation_reason': recommendation_reason,
            'current_price': quote_df['close'].iloc[-1] if not quote_df.empty else 0,
            'price_change': self._calculate_price_change(quote_df),
            'news_count': len(news_list),
            'data_quality': self._assess_data_quality(quote_df, fundamental, news_list)
        }
        
        return result
    
    def _calculate_fundamental_score(self, fundamental: Dict, quote_df: pd.DataFrame) -> float:
        """计算基本面得分"""
        if not fundamental or quote_df.empty:
            return 0.5
        
        try:
            score_components = []
            
            # 1. 市盈率得分（PE越低越好）
            pe = fundamental.get('pe', 0)
            if pe > 0:
                # 假设PE在0-50之间，越低越好
                pe_score = max(0, 1 - pe / 50)
                score_components.append(('pe', pe_score, 0.4))
            
            # 2. 市净率得分（PB越低越好）
            pb = fundamental.get('pb', 0)
            if pb > 0:
                # 假设PB在0-5之间，越低越好
                pb_score = max(0, 1 - pb / 5)
                score_components.append(('pb', pb_score, 0.3))
            
            # 3. 价格趋势（近期表现）
            if len(quote_df) >= 20:
                closes = quote_df['close'].tail(20)
                if len(closes) >= 2:
                    # 20日收益率
                    returns = (closes.iloc[-1] - closes.iloc[0]) / closes.iloc[0]
                    # 转换为得分：-10%到+10%映射到0-1
                    trend_score = 0.5 + returns / 0.2  # 20%的变化对应1.0分
                    trend_score = max(0, min(1, trend_score))
                    score_components.append(('trend', trend_score, 0.3))
            
            # 计算加权得分
            if score_components:
                total_weight = sum(w for _, _, w in score_components)
                weighted_score = sum(s * w for _, s, w in score_components) / total_weight
                return weighted_score
            
            return 0.5
        except Exception as e:
            logger.error(f"计算基本面得分失败: {e}")
            return 0.5
    
    def _calculate_technical_score(self, quote_df: pd.DataFrame) -> float:
        """计算技术面得分"""
        if quote_df.empty or len(quote_df) < 30:
            return 0.5
        
        try:
            closes = quote_df['close']
            score = 0.5
            signal_count = 0
            
            # 1. 移动平均线信号
            if len(closes) >= 20:
                ma_short = closes.rolling(window=TechnicalConfig.MA_SHORT).mean()
                ma_mid = closes.rolling(window=TechnicalConfig.MA_MID).mean()
                
                if not pd.isna(ma_short.iloc[-1]) and not pd.isna(ma_mid.iloc[-1]):
                    if ma_short.iloc[-1] > ma_mid.iloc[-1]:
                        score += 0.15  # 金叉信号
                        signal_count += 1
                    elif ma_short.iloc[-1] < ma_mid.iloc[-1]:
                        score -= 0.1   # 死叉信号
            
            # 2. RSI信号
            if len(closes) >= TechnicalConfig.RSI_PERIOD + 10:
                # 计算价格变化
                delta = closes.diff()
                gain = delta.where(delta > 0, 0)
                loss = -delta.where(delta < 0, 0)
                
                avg_gain = gain.rolling(window=TechnicalConfig.RSI_PERIOD).mean()
                avg_loss = loss.rolling(window=TechnicalConfig.RSI_PERIOD).mean()
                
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                
                if not pd.isna(rsi.iloc[-1]):
                    rsi_value = rsi.iloc[-1]
                    if rsi_value < 30:
                        score += 0.1  # 超卖，买入信号
                        signal_count += 1
                    elif rsi_value > 70:
                        score -= 0.1  # 超买，卖出信号
            
            # 3. 价格位置（相对高低）
            if len(closes) >= 60:
                high_60 = closes.tail(60).max()
                low_60 = closes.tail(60).min()
                current = closes.iloc[-1]
                
                if high_60 != low_60:
                    position = (current - low_60) / (high_60 - low_60)
                    # 在0.3-0.7之间得分较高
                    if 0.3 <= position <= 0.7:
                        score += 0.05
                        signal_count += 1
                    elif position < 0.2:
                        score += 0.1  # 接近底部
                        signal_count += 1
            
            # 4. 成交量验证
            if 'volume' in quote_df.columns and len(quote_df) >= 5:
                volumes = quote_df['volume'].tail(5)
                price_changes = closes.pct_change().tail(5)
                
                # 价量齐升
                if len(volumes) >= 2 and len(price_changes) >= 2:
                    volume_up = volumes.iloc[-1] > volumes.iloc[-2]
                    price_up = price_changes.iloc[-1] > 0
                    
                    if volume_up and price_up:
                        score += 0.05
                        signal_count += 1
                    elif volume_up and not price_up:
                        score -= 0.03  # 放量下跌
            
            # 根据信号数量调整得分
            if signal_count > 0:
                score = min(1.0, score)
                score = max(0.0, score)
            
            return score
        except Exception as e:
            logger.error(f"计算技术面得分失败: {e}")
            return 0.5
    
    def _calculate_capital_score(self, quote_df: pd.DataFrame) -> float:
        """计算资金面得分"""
        if quote_df.empty:
            return 0.5
        
        try:
            score = 0.5
            
            # 1. 近期成交量变化
            if 'volume' in quote_df.columns and len(quote_df) >= 10:
                volumes = quote_df['volume'].tail(10)
                volume_ma5 = volumes.rolling(window=5).mean()
                
                if not pd.isna(volume_ma5.iloc[-1]) and volume_ma5.iloc[-1] > 0:
                    # 当前成交量相对于5日均量的比率
                    volume_ratio = volumes.iloc[-1] / volume_ma5.iloc[-1]
                    
                    if volume_ratio > 1.5:
                        score += 0.2  # 明显放量
                    elif volume_ratio > 1.2:
                        score += 0.1  # 温和放量
                    elif volume_ratio < 0.8:
                        score -= 0.1  # 缩量
            
            # 2. 价格与成交量关系
            if 'volume' in quote_df.columns and len(quote_df) >= 5:
                closes = quote_df['close'].tail(5)
                volumes = quote_df['volume'].tail(5)
                
                price_change = (closes.iloc[-1] - closes.iloc[0]) / closes.iloc[0]
                volume_change = (volumes.iloc[-1] - volumes.iloc[0]) / volumes.iloc[0] if volumes.iloc[0] > 0 else 0
                
                # 价量齐升为最佳
                if price_change > 0.02 and volume_change > 0.1:
                    score += 0.15
                # 价升量减需谨慎
                elif price_change > 0.02 and volume_change < -0.1:
                    score -= 0.1
            
            return max(0, min(1, score))
        except Exception as e:
            logger.error(f"计算资金面得分失败: {e}")
            return 0.5
    
    def _calculate_sentiment_score(self, news_list: List[Dict]) -> float:
        """计算情绪面得分"""
        if not news_list:
            return 0.3  # 无新闻，得分较低
        
        try:
            total_news = len(news_list)
            positive_score = 0
            negative_score = 0
            
            for news in news_list:
                title = news.get('title', '')
                content = news.get('content', '')
                text = title + ' ' + content
                
                # 关键词匹配
                positive_words = sum(1 for word in SentimentConfig.POSITIVE_WORDS if word in text)
                negative_words = sum(1 for word in SentimentConfig.NEGATIVE_WORDS if word in text)
                
                if positive_words > negative_words:
                    positive_score += 1
                elif negative_words > positive_words:
                    negative_score += 1
                else:
                    # 中性新闻
                    positive_score += 0.5
                    negative_score += 0.5
            
            # 计算净情绪得分
            if total_news > 0:
                net_sentiment = (positive_score - negative_score) / total_news
                # 从-1到1映射到0到1
                sentiment_normalized = (net_sentiment + 1) / 2
            else:
                sentiment_normalized = 0.5
            
            # 新闻数量加权
            count_factor = min(1.0, total_news / 10)  # 10条新闻为上限
            
            final_score = 0.7 * sentiment_normalized + 0.3 * count_factor
            
            return max(0, min(1, final_score))
        except Exception as e:
            logger.error(f"计算情绪面得分失败: {e}")
            return 0.5
    
    def _calculate_price_change(self, quote_df: pd.DataFrame) -> Dict:
        """计算价格变化"""
        if quote_df.empty:
            return {'1d': 0, '5d': 0, '20d': 0}
        
        try:
            closes = quote_df['close']
            changes = {}
            
            # 1日变化
            if len(closes) >= 2:
                changes['1d'] = (closes.iloc[-1] - closes.iloc[-2]) / closes.iloc[-2] * 100
            
            # 5日变化
            if len(closes) >= 6:
                changes['5d'] = (closes.iloc[-1] - closes.iloc[-6]) / closes.iloc[-6] * 100
            
            # 20日变化
            if len(closes) >= 21:
                changes['20d'] = (closes.iloc[-1] - closes.iloc[-21]) / closes.iloc[-21] * 100
            
            return changes
        except:
            return {'1d': 0, '5d': 0, '20d': 0}
    
    def _assess_data_quality(self, quote_df: pd.DataFrame, fundamental: Dict, news_list: List[Dict]) -> str:
        """评估数据质量"""
        quality_score = 0
        
        # 行情数据质量
        if not quote_df.empty and len(quote_df) >= 60:
            quality_score += 2
        
        # 基本面数据质量
        if fundamental and len(fundamental) >= 2:
            quality_score += 1
        
        # 新闻数据质量
        if len(news_list) >= 3:
            quality_score += 1
        
        if quality_score >= 3:
            return 'high'
        elif quality_score >= 2:
            return 'medium'
        else:
            return 'low'
    
    def _generate_trading_advice(self, quote_df: pd.DataFrame, technical_score: float, total_score: float) -> Dict:
        """生成买卖建议"""
        if quote_df.empty:
            return {
                'action': '观望',
                'buy_price': 0,
                'stop_loss': 0,
                'target_price': 0,
                'confidence': 0,
                'reason': '数据不足'
            }
        
        try:
            closes = quote_df['close']
            current_price = closes.iloc[-1]
            
            # 计算支撑位和压力位（简化版）
            if len(closes) >= 20:
                # 近期低点作为支撑
                recent_low = closes.tail(20).min()
                # 近期高点作为压力
                recent_high = closes.tail(20).max()
                
                # 移动平均线作为参考
                ma_20 = closes.rolling(window=20).mean().iloc[-1] if len(closes) >= 20 else current_price
                ma_60 = closes.rolling(window=60).mean().iloc[-1] if len(closes) >= 60 else current_price
            else:
                recent_low = current_price * 0.95
                recent_high = current_price * 1.05
                ma_20 = current_price
                ma_60 = current_price
            
            # 根据得分决定操作
            if total_score >= 0.7:
                action = '买入'
                buy_price = min(current_price, ma_20)  # 当前价或均线价
                stop_loss = recent_low * 0.97  # 跌破支撑3%
                target_price = recent_high * 1.03  # 突破压力3%
                confidence = min(0.9, total_score * 1.2)
                reason = '综合评分较高，技术面向好'
            elif total_score >= 0.6:
                action = '关注'
                buy_price = ma_20
                stop_loss = recent_low * 0.95
                target_price = recent_high
                confidence = total_score
                reason = '评分中等，可逢低关注'
            elif total_score >= 0.4:
                action = '观望'
                buy_price = 0
                stop_loss = 0
                target_price = 0
                confidence = 0.5
                reason = '评分一般，建议观望'
            else:
                action = '回避'
                buy_price = 0
                stop_loss = 0
                target_price = 0
                confidence = 0.3
                reason = '评分较低，建议回避'
            
            return {
                'action': action,
                'buy_price': round(buy_price, 2),
                'stop_loss': round(stop_loss, 2),
                'target_price': round(target_price, 2),
                'confidence': round(confidence, 2),
                'reason': reason
            }
        except Exception as e:
            logger.error(f"生成买卖建议失败: {e}")
            return {
                'action': '观望',
                'buy_price': 0,
                'stop_loss': 0,
                'target_price': 0,
                'confidence': 0,
                'reason': '分析失败'
            }
    
    def _generate_recommendation_reason(self, fundamental_score: float, technical_score: float,
                                      capital_score: float, sentiment_score: float) -> str:
        """生成推荐理由"""
        reasons = []
        
        # 基本面理由
        if fundamental_score > 0.7:
            reasons.append("基本面优秀")
        elif fundamental_score > 0.6:
            reasons.append("基本面良好")
        elif fundamental_score < 0.4:
            reasons.append("基本面偏弱")
        
        # 技术面理由
        if technical_score > 0.7:
            reasons.append("技术形态向好")
        elif technical_score > 0.6:
            reasons.append("技术面改善")
        elif technical_score < 0.4:
            reasons.append("技术面偏弱")
        
        # 资金面理由
        if capital_score > 0.7:
            reasons.append("资金关注度高")
        elif capital_score > 0.6:
            reasons.append("资金小幅流入")
        elif capital_score < 0.4:
            reasons.append("资金关注度低")
        
        # 情绪面理由
        if sentiment_score > 0.7:
            reasons.append("市场情绪积极")
        elif sentiment_score > 0.6:
            reasons.append("情绪面偏暖")
        elif sentiment_score < 0.4:
            reasons.append("情绪面偏冷")
        
        if not reasons:
            reasons.append("各项指标均衡")
        
        return "，".join(reasons)


if __name__ == "__main__":
    # 测试代码
    import logging
    logging.basicConfig(level=logging.INFO)
    
    recommender = StockRecommender()
    
    # 测试为某个行业推荐股票
    industry_code = "801110"  # 医药生物
    industry_name = "医药生物"
    
    stocks = recommender.recommend_stocks_for_industry(industry_code, industry_name, top_n=3)
    
    print(f"行业 {industry_name} 推荐股票:")
    for i, stock in enumerate(stocks, 1):
        print(f"{i}. {stock['stock_name']}({stock['stock_code']})")
        print(f"   综合得分: {stock['total_score']:.2f} "
              f"(基本面:{stock['fundamental_score']:.2f}, "
              f"技术面:{stock['technical_score']:.2f}, "
              f"资金面:{stock['capital_score']:.2f}, "
              f"情绪面:{stock['sentiment_score']:.2f})")
        print(f"   当前价: {stock['current_price']:.2f}, "
              f"涨跌幅: 1日{stock['price_change'].get('1d', 0):.1f}%, "
              f"5日{stock['price_change'].get('5d', 0):.1f}%")
        print(f"   操作建议: {stock['trading_advice']['action']} "
              f"(信心:{stock['trading_advice']['confidence']:.2f})")
        print(f"   理由: {stock['recommendation_reason']}")
        print()