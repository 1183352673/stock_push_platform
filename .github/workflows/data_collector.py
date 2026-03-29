"""
数据采集模块 - 从公开API获取股票数据
"""

import pandas as pd
import numpy as np
import akshare as ak
import efinance as ef
import requests
from datetime import datetime, timedelta
import time
import json
import logging
from typing import Dict, List, Optional, Tuple

from config import Config

logger = logging.getLogger(__name__)

class DataCollector:
    """数据采集器"""
    
    def __init__(self):
        self.today = Config.CURRENT_DATE
        
    def get_industry_list(self) -> pd.DataFrame:
        """
        获取行业列表（申万一级行业）
        Returns:
            DataFrame with columns: ['industry_code', 'industry_name', 'stock_count', ...]
        """
        try:
            logger.info("获取申万一级行业列表...")
            # 使用akshare获取申万一级行业
            industry_df = ak.sw_index_first_info()
            logger.info(f"获取到 {len(industry_df)} 个申万一级行业")
            return industry_df
        except Exception as e:
            logger.error(f"获取行业列表失败: {e}")
            # 返回示例数据（备用）
            return self._get_fallback_industry_list()
    
    def _get_fallback_industry_list(self) -> pd.DataFrame:
        """备用行业列表"""
        industries = [
            {"industry_code": "801010", "industry_name": "农林牧渔"},
            {"industry_code": "801020", "industry_name": "采掘"},
            {"industry_code": "801030", "industry_name": "化工"},
            {"industry_code": "801040", "industry_name": "钢铁"},
            {"industry_code": "801050", "industry_name": "有色金属"},
            {"industry_code": "801060", "industry_name": "电子"},
            {"industry_code": "801070", "industry_name": "家用电器"},
            {"industry_code": "801080", "industry_name": "食品饮料"},
            {"industry_code": "801090", "industry_name": "纺织服装"},
            {"industry_code": "801100", "industry_name": "轻工制造"},
            {"industry_code": "801110", "industry_name": "医药生物"},
            {"industry_code": "801120", "industry_name": "公用事业"},
            {"industry_code": "801130", "industry_name": "交通运输"},
            {"industry_code": "801140", "industry_name": "房地产"},
            {"industry_code": "801150", "industry_name": "商业贸易"},
            {"industry_code": "801160", "industry_name": "休闲服务"},
            {"industry_code": "801170", "industry_name": "综合"},
            {"industry_code": "801180", "industry_name": "建筑材料"},
            {"industry_code": "801190", "industry_name": "建筑装饰"},
            {"industry_code": "801200", "industry_name": "电气设备"},
            {"industry_code": "801210", "industry_name": "国防军工"},
            {"industry_code": "801220", "industry_name": "计算机"},
            {"industry_code": "801230", "industry_name": "传媒"},
            {"industry_code": "801240", "industry_name": "通信"},
            {"industry_code": "801250", "industry_name": "银行"},
            {"industry_code": "801260", "industry_name": "非银金融"},
            {"industry_code": "801270", "industry_name": "汽车"},
            {"industry_code": "801280", "industry_name": "机械设备"},
        ]
        return pd.DataFrame(industries)
    
    def get_industry_quote(self, industry_code: str, days: int = 60) -> pd.DataFrame:
        """
        获取行业指数行情
        Args:
            industry_code: 行业代码
            days: 获取多少天的数据
        Returns:
            DataFrame with columns: ['date', 'open', 'high', 'low', 'close', 'volume', 'amount']
        """
        try:
            logger.info(f"获取行业 {industry_code} 行情数据...")
            # 使用akshare获取行业指数
            end_date = self.today
            start_date = (datetime.now() - timedelta(days=days*2)).strftime("%Y%m%d")  # 多取一些
            
            df = ak.sw_index_daily(industry_code, start_date, end_date)
            if not df.empty:
                df.columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'amount']
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date')
                logger.info(f"获取到行业 {industry_code} {len(df)} 条行情数据")
            return df
        except Exception as e:
            logger.error(f"获取行业 {industry_code} 行情失败: {e}")
            return pd.DataFrame()
    
    def get_industry_capital_flow(self, industry_code: str, days: int = 5) -> pd.DataFrame:
        """
        获取行业资金流向
        Args:
            industry_code: 行业代码
            days: 获取多少天的数据
        Returns:
            DataFrame with columns: ['date', 'main_net_inflow', 'retail_net_inflow', 'total_net_inflow']
        """
        try:
            logger.info(f"获取行业 {industry_code} 资金流向...")
            # 使用efinance获取资金流向
            end_date = self.today
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
            
            # 注意：efinance可能需要行业代码转换
            # 这里使用简化版本，实际可能需要调整
            stock_code = self._industry_to_stock_code(industry_code)
            if stock_code:
                df = ef.stock.get_main_fund_flow(stock_code, start_date, end_date)
                return df
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"获取行业 {industry_code} 资金流向失败: {e}")
            return pd.DataFrame()
    
    def _industry_to_stock_code(self, industry_code: str) -> str:
        """行业代码转换为代表性股票代码（简化版）"""
        # 这里需要一个映射表，暂时返回空
        return ""
    
    def get_industry_news(self, industry_name: str, days: int = 1) -> List[Dict]:
        """
        获取行业相关新闻
        Args:
            industry_name: 行业名称
            days: 最近几天的新闻
        Returns:
            List of news dicts with keys: ['title', 'content', 'source', 'time', 'url']
        """
        try:
            logger.info(f"获取 {industry_name} 行业新闻...")
            news_list = []
            
            # 使用akshare获取新闻（简化版）
            # 实际可能需要多个新闻源
            df = ak.stock_news_em(symbol="", industry=industry_name)
            if not df.empty:
                for _, row in df.iterrows():
                    news = {
                        'title': row.get('新闻标题', ''),
                        'content': row.get('新闻内容', ''),
                        'source': row.get('来源', ''),
                        'time': row.get('发布时间', ''),
                        'url': row.get('新闻链接', ''),
                        'industry': industry_name
                    }
                    news_list.append(news)
            
            logger.info(f"获取到 {industry_name} 行业 {len(news_list)} 条新闻")
            return news_list
        except Exception as e:
            logger.error(f"获取 {industry_name} 行业新闻失败: {e}")
            return []
    
    def get_stocks_by_industry(self, industry_code: str) -> pd.DataFrame:
        """
        获取行业内的股票列表
        Args:
            industry_code: 行业代码
        Returns:
            DataFrame with columns: ['code', 'name', 'industry', ...]
        """
        try:
            logger.info(f"获取行业 {industry_code} 的股票列表...")
            # 使用akshare获取行业成分股
            df = ak.sw_index_cons(industry_code)
            if not df.empty:
                logger.info(f"获取到行业 {industry_code} 的 {len(df)} 只股票")
                return df
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"获取行业 {industry_code} 股票列表失败: {e}")
            return pd.DataFrame()
    
    def get_stock_quote(self, stock_code: str, days: int = 250) -> pd.DataFrame:
        """
        获取个股行情数据
        Args:
            stock_code: 股票代码（带交易所前缀，如 'sh600000'）
            days: 获取多少天的数据
        Returns:
            DataFrame with columns: ['date', 'open', 'high', 'low', 'close', 'volume', 'amount']
        """
        try:
            logger.info(f"获取股票 {stock_code} 行情数据...")
            
            # 确定交易所
            if stock_code.startswith('sh') or stock_code.startswith('sz'):
                code = stock_code[2:]
            else:
                code = stock_code
            
            # 使用akshare获取日线数据
            end_date = self.today
            start_date = (datetime.now() - timedelta(days=days*2)).strftime("%Y%m%d")
            
            df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start_date, end_date=end_date)
            if not df.empty:
                df.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'amount', 'amplitude', 
                             'pct_change', 'change', 'turnover']
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date')
                logger.info(f"获取到股票 {stock_code} {len(df)} 条行情数据")
            return df
        except Exception as e:
            logger.error(f"获取股票 {stock_code} 行情失败: {e}")
            return pd.DataFrame()
    
    def get_stock_fundamental(self, stock_code: str) -> Dict:
        """
        获取个股基本面数据
        Args:
            stock_code: 股票代码
        Returns:
            Dict with fundamental metrics
        """
        try:
            logger.info(f"获取股票 {stock_code} 基本面数据...")
            
            # 使用akshare获取基本面数据
            # 这里获取多个基本面指标
            fundamental = {}
            
            # 市盈率、市净率等
            df = ak.stock_a_lg_indicator(stock_code)
            if not df.empty:
                latest = df.iloc[-1]
                fundamental['pe'] = latest.get('pe', 0)
                fundamental['pb'] = latest.get('pb', 0)
                fundamental['ps'] = latest.get('ps', 0)
            
            # 财务指标
            # 这里可以添加更多财务指标获取逻辑
            
            return fundamental
        except Exception as e:
            logger.error(f"获取股票 {stock_code} 基本面数据失败: {e}")
            return {}
    
    def get_stock_news(self, stock_code: str, days: int = 3) -> List[Dict]:
        """
        获取个股相关新闻
        Args:
            stock_code: 股票代码
            days: 最近几天的新闻
        Returns:
            List of news dicts
        """
        try:
            logger.info(f"获取股票 {stock_code} 新闻...")
            
            # 使用akshare获取个股新闻
            df = ak.stock_news_em(symbol=stock_code)
            news_list = []
            
            if not df.empty:
                for _, row in df.iterrows():
                    news = {
                        'title': row.get('新闻标题', ''),
                        'content': row.get('新闻内容', ''),
                        'source': row.get('来源', ''),
                        'time': row.get('发布时间', ''),
                        'url': row.get('新闻链接', ''),
                        'stock_code': stock_code
                    }
                    news_list.append(news)
            
            logger.info(f"获取到股票 {stock_code} {len(news_list)} 条新闻")
            return news_list
        except Exception as e:
            logger.error(f"获取股票 {stock_code} 新闻失败: {e}")
            return []
    
    def get_market_overview(self) -> Dict:
        """
        获取市场概览数据
        Returns:
            Dict with market overview metrics
        """
        try:
            logger.info("获取市场概览数据...")
            
            overview = {}
            
            # 获取上证指数、深证成指、创业板指
            indices = {
                'sh000001': '上证指数',
                'sz399001': '深证成指',
                'sz399006': '创业板指'
            }
            
            for code, name in indices.items():
                df = self.get_stock_quote(code, days=1)
                if not df.empty:
                    latest = df.iloc[-1]
                    overview[name] = {
                        'close': latest['close'],
                        'change': latest.get('change', 0),
                        'pct_change': latest.get('pct_change', 0)
                    }
            
            # 获取市场情绪指标（如涨跌家数）
            try:
                market_data = ak.stock_zh_a_spot()
                if not market_data.empty:
                    rise_count = len(market_data[market_data['涨跌幅'] > 0])
                    fall_count = len(market_data[market_data['涨跌幅'] < 0])
                    overview['rise_fall'] = {
                        'rise': rise_count,
                        'fall': fall_count,
                        'total': len(market_data)
                    }
            except:
                pass
            
            return overview
        except Exception as e:
            logger.error(f"获取市场概览失败: {e}")
            return {}


if __name__ == "__main__":
    # 测试代码
    collector = DataCollector()
    
    # 测试获取行业列表
    industries = collector.get_industry_list()
    print(f"行业数量: {len(industries)}")
    print(industries.head())
    
    # 测试获取行业行情
    if not industries.empty:
        industry_code = industries.iloc[0]['industry_code']
        quote = collector.get_industry_quote(industry_code, days=30)
        print(f"行业行情数据: {len(quote)} 条")
        if not quote.empty:
            print(quote.tail())