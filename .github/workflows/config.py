"""
配置文件 - 股票信息推送平台
"""

import os
from datetime import datetime

# ==================== 基本配置 ====================
class Config:
    """全局配置"""
    
    # 时间设置
    CURRENT_DATE = datetime.now().strftime("%Y-%m-%d")
    
    # 行业配置
    INDUSTRY_COUNT = 5  # 推送的行业数量
    STOCKS_PER_INDUSTRY = 5  # 每个行业推荐的股票数量
    
    # 分析周期
    SHORT_TERM_DAYS = 20  # 短期：20个交易日 ≈ 4周
    MID_TERM_DAYS = 120   # 中期：120个交易日 ≈ 6个月
    LONG_TERM_DAYS = 750  # 长期：750个交易日 ≈ 3年（250交易日/年）
    
    # 数据源配置
    DATA_SOURCES = {
        "akshare": {
            "enabled": True,
            "timeout": 30
        },
        "efinance": {
            "enabled": True,
            "timeout": 30
        }
    }
    
    # 企业微信机器人配置（通过环境变量获取）
    WECOM_WEBHOOK = os.getenv("WECOM_WEBHOOK", "")
    
    # GitHub Pages URL（用于报告链接）
    GITHUB_PAGES_URL = os.getenv("GITHUB_PAGES_URL", "https://yourusername.github.io/stock_push_platform")
    
    # 文件存储路径
    DATA_DIR = "data"
    REPORT_DIR = "reports"
    IMAGE_DIR = "images"
    
    # 日志配置
    LOG_LEVEL = "INFO"
    LOG_FILE = "logs/stock_platform.log"

# ==================== 行业评分权重 ====================
class IndustryWeights:
    """行业评分权重配置"""
    
    # 资金流入得分权重
    CAPITAL_FLOW_WEIGHT = 0.4
    
    # 价格动量得分权重
    PRICE_MOMENTUM_WEIGHT = 0.3
    
    # 新闻热度得分权重
    NEWS_HEAT_WEIGHT = 0.3

# ==================== 个股评分权重 ====================
class StockWeights:
    """个股评分权重配置"""
    
    # 基本面得分权重
    FUNDAMENTAL_WEIGHT = 0.25
    
    # 技术面得分权重
    TECHNICAL_WEIGHT = 0.25
    
    # 资金面得分权重
    CAPITAL_WEIGHT = 0.25
    
    # 情绪面得分权重
    SENTIMENT_WEIGHT = 0.25

# ==================== 技术指标配置 ====================
class TechnicalConfig:
    """技术指标参数"""
    
    # MACD参数
    MACD_FAST = 12
    MACD_SLOW = 26
    MACD_SIGNAL = 9
    
    # RSI参数
    RSI_PERIOD = 14
    
    # 移动平均线参数
    MA_SHORT = 20    # 短期均线
    MA_MID = 60      # 中期均线
    MA_LONG = 250    # 长期均线
    
    # 布林带参数
    BOLL_PERIOD = 20
    BOLL_STD = 2

# ==================== 情感分析配置 ====================
class SentimentConfig:
    """情感分析关键词"""
    
    # 正向关键词（利好）
    POSITIVE_WORDS = [
        "增长", "盈利", "上涨", "突破", "创新", "利好", "推荐", "买入", "增持",
        "看好", "机会", "复苏", "改善", "超预期", "大涨", "飙升", "涨停",
        "优秀", "强劲", "稳健", "提升", "扩张", "发展", "领先", "龙头",
        "政策支持", "补贴", "减税", "降息", "改革", "开放"
    ]
    
    # 负向关键词（利空）
    NEGATIVE_WORDS = [
        "下跌", "亏损", "下跌", "跌破", "风险", "利空", "卖出", "减持",
        "看空", "警告", "危机", "恶化", "不及预期", "大跌", "暴跌", "跌停",
        "困难", "疲软", "下滑", "收缩", "衰退", "落后", "问题", "处罚",
        "调查", "罚款", "诉讼", "债务", "违约", "破产", "退市"
    ]

# ==================== 推送消息模板 ====================
class MessageTemplates:
    """企业微信消息模板"""
    
    # 日报标题
    DAILY_TITLE = "📈 股票信息日报 - {date}"
    
    # 周报标题
    WEEKLY_TITLE = "📊 股票信息周报 - {date}"
    
    # 消息正文模板
    DAILY_MESSAGE = """**📅 日报摘要 - {date}**

**🎯 今日潜力行业 Top {count}:**
{industry_summary}

**📊 个股推荐摘要:**
{stock_summary}

**⚠️ 风险提示:**
{risk_warnings}

详细报告请查看: {report_url}
"""
    
    # 行业摘要模板
    INDUSTRY_SUMMARY_ITEM = "{rank}. {industry_name} (评分: {score:.2f}) - {reason}"
    
    # 个股摘要模板
    STOCK_SUMMARY_ITEM = "• {stock_name}({stock_code}) - 综合得分: {score:.2f} - 建议: {advice}"

# 创建必要的目录
def create_directories():
    """创建必要的目录结构"""
    dirs = [Config.DATA_DIR, Config.REPORT_DIR, Config.IMAGE_DIR, "logs"]
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
