# 股票信息推送平台

基于 GitHub Actions + 企业微信机器人的自动化股票分析推送系统。

## 功能特点
- 每日自动抓取行业数据（行情、资金流、新闻）
- 综合评分选出 Top 3-5 潜力行业
- 每个行业推荐 3-5 只股票（基本面+技术面+资金面+情绪面）
- 生成日报/周报并推送到企业微信
- 全免费架构（GitHub Actions + 公开数据API）

## 文件结构
```
stock_push_platform/
├── README.md                   # 项目说明
├── requirements.txt            # Python依赖
├── config.py                   # 配置文件
├── data_collector.py           # 数据采集模块
├── industry_analyzer.py        # 行业分析模块
├── stock_recommender.py        # 个股推荐模块
├── report_generator.py         # 报告生成模块
├── wecom_notifier.py           # 企业微信推送模块
├── main.py                     # 主程序
├── daily_report.py             # 日报任务入口
├── weekly_report.py            # 周报任务入口
├── .github/workflows/
│   └── daily_stock_report.yml  # GitHub Actions 工作流
└── templates/
    ├── daily_report.md         # 日报模板
    └── weekly_report.md        # 周报模板
```

## 配置步骤
1. 注册企业微信（个人可注册）
2. 创建群聊，添加群机器人，获取 Webhook URL
3. 将 Webhook URL 添加到 GitHub Secrets（WECOM_WEBHOOK）
4. Fork 本仓库，启用 Actions
5. 系统将每天18:00（北京时间）自动运行

## 数据源
- 行情数据：akshare（东方财富、新浪财经）
- 资金流向：efinance
- 新闻数据：腾讯财经、新浪财经
- 行业分类：申万一级行业

## 分析逻辑
### 行业评分（每日）
1. 资金流入得分：近5日主力净流入累计
2. 价格动量得分：近20日涨跌幅
3. 新闻热度得分：当日新闻数量 × 情绪系数（正向1.0，中性0.5，负向0.2）

### 个股推荐（每个行业Top 3-5）
1. 基本面得分：PE/PB/ROE 分位数（越低越好）
2. 技术面得分：MACD金叉(+1)、RSI<30(+1)、突破20日均线(+1)
3. 资金面得分：主力净流入占比
4. 情绪面得分：新闻正向词频占比

## 风险提示
本平台仅供学习参考，不构成投资建议。股市有风险，投资需谨慎。