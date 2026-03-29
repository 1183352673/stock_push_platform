# 部署指南

## 1. 注册企业微信并获取Webhook

### 步骤
1. 下载企业微信APP（个人可注册）
2. 注册企业微信账号
3. 创建群聊（可以只有自己）
4. 点击群聊右上角 → 群机器人 → 添加机器人
5. 获取Webhook URL（格式：`https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxxxxxx`）

### 注意事项
- Webhook URL需要妥善保管，不要泄露
- 机器人消息频率限制：20条/分钟
- 支持Markdown格式消息

## 2. Fork GitHub仓库

1. 访问GitHub上的项目仓库
2. 点击右上角 "Fork" 按钮
3. 等待Fork完成

## 3. 配置GitHub Secrets

在你的Fork仓库中：
1. 进入 Settings → Secrets and variables → Actions
2. 点击 "New repository secret"

添加以下Secrets：

### 必需配置
- `WECOM_WEBHOOK`: 你的企业微信机器人Webhook URL

### 可选配置
- `GITHUB_PAGES_URL`: 如果你部署了GitHub Pages，可以设置报告链接
  - 格式：`https://你的用户名.github.io/stock_push_platform`

## 4. 启用GitHub Actions

1. 进入 Actions 标签页
2. 点击 "I understand my workflows, go ahead and enable them"
3. 工作流将自动运行

## 5. 手动测试

### 方法1：通过GitHub Actions界面
1. 进入 Actions → "股票信息日报推送"
2. 点击 "Run workflow"
3. 选择分支（默认为main）
4. 点击 "Run workflow" 按钮

### 方法2：本地测试
```bash
# 克隆仓库
git clone https://github.com/你的用户名/stock_push_platform.git
cd stock_push_platform

# 安装依赖
pip install -r requirements.txt

# 测试Webhook连接
export WECOM_WEBHOOK="你的Webhook URL"
python -c "from wecom_notifier import WeComNotifier; n = WeComNotifier('$WECOM_WEBHOOK'); n.test_connection()"

# 生成测试报告（不推送）
python main.py --mode test --no-push

# 生成日报（不推送）
python main.py --mode daily --no-push

# 生成日报并推送
python main.py --mode daily
```

## 6. 定时任务说明

### 日报
- 运行时间：每天北京时间8:30（UTC 0:30）
- 可以修改 `.github/workflows/daily_stock_report.yml` 中的cron表达式调整时间

### 周报
- 需要手动触发或配置额外定时任务
- 可以通过GitHub Actions界面手动运行周报任务

## 7. 自定义配置

### 修改分析参数
编辑 `config.py`：
- `INDUSTRY_COUNT`: 分析的行业数量（默认5）
- `STOCKS_PER_INDUSTRY`: 每个行业推荐的股票数量（默认5）
- 权重配置：`IndustryWeights`, `StockWeights` 类

### 修改关键词
编辑 `config.py` 中的 `SentimentConfig` 类：
- `POSITIVE_WORDS`: 正向情感关键词
- `NEGATIVE_WORDS`: 负向情感关键词

## 8. 故障排除

### 常见问题

#### 1. 依赖安装失败
```bash
# 如果TA-LIB安装失败，可以跳过
pip install pandas-ta  # 替代TA-LIB
# 然后修改代码中的技术指标计算部分
```

#### 2. API限制
- 部分数据源可能有频率限制
- 如果遇到限制，可以增加延时或减少请求频率

#### 3. 推送失败
- 检查Webhook URL是否正确
- 检查网络连接
- 查看GitHub Actions日志

#### 4. 数据获取失败
- 检查网络连接
- 数据源API可能更新，需要调整代码
- 查看日志中的具体错误信息

## 9. 数据安全

### 注意事项
1. **不要**将Webhook URL提交到公开仓库
2. **不要**在代码中硬编码敏感信息
3. 使用GitHub Secrets管理敏感配置
4. 定期检查API使用情况

## 10. 更新和维护

### 定期更新
```bash
# 拉取最新代码
git pull origin main

# 更新依赖
pip install -r requirements.txt --upgrade
```

### 备份
- 定期备份 `reports/` 目录中的重要报告
- 可以考虑将报告推送到其他存储服务

---

## 后续优化建议

1. **数据源扩展**：添加更多数据源提高数据质量
2. **分析算法优化**：引入机器学习模型提高预测准确性
3. **推送渠道扩展**：支持微信个人号、Telegram、钉钉等
4. **监控告警**：添加运行状态监控和异常告警
5. **用户界面**：开发简单的Web界面查看历史报告

---

**重要提醒**：本平台仅供学习参考，不构成投资建议。股市有风险，投资需谨慎。