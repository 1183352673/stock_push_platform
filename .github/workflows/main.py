"""
主程序 - 股票信息推送平台
"""

import argparse
import logging
import sys
import os
from datetime import datetime

from config import Config, create_directories
from report_generator import ReportGenerator
from wecom_notifier import WeComNotifier

# 配置日志
def setup_logging():
    """配置日志"""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"stock_platform_{Config.CURRENT_DATE}.log")
    
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='股票信息推送平台')
    parser.add_argument('--mode', choices=['daily', 'weekly', 'test'], 
                       default='daily', help='运行模式')
    parser.add_argument('--no-push', action='store_true', 
                       help='不推送消息，仅生成报告')
    parser.add_argument('--test-webhook', action='store_true',
                       help='测试企业微信Webhook连接')
    parser.add_argument('--industry-count', type=int, default=Config.INDUSTRY_COUNT,
                       help='分析的行业数量')
    parser.add_argument('--stocks-per-industry', type=int, 
                       default=Config.STOCKS_PER_INDUSTRY,
                       help='每个行业推荐的股票数量')
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # 创建目录
    create_directories()
    
    logger.info(f"股票信息推送平台启动 - 模式: {args.mode}")
    logger.info(f"当前日期: {Config.CURRENT_DATE}")
    logger.info(f"行业数量: {args.industry_count}, 每行业股票数: {args.stocks_per_industry}")
    
    # 更新配置
    Config.INDUSTRY_COUNT = args.industry_count
    Config.STOCKS_PER_INDUSTRY = args.stocks_per_industry
    
    try:
        # 测试Webhook连接
        if args.test_webhook:
            logger.info("测试企业微信Webhook连接...")
            notifier = WeComNotifier()
            if notifier.test_connection():
                logger.info("Webhook连接测试成功")
                return 0
            else:
                logger.error("Webhook连接测试失败")
                return 1
        
        # 创建报告生成器
        generator = ReportGenerator()
        
        # 创建通知器
        notifier = WeComNotifier()
        
        # 根据模式运行
        if args.mode == 'daily':
            logger.info("开始生成日报...")
            report_data = generator.generate_daily_report()
            
            if not args.no_push:
                logger.info("推送日报到企业微信...")
                success = notifier.send_daily_report(report_data)
                if success:
                    logger.info("日报推送成功")
                else:
                    logger.error("日报推送失败")
            else:
                logger.info("跳过推送（--no-push 模式）")
            
            # 输出摘要
            _print_report_summary(report_data, '日报')
            
        elif args.mode == 'weekly':
            logger.info("开始生成周报...")
            report_data = generator.generate_weekly_report()
            
            if not args.no_push:
                logger.info("推送周报到企业微信...")
                success = notifier.send_weekly_report(report_data)
                if success:
                    logger.info("周报推送成功")
                else:
                    logger.error("周报推送失败")
            else:
                logger.info("跳过推送（--no-push 模式）")
            
            # 输出摘要
            _print_report_summary(report_data, '周报')
            
        elif args.mode == 'test':
            logger.info("测试模式 - 生成示例报告...")
            
            # 生成测试数据
            test_report = {
                'report_date': Config.CURRENT_DATE,
                'report_type': 'test',
                'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'summary': '测试报告生成成功',
                'top_industries': [
                    {
                        'industry_name': '测试行业1',
                        'total_score': 0.85,
                        'recommendation_reason': '测试原因1'
                    },
                    {
                        'industry_name': '测试行业2', 
                        'total_score': 0.75,
                        'recommendation_reason': '测试原因2'
                    }
                ]
            }
            
            if not args.no_push:
                logger.info("发送测试消息...")
                success = notifier.send_custom_message(
                    title="测试报告",
                    content="股票信息推送平台测试运行成功。",
                    report_url=f"{Config.GITHUB_PAGES_URL}/test"
                )
                if success:
                    logger.info("测试消息发送成功")
                else:
                    logger.error("测试消息发送失败")
            
            _print_report_summary(test_report, '测试报告')
        
        logger.info("程序执行完成")
        return 0
        
    except Exception as e:
        logger.error(f"程序执行失败: {e}", exc_info=True)
        
        # 尝试发送错误通知
        try:
            if not args.no_push:
                notifier = WeComNotifier()
                notifier.send_custom_message(
                    title="程序执行错误",
                    content=f"股票信息推送平台执行失败:\n\n{str(e)[:200]}",
                    report_url=""
                )
        except:
            pass
        
        return 1

def _print_report_summary(report_data: dict, report_type: str):
    """打印报告摘要"""
    print(f"\n{'='*60}")
    print(f"{report_type}摘要")
    print(f"{'='*60}")
    
    print(f"报告日期: {report_data.get('report_date', 'N/A')}")
    print(f"生成时间: {report_data.get('generated_at', 'N/A')}")
    print(f"报告类型: {report_data.get('report_type', 'N/A')}")
    
    if 'summary' in report_data and report_data['summary']:
        print(f"\n摘要: {report_data['summary']}")
    
    if 'top_industries' in report_data and report_data['top_industries']:
        print(f"\n行业分析 ({len(report_data['top_industries'])} 个):")
        for i, industry in enumerate(report_data['top_industries'][:3], 1):
            print(f"  {i}. {industry.get('industry_name', 'N/A')} - "
                  f"评分: {industry.get('total_score', 0):.2f}")
    
    if 'stock_recommendations' in report_data and report_data['stock_recommendations']:
        print(f"\n股票推荐 ({len(report_data['stock_recommendations'])} 只):")
        for i, stock in enumerate(report_data['stock_recommendations'][:3], 1):
            print(f"  {i}. {stock.get('stock_name', 'N/A')} - "
                  f"评分: {stock.get('total_score', 0):.2f} - "
                  f"建议: {stock.get('trading_advice', {}).get('action', 'N/A')}")
    
    print(f"\n{'='*60}")

if __name__ == "__main__":
    sys.exit(main())