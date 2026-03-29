"""
日报任务入口 - 用于GitHub Actions定时执行
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import main

if __name__ == "__main__":
    # 设置命令行参数
    sys.argv = [sys.argv[0], "--mode", "daily"]
    
    # 运行主程序
    exit_code = main()
    sys.exit(exit_code)