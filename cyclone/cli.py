#!/usr/bin/env python3
"""
Cyclone CLI 工具

提供命令行接口用于项目管理和开发工具
"""

import sys
import argparse
from . import __version__


def main():
    """CLI主入口函数"""
    parser = argparse.ArgumentParser(
        prog='cyclone',
        description='Cyclone 异步Web框架 CLI 工具'
    )
    
    parser.add_argument(
        '--version', 
        action='version', 
        version=f'Cyclone {__version__}'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 版本命令
    version_parser = subparsers.add_parser('version', help='显示版本信息')
    
    # 信息命令
    info_parser = subparsers.add_parser('info', help='显示框架信息')
    
    args = parser.parse_args()
    
    if args.command == 'version':
        print(f"Cyclone {__version__}")
        print("一个现代化的异步Web后端框架")
        
    elif args.command == 'info':
        print(f"🌪️ Cyclone 异步Web框架 v{__version__}")
        print()
        print("核心特性:")
        print("  ✅ 异步I/O处理")
        print("  ✅ MySQL数据库支持")
        print("  ✅ 强大的配置系统")
        print("  ✅ 中间件支持")
        print("  ✅ 类型安全")
        print()
        print("文档: https://github.com/jiaochanghao/Cyclone")
        print("问题反馈: https://github.com/jiaochanghao/Cyclone/issues")
        
    else:
        parser.print_help()


if __name__ == '__main__':
    main() 