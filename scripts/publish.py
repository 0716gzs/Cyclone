#!/usr/bin/env python3
"""
Cyclone 发布脚本

自动化发布到 PyPI 的过程
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(cmd, check=True):
    """运行命令并打印输出"""
    print(f"🔧 执行: {cmd}")
    result = subprocess.run(cmd, shell=True, check=check)
    return result.returncode == 0


def clean_build():
    """清理构建文件"""
    print("🧹 清理构建文件...")
    
    dirs_to_clean = ['build', 'dist', '*.egg-info']
    for pattern in dirs_to_clean:
        for path in Path('.').glob(pattern):
            if path.is_dir():
                shutil.rmtree(path)
                print(f"  ✅ 删除目录: {path}")
            else:
                path.unlink()
                print(f"  ✅ 删除文件: {path}")


def check_prerequisites():
    """检查发布前提条件"""
    print("✅ 检查发布前提条件...")
    
    # 检查必需工具
    tools = ['twine', 'build']
    for tool in tools:
        if not run_command(f"python -m {tool} --help > /dev/null 2>&1", check=False):
            print(f"❌ 缺少工具: {tool}")
            print(f"请安装: pip install {tool}")
            return False
    
    # 检查是否在git仓库中
    if not Path('.git').exists():
        print("❌ 不在git仓库中")
        return False
    
    # 检查是否有未提交的更改
    result = subprocess.run(['git', 'status', '--porcelain'], 
                          capture_output=True, text=True)
    if result.stdout.strip():
        print("❌ 有未提交的更改:")
        print(result.stdout)
        print("请先提交所有更改")
        return False
    
    print("✅ 所有前提条件检查通过")
    return True


def build_package():
    """构建包"""
    print("📦 构建包...")
    
    # 使用build模块构建
    if not run_command("python -m build"):
        print("❌ 构建失败")
        return False
    
    print("✅ 构建完成")
    return True


def check_package():
    """检查包的完整性"""
    print("🔍 检查包完整性...")
    
    # 使用twine检查
    if not run_command("python -m twine check dist/*"):
        print("❌ 包检查失败")
        return False
    
    print("✅ 包检查通过")
    return True


def upload_to_testpypi():
    """上传到测试PyPI"""
    print("🧪 上传到测试PyPI...")
    
    cmd = "python -m twine upload --repository testpypi dist/*"
    if not run_command(cmd, check=False):
        print("❌ 上传到测试PyPI失败")
        return False
    
    print("✅ 上传到测试PyPI成功")
    return True


def upload_to_pypi():
    """上传到正式PyPI"""
    print("🚀 上传到正式PyPI...")
    
    response = input("确认上传到正式PyPI? (y/N): ")
    if response.lower() != 'y':
        print("⏹️ 取消上传")
        return False
    
    cmd = "python -m twine upload dist/*"
    if not run_command(cmd, check=False):
        print("❌ 上传到正式PyPI失败")
        return False
    
    print("✅ 上传到正式PyPI成功")
    return True


def create_git_tag():
    """创建Git标签"""
    print("🏷️ 创建Git标签...")
    
    # 读取版本号
    sys.path.insert(0, '.')
    from cyclone import __version__
    
    tag = f"v{__version__}"
    
    # 检查标签是否已存在
    result = subprocess.run(['git', 'tag', '-l', tag], 
                          capture_output=True, text=True)
    if result.stdout.strip():
        print(f"⚠️ 标签 {tag} 已存在")
        return True
    
    # 创建标签
    if not run_command(f"git tag {tag}"):
        print("❌ 创建标签失败")
        return False
    
    print(f"✅ 创建标签: {tag}")
    
    # 推送标签
    response = input("推送标签到远程仓库? (y/N): ")
    if response.lower() == 'y':
        if run_command(f"git push origin {tag}"):
            print("✅ 标签已推送到远程仓库")
        else:
            print("❌ 推送标签失败")
    
    return True


def main():
    """主函数"""
    print("🌪️ Cyclone 发布脚本")
    print("=" * 50)
    
    # 检查前提条件
    if not check_prerequisites():
        sys.exit(1)
    
    # 清理构建文件
    clean_build()
    
    # 构建包
    if not build_package():
        sys.exit(1)
    
    # 检查包
    if not check_package():
        sys.exit(1)
    
    # 询问发布选项
    print("\n📋 发布选项:")
    print("1. 只上传到测试PyPI")
    print("2. 上传到测试PyPI + 正式PyPI")
    print("3. 只上传到正式PyPI")
    print("4. 只构建，不上传")
    
    choice = input("请选择 (1-4): ")
    
    if choice == "1":
        upload_to_testpypi()
    elif choice == "2":
        if upload_to_testpypi():
            upload_to_pypi()
    elif choice == "3":
        upload_to_pypi()
    elif choice == "4":
        print("✅ 只构建，不上传")
    else:
        print("❌ 无效选择")
        sys.exit(1)
    
    # 创建Git标签
    create_git_tag()
    
    print("\n🎉 发布完成!")
    print("📚 使用说明:")
    print("  pip install cyclone-web")
    print("  或从测试PyPI安装:")
    print("  pip install -i https://test.pypi.org/simple/ cyclone-web")


if __name__ == "__main__":
    main() 