#!/usr/bin/env python3
"""
Cyclone 发布助手脚本

自动化发布准备过程
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, check=True):
    """运行命令并打印输出"""
    print(f"🔧 执行: {cmd}")
    result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return result.returncode == 0

def check_prerequisites():
    """检查发布前提条件"""
    print("✅ 检查发布前提条件...")
    
    # 检查必需工具
    tools = [
        ('python', 'Python解释器'),
        ('git', 'Git版本控制'),
        ('pip', 'Python包管理器'),
    ]
    
    for tool, desc in tools:
        if not run_command(f"which {tool}", check=False):
            print(f"❌ 缺少工具: {tool} ({desc})")
            return False
    
    print("✅ 所有前提条件检查通过")
    return True

def run_tests():
    """运行测试"""
    print("\n🧪 运行测试...")
    if not run_command("python comprehensive_test.py --test-only"):
        print("❌ 测试失败")
        return False
    
    print("✅ 测试通过")
    return True

def install_build_tools():
    """安装构建工具"""
    print("\n📦 安装构建工具...")
    
    tools = ['build', 'twine', 'wheel']
    for tool in tools:
        print(f"安装 {tool}...")
        if not run_command(f"pip install {tool}"):
            print(f"❌ 安装 {tool} 失败")
            return False
    
    print("✅ 构建工具安装完成")
    return True

def build_package():
    """构建包"""
    print("\n📦 构建包...")
    
    # 清理旧的构建文件
    print("🧹 清理旧文件...")
    for pattern in ['build', 'dist', '*.egg-info']:
        for path in Path('.').glob(pattern):
            if path.is_dir():
                shutil.rmtree(path)
                print(f"  删除目录: {path}")
            else:
                path.unlink()
                print(f"  删除文件: {path}")
    
    # 构建
    if not run_command("python -m build"):
        print("❌ 构建失败")
        return False
    
    # 检查包
    if not run_command("python -m twine check dist/*"):
        print("❌ 包检查失败")
        return False
    
    print("✅ 包构建完成")
    return True

def show_package_info():
    """显示包信息"""
    print("\n📋 包信息:")
    
    dist_dir = Path('dist')
    if dist_dir.exists():
        for file in dist_dir.glob('*'):
            size = file.stat().st_size
            print(f"  📦 {file.name} ({size:,} bytes)")
    
    print("\n🔍 包内容预览:")
    if run_command("python -m tarfile -l dist/*.tar.gz | head -20", check=False):
        pass
    
    print("\n📊 包统计:")
    run_command("find cyclone -name '*.py' -exec wc -l {} + | tail -1", check=False)

def create_git_tag():
    """创建Git标签"""
    print("\n🏷️ 创建Git标签...")
    
    # 读取版本号
    sys.path.insert(0, '.')
    try:
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
        return True
        
    except ImportError:
        print("❌ 无法导入版本号")
        return False

def show_publishing_instructions():
    """显示发布说明"""
    print("\n" + "="*60)
    print("🚀 发布说明")
    print("="*60)
    
    print("\n📋 下一步操作:")
    print("1. 检查 dist/ 目录中的包文件")
    print("2. 上传到测试PyPI (可选):")
    print("   python -m twine upload --repository testpypi dist/*")
    print("3. 上传到正式PyPI:")
    print("   python -m twine upload dist/*")
    print("4. 推送Git标签:")
    print("   git push origin --tags")
    print("5. 在GitHub上创建Release")
    
    print("\n🔗 相关链接:")
    print("- PyPI: https://pypi.org/project/cyclone-web/")
    print("- 测试PyPI: https://test.pypi.org/project/cyclone-web/")
    print("- GitHub: https://github.com/jiaochanghao/Cyclone")
    
    print("\n📚 安装命令:")
    print("  pip install cyclone-web")
    print("  或从测试PyPI:")
    print("  pip install -i https://test.pypi.org/simple/ cyclone-web")

def main():
    """主函数"""
    print("🌪️ Cyclone 发布助手")
    print("=" * 50)
    
    try:
        # 检查前提条件
        if not check_prerequisites():
            sys.exit(1)
        
        # 运行测试
        if not run_tests():
            sys.exit(1)
        
        # 安装构建工具
        if not install_build_tools():
            sys.exit(1)
        
        # 构建包
        if not build_package():
            sys.exit(1)
        
        # 显示包信息
        show_package_info()
        
        # 创建Git标签
        create_git_tag()
        
        # 显示发布说明
        show_publishing_instructions()
        
        print("\n🎉 发布准备完成!")
        
    except KeyboardInterrupt:
        print("\n⏹️ 被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 