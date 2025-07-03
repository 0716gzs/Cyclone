#!/usr/bin/env python3
"""
Cyclone 自定义配置系统使用示例

演示如何使用各种配置方式来自定义框架设置
"""

import os
from cyclone import (
    Application, get_settings, 
    configure_from_file, configure_from_dict, configure_from_object,
    configure_database, add_middleware, remove_middleware,
    create_custom_settings, validate_settings
)


def demo_basic_configuration():
    """演示基础配置功能"""
    print("=== 基础配置演示 ===")
    
    # 获取当前设置
    settings = get_settings()
    print(f"当前调试模式: {settings.DEBUG}")
    print(f"当前端口: {settings.PORT}")
    
    # 直接设置配置项
    settings.set('DEBUG', False)
    settings.set('PORT', 9000)
    print(f"修改后调试模式: {settings.DEBUG}")
    print(f"修改后端口: {settings.PORT}")
    
    # 批量更新配置
    settings.update(
        HOST='0.0.0.0',
        WORKERS=4,
        MAX_REQUEST_SIZE=20 * 1024 * 1024  # 20MB
    )
    print(f"批量更新后主机: {settings.HOST}")
    print(f"批量更新后工作进程数: {settings.WORKERS}")


def demo_file_configuration():
    """演示从文件加载配置"""
    print("\n=== 文件配置演示 ===")
    
    try:
        # 从Python文件加载配置
        configure_from_file('config_examples/development.py')
        settings = get_settings()
        print(f"从Python文件加载 - 数据库名: {settings.DATABASE['NAME']}")
        print(f"从Python文件加载 - API限制: {settings.API_RATE_LIMIT}")
        
        # 从JSON文件加载配置
        configure_from_file('config_examples/production.json')
        print(f"从JSON文件加载 - 生产环境调试模式: {settings.DEBUG}")
        print(f"从JSON文件加载 - 允许的主机: {settings.ALLOWED_HOSTS}")
        
    except FileNotFoundError as e:
        print(f"配置文件未找到: {e}")
    except Exception as e:
        print(f"加载配置时出错: {e}")


def demo_dict_configuration():
    """演示从字典加载配置"""
    print("\n=== 字典配置演示 ===")
    
    # 自定义配置字典
    custom_config = {
        'DEBUG': True,
        'PORT': 8080,
        'DATABASE': {
            'NAME': 'my_custom_db',
            'POOL_SIZE': 15,
        },
        'CUSTOM_API_KEY': 'your-api-key-here',
        'FEATURE_FLAGS': {
            'ENABLE_CACHE': True,
            'ENABLE_COMPRESSION': False,
        }
    }
    
    # 使用合并模式加载配置
    configure_from_dict(custom_config, merge=True)
    
    settings = get_settings()
    print(f"字典配置 - 端口: {settings.PORT}")
    print(f"字典配置 - 数据库名: {settings.DATABASE['NAME']}")
    print(f"字典配置 - 自定义API密钥: {settings.CUSTOM_API_KEY}")
    print(f"字典配置 - 功能标志: {settings.FEATURE_FLAGS}")


def demo_object_configuration():
    """演示从对象加载配置"""
    print("\n=== 对象配置演示 ===")
    
    class CustomConfig:
        """自定义配置类"""
        DEBUG = False
        HOST = '127.0.0.1'
        PORT = 7000
        
        # 自定义配置项
        APP_NAME = 'My Cyclone App'
        VERSION = '1.0.0'
        AUTHOR = 'Developer'
        
        # 功能开关
        ENABLE_MONITORING = True
        ENABLE_METRICS = True
    
    # 从配置对象加载
    config_obj = CustomConfig()
    configure_from_object(config_obj)
    
    settings = get_settings()
    print(f"对象配置 - 应用名称: {settings.APP_NAME}")
    print(f"对象配置 - 版本: {settings.VERSION}")
    print(f"对象配置 - 作者: {settings.AUTHOR}")
    print(f"对象配置 - 启用监控: {settings.ENABLE_MONITORING}")


def demo_database_configuration():
    """演示数据库配置"""
    print("\n=== 数据库配置演示 ===")
    
    # 配置数据库连接
    configure_database(
        engine='aiomysql',
        NAME='my_app_db',
        USER='app_user',
        PASSWORD='app_password',
        HOST='db.myapp.com',
        PORT=3306,
        POOL_SIZE=25,
        MAX_OVERFLOW=50
    )
    
    settings = get_settings()
    print(f"数据库配置 - 引擎: {settings.DATABASE['ENGINE']}")
    print(f"数据库配置 - 名称: {settings.DATABASE['NAME']}")
    print(f"数据库配置 - 主机: {settings.DATABASE['HOST']}")
    print(f"数据库配置 - 连接池大小: {settings.DATABASE['POOL_SIZE']}")


def demo_middleware_configuration():
    """演示中间件配置"""
    print("\n=== 中间件配置演示 ===")
    
    settings = get_settings()
    print("当前中间件:")
    for middleware in settings.MIDDLEWARE:
        print(f"  - {middleware}")
    
    # 添加自定义中间件
    add_middleware('myapp.middleware.CustomAuthMiddleware')
    add_middleware('myapp.middleware.MetricsMiddleware')
    
    print("\n添加自定义中间件后:")
    for middleware in settings.MIDDLEWARE:
        print(f"  - {middleware}")
    
    # 移除某个中间件
    remove_middleware('cyclone.middleware.SecurityMiddleware')
    
    print("\n移除安全中间件后:")
    for middleware in settings.MIDDLEWARE:
        print(f"  - {middleware}")


def demo_validation():
    """演示配置验证"""
    print("\n=== 配置验证演示 ===")
    
    settings = get_settings()
    
    # 添加自定义验证器
    def api_key_validator(api_key):
        """API密钥验证器"""
        return isinstance(api_key, str) and len(api_key) >= 10
    
    def version_validator(version):
        """版本号验证器"""
        return isinstance(version, str) and '.' in version
    
    settings.add_validator('CUSTOM_API_KEY', api_key_validator)
    settings.add_validator('VERSION', version_validator)
    
    # 验证所有配置
    errors = validate_settings()
    if errors:
        print("配置验证错误:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("所有配置验证通过！")
    
    # 测试验证器
    try:
        settings.set('CUSTOM_API_KEY', 'short')  # 应该失败
    except ValueError as e:
        print(f"验证器工作正常: {e}")
    
    settings.set('CUSTOM_API_KEY', 'this-is-a-long-enough-api-key')  # 应该成功
    print("API密钥设置成功")


def demo_config_hooks():
    """演示配置钩子"""
    print("\n=== 配置钩子演示 ===")
    
    settings = get_settings()
    
    # 添加配置变更钩子
    def config_change_logger(key, value):
        """配置变更日志钩子"""
        print(f"配置变更: {key} = {value}")
    
    def port_change_handler(key, value):
        """端口变更处理钩子"""
        if key == 'PORT' and value < 1024:
            print(f"警告: 端口 {value} 需要管理员权限")
    
    settings.add_config_hook(config_change_logger)
    settings.add_config_hook(port_change_handler)
    
    # 测试钩子
    settings.set('PORT', 80)
    settings.set('DEBUG', True)
    settings.set('APP_NAME', 'Test App')


def demo_custom_settings_instance():
    """演示创建自定义设置实例"""
    print("\n=== 自定义设置实例演示 ===")
    
    # 创建专用于API服务的配置
    api_settings = create_custom_settings(
        DEBUG=False,
        PORT=8001,
        APP_NAME='API Service',
        API_VERSION='v1',
        ENABLE_DOCS=True,
        MAX_CONNECTIONS=1000
    )
    
    print(f"API服务配置 - 名称: {api_settings.APP_NAME}")
    print(f"API服务配置 - 版本: {api_settings.API_VERSION}")
    print(f"API服务配置 - 端口: {api_settings.PORT}")
    print(f"API服务配置 - 启用文档: {api_settings.ENABLE_DOCS}")
    
    # 创建应用实例时使用自定义配置
    api_app = Application(api_settings)
    print("使用自定义配置创建API应用成功")


def main():
    """主演示函数"""
    print("🌪️ Cyclone 自定义配置系统演示\n")
    
    # 按顺序演示各种配置功能
    demo_basic_configuration()
    demo_file_configuration()
    demo_dict_configuration()
    demo_object_configuration()
    demo_database_configuration()
    demo_middleware_configuration()
    demo_validation()
    demo_config_hooks()
    demo_custom_settings_instance()
    
    print("\n✅ 所有配置演示完成！")
    print("\n📚 配置文件示例:")
    print("  - config_examples/development.py (Python配置)")
    print("  - config_examples/production.json (JSON配置)")
    
    print("\n🚀 使用建议:")
    print("  1. 开发环境使用Python配置文件")
    print("  2. 生产环境使用JSON/YAML配置文件")
    print("  3. 使用环境变量覆盖敏感配置")
    print("  4. 添加配置验证器确保配置正确")
    print("  5. 使用配置钩子实现配置变更响应")


if __name__ == "__main__":
    main() 