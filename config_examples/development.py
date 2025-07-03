'''
Author: jiaochanghao jch_2154195820@163.com
Date: 2025-07-03 11:15:04
LastEditors: jiaochanghao jch_2154195820@163.com
LastEditTime: 2025-07-03 11:18:46
FilePath: /Cyclone/config_examples/development.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
# -*- coding: utf-8 -*-
"""
开发环境配置示例
"""

# 基础设置
DEBUG = True
HOST = "127.0.0.1"
PORT = 8000

# 数据库配置
DATABASE = {
    'ENGINE': 'aiomysql',
    'NAME': 'cyclone_dev',
    'USER': 'root',
    'PASSWORD': 'dev_password',
    'HOST': 'localhost',
    'PORT': 3306,
    'POOL_SIZE': 5,
    'MAX_OVERFLOW': 10,
}

# 或使用URL配置
# DATABASE = {
#     'URL': 'mysql://root:dev_password@localhost:3306/cyclone_dev'
# }

# 中间件配置
MIDDLEWARE = [
    'cyclone.middleware.CORSMiddleware',
    'cyclone.middleware.SecurityMiddleware',
    'cyclone.middleware.RequestLoggingMiddleware',
    'myapp.middleware.DevMiddleware',  # 自定义开发中间件
]

# 静态文件配置
STATIC_URL = '/static/'
STATIC_ROOT = 'static'

# 模板配置
TEMPLATES = {
    'DIRS': ['templates', 'dev_templates'],
    'AUTO_RELOAD': True,
}

# 缓存配置（开发环境使用内存缓存）
CACHE = {
    'BACKEND': 'memory',
    'TIMEOUT': 60,  # 短超时时间便于测试
    'MAX_ENTRIES': 100,
}

# 安全配置
SECRET_KEY = 'dev-secret-key-please-change-in-production'
ALLOWED_HOSTS = ['*']

# 日志配置
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'cyclone': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# 自定义配置项
API_RATE_LIMIT = 1000  # 开发环境高限制
EMAIL_BACKEND = 'console'  # 开发环境使用控制台输出
ENABLE_DEBUG_TOOLBAR = True 