# 🔧 Cyclone 自定义配置系统指南

Cyclone框架提供了强大而灵活的配置系统，支持多种配置方式，让你可以轻松地自定义框架设置。

## ✨ 功能特性

- 🔄 **多种配置方式** - 支持Python文件、JSON、YAML、字典、对象等配置方式
- ✅ **配置验证** - 自定义验证器确保配置正确性
- 🎣 **配置钩子** - 配置变更时自动执行回调函数
- 🔗 **智能合并** - 字典类型配置智能合并，避免覆盖
- 📁 **环境隔离** - 支持不同环境的配置文件
- 🛡️ **类型安全** - 完整的类型注解支持

## 🚀 基础使用

### 1. 获取和设置配置

```python
from cyclone import get_settings

# 获取当前设置
settings = get_settings()

# 直接设置配置项
settings.set('DEBUG', False)
settings.set('PORT', 9000)

# 批量更新配置
settings.update(
    HOST='0.0.0.0',
    WORKERS=4,
    MAX_REQUEST_SIZE=20 * 1024 * 1024
)
```

### 2. 从文件加载配置

#### Python配置文件 (`config/development.py`)

```python
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
}

# 自定义配置项
API_RATE_LIMIT = 1000
ENABLE_DEBUG_TOOLBAR = True
```

#### JSON配置文件 (`config/production.json`)

```json
{
  "DEBUG": false,
  "HOST": "0.0.0.0",
  "PORT": 80,
  "DATABASE": {
    "ENGINE": "aiomysql",
    "NAME": "cyclone_prod",
    "USER": "cyclone_user",
    "PASSWORD": "secure_password",
    "HOST": "db.example.com",
    "PORT": 3306
  },
  "API_RATE_LIMIT": 100,
  "ENABLE_DEBUG_TOOLBAR": false
}
```

#### 加载配置文件

```python
from cyclone import configure_from_file

# 自动检测文件格式
configure_from_file('config/development.py')
configure_from_file('config/production.json')

# 指定文件格式
configure_from_file('config/app.yaml', format='yaml')
```

### 3. 从字典加载配置

```python
from cyclone import configure_from_dict

custom_config = {
    'DEBUG': True,
    'PORT': 8080,
    'DATABASE': {
        'NAME': 'my_custom_db',
        'POOL_SIZE': 15,
    },
    'FEATURE_FLAGS': {
        'ENABLE_CACHE': True,
        'ENABLE_COMPRESSION': False,
    }
}

# 使用合并模式（推荐）
configure_from_dict(custom_config, merge=True)
```

### 4. 从配置对象加载

```python
from cyclone import configure_from_object

class AppConfig:
    DEBUG = False
    PORT = 8000
    APP_NAME = 'My App'
    VERSION = '1.0.0'
    
    # 功能开关
    ENABLE_MONITORING = True
    ENABLE_METRICS = True

configure_from_object(AppConfig())
```

## 🔧 高级功能

### 1. 数据库配置

```python
from cyclone import configure_database

# 直接配置数据库
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
```

### 2. 中间件管理

```python
from cyclone import add_middleware, remove_middleware

# 添加自定义中间件
add_middleware('myapp.middleware.CustomAuthMiddleware')
add_middleware('myapp.middleware.MetricsMiddleware')

# 移除中间件
remove_middleware('cyclone.middleware.SecurityMiddleware')
```

### 3. 配置验证

```python
from cyclone import get_settings, validate_settings

settings = get_settings()

# 添加自定义验证器
def api_key_validator(api_key):
    return isinstance(api_key, str) and len(api_key) >= 10

def port_validator(port):
    return isinstance(port, int) and 1 <= port <= 65535

settings.add_validator('API_KEY', api_key_validator)
settings.add_validator('PORT', port_validator)

# 验证所有配置
errors = validate_settings()
if errors:
    for error in errors:
        print(f"配置错误: {error}")
```

### 4. 配置变更钩子

```python
from cyclone import get_settings

settings = get_settings()

# 添加配置变更钩子
def config_change_logger(key, value):
    print(f"配置变更: {key} = {value}")

def security_check(key, value):
    if key == 'DEBUG' and value and not settings.is_debug():
        print("警告: 生产环境不应启用DEBUG模式")

settings.add_config_hook(config_change_logger)
settings.add_config_hook(security_check)
```

### 5. 创建自定义配置实例

```python
from cyclone import create_custom_settings, Application

# 创建API服务专用配置
api_settings = create_custom_settings(
    DEBUG=False,
    PORT=8001,
    APP_NAME='API Service',
    API_VERSION='v1',
    ENABLE_DOCS=True
)

# 使用自定义配置创建应用
api_app = Application(api_settings)
```

## 📁 推荐的项目结构

```
myproject/
├── app.py                      # 主应用文件
├── config/                     # 配置文件目录
│   ├── __init__.py
│   ├── base.py                 # 基础配置
│   ├── development.py          # 开发环境配置
│   ├── production.json         # 生产环境配置
│   └── testing.py             # 测试环境配置
├── myapp/                      # 应用代码
│   ├── __init__.py
│   ├── views.py
│   ├── models.py
│   └── middleware.py
└── requirements.txt
```

### 基础配置 (`config/base.py`)

```python
# 基础配置，所有环境共享
import os

# 项目基础信息
PROJECT_NAME = 'My Cyclone App'
VERSION = '1.0.0'

# 数据库基础配置
DATABASE = {
    'ENGINE': 'aiomysql',
    'POOL_SIZE': 10,
    'MAX_OVERFLOW': 20,
}

# 中间件配置
MIDDLEWARE = [
    'cyclone.middleware.CORSMiddleware',
    'cyclone.middleware.SecurityMiddleware',
    'cyclone.middleware.RequestLoggingMiddleware',
]

# 静态文件配置
STATIC_URL = '/static/'
STATIC_ROOT = 'static'

# 模板配置
TEMPLATES = {
    'DIRS': ['templates'],
    'AUTO_RELOAD': True,
}
```

### 开发环境配置 (`config/development.py`)

```python
from .base import *

# 开发环境特定配置
DEBUG = True
HOST = "127.0.0.1"
PORT = 8000

# 开发数据库
DATABASE.update({
    'NAME': 'myapp_dev',
    'USER': 'root',
    'PASSWORD': '',
    'HOST': 'localhost',
    'PORT': 3306,
})

# 开发环境中间件
MIDDLEWARE.append('myapp.middleware.DebugMiddleware')

# 开发环境特定配置
SECRET_KEY = 'dev-secret-key'
ALLOWED_HOSTS = ['*']
```

## 🎯 最佳实践

### 1. 环境配置管理

```python
import os
from cyclone import configure_from_file

# 根据环境变量选择配置文件
environment = os.environ.get('CYCLONE_ENV', 'development')
config_file = f'config/{environment}.py'

try:
    configure_from_file(config_file)
    print(f"已加载 {environment} 环境配置")
except FileNotFoundError:
    print(f"警告: 配置文件 {config_file} 不存在，使用默认配置")
```

### 2. 敏感配置处理

```python
import os
from cyclone import get_settings

settings = get_settings()

# 从环境变量获取敏感信息
settings.set('SECRET_KEY', os.environ.get('SECRET_KEY', 'default-key'))
settings.set('DATABASE', {
    **settings.DATABASE,
    'PASSWORD': os.environ.get('DB_PASSWORD', '')
})
```

### 3. 配置验证和检查

```python
from cyclone import get_settings, validate_settings

def validate_production_config():
    """验证生产环境配置"""
    settings = get_settings()
    
    if settings.is_production():
        assert not settings.DEBUG, "生产环境不能启用DEBUG模式"
        assert settings.SECRET_KEY != 'default-key', "生产环境必须设置自定义SECRET_KEY"
        assert settings.DATABASE.get('PASSWORD'), "生产环境必须设置数据库密码"
    
    # 验证配置项
    errors = validate_settings()
    if errors:
        raise ValueError(f"配置验证失败: {errors}")

# 应用启动时验证配置
validate_production_config()
```

## 🔍 故障排除

### 1. 配置文件找不到

```python
import os
from cyclone import configure_from_file

config_file = 'config/production.py'
if not os.path.exists(config_file):
    print(f"错误: 配置文件 {config_file} 不存在")
    # 处理错误或使用默认配置
```

### 2. 配置验证失败

```python
from cyclone import validate_settings

try:
    errors = validate_settings()
    if errors:
        print("配置验证错误:")
        for error in errors:
            print(f"  - {error}")
except Exception as e:
    print(f"配置验证异常: {e}")
```

### 3. 配置合并问题

```python
from cyclone import configure_from_dict

# 如果不想合并字典配置，使用 merge=False
configure_from_dict(config_dict, merge=False)

# 或者手动合并特定配置
settings = get_settings()
settings.merge_dict_config('DATABASE', new_db_config)
```

## 📚 完整示例

查看 `custom_config_example.py` 文件了解所有功能的完整演示。

运行示例：

```bash
python custom_config_example.py
```

## 🎉 总结

Cyclone的自定义配置系统为你提供了强大而灵活的配置管理能力：

- ✅ **多种配置源** - 文件、字典、对象、环境变量
- ✅ **智能合并** - 避免配置覆盖问题
- ✅ **配置验证** - 确保配置正确性
- ✅ **变更监听** - 配置变更时自动响应
- ✅ **类型安全** - 完整的类型支持
- ✅ **环境隔离** - 支持多环境配置

这个配置系统让你可以轻松管理复杂的应用配置，提高开发效率和应用的可维护性。 