"""
Cyclone 设置模块

集中管理框架的所有配置项，支持多种自定义配置方式
"""

import os
import json
import importlib.util
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Callable


class Settings:
    """Cyclone框架设置类"""
    
    def __init__(self):
        self.load_defaults()
        self.load_from_env()
        self._custom_validators = {}
        self._config_hooks = []
    
    def load_defaults(self):
        """加载默认设置"""
        # 服务器配置
        self.DEBUG = True
        self.HOST = "127.0.0.1"
        self.PORT = 8000
        self.WORKERS = 1
        self.BACKLOG = 2048
        
        # 请求配置
        self.MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
        self.REQUEST_TIMEOUT = 30  # 30秒
        self.KEEP_ALIVE_TIMEOUT = 75  # 75秒
        
        # 数据库配置（MySQL）
        self.DATABASE = {
            'ENGINE': 'aiomysql',
            'NAME': 'cyclone',
            'USER': 'root',
            'PASSWORD': '',
            'HOST': 'localhost',
            'PORT': 3306,
            'POOL_SIZE': 10,
            'MAX_OVERFLOW': 20,
        }
        
        # 中间件配置
        self.MIDDLEWARE = [
            'cyclone.middleware.CORSMiddleware',
            'cyclone.middleware.SecurityMiddleware',
            'cyclone.middleware.RequestLoggingMiddleware',
        ]
        
        # 模板配置
        self.TEMPLATES = {
            'DIRS': ['templates'],
            'AUTO_RELOAD': True,
        }
        
        # 静态文件配置
        self.STATIC_URL = '/static/'
        self.STATIC_ROOT = 'static'
        
        # 安全配置
        self.SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
        self.ALLOWED_HOSTS = ['*']
        
        # 缓存配置
        self.CACHE = {
            'BACKEND': 'memory',
            'TIMEOUT': 300,
            'MAX_ENTRIES': 1000,
        }
        
        # 日志配置
        self.LOGGING = {
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
                    'formatter': 'simple',
                },
                'file': {
                    'class': 'logging.FileHandler',
                    'filename': 'cyclone.log',
                    'formatter': 'verbose',
                },
            },
            'loggers': {
                'cyclone': {
                    'handlers': ['console', 'file'],
                    'level': 'INFO',
                    'propagate': False,
                },
            },
        }
    
    def load_from_env(self):
        """从环境变量加载配置"""
        self.DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
        self.HOST = os.environ.get('HOST', self.HOST)
        self.PORT = int(os.environ.get('PORT', self.PORT))
        
        # 数据库配置
        if 'DATABASE_URL' in os.environ:
            self.DATABASE['URL'] = os.environ['DATABASE_URL']
        
        # 从环境变量更新数据库配置
        db_config_mapping = {
            'DATABASE_NAME': 'NAME',
            'DATABASE_USER': 'USER',
            'DATABASE_PASSWORD': 'PASSWORD',
            'DATABASE_HOST': 'HOST',
            'DATABASE_PORT': 'PORT',
        }
        
        for env_key, db_key in db_config_mapping.items():
            if env_key in os.environ:
                if db_key == 'PORT':
                    self.DATABASE[db_key] = int(os.environ[env_key])
                else:
                    self.DATABASE[db_key] = os.environ[env_key]
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return getattr(self, key, default)
    
    def set(self, key: str, value: Any, validate: bool = True):
        """设置配置项"""
        if validate and key in self._custom_validators:
            validator = self._custom_validators[key]
            if not validator(value):
                raise ValueError(f"配置项 {key} 的值 {value} 验证失败")
        
        setattr(self, key, value)
        
        # 执行配置钩子
        for hook in self._config_hooks:
            try:
                hook(key, value)
            except Exception as e:
                print(f"配置钩子执行失败: {e}")
    
    def update(self, **kwargs):
        """批量更新配置"""
        for key, value in kwargs.items():
            self.set(key, value)
    
    def update_dict(self, config_dict: Dict[str, Any], validate: bool = True):
        """从字典更新配置"""
        for key, value in config_dict.items():
            self.set(key, value, validate)
    
    def merge_dict_config(self, key: str, config_dict: Dict[str, Any]):
        """合并字典类型的配置"""
        if hasattr(self, key):
            existing_config = getattr(self, key)
            if isinstance(existing_config, dict):
                existing_config.update(config_dict)
            else:
                setattr(self, key, config_dict)
        else:
            setattr(self, key, config_dict)
    
    def add_validator(self, key: str, validator: Callable[[Any], bool]):
        """添加配置项验证器"""
        self._custom_validators[key] = validator
    
    def add_config_hook(self, hook: Callable[[str, Any], None]):
        """添加配置变更钩子"""
        self._config_hooks.append(hook)
    
    def get_database_url(self) -> str:
        """获取数据库连接URL"""
        if 'URL' in self.DATABASE:
            return self.DATABASE['URL']
        
        db_config = self.DATABASE
        return (
            f"{db_config['ENGINE']}://"
            f"{db_config['USER']}:{db_config['PASSWORD']}@"
            f"{db_config['HOST']}:{db_config['PORT']}/{db_config['NAME']}"
        )
    
    def is_debug(self) -> bool:
        """是否为调试模式"""
        return self.DEBUG
    
    def is_production(self) -> bool:
        """是否为生产模式"""
        return not self.DEBUG
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        config_dict = {}
        for attr_name in dir(self):
            if not attr_name.startswith('_') and not callable(getattr(self, attr_name)):
                config_dict[attr_name] = getattr(self, attr_name)
        return config_dict
    
    def validate_all(self) -> List[str]:
        """验证所有配置项，返回错误列表"""
        errors = []
        
        for key, validator in self._custom_validators.items():
            if hasattr(self, key):
                value = getattr(self, key)
                try:
                    if not validator(value):
                        errors.append(f"配置项 {key} 验证失败")
                except Exception as e:
                    errors.append(f"配置项 {key} 验证时出错: {e}")
        
        return errors


# 默认设置实例
default_settings = Settings()


def get_settings() -> Settings:
    """获取设置实例"""
    return default_settings


def configure(settings_module: str = None, **kwargs):
    """配置框架设置"""
    if settings_module:
        # 从模块加载设置
        import importlib
        module = importlib.import_module(settings_module)
        
        for attr_name in dir(module):
            if not attr_name.startswith('_'):
                attr_value = getattr(module, attr_name)
                setattr(default_settings, attr_name, attr_value)
    
    # 从关键字参数更新设置
    if kwargs:
        default_settings.update(**kwargs)


def load_settings_from_file(file_path: Union[str, Path], format: str = 'auto') -> Dict[str, Any]:
    """从文件加载配置
    
    Args:
        file_path: 配置文件路径
        format: 文件格式 ('py', 'json', 'yaml', 'auto')
    
    Returns:
        配置字典
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {file_path}")
    
    # 自动检测格式
    if format == 'auto':
        suffix = file_path.suffix.lower()
        if suffix == '.py':
            format = 'py'
        elif suffix == '.json':
            format = 'json'
        elif suffix in ['.yaml', '.yml']:
            format = 'yaml'
        else:
            raise ValueError(f"无法识别的配置文件格式: {suffix}")
    
    if format == 'py':
        return _load_python_config(file_path)
    elif format == 'json':
        return _load_json_config(file_path)
    elif format == 'yaml':
        return _load_yaml_config(file_path)
    else:
        raise ValueError(f"不支持的配置格式: {format}")


def _load_python_config(file_path: Path) -> Dict[str, Any]:
    """加载Python配置文件"""
    spec = importlib.util.spec_from_file_location("config", file_path)
    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)
    
    config_dict = {}
    for attr_name in dir(config_module):
        if not attr_name.startswith('_'):
            config_dict[attr_name] = getattr(config_module, attr_name)
    
    return config_dict


def _load_json_config(file_path: Path) -> Dict[str, Any]:
    """加载JSON配置文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _load_yaml_config(file_path: Path) -> Dict[str, Any]:
    """加载YAML配置文件"""
    try:
        import yaml
    except ImportError:
        raise ImportError("请安装PyYAML以支持YAML配置文件: pip install PyYAML")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def configure_from_file(file_path: Union[str, Path], format: str = 'auto', 
                       merge: bool = True, validate: bool = True):
    """从文件配置框架设置
    
    Args:
        file_path: 配置文件路径
        format: 文件格式
        merge: 是否合并字典类型的配置
        validate: 是否验证配置
    """
    config_dict = load_settings_from_file(file_path, format)
    
    if merge:
        # 智能合并配置
        for key, value in config_dict.items():
            if isinstance(value, dict) and hasattr(default_settings, key):
                existing_value = getattr(default_settings, key)
                if isinstance(existing_value, dict):
                    default_settings.merge_dict_config(key, value)
                    continue
            
            default_settings.set(key, value, validate)
    else:
        default_settings.update_dict(config_dict, validate)


def configure_from_dict(config_dict: Dict[str, Any], merge: bool = True, validate: bool = True):
    """从字典配置框架设置
    
    Args:
        config_dict: 配置字典
        merge: 是否合并字典类型的配置
        validate: 是否验证配置
    """
    if merge:
        for key, value in config_dict.items():
            if isinstance(value, dict) and hasattr(default_settings, key):
                existing_value = getattr(default_settings, key)
                if isinstance(existing_value, dict):
                    default_settings.merge_dict_config(key, value)
                    continue
            
            default_settings.set(key, value, validate)
    else:
        default_settings.update_dict(config_dict, validate)


def configure_from_object(config_object: Any, validate: bool = True):
    """从对象配置框架设置
    
    Args:
        config_object: 配置对象
        validate: 是否验证配置
    """
    for attr_name in dir(config_object):
        if not attr_name.startswith('_'):
            attr_value = getattr(config_object, attr_name)
            if not callable(attr_value):
                default_settings.set(attr_name, attr_value, validate)


def configure_database(engine: str = 'aiomysql', **db_config):
    """配置数据库设置
    
    Args:
        engine: 数据库引擎（目前仅支持aiomysql）
        **db_config: 数据库配置参数
    """
    if engine != 'aiomysql':
        raise ValueError("目前仅支持MySQL数据库 (aiomysql)")
    
    database_config = {
        'ENGINE': engine,
        **db_config
    }
    
    default_settings.merge_dict_config('DATABASE', database_config)


def add_middleware(middleware_class: str):
    """添加中间件到配置
    
    Args:
        middleware_class: 中间件类的完整路径
    """
    if middleware_class not in default_settings.MIDDLEWARE:
        default_settings.MIDDLEWARE.append(middleware_class)


def remove_middleware(middleware_class: str):
    """从配置中移除中间件
    
    Args:
        middleware_class: 中间件类的完整路径
    """
    if middleware_class in default_settings.MIDDLEWARE:
        default_settings.MIDDLEWARE.remove(middleware_class)


def create_custom_settings(**kwargs) -> Settings:
    """创建自定义设置实例
    
    Args:
        **kwargs: 自定义配置项
    
    Returns:
        新的设置实例
    """
    settings = Settings()
    settings.update(**kwargs)
    return settings


def validate_settings() -> List[str]:
    """验证当前设置，返回错误列表"""
    return default_settings.validate_all()


# 预定义的配置验证器
def port_validator(port: int) -> bool:
    """端口号验证器"""
    return isinstance(port, int) and 1 <= port <= 65535


def debug_validator(debug: bool) -> bool:
    """调试模式验证器"""
    return isinstance(debug, bool)


def host_validator(host: str) -> bool:
    """主机地址验证器"""
    return isinstance(host, str) and len(host) > 0


# 注册默认验证器
default_settings.add_validator('PORT', port_validator)
default_settings.add_validator('DEBUG', debug_validator)
default_settings.add_validator('HOST', host_validator) 