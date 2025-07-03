"""
Cyclone 请求模块

封装HTTP请求的所有信息
"""

import json
import urllib.parse
from typing import Dict, Any, Optional, Union, List
from .utils import (
    parse_query_string, 
    parse_multipart_form_data, 
    parse_json_body, 
    parse_form_data,
    parse_content_type,
    get_client_ip
)


class Request:
    """HTTP请求对象"""
    
    def __init__(self, method: str, path: str, query_string: str = "", 
                 headers: Optional[Dict[str, str]] = None, 
                 body: bytes = b"", version: str = "1.1"):
        self.method = method.upper()
        self.path = path
        self.query_string = query_string
        self.headers = headers or {}
        self.body = body
        self.version = version
        
        # 解析URL
        self.url = self._parse_url()
        
        # 解析查询参数
        self.query_params = parse_query_string(query_string)
        
        # 解析请求体
        self._form_data = None
        self._json_data = None
        self._files = None
        
        # 路由参数（由路由器设置）
        self.route_params = {}
        
        # 中间件可以设置的额外属性
        self.user = None
        self.session = None
        self.extras = {}
    
    def _parse_url(self) -> str:
        """解析完整URL"""
        if self.query_string:
            return f"{self.path}?{self.query_string}"
        return self.path
    
    @property
    def content_type(self) -> str:
        """获取Content-Type"""
        return self.headers.get('content-type', 'text/plain')
    
    @property
    def content_length(self) -> int:
        """获取Content-Length"""
        return int(self.headers.get('content-length', 0))
    
    @property
    def client_ip(self) -> str:
        """获取客户端IP地址"""
        return get_client_ip(self.headers)
    
    @property
    def user_agent(self) -> str:
        """获取User-Agent"""
        return self.headers.get('user-agent', '')
    
    @property
    def host(self) -> str:
        """获取Host头部"""
        return self.headers.get('host', '')
    
    @property
    def is_ajax(self) -> bool:
        """是否为AJAX请求"""
        return self.headers.get('x-requested-with', '').lower() == 'xmlhttprequest'
    
    @property
    def is_secure(self) -> bool:
        """是否为HTTPS请求"""
        return (
            self.headers.get('x-forwarded-proto', '').lower() == 'https' or
            self.headers.get('x-forwarded-ssl', '').lower() == 'on'
        )
    
    def get_header(self, name: str, default: str = None) -> Optional[str]:
        """获取指定头部"""
        return self.headers.get(name.lower(), default)
    
    def get_query_param(self, name: str, default: str = None) -> Optional[str]:
        """获取查询参数"""
        return self.query_params.get(name, default)
    
    def get_route_param(self, name: str, default: Any = None) -> Any:
        """获取路由参数"""
        return self.route_params.get(name, default)
    
    async def json(self) -> Dict[str, Any]:
        """解析JSON请求体"""
        if self._json_data is None:
            content_type, _ = parse_content_type(self.content_type)
            if content_type == 'application/json':
                self._json_data = parse_json_body(self.body)
            else:
                self._json_data = {}
        return self._json_data
    
    async def form(self) -> Dict[str, str]:
        """解析表单数据"""
        if self._form_data is None:
            content_type, params = parse_content_type(self.content_type)
            
            if content_type == 'application/x-www-form-urlencoded':
                self._form_data = parse_form_data(self.body)
            elif content_type == 'multipart/form-data':
                boundary = params.get('boundary')
                if boundary:
                    multipart_data = parse_multipart_form_data(self.body, boundary)
                    self._form_data = {
                        k: v.decode('utf-8') if isinstance(v, bytes) else v
                        for k, v in multipart_data.items()
                    }
                else:
                    self._form_data = {}
            else:
                self._form_data = {}
        
        return self._form_data
    
    async def files(self) -> Dict[str, bytes]:
        """解析文件上传"""
        if self._files is None:
            content_type, params = parse_content_type(self.content_type)
            
            if content_type == 'multipart/form-data':
                boundary = params.get('boundary')
                if boundary:
                    multipart_data = parse_multipart_form_data(self.body, boundary)
                    self._files = {
                        k: v for k, v in multipart_data.items()
                        if isinstance(v, bytes)
                    }
                else:
                    self._files = {}
            else:
                self._files = {}
        
        return self._files
    
    async def text(self) -> str:
        """获取请求体文本"""
        try:
            return self.body.decode('utf-8')
        except UnicodeDecodeError:
            return self.body.decode('utf-8', errors='replace')
    
    async def bytes(self) -> bytes:
        """获取请求体字节数据"""
        return self.body
    
    def get_form_value(self, name: str, default: str = None) -> Optional[str]:
        """获取表单字段值（同步方法）"""
        # 这是一个简化版本，实际使用时建议使用async form()方法
        content_type, params = parse_content_type(self.content_type)
        
        if content_type == 'application/x-www-form-urlencoded':
            form_data = parse_form_data(self.body)
            return form_data.get(name, default)
        
        return default
    
    def get_json_value(self, name: str, default: Any = None) -> Any:
        """获取JSON字段值（同步方法）"""
        # 这是一个简化版本，实际使用时建议使用async json()方法
        content_type, _ = parse_content_type(self.content_type)
        
        if content_type == 'application/json':
            json_data = parse_json_body(self.body)
            return json_data.get(name, default)
        
        return default
    
    def accepts(self, content_type: str) -> bool:
        """检查客户端是否接受指定的内容类型"""
        accept_header = self.headers.get('accept', '')
        return content_type in accept_header or '*/*' in accept_header
    
    def set_route_params(self, params: Dict[str, Any]):
        """设置路由参数（由路由器调用）"""
        self.route_params = params
    
    def set_extra(self, key: str, value: Any):
        """设置额外属性"""
        self.extras[key] = value
    
    def get_extra(self, key: str, default: Any = None) -> Any:
        """获取额外属性"""
        return self.extras.get(key, default)
    
    def __repr__(self) -> str:
        return f"<Request {self.method} {self.path}>"
    
    def __str__(self) -> str:
        return f"{self.method} {self.url}" 