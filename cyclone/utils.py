"""
Cyclone 工具函数模块

提供HTTP解析、数据处理等工具函数
"""

import re
import json
import urllib.parse
from typing import Dict, Any, Optional, Union, List, Tuple


def parse_query_string(query_string: str) -> Dict[str, str]:
    """解析查询字符串"""
    if not query_string:
        return {}
    
    return dict(urllib.parse.parse_qsl(query_string))


def parse_headers(header_lines: List[str]) -> Dict[str, str]:
    """解析HTTP头部"""
    headers = {}
    for line in header_lines:
        if ':' in line:
            key, value = line.split(':', 1)
            headers[key.strip().lower()] = value.strip()
    return headers


def parse_content_type(content_type: str) -> Tuple[str, Dict[str, str]]:
    """解析Content-Type头部"""
    if not content_type:
        return "text/plain", {}
    
    parts = content_type.split(';')
    main_type = parts[0].strip().lower()
    params = {}
    
    for part in parts[1:]:
        if '=' in part:
            key, value = part.split('=', 1)
            params[key.strip()] = value.strip().strip('"')
    
    return main_type, params


def parse_multipart_form_data(body: bytes, boundary: str) -> Dict[str, Any]:
    """解析multipart/form-data数据"""
    boundary = boundary.encode()
    parts = body.split(b'--' + boundary)
    form_data = {}
    
    for part in parts[1:-1]:  # 跳过首尾空白部分
        if not part.strip():
            continue
            
        header_end = part.find(b'\r\n\r\n')
        if header_end == -1:
            continue
            
        header_data = part[:header_end].decode('utf-8')
        body_data = part[header_end + 4:]
        
        # 解析Content-Disposition头部
        content_disposition = None
        for line in header_data.split('\r\n'):
            if line.lower().startswith('content-disposition:'):
                content_disposition = line
                break
        
        if content_disposition:
            # 提取name
            name_match = re.search(r'name="([^"]+)"', content_disposition)
            if name_match:
                name = name_match.group(1)
                form_data[name] = body_data.rstrip(b'\r\n')
    
    return form_data


def parse_json_body(body: bytes) -> Dict[str, Any]:
    """解析JSON请求体"""
    try:
        return json.loads(body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def parse_form_data(body: bytes) -> Dict[str, str]:
    """解析application/x-www-form-urlencoded数据"""
    try:
        query_string = body.decode('utf-8')
        return parse_query_string(query_string)
    except UnicodeDecodeError:
        return {}


def build_http_response(status_code: int, headers: Dict[str, str], body: bytes) -> bytes:
    """构建HTTP响应"""
    status_line = f"HTTP/1.1 {status_code} {get_status_text(status_code)}\r\n"
    
    # 确保必要的头部存在
    if 'content-length' not in {k.lower() for k in headers.keys()}:
        headers['Content-Length'] = str(len(body))
    
    if 'content-type' not in {k.lower() for k in headers.keys()}:
        headers['Content-Type'] = 'text/plain'
    
    header_lines = []
    for key, value in headers.items():
        header_lines.append(f"{key}: {value}\r\n")
    
    response = (status_line + ''.join(header_lines) + '\r\n').encode('utf-8') + body
    return response


def get_status_text(status_code: int) -> str:
    """获取HTTP状态码对应的文本"""
    status_texts = {
        200: "OK",
        201: "Created",
        202: "Accepted",
        204: "No Content",
        301: "Moved Permanently",
        302: "Found",
        304: "Not Modified",
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        409: "Conflict",
        422: "Unprocessable Entity",
        500: "Internal Server Error",
        501: "Not Implemented",
        502: "Bad Gateway",
        503: "Service Unavailable",
    }
    return status_texts.get(status_code, "Unknown")


def extract_route_params(pattern: str, path: str) -> Optional[Dict[str, str]]:
    """从路径中提取路由参数"""
    # 将路由模式转换为正则表达式
    # 例如: "/users/<user_id:int>" -> "/users/(?P<user_id>\d+)"
    
    regex_pattern = pattern
    param_types = {}
    
    # 查找所有参数
    param_matches = re.findall(r'<([^>]+)>', pattern)
    
    for param_match in param_matches:
        if ':' in param_match:
            param_name, param_type = param_match.split(':', 1)
        else:
            param_name, param_type = param_match, 'str'
        
        param_types[param_name] = param_type
        
        # 替换为正则表达式
        if param_type == 'int':
            regex_replace = f'(?P<{param_name}>\\d+)'
        elif param_type == 'float':
            regex_replace = f'(?P<{param_name}>\\d+\\.\\d+)'
        elif param_type == 'uuid':
            regex_replace = f'(?P<{param_name}>[0-9a-f]{{8}}-[0-9a-f]{{4}}-[0-9a-f]{{4}}-[0-9a-f]{{4}}-[0-9a-f]{{12}})'
        else:  # str
            regex_replace = f'(?P<{param_name}>[^/]+)'
        
        regex_pattern = regex_pattern.replace(f'<{param_match}>', regex_replace)
    
    # 匹配路径
    match = re.match(f'^{regex_pattern}$', path)
    if not match:
        return None
    
    # 转换参数类型
    params = match.groupdict()
    for param_name, param_value in params.items():
        param_type = param_types.get(param_name, 'str')
        if param_type == 'int':
            params[param_name] = int(param_value)
        elif param_type == 'float':
            params[param_name] = float(param_value)
        # str和uuid保持字符串
    
    return params


def safe_json_encode(obj: Any) -> str:
    """安全的JSON编码"""
    try:
        return json.dumps(obj, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return json.dumps({"error": "JSON encoding failed"})


def get_client_ip(headers: Dict[str, str]) -> str:
    """获取客户端IP地址"""
    # 检查代理头部
    forwarded_for = headers.get('x-forwarded-for')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    
    real_ip = headers.get('x-real-ip')
    if real_ip:
        return real_ip
    
    return "127.0.0.1"  # 默认值


def is_safe_path(path: str) -> bool:
    """检查路径是否安全（防止路径遍历攻击）"""
    # 规范化路径
    normalized = urllib.parse.unquote(path)
    
    # 检查是否包含危险字符
    dangerous_patterns = ['..', '~', '\\']
    for pattern in dangerous_patterns:
        if pattern in normalized:
            return False
    
    return True 