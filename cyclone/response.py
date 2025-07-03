"""
Cyclone 响应模块

用于构建HTTP响应的类和函数
"""

import json
import os
import mimetypes
from typing import Dict, Any, Optional, Union, List
from .utils import safe_json_encode, get_status_text


class Response:
    """HTTP响应基类"""
    
    def __init__(self, body: Union[str, bytes] = "", status: int = 200, 
                 headers: Optional[Dict[str, str]] = None, 
                 content_type: str = "text/plain"):
        self.status = status
        self.headers = headers or {}
        self.content_type = content_type
        
        # 确保body是字节类型
        if isinstance(body, str):
            self.body = body.encode('utf-8')
        else:
            self.body = body
        
        # 设置默认头部
        self._set_default_headers()
    
    def _set_default_headers(self):
        """设置默认头部"""
        if 'content-type' not in {k.lower() for k in self.headers.keys()}:
            self.headers['Content-Type'] = self.content_type
        
        if 'content-length' not in {k.lower() for k in self.headers.keys()}:
            self.headers['Content-Length'] = str(len(self.body))
    
    def set_header(self, key: str, value: str):
        """设置响应头部"""
        self.headers[key] = value
    
    def get_header(self, key: str, default: str = None) -> Optional[str]:
        """获取响应头部"""
        return self.headers.get(key, default)
    
    def set_cookie(self, key: str, value: str, max_age: int = None, 
                   expires: str = None, path: str = "/", domain: str = None,
                   secure: bool = False, httponly: bool = False):
        """设置Cookie"""
        cookie_parts = [f"{key}={value}"]
        
        if max_age is not None:
            cookie_parts.append(f"Max-Age={max_age}")
        
        if expires:
            cookie_parts.append(f"Expires={expires}")
        
        if path:
            cookie_parts.append(f"Path={path}")
        
        if domain:
            cookie_parts.append(f"Domain={domain}")
        
        if secure:
            cookie_parts.append("Secure")
        
        if httponly:
            cookie_parts.append("HttpOnly")
        
        # 处理多个Cookie
        if 'Set-Cookie' in self.headers:
            existing_cookies = self.headers['Set-Cookie']
            if isinstance(existing_cookies, str):
                existing_cookies = [existing_cookies]
            existing_cookies.append("; ".join(cookie_parts))
            self.headers['Set-Cookie'] = existing_cookies
        else:
            self.headers['Set-Cookie'] = "; ".join(cookie_parts)
    
    def delete_cookie(self, key: str, path: str = "/", domain: str = None):
        """删除Cookie"""
        self.set_cookie(key, "", max_age=0, path=path, domain=domain)
    
    def to_bytes(self) -> bytes:
        """转换为字节数据"""
        return self.body
    
    def __len__(self) -> int:
        return len(self.body)
    
    def __str__(self) -> str:
        return f"<Response {self.status}>"


class JSONResponse(Response):
    """JSON响应"""
    
    def __init__(self, data: Any, status: int = 200, 
                 headers: Optional[Dict[str, str]] = None,
                 ensure_ascii: bool = False, indent: int = None):
        self.data = data
        self.ensure_ascii = ensure_ascii
        self.indent = indent
        
        # 序列化JSON数据
        if isinstance(data, (dict, list)):
            json_str = json.dumps(data, ensure_ascii=ensure_ascii, 
                                indent=indent, default=str)
        else:
            json_str = safe_json_encode(data)
        
        super().__init__(
            body=json_str,
            status=status,
            headers=headers,
            content_type="application/json; charset=utf-8"
        )


class HTMLResponse(Response):
    """HTML响应"""
    
    def __init__(self, html: str, status: int = 200, 
                 headers: Optional[Dict[str, str]] = None):
        super().__init__(
            body=html,
            status=status,
            headers=headers,
            content_type="text/html; charset=utf-8"
        )


class PlainTextResponse(Response):
    """纯文本响应"""
    
    def __init__(self, text: str, status: int = 200, 
                 headers: Optional[Dict[str, str]] = None):
        super().__init__(
            body=text,
            status=status,
            headers=headers,
            content_type="text/plain; charset=utf-8"
        )


class FileResponse(Response):
    """文件响应"""
    
    def __init__(self, file_path: str, filename: str = None, 
                 content_type: str = None, 
                 headers: Optional[Dict[str, str]] = None):
        self.file_path = file_path
        self.filename = filename or os.path.basename(file_path)
        
        # 读取文件内容
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # 自动检测content-type
        if content_type is None:
            content_type, _ = mimetypes.guess_type(file_path)
            if content_type is None:
                content_type = 'application/octet-stream'
        
        super().__init__(
            body=file_content,
            status=200,
            headers=headers,
            content_type=content_type
        )
        
        # 设置文件下载头部
        self.set_header('Content-Disposition', f'attachment; filename="{self.filename}"')


class StreamResponse(Response):
    """流响应（用于大文件或实时数据）"""
    
    def __init__(self, stream_generator, content_type: str = "application/octet-stream",
                 headers: Optional[Dict[str, str]] = None):
        self.stream_generator = stream_generator
        
        super().__init__(
            body=b"",  # 流响应的body在发送时生成
            status=200,
            headers=headers,
            content_type=content_type
        )
    
    def to_bytes(self) -> bytes:
        """流响应需要特殊处理"""
        # 这里只是占位符，实际的流数据由服务器处理
        return b""


class RedirectResponse(Response):
    """重定向响应"""
    
    def __init__(self, url: str, status: int = 302, 
                 headers: Optional[Dict[str, str]] = None):
        super().__init__(
            body="",
            status=status,
            headers=headers,
            content_type="text/html"
        )
        self.set_header('Location', url)


class XMLResponse(Response):
    """XML响应"""
    
    def __init__(self, xml_data: str, status: int = 200, 
                 headers: Optional[Dict[str, str]] = None):
        super().__init__(
            body=xml_data,
            status=status,
            headers=headers,
            content_type="application/xml; charset=utf-8"
        )


class CSVResponse(Response):
    """CSV响应"""
    
    def __init__(self, csv_data: str, filename: str = "export.csv",
                 status: int = 200, headers: Optional[Dict[str, str]] = None):
        super().__init__(
            body=csv_data,
            status=status,
            headers=headers,
            content_type="text/csv; charset=utf-8"
        )
        self.set_header('Content-Disposition', f'attachment; filename="{filename}"')


class ErrorResponse(Response):
    """错误响应"""
    
    def __init__(self, error_message: str, status: int = 500, 
                 headers: Optional[Dict[str, str]] = None,
                 include_traceback: bool = False):
        
        error_data = {
            "error": error_message,
            "status": status,
            "status_text": get_status_text(status)
        }
        
        if include_traceback:
            import traceback
            error_data["traceback"] = traceback.format_exc()
        
        json_str = json.dumps(error_data, ensure_ascii=False, indent=2)
        
        super().__init__(
            body=json_str,
            status=status,
            headers=headers,
            content_type="application/json; charset=utf-8"
        )


# 便捷函数

def json_response(data: Any, status: int = 200, **kwargs) -> JSONResponse:
    """创建JSON响应"""
    return JSONResponse(data, status, **kwargs)


def html_response(html: str, status: int = 200, **kwargs) -> HTMLResponse:
    """创建HTML响应"""
    return HTMLResponse(html, status, **kwargs)


def text_response(text: str, status: int = 200, **kwargs) -> PlainTextResponse:
    """创建文本响应"""
    return PlainTextResponse(text, status, **kwargs)


def file_response(file_path: str, **kwargs) -> FileResponse:
    """创建文件响应"""
    return FileResponse(file_path, **kwargs)


def redirect_response(url: str, status: int = 302, **kwargs) -> RedirectResponse:
    """创建重定向响应"""
    return RedirectResponse(url, status, **kwargs)


def error_response(message: str, status: int = 500, **kwargs) -> ErrorResponse:
    """创建错误响应"""
    return ErrorResponse(message, status, **kwargs) 