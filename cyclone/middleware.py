"""
Cyclone 中间件模块

提供中间件基类和常用的内置中间件
"""

import time
import logging
from typing import Callable, Dict, List, Optional, Any
from .request import Request
from .response import Response, JSONResponse
from .exceptions import HTTPException, MiddlewareError


class Middleware:
    """中间件基类"""
    
    def __init__(self, app: Callable = None):
        self.app = app
    
    async def __call__(self, request: Request) -> Response:
        """中间件调用入口"""
        # 处理请求阶段
        try:
            request = await self.process_request(request)
            if isinstance(request, Response):
                # 如果process_request返回Response，直接返回
                return request
        except Exception as e:
            return await self.process_exception(request, e)
        
        # 调用下一个中间件或视图
        try:
            response = await self.app(request)
        except Exception as e:
            return await self.process_exception(request, e)
        
        # 处理响应阶段
        try:
            response = await self.process_response(request, response)
        except Exception as e:
            return await self.process_exception(request, e)
        
        return response
    
    async def process_request(self, request: Request) -> Request:
        """处理请求（在视图处理之前）"""
        return request
    
    async def process_response(self, request: Request, response: Response) -> Response:
        """处理响应（在视图处理之后）"""
        return response
    
    async def process_exception(self, request: Request, exception: Exception) -> Response:
        """处理异常"""
        if isinstance(exception, HTTPException):
            return JSONResponse(
                {"error": exception.message, "status": exception.status_code},
                status=exception.status_code,
                headers=exception.headers
            )
        else:
            # 记录异常
            logging.error(f"未处理的异常: {exception}", exc_info=True)
            return JSONResponse(
                {"error": "内部服务器错误"},
                status=500
            )


class CORSMiddleware(Middleware):
    """CORS中间件"""
    
    def __init__(self, app: Callable = None, 
                 allow_origins: List[str] = None,
                 allow_methods: List[str] = None,
                 allow_headers: List[str] = None,
                 allow_credentials: bool = False,
                 max_age: int = 3600):
        super().__init__(app)
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allow_headers = allow_headers or ["*"]
        self.allow_credentials = allow_credentials
        self.max_age = max_age
    
    async def process_request(self, request: Request) -> Request:
        """处理CORS预检请求"""
        if request.method == "OPTIONS":
            # 返回预检响应
            return Response(
                "",
                headers=self._get_cors_headers(request)
            )
        return request
    
    async def process_response(self, request: Request, response: Response) -> Response:
        """添加CORS头部"""
        cors_headers = self._get_cors_headers(request)
        for key, value in cors_headers.items():
            response.set_header(key, value)
        return response
    
    def _get_cors_headers(self, request: Request) -> Dict[str, str]:
        """获取CORS头部"""
        headers = {}
        
        # 处理Origin
        origin = request.get_header("origin")
        if origin and self._is_origin_allowed(origin):
            headers["Access-Control-Allow-Origin"] = origin
        elif "*" in self.allow_origins:
            headers["Access-Control-Allow-Origin"] = "*"
        
        # 处理Methods
        headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
        
        # 处理Headers
        if "*" in self.allow_headers:
            requested_headers = request.get_header("access-control-request-headers")
            if requested_headers:
                headers["Access-Control-Allow-Headers"] = requested_headers
            else:
                headers["Access-Control-Allow-Headers"] = "*"
        else:
            headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
        
        # 处理Credentials
        if self.allow_credentials:
            headers["Access-Control-Allow-Credentials"] = "true"
        
        # 处理Max-Age
        if request.method == "OPTIONS":
            headers["Access-Control-Max-Age"] = str(self.max_age)
        
        return headers
    
    def _is_origin_allowed(self, origin: str) -> bool:
        """检查Origin是否被允许"""
        return origin in self.allow_origins or "*" in self.allow_origins


class SecurityMiddleware(Middleware):
    """安全中间件"""
    
    def __init__(self, app: Callable = None,
                 force_https: bool = False,
                 hsts_max_age: int = 31536000,
                 content_type_nosniff: bool = True,
                 frame_deny: bool = True,
                 xss_protection: bool = True):
        super().__init__(app)
        self.force_https = force_https
        self.hsts_max_age = hsts_max_age
        self.content_type_nosniff = content_type_nosniff
        self.frame_deny = frame_deny
        self.xss_protection = xss_protection
    
    async def process_request(self, request: Request) -> Request:
        """处理安全检查"""
        # 强制HTTPS
        if self.force_https and not request.is_secure:
            # 重定向到HTTPS
            from .response import RedirectResponse
            https_url = f"https://{request.host}{request.url}"
            return RedirectResponse(https_url, status=301)
        
        return request
    
    async def process_response(self, request: Request, response: Response) -> Response:
        """添加安全头部"""
        # HSTS
        if request.is_secure and self.hsts_max_age:
            response.set_header(
                "Strict-Transport-Security",
                f"max-age={self.hsts_max_age}; includeSubDomains"
            )
        
        # Content-Type Nosniff
        if self.content_type_nosniff:
            response.set_header("X-Content-Type-Options", "nosniff")
        
        # Frame Options
        if self.frame_deny:
            response.set_header("X-Frame-Options", "DENY")
        
        # XSS Protection
        if self.xss_protection:
            response.set_header("X-XSS-Protection", "1; mode=block")
        
        return response


class RequestLoggingMiddleware(Middleware):
    """请求日志中间件"""
    
    def __init__(self, app: Callable = None, 
                 logger: logging.Logger = None,
                 log_level: int = logging.INFO):
        super().__init__(app)
        self.logger = logger or logging.getLogger('cyclone.requests')
        self.log_level = log_level
    
    async def process_request(self, request: Request) -> Request:
        """记录请求开始"""
        request.start_time = time.time()
        
        self.logger.log(
            self.log_level,
            f"请求开始: {request.method} {request.path} from {request.client_ip}"
        )
        
        return request
    
    async def process_response(self, request: Request, response: Response) -> Response:
        """记录请求完成"""
        duration = time.time() - getattr(request, 'start_time', time.time())
        
        self.logger.log(
            self.log_level,
            f"请求完成: {request.method} {request.path} "
            f"-> {response.status} in {duration:.3f}s"
        )
        
        return response


class RateLimitMiddleware(Middleware):
    """限流中间件"""
    
    def __init__(self, app: Callable = None,
                 max_requests: int = 100,
                 window_seconds: int = 60,
                 key_func: Callable = None):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.key_func = key_func or self._default_key_func
        self.requests = {}  # 简单的内存存储
    
    def _default_key_func(self, request: Request) -> str:
        """默认的键函数（基于IP）"""
        return request.client_ip
    
    async def process_request(self, request: Request) -> Request:
        """检查限流"""
        key = self.key_func(request)
        now = time.time()
        
        # 清理过期的记录
        self._cleanup_expired_records(now)
        
        # 检查当前请求
        if key not in self.requests:
            self.requests[key] = []
        
        # 过滤窗口内的请求
        window_start = now - self.window_seconds
        self.requests[key] = [
            timestamp for timestamp in self.requests[key]
            if timestamp > window_start
        ]
        
        # 检查是否超过限制
        if len(self.requests[key]) >= self.max_requests:
            from .response import JSONResponse
            return JSONResponse(
                {"error": "请求过于频繁，请稍后再试"},
                status=429,
                headers={"Retry-After": str(self.window_seconds)}
            )
        
        # 记录当前请求
        self.requests[key].append(now)
        
        return request
    
    def _cleanup_expired_records(self, now: float):
        """清理过期记录"""
        window_start = now - self.window_seconds
        keys_to_remove = []
        
        for key, timestamps in self.requests.items():
            # 移除过期的时间戳
            self.requests[key] = [
                timestamp for timestamp in timestamps
                if timestamp > window_start
            ]
            
            # 如果列表为空，标记为删除
            if not self.requests[key]:
                keys_to_remove.append(key)
        
        # 删除空的键
        for key in keys_to_remove:
            del self.requests[key]


class CompressionMiddleware(Middleware):
    """压缩中间件"""
    
    def __init__(self, app: Callable = None,
                 min_size: int = 1024,
                 compression_level: int = 6):
        super().__init__(app)
        self.min_size = min_size
        self.compression_level = compression_level
    
    async def process_response(self, request: Request, response: Response) -> Response:
        """压缩响应"""
        # 检查是否支持压缩
        accept_encoding = request.get_header("accept-encoding", "")
        if "gzip" not in accept_encoding:
            return response
        
        # 检查响应大小
        if len(response.body) < self.min_size:
            return response
        
        # 检查Content-Type
        content_type = response.get_header("content-type", "")
        if not self._should_compress(content_type):
            return response
        
        # 压缩响应体
        try:
            import gzip
            compressed_body = gzip.compress(response.body, compresslevel=self.compression_level)
            response.body = compressed_body
            response.set_header("Content-Encoding", "gzip")
            response.set_header("Content-Length", str(len(compressed_body)))
            response.set_header("Vary", "Accept-Encoding")
        except Exception as e:
            # 压缩失败，返回原始响应
            logging.warning(f"压缩失败: {e}")
        
        return response
    
    def _should_compress(self, content_type: str) -> bool:
        """检查是否应该压缩"""
        compressible_types = [
            "text/",
            "application/json",
            "application/javascript",
            "application/xml",
            "application/x-javascript",
        ]
        
        return any(content_type.startswith(ct) for ct in compressible_types)


class AuthenticationMiddleware(Middleware):
    """认证中间件"""
    
    def __init__(self, app: Callable = None, 
                 auth_func: Callable = None,
                 exclude_paths: List[str] = None):
        super().__init__(app)
        self.auth_func = auth_func or self._default_auth_func
        self.exclude_paths = exclude_paths or []
    
    async def _default_auth_func(self, request: Request) -> Optional[Any]:
        """默认认证函数"""
        # 简单的Token认证示例
        auth_header = request.get_header("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            # 这里应该验证token
            return {"user_id": "123", "username": "user"}
        return None
    
    async def process_request(self, request: Request) -> Request:
        """处理认证"""
        # 检查是否需要认证
        if any(request.path.startswith(path) for path in self.exclude_paths):
            return request
        
        # 执行认证
        user = await self.auth_func(request)
        if user is None:
            from .response import JSONResponse
            return JSONResponse(
                {"error": "未授权访问"},
                status=401,
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # 将用户信息添加到请求中
        request.user = user
        
        return request


# 中间件栈

class MiddlewareStack:
    """中间件栈"""
    
    def __init__(self):
        self.middlewares: List[Middleware] = []
    
    def add(self, middleware: Middleware):
        """添加中间件"""
        self.middlewares.append(middleware)
    
    def create_handler(self, view_func: Callable) -> Callable:
        """创建带中间件的处理器"""
        handler = view_func
        
        # 反向遍历中间件栈
        for middleware in reversed(self.middlewares):
            middleware.app = handler
            handler = middleware
        
        return handler
    
    def __len__(self) -> int:
        return len(self.middlewares)
    
    def __iter__(self):
        return iter(self.middlewares)


# 便捷函数

def create_middleware_stack() -> MiddlewareStack:
    """创建中间件栈"""
    return MiddlewareStack()


def apply_middlewares(middlewares: List[Middleware], view_func: Callable) -> Callable:
    """应用中间件到视图函数"""
    stack = MiddlewareStack()
    for middleware in middlewares:
        stack.add(middleware)
    return stack.create_handler(view_func) 