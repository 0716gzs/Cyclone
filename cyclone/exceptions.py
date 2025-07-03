"""
Cyclone 异常处理模块

定义框架级别的异常和HTTP异常
"""

class CycloneException(Exception):
    """Cyclone框架基础异常类"""
    pass


class HTTPException(CycloneException):
    """HTTP异常基类"""
    
    def __init__(self, status_code: int, message: str = None, headers: dict = None):
        self.status_code = status_code
        self.message = message or self.get_default_message()
        self.headers = headers or {}
        super().__init__(self.message)
    
    def get_default_message(self):
        """获取默认错误消息"""
        return f"HTTP {self.status_code} Error"


class HTTPBadRequest(HTTPException):
    """400 Bad Request"""
    
    def __init__(self, message: str = "Bad Request", headers: dict = None):
        super().__init__(400, message, headers)


class HTTPNotFound(HTTPException):
    """404 Not Found"""
    
    def __init__(self, message: str = "Not Found", headers: dict = None):
        super().__init__(404, message, headers)


class HTTPMethodNotAllowed(HTTPException):
    """405 Method Not Allowed"""
    
    def __init__(self, message: str = "Method Not Allowed", headers: dict = None):
        super().__init__(405, message, headers)


class HTTPInternalServerError(HTTPException):
    """500 Internal Server Error"""
    
    def __init__(self, message: str = "Internal Server Error", headers: dict = None):
        super().__init__(500, message, headers)


class HTTPNotImplemented(HTTPException):
    """501 Not Implemented"""
    
    def __init__(self, message: str = "Not Implemented", headers: dict = None):
        super().__init__(501, message, headers)


class HTTPServiceUnavailable(HTTPException):
    """503 Service Unavailable"""
    
    def __init__(self, message: str = "Service Unavailable", headers: dict = None):
        super().__init__(503, message, headers)


class ValidationError(CycloneException):
    """数据验证异常"""
    pass


class DatabaseError(CycloneException):
    """数据库操作异常"""
    pass


class MiddlewareError(CycloneException):
    """中间件异常"""
    pass


class RouterError(CycloneException):
    """路由异常"""
    pass


class ViewError(CycloneException):
    """视图异常"""
    pass 