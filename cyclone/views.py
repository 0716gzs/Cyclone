"""
Cyclone 视图模块

提供视图基类和装饰器，支持函数视图和类视图
"""

import asyncio
import functools
from typing import Any, Callable, Dict, List, Optional, Union
from .request import Request
from .response import Response, JSONResponse, HTMLResponse, ErrorResponse
from .exceptions import HTTPMethodNotAllowed, HTTPNotFound, ViewError


class View:
    """视图基类"""
    
    # 支持的HTTP方法
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace']
    
    def __init__(self):
        self.request = None
        self.route_params = {}
    
    async def dispatch(self, request: Request, **kwargs) -> Response:
        """分发请求到对应的处理方法"""
        self.request = request
        self.route_params = kwargs
        
        # 获取HTTP方法对应的处理函数
        method = request.method.lower()
        handler = getattr(self, method, None)
        
        if handler is None:
            # 检查是否有其他支持的方法
            allowed_methods = [m.upper() for m in self.http_method_names 
                             if hasattr(self, m) and callable(getattr(self, m))]
            
            if not allowed_methods:
                raise HTTPNotFound("视图没有定义任何处理方法")
            
            raise HTTPMethodNotAllowed(
                f"方法 {request.method} 不被支持。支持的方法: {', '.join(allowed_methods)}"
            )
        
        # 调用处理方法
        if asyncio.iscoroutinefunction(handler):
            return await handler(request, **kwargs)
        else:
            return handler(request, **kwargs)
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """获取模板上下文数据"""
        context = {
            'request': self.request,
            'view': self,
        }
        context.update(kwargs)
        return context
    
    def get_template_name(self) -> str:
        """获取模板名称"""
        # 默认模板名称基于视图类名
        class_name = self.__class__.__name__
        if class_name.endswith('View'):
            class_name = class_name[:-4]  # 去掉'View'后缀
        
        return f"{class_name.lower()}.html"
    
    def render_template(self, template_name: str = None, context: Dict[str, Any] = None) -> HTMLResponse:
        """渲染模板"""
        if template_name is None:
            template_name = self.get_template_name()
        
        if context is None:
            context = self.get_context_data()
        
        # 简化的模板渲染（实际项目中需要集成真正的模板引擎）
        html_content = f"<html><body><h1>模板: {template_name}</h1><pre>{context}</pre></body></html>"
        return HTMLResponse(html_content)
    
    def json_response(self, data: Any, status: int = 200, **kwargs) -> JSONResponse:
        """返回JSON响应"""
        return JSONResponse(data, status, **kwargs)
    
    def error_response(self, message: str, status: int = 400, **kwargs) -> ErrorResponse:
        """返回错误响应"""
        return ErrorResponse(message, status, **kwargs)
    
    # 默认的HTTP方法处理器（可以被子类覆盖）
    
    async def get(self, request: Request, **kwargs) -> Response:
        """处理GET请求"""
        return self.render_template()
    
    async def post(self, request: Request, **kwargs) -> Response:
        """处理POST请求"""
        return self.json_response({"message": "POST请求处理成功"})
    
    async def put(self, request: Request, **kwargs) -> Response:
        """处理PUT请求"""
        return self.json_response({"message": "PUT请求处理成功"})
    
    async def patch(self, request: Request, **kwargs) -> Response:
        """处理PATCH请求"""
        return self.json_response({"message": "PATCH请求处理成功"})
    
    async def delete(self, request: Request, **kwargs) -> Response:
        """处理DELETE请求"""
        return self.json_response({"message": "DELETE请求处理成功"})
    
    async def head(self, request: Request, **kwargs) -> Response:
        """处理HEAD请求"""
        return Response("")
    
    async def options(self, request: Request, **kwargs) -> Response:
        """处理OPTIONS请求"""
        # 返回支持的方法
        allowed_methods = [m.upper() for m in self.http_method_names 
                         if hasattr(self, m) and callable(getattr(self, m))]
        
        return Response("", headers={"Allow": ", ".join(allowed_methods)})


class TemplateView(View):
    """模板视图基类"""
    
    template_name = None
    
    def get_template_name(self) -> str:
        """获取模板名称"""
        if self.template_name:
            return self.template_name
        return super().get_template_name()
    
    async def get(self, request: Request, **kwargs) -> Response:
        """渲染模板"""
        context = self.get_context_data(**kwargs)
        return self.render_template(context=context)


class JSONView(View):
    """JSON API视图基类"""
    
    async def get(self, request: Request, **kwargs) -> Response:
        """返回JSON数据"""
        data = await self.get_data(**kwargs)
        return self.json_response(data)
    
    async def get_data(self, **kwargs) -> Dict[str, Any]:
        """获取要返回的数据"""
        return {"message": "JSON视图"}


class ListView(View):
    """列表视图基类"""
    
    model = None
    template_name = None
    context_object_name = 'object_list'
    
    async def get(self, request: Request, **kwargs) -> Response:
        """获取对象列表"""
        object_list = await self.get_queryset()
        context = self.get_context_data(object_list=object_list, **kwargs)
        return self.render_template(context=context)
    
    async def get_queryset(self):
        """获取查询集"""
        if self.model:
            # 这里需要与ORM集成
            return []
        return []
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """获取上下文数据"""
        context = super().get_context_data(**kwargs)
        if 'object_list' in kwargs:
            context[self.context_object_name] = kwargs['object_list']
        return context


class DetailView(View):
    """详细视图基类"""
    
    model = None
    template_name = None
    context_object_name = 'object'
    pk_url_kwarg = 'pk'
    
    async def get(self, request: Request, **kwargs) -> Response:
        """获取单个对象"""
        obj = await self.get_object(**kwargs)
        context = self.get_context_data(object=obj, **kwargs)
        return self.render_template(context=context)
    
    async def get_object(self, **kwargs):
        """获取单个对象"""
        if self.model:
            # 这里需要与ORM集成
            pk = kwargs.get(self.pk_url_kwarg)
            if pk:
                return {"id": pk, "name": f"对象 {pk}"}
        return None
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """获取上下文数据"""
        context = super().get_context_data(**kwargs)
        if 'object' in kwargs:
            context[self.context_object_name] = kwargs['object']
        return context


# 装饰器

def route(path: str, methods: List[str] = None, name: str = None, middleware: List[Callable] = None):
    """路由装饰器"""
    def decorator(func: Callable) -> Callable:
        # 将路由信息附加到函数上
        func._route_path = path
        func._route_methods = methods or ['GET']
        func._route_name = name
        func._route_middleware = middleware or []
        return func
    return decorator


def require_methods(methods: List[str]):
    """要求特定HTTP方法的装饰器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            if request.method not in methods:
                allowed_methods = ', '.join(methods)
                raise HTTPMethodNotAllowed(f"只允许方法: {allowed_methods}")
            
            if asyncio.iscoroutinefunction(func):
                return await func(request, *args, **kwargs)
            else:
                return func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_GET(func: Callable) -> Callable:
    """要求GET方法的装饰器"""
    return require_methods(['GET'])(func)


def require_POST(func: Callable) -> Callable:
    """要求POST方法的装饰器"""
    return require_methods(['POST'])(func)


def require_ajax(func: Callable) -> Callable:
    """要求AJAX请求的装饰器"""
    @functools.wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        if not request.is_ajax:
            raise HTTPMethodNotAllowed("此端点只接受AJAX请求")
        
        if asyncio.iscoroutinefunction(func):
            return await func(request, *args, **kwargs)
        else:
            return func(request, *args, **kwargs)
    return wrapper


def csrf_exempt(func: Callable) -> Callable:
    """CSRF豁免装饰器"""
    func._csrf_exempt = True
    return func


def cache_control(**kwargs):
    """缓存控制装饰器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(request: Request, *args, **kwargs_inner):
            if asyncio.iscoroutinefunction(func):
                response = await func(request, *args, **kwargs_inner)
            else:
                response = func(request, *args, **kwargs_inner)
            
            # 设置缓存控制头部
            cache_directives = []
            for key, value in kwargs.items():
                if key == 'max_age':
                    cache_directives.append(f'max-age={value}')
                elif key == 'no_cache' and value:
                    cache_directives.append('no-cache')
                elif key == 'no_store' and value:
                    cache_directives.append('no-store')
                elif key == 'must_revalidate' and value:
                    cache_directives.append('must-revalidate')
                elif key == 'public' and value:
                    cache_directives.append('public')
                elif key == 'private' and value:
                    cache_directives.append('private')
            
            if cache_directives:
                response.set_header('Cache-Control', ', '.join(cache_directives))
            
            return response
        return wrapper
    return decorator


def never_cache(func: Callable) -> Callable:
    """永不缓存装饰器"""
    return cache_control(no_cache=True, no_store=True, must_revalidate=True)(func)


# 便捷函数

def view_function(func: Callable) -> Callable:
    """将函数转换为视图函数"""
    @functools.wraps(func)
    async def wrapper(request: Request, **kwargs) -> Response:
        if asyncio.iscoroutinefunction(func):
            result = await func(request, **kwargs)
        else:
            result = func(request, **kwargs)
        
        # 如果返回的不是Response对象，则创建一个
        if not isinstance(result, Response):
            if isinstance(result, dict):
                result = JSONResponse(result)
            elif isinstance(result, str):
                result = HTMLResponse(result)
            else:
                result = Response(str(result))
        
        return result
    return wrapper


def as_view(view_class: type) -> Callable:
    """将类视图转换为可调用的视图函数"""
    async def view_func(request: Request, **kwargs) -> Response:
        instance = view_class()
        return await instance.dispatch(request, **kwargs)
    
    # 复制一些有用的属性
    view_func.__name__ = view_class.__name__
    view_func.__doc__ = view_class.__doc__
    view_func.__module__ = view_class.__module__
    
    return view_func 