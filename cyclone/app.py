"""
Cyclone 应用模块

应用类作为整个框架的核心，整合所有模块
"""

import asyncio
import logging
from typing import Callable, Dict, List, Optional, Any, Type, Union
from .server import AsyncHTTPServer, create_server
from .router import Router, RouteGroup
from .middleware import Middleware, MiddlewareStack
from .request import Request
from .response import Response, ErrorResponse
from .views import View, as_view
from .settings import Settings, get_settings
from .exceptions import HTTPException, HTTPNotFound
from .database.pool import DatabasePool


class Application:
    """Cyclone应用类"""
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.router = Router()
        self.middleware_stack = MiddlewareStack()
        self.db_pool: Optional[DatabasePool] = None
        self.logger = logging.getLogger(__name__)
        
        # 应用状态
        self.is_configured = False
        self.is_running = False
        self.startup_handlers = []
        self.shutdown_handlers = []
        
        # 加载默认中间件
        self._load_default_middleware()
    
    def _load_default_middleware(self):
        """加载默认中间件"""
        middleware_classes = []
        
        # 从设置中加载中间件
        for middleware_path in self.settings.MIDDLEWARE:
            try:
                # 动态导入中间件类
                module_path, class_name = middleware_path.rsplit('.', 1)
                module = __import__(module_path, fromlist=[class_name])
                middleware_class = getattr(module, class_name)
                middleware_classes.append(middleware_class)
            except (ImportError, AttributeError) as e:
                self.logger.warning(f"无法加载中间件 {middleware_path}: {e}")
        
        # 实例化中间件
        for middleware_class in middleware_classes:
            try:
                middleware_instance = middleware_class()
                self.middleware_stack.add(middleware_instance)
            except Exception as e:
                self.logger.warning(f"无法实例化中间件 {middleware_class}: {e}")
    
    def configure(self, **kwargs):
        """配置应用"""
        if kwargs:
            self.settings.update(**kwargs)
        
        # 配置日志
        self._configure_logging()
        
        # 初始化数据库连接池
        if self.settings.DATABASE.get('ENGINE'):
            self._configure_database()
        
        self.is_configured = True
    
    def _configure_logging(self):
        """配置日志"""
        logging.basicConfig(
            level=logging.DEBUG if self.settings.DEBUG else logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _configure_database(self):
        """配置数据库"""
        try:
            from .database.pool import DatabasePool
            self.db_pool = DatabasePool(self.settings.DATABASE)
        except ImportError as e:
            self.logger.warning(f"无法导入数据库模块: {e}")
    
    def add_route(self, path: str, view: Union[Callable, Type[View]], 
                  methods: List[str] = None, name: str = None, 
                  middleware: List[Middleware] = None):
        """添加路由"""
        # 处理类视图
        if isinstance(view, type) and issubclass(view, View):
            view = as_view(view)
        
        self.router.add_route(path, view, methods, name, middleware)
    
    def route(self, path: str, methods: List[str] = None, name: str = None, 
              middleware: List[Middleware] = None):
        """路由装饰器"""
        def decorator(func: Callable) -> Callable:
            self.add_route(path, func, methods, name, middleware)
            return func
        return decorator
    
    def get(self, path: str, name: str = None, middleware: List[Middleware] = None):
        """GET路由装饰器"""
        return self.route(path, ['GET'], name, middleware)
    
    def post(self, path: str, name: str = None, middleware: List[Middleware] = None):
        """POST路由装饰器"""
        return self.route(path, ['POST'], name, middleware)
    
    def put(self, path: str, name: str = None, middleware: List[Middleware] = None):
        """PUT路由装饰器"""
        return self.route(path, ['PUT'], name, middleware)
    
    def delete(self, path: str, name: str = None, middleware: List[Middleware] = None):
        """DELETE路由装饰器"""
        return self.route(path, ['DELETE'], name, middleware)
    
    def patch(self, path: str, name: str = None, middleware: List[Middleware] = None):
        """PATCH路由装饰器"""
        return self.route(path, ['PATCH'], name, middleware)
    
    def group(self, prefix: str, middleware: List[Middleware] = None) -> RouteGroup:
        """创建路由组"""
        from .router import RouteGroup
        return RouteGroup(prefix, self.router, middleware)
    
    def add_middleware(self, middleware: Middleware):
        """添加中间件"""
        self.middleware_stack.add(middleware)
    
    def include_router(self, router: Router, prefix: str = ""):
        """包含其他路由器"""
        for route in router.routes:
            full_path = prefix + route.path
            self.router.add_route(full_path, route.view, route.methods, 
                                route.name, route.middleware)
    
    def on_startup(self, handler: Callable):
        """注册启动处理器"""
        self.startup_handlers.append(handler)
        return handler
    
    def on_shutdown(self, handler: Callable):
        """注册关闭处理器"""
        self.shutdown_handlers.append(handler)
        return handler
    
    async def startup(self):
        """应用启动"""
        self.logger.info("正在启动Cyclone应用...")
        
        # 初始化数据库连接池
        if self.db_pool:
            await self.db_pool.initialize()
        
        # 执行启动处理器
        for handler in self.startup_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler()
                else:
                    handler()
            except Exception as e:
                self.logger.error(f"启动处理器执行失败: {e}", exc_info=True)
        
        self.logger.info("Cyclone应用启动完成")
    
    async def shutdown(self):
        """应用关闭"""
        self.logger.info("正在关闭Cyclone应用...")
        
        # 执行关闭处理器
        for handler in self.shutdown_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler()
                else:
                    handler()
            except Exception as e:
                self.logger.error(f"关闭处理器执行失败: {e}", exc_info=True)
        
        # 关闭数据库连接池
        if self.db_pool:
            await self.db_pool.close()
        
        self.is_running = False
        self.logger.info("Cyclone应用关闭完成")
    
    async def handle_request(self, request: Request) -> Response:
        """处理HTTP请求"""
        try:
            # 解析路由
            view_func, route_params, route_middleware = self.router.resolve(
                request.path, request.method
            )
            
            # 设置路由参数
            request.set_route_params(route_params)
            
            # 创建处理器（应用中间件）
            handler = view_func
            
            # 应用路由级中间件
            if route_middleware:
                for middleware in reversed(route_middleware):
                    middleware.app = handler
                    handler = middleware
            
            # 应用全局中间件
            handler = self.middleware_stack.create_handler(handler)
            
            # 执行处理器
            response = await handler(request)
            
            # 确保返回的是Response对象
            if not isinstance(response, Response):
                response = Response(str(response))
            
            return response
            
        except HTTPException as e:
            return ErrorResponse(e.message, e.status_code, e.headers)
        except Exception as e:
            self.logger.error(f"处理请求时发生错误: {e}", exc_info=True)
            
            if self.settings.DEBUG:
                import traceback
                error_message = traceback.format_exc()
                return ErrorResponse(error_message, 500, include_traceback=True)
            else:
                return ErrorResponse("内部服务器错误", 500)
    
    def create_server(self, host: str = None, port: int = None, **kwargs) -> AsyncHTTPServer:
        """创建HTTP服务器"""
        host = host or self.settings.HOST
        port = port or self.settings.PORT
        
        server_kwargs = {
            'backlog': self.settings.BACKLOG,
            'max_request_size': self.settings.MAX_REQUEST_SIZE,
            **kwargs
        }
        
        return create_server(self.handle_request, host, port, **server_kwargs)
    
    async def run_async(self, host: str = None, port: int = None, **kwargs):
        """异步运行应用"""
        if not self.is_configured:
            self.configure()
        
        # 启动应用
        await self.startup()
        
        # 创建并运行服务器
        server = self.create_server(host, port, **kwargs)
        
        try:
            self.is_running = True
            await server.serve_forever()
        except KeyboardInterrupt:
            self.logger.info("收到中断信号")
        except Exception as e:
            self.logger.error(f"服务器运行错误: {e}", exc_info=True)
        finally:
            await self.shutdown()
    
    def run(self, host: str = None, port: int = None, **kwargs):
        """运行应用"""
        try:
            asyncio.run(self.run_async(host, port, **kwargs))
        except KeyboardInterrupt:
            self.logger.info("应用被中断")
        except Exception as e:
            self.logger.error(f"应用运行错误: {e}", exc_info=True)
    
    def test_client(self):
        """创建测试客户端"""
        from .testing import TestClient
        return TestClient(self)
    
    def url_for(self, name: str, **params) -> str:
        """生成URL"""
        return self.router.url_for(name, **params)
    
    def get_routes(self) -> List[Dict[str, Any]]:
        """获取所有路由信息"""
        routes = []
        for route in self.router.routes:
            routes.append({
                'path': route.path,
                'methods': route.methods,
                'name': route.name,
                'view': route.view.__name__ if hasattr(route.view, '__name__') else str(route.view),
            })
        return routes
    
    def debug_info(self) -> Dict[str, Any]:
        """获取调试信息"""
        return {
            'settings': {
                'DEBUG': self.settings.DEBUG,
                'HOST': self.settings.HOST,
                'PORT': self.settings.PORT,
            },
            'routes': self.get_routes(),
            'middleware': [
                middleware.__class__.__name__ 
                for middleware in self.middleware_stack.middlewares
            ],
            'database': {
                'configured': self.db_pool is not None,
                'engine': self.settings.DATABASE.get('ENGINE'),
            },
            'status': {
                'configured': self.is_configured,
                'running': self.is_running,
            }
        }
    
    def __repr__(self) -> str:
        return f"<Cyclone Application: {len(self.router.routes)} routes>"


# 便捷函数

def create_app(settings: Optional[Settings] = None) -> Application:
    """创建应用实例"""
    return Application(settings)


def run_app(app: Application, host: str = None, port: int = None, **kwargs):
    """运行应用"""
    app.run(host, port, **kwargs)


async def run_app_async(app: Application, host: str = None, port: int = None, **kwargs):
    """异步运行应用"""
    await app.run_async(host, port, **kwargs)


# 全局应用实例（可选）
_default_app = None


def get_app() -> Optional[Application]:
    """获取默认应用实例"""
    return _default_app


def set_app(app: Application):
    """设置默认应用实例"""
    global _default_app
    _default_app = app


def create_default_app(settings: Optional[Settings] = None) -> Application:
    """创建并设置默认应用实例"""
    app = create_app(settings)
    set_app(app)
    return app 