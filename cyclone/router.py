"""
Cyclone 路由模块

提供URL路径映射到视图的路由功能
"""

import re
from typing import Dict, List, Tuple, Optional, Callable, Union, Any
from .exceptions import HTTPNotFound, HTTPMethodNotAllowed, RouterError
from .utils import extract_route_params


class Route:
    """路由记录"""
    
    def __init__(self, path: str, view: Callable, methods: List[str], 
                 name: str = None, middleware: List[Callable] = None):
        self.path = path
        self.view = view
        self.methods = [method.upper() for method in methods]
        self.name = name
        self.middleware = middleware or []
        
        # 编译路由正则表达式
        self.regex, self.param_names = self._compile_path(path)
    
    def _compile_path(self, path: str) -> Tuple[re.Pattern, List[str]]:
        """编译路由路径为正则表达式"""
        param_names = []
        regex_pattern = path
        
        # 查找所有参数 <param_name> 或 <param_name:type>
        param_matches = re.findall(r'<([^>]+)>', path)
        
        for param_match in param_matches:
            if ':' in param_match:
                param_name, param_type = param_match.split(':', 1)
            else:
                param_name, param_type = param_match, 'str'
            
            param_names.append(param_name)
            
            # 根据类型生成正则表达式
            if param_type == 'int':
                regex_replace = r'(?P<{}>\d+)'.format(param_name)
            elif param_type == 'float':
                regex_replace = r'(?P<{}>\d+\.\d+)'.format(param_name)
            elif param_type == 'uuid':
                regex_replace = r'(?P<{}>[0-9a-f]{{8}}-[0-9a-f]{{4}}-[0-9a-f]{{4}}-[0-9a-f]{{4}}-[0-9a-f]{{12}})'.format(param_name)
            elif param_type == 'path':
                regex_replace = r'(?P<{}>.+)'.format(param_name)
            else:  # str
                regex_replace = r'(?P<{}>[^/]+)'.format(param_name)
            
            regex_pattern = regex_pattern.replace(f'<{param_match}>', regex_replace)
        
        # 编译正则表达式
        try:
            compiled_regex = re.compile(f'^{regex_pattern}$')
        except re.error as e:
            raise RouterError(f"路由模式编译失败: {path}, 错误: {e}")
        
        return compiled_regex, param_names
    
    def match(self, path: str) -> Optional[Dict[str, Any]]:
        """匹配路径并提取参数"""
        match = self.regex.match(path)
        if not match:
            return None
        
        # 提取参数并转换类型
        params = {}
        for param_name, param_value in match.groupdict().items():
            # 根据参数名推断类型并转换
            if param_name in self.param_names:
                # 这里可以根据原始路径中的类型声明来转换
                # 为简化，我们使用智能转换
                if param_value.isdigit():
                    params[param_name] = int(param_value)
                elif param_value.replace('.', '', 1).isdigit():
                    params[param_name] = float(param_value)
                else:
                    params[param_name] = param_value
            else:
                params[param_name] = param_value
        
        return params
    
    def __repr__(self) -> str:
        return f"<Route {self.methods} {self.path}>"


class Router:
    """路由器"""
    
    def __init__(self):
        self.routes: List[Route] = []
        self.route_names: Dict[str, Route] = {}
    
    def add_route(self, path: str, view: Callable, methods: List[str] = None,
                  name: str = None, middleware: List[Callable] = None):
        """添加路由"""
        if methods is None:
            methods = ['GET']
        
        # 验证方法
        valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
        for method in methods:
            if method.upper() not in valid_methods:
                raise RouterError(f"不支持的HTTP方法: {method}")
        
        # 创建路由
        route = Route(path, view, methods, name, middleware)
        self.routes.append(route)
        
        # 如果有名称，添加到名称映射
        if name:
            if name in self.route_names:
                raise RouterError(f"路由名称已存在: {name}")
            self.route_names[name] = route
    
    def resolve(self, path: str, method: str = 'GET') -> Tuple[Callable, Dict[str, Any], List[Callable]]:
        """解析路径，返回视图函数、参数和中间件"""
        method = method.upper()
        matched_routes = []
        
        # 查找匹配的路由
        for route in self.routes:
            params = route.match(path)
            if params is not None:
                matched_routes.append((route, params))
        
        if not matched_routes:
            raise HTTPNotFound(f"未找到路径: {path}")
        
        # 检查HTTP方法
        allowed_methods = set()
        for route, params in matched_routes:
            allowed_methods.update(route.methods)
            if method in route.methods:
                return route.view, params, route.middleware
        
        # 如果找到路径但方法不匹配
        raise HTTPMethodNotAllowed(
            f"方法 {method} 不允许用于路径 {path}。允许的方法: {', '.join(allowed_methods)}"
        )
    
    def get_route_by_name(self, name: str) -> Optional[Route]:
        """通过名称获取路由"""
        return self.route_names.get(name)
    
    def url_for(self, name: str, **params) -> str:
        """根据路由名称和参数生成URL"""
        route = self.get_route_by_name(name)
        if not route:
            raise RouterError(f"未找到路由名称: {name}")
        
        url = route.path
        
        # 替换参数
        for param_name, param_value in params.items():
            # 查找参数模式
            param_pattern = f'<{param_name}>'
            if param_pattern in url:
                url = url.replace(param_pattern, str(param_value))
                continue
            
            # 查找带类型的参数模式
            for param_match in re.findall(r'<([^>]+)>', url):
                if ':' in param_match:
                    name_part, type_part = param_match.split(':', 1)
                    if name_part == param_name:
                        url = url.replace(f'<{param_match}>', str(param_value))
                        break
        
        return url
    
    def get_all_routes(self) -> List[Route]:
        """获取所有路由"""
        return self.routes.copy()
    
    def remove_route(self, path: str, methods: List[str] = None):
        """移除路由"""
        if methods is None:
            methods = ['GET']
        
        methods = [method.upper() for method in methods]
        
        # 查找并移除匹配的路由
        routes_to_remove = []
        for route in self.routes:
            if route.path == path and any(method in route.methods for method in methods):
                routes_to_remove.append(route)
        
        for route in routes_to_remove:
            self.routes.remove(route)
            # 如果有名称，也从名称映射中移除
            if route.name and route.name in self.route_names:
                del self.route_names[route.name]
    
    def clear(self):
        """清空所有路由"""
        self.routes.clear()
        self.route_names.clear()
    
    def __len__(self) -> int:
        return len(self.routes)
    
    def __iter__(self):
        return iter(self.routes)


class RouteGroup:
    """路由组，用于批量添加具有相同前缀的路由"""
    
    def __init__(self, prefix: str, router: Router, middleware: List[Callable] = None):
        self.prefix = prefix.rstrip('/')
        self.router = router
        self.middleware = middleware or []
    
    def add_route(self, path: str, view: Callable, methods: List[str] = None,
                  name: str = None, middleware: List[Callable] = None):
        """添加路由到组"""
        full_path = self.prefix + path
        
        # 合并中间件
        combined_middleware = self.middleware.copy()
        if middleware:
            combined_middleware.extend(middleware)
        
        self.router.add_route(full_path, view, methods, name, combined_middleware)
    
    def group(self, prefix: str, middleware: List[Callable] = None) -> 'RouteGroup':
        """创建子组"""
        full_prefix = self.prefix + prefix
        
        # 合并中间件
        combined_middleware = self.middleware.copy()
        if middleware:
            combined_middleware.extend(middleware)
        
        return RouteGroup(full_prefix, self.router, combined_middleware)
    
    def get(self, path: str, view: Callable, name: str = None, middleware: List[Callable] = None):
        """GET路由的便捷方法"""
        self.add_route(path, view, ['GET'], name, middleware)
    
    def post(self, path: str, view: Callable, name: str = None, middleware: List[Callable] = None):
        """POST路由的便捷方法"""
        self.add_route(path, view, ['POST'], name, middleware)
    
    def put(self, path: str, view: Callable, name: str = None, middleware: List[Callable] = None):
        """PUT路由的便捷方法"""
        self.add_route(path, view, ['PUT'], name, middleware)
    
    def delete(self, path: str, view: Callable, name: str = None, middleware: List[Callable] = None):
        """DELETE路由的便捷方法"""
        self.add_route(path, view, ['DELETE'], name, middleware)
    
    def patch(self, path: str, view: Callable, name: str = None, middleware: List[Callable] = None):
        """PATCH路由的便捷方法"""
        self.add_route(path, view, ['PATCH'], name, middleware)


# 便捷函数

def create_router() -> Router:
    """创建新的路由器"""
    return Router()


def create_route_group(prefix: str, router: Router, middleware: List[Callable] = None) -> RouteGroup:
    """创建路由组"""
    return RouteGroup(prefix, router, middleware) 