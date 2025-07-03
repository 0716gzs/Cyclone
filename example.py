#!/usr/bin/env python3
"""
Cyclone 框架示例应用

演示如何使用Cyclone框架构建异步Web应用
"""

import asyncio
from cyclone import (
    Application, JSONResponse, HTMLResponse,
    View, JSONView, route, require_POST,
    CORSMiddleware, RequestLoggingMiddleware,
    Model, CharField, IntegerField, DateTimeField,
    Settings
)


# 1. 定义数据模型
class User(Model):
    """用户模型"""
    __table__ = 'users'
    
    id = IntegerField(primary_key=True)
    name = CharField(max_length=100, nullable=False)
    email = CharField(max_length=255, unique=True, nullable=False)
    created_at = DateTimeField(auto_now_add=True)


# 2. 定义视图
class IndexView(View):
    """首页视图"""
    
    async def get(self, request, **kwargs):
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Cyclone 框架演示</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 800px; margin: 0 auto; }
                .endpoint { margin: 20px 0; padding: 15px; background: #f5f5f5; border-radius: 5px; }
                .method { color: #007bff; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🌪️ Cyclone 异步Web框架</h1>
                <p>欢迎使用Cyclone框架！这是一个基于协程和异步I/O的高性能Web框架。</p>
                
                <h2>📋 可用端点</h2>
                
                <div class="endpoint">
                    <span class="method">GET</span> <code>/</code> - 首页
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> <code>/api/hello</code> - JSON API示例
                </div>
                
                <div class="endpoint">
                    <span class="method">POST</span> <code>/api/echo</code> - 回显数据
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> <code>/api/users</code> - 用户列表
                </div>
                
                <div class="endpoint">
                    <span class="method">POST</span> <code>/api/users</code> - 创建用户
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> <code>/api/users/&lt;user_id:int&gt;</code> - 获取用户详情
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> <code>/debug</code> - 调试信息
                </div>
                
                <h2>🚀 功能特性</h2>
                <ul>
                    <li>✅ 基于asyncio的异步I/O</li>
                    <li>✅ 路由系统（支持参数）</li>
                    <li>✅ 中间件支持</li>
                    <li>✅ 类视图和函数视图</li>
                    <li>✅ JSON/HTML响应</li>
                    <li>✅ 异步ORM模型</li>
                    <li>✅ CORS支持</li>
                    <li>✅ 请求日志</li>
                </ul>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(html_content)


class APIView(JSONView):
    """API基础视图"""
    
    async def get_data(self, **kwargs):
        return {
            "message": "Hello from Cyclone!",
            "framework": "Cyclone",
            "version": "0.1.0",
            "async": True,
            "timestamp": "2024-01-01T00:00:00Z"
        }


class UserListView(JSONView):
    """用户列表视图"""
    
    async def get(self, request, **kwargs):
        # 模拟用户数据
        users = [
            {"id": 1, "name": "张三", "email": "zhangsan@example.com"},
            {"id": 2, "name": "李四", "email": "lisi@example.com"},
            {"id": 3, "name": "王五", "email": "wangwu@example.com"},
        ]
        return JSONResponse({
            "users": users,
            "total": len(users)
        })
    
    @require_POST
    async def post(self, request, **kwargs):
        # 创建用户
        data = await request.json()
        
        # 验证数据
        if not data.get("name") or not data.get("email"):
            return JSONResponse(
                {"error": "姓名和邮箱不能为空"}, 
                status=400
            )
        
        # 模拟创建用户
        new_user = {
            "id": 4,
            "name": data["name"],
            "email": data["email"],
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        return JSONResponse(new_user, status=201)


class UserDetailView(JSONView):
    """用户详情视图"""
    
    async def get(self, request, **kwargs):
        user_id = kwargs.get("user_id")
        
        # 模拟查找用户
        if user_id == 1:
            user = {"id": 1, "name": "张三", "email": "zhangsan@example.com"}
        elif user_id == 2:
            user = {"id": 2, "name": "李四", "email": "lisi@example.com"}
        else:
            return JSONResponse({"error": "用户不存在"}, status=404)
        
        return JSONResponse(user)


# 3. 函数视图示例
@route("/api/echo", methods=["POST"])
async def echo_view(request):
    """回显视图"""
    try:
        data = await request.json()
        return JSONResponse({
            "echo": data,
            "method": request.method,
            "path": request.path,
            "content_type": request.content_type
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status=400)


async def debug_view(request):
    """调试信息视图"""
    app = request.get_extra("app")  # 假设中间件设置了这个
    
    debug_info = {
        "request": {
            "method": request.method,
            "path": request.path,
            "headers": dict(request.headers),
            "query_params": request.query_params,
            "client_ip": request.client_ip,
            "user_agent": request.user_agent,
        },
        "framework": {
            "name": "Cyclone",
            "version": "0.1.0",
        }
    }
    
    return JSONResponse(debug_info, indent=2)


# 4. 自定义中间件
class CustomHeaderMiddleware:
    """自定义头部中间件"""
    
    def __init__(self, app=None):
        self.app = app
    
    async def __call__(self, request):
        response = await self.app(request)
        response.set_header("X-Powered-By", "Cyclone/0.1.0")
        response.set_header("X-Custom-Header", "Hello from Cyclone!")
        return response


# 5. 创建应用
def create_cyclone_app():
    """创建Cyclone应用"""
    
    # 创建自定义设置
    settings = Settings()
    settings.DEBUG = True
    settings.HOST = "127.0.0.1"
    settings.PORT = 8000
    
    # 创建应用
    app = Application(settings)
    
    # 添加中间件
    app.add_middleware(CORSMiddleware(
        allow_origins=["*"],
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"]
    ))
    app.add_middleware(RequestLoggingMiddleware())
    app.add_middleware(CustomHeaderMiddleware())
    
    # 注册路由
    app.add_route("/", IndexView, name="index")
    app.add_route("/api/hello", APIView, name="api_hello")
    app.add_route("/api/users", UserListView, name="user_list")
    app.add_route("/api/users/<user_id:int>", UserDetailView, name="user_detail")
    app.add_route("/debug", debug_view, name="debug")
    
    # 使用装饰器注册的路由会自动添加
    
    # 添加启动和关闭处理器
    @app.on_startup
    async def startup():
        print("🌪️ Cyclone应用启动完成!")
        print(f"📍 访问地址: http://{settings.HOST}:{settings.PORT}")
        print("📚 查看所有可用端点请访问: /")
    
    @app.on_shutdown
    async def shutdown():
        print("👋 Cyclone应用已关闭")
    
    return app


# 6. 主程序
def main():
    """主程序入口"""
    print("🚀 启动Cyclone框架演示应用...")
    
    # 创建应用
    app = create_cyclone_app()
    
    # 显示路由信息
    print("\n📋 注册的路由:")
    for route_info in app.get_routes():
        methods = "/".join(route_info["methods"])
        print(f"  [{methods}] {route_info['path']} -> {route_info['view']}")
    
    print("\n🌟 框架特性演示:")
    print("  - 异步I/O处理")
    print("  - 路由参数解析")
    print("  - 中间件支持")
    print("  - JSON/HTML响应")
    print("  - CORS支持")
    print("  - 请求日志记录")
    
    # 运行应用
    try:
        app.run()
    except KeyboardInterrupt:
        print("\n⏹️ 收到中断信号，正在关闭应用...")


if __name__ == "__main__":
    main() 