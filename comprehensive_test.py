'''
Author: jiaochanghao jch_2154195820@163.com
Date: 2025-07-03 11:24:38
LastEditors: jiaochanghao jch_2154195820@163.com
LastEditTime: 2025-07-03 11:57:26
FilePath: /Cyclone/comprehensive_test.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
#!/usr/bin/env python3
"""
Cyclone Framework 综合测试示例

完整测试框架的所有功能：
- 自定义配置系统
- 中间件系统（内置和自定义）
- 视图系统（函数视图和类视图）
- 路由系统（静态和动态路由）
- 数据库操作（模型和ORM）
- 请求处理和响应生成
"""

import asyncio
import time
import json
import sys
from datetime import datetime
from cyclone import (
    Application, JSONResponse, HTMLResponse, 
    View, JSONView, TemplateView,
    Model, CharField, IntegerField, DateTimeField, BooleanField,
    Middleware, CORSMiddleware, RequestLoggingMiddleware,
    get_settings, configure_from_dict, configure_database,
    route, require_POST, require_GET, as_view
)

# ================================
# 1. 自定义配置测试
# ================================

def setup_custom_config():
    """设置自定义配置"""
    print("🔧 正在设置自定义配置...")
    
    custom_config = {
        'DEBUG': True,
        'HOST': '127.0.0.1',
        'PORT': 8888,
        'APP_NAME': 'Cyclone综合测试应用',
        'VERSION': '1.0.0',
        'AUTHOR': '0716gzs',
        
        # 数据库配置（MySQL测试）
        'DATABASE': {
            'ENGINE': 'aiomysql',
            'NAME': 'test_cyclone',
            'USER': 'root',
            'PASSWORD': '0716gzs.cn',
            'HOST': 'localhost',
            'PORT': 3306,
            'POOL_SIZE': 5,
            'MAX_OVERFLOW': 10,
        },
        
        # 功能开关
        'FEATURE_FLAGS': {
            'ENABLE_API_DOCS': True,
            'ENABLE_METRICS': True,
            'ENABLE_CACHE': True,
        },
        
        # API配置
        'API_RATE_LIMIT': 1000,
        'API_VERSION': 'v1',
    }
    
    configure_from_dict(custom_config, merge=True)
    
    settings = get_settings()
    print(f"✅ 配置加载完成 - 应用名称: {settings.APP_NAME}")
    print(f"✅ 数据库引擎: {settings.DATABASE['ENGINE']}")
    print(f"✅ 功能标志: {settings.FEATURE_FLAGS}")
    
    return settings

# ================================
# 2. 数据模型测试
# ================================

class User(Model):
    """用户模型"""
    __table__ = 'test_users'
    
    id = IntegerField(primary_key=True)
    username = CharField(max_length=50, unique=True, nullable=False)
    email = CharField(max_length=100, unique=True, nullable=False)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)

class Post(Model):
    """文章模型"""
    __table__ = 'test_posts'
    
    id = IntegerField(primary_key=True)
    title = CharField(max_length=200, nullable=False)
    content = CharField(max_length=10000)
    author_id = IntegerField(nullable=False)
    is_published = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)

# ================================
# 3. 自定义中间件测试
# ================================

class RequestTimingMiddleware(Middleware):
    """请求计时中间件"""
    
    async def process_request(self, request):
        request.start_time = time.time()
        return request
    
    async def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            response.set_header('X-Response-Time', f"{duration:.3f}s")
        return response

class CustomAuthMiddleware(Middleware):
    """自定义认证中间件"""
    
    async def process_request(self, request):
        # 简单的API Key认证
        if request.path.startswith('/api/'):
            api_key = request.get_header('x-api-key')
            if not api_key:
                return JSONResponse({'error': '缺少API密钥'}, status=401)
            
            if api_key != 'test-api-key-123':
                return JSONResponse({'error': 'API密钥无效'}, status=401)
            
            # 设置用户信息
            request.user = {'api_key': api_key, 'authenticated': True}
        
        return request

class ResponseHeaderMiddleware(Middleware):
    """响应头中间件"""
    
    async def process_response(self, request, response):
        response.set_header('X-Powered-By', 'Cyclone/1.0.0')
        response.set_header('X-Content-Type-Options', 'nosniff')
        return response

# ================================
# 4. 视图系统测试
# ================================

class HomeView(TemplateView):
    """首页视图"""
    
    async def get(self, request, **kwargs):
        settings = get_settings()
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{settings.APP_NAME}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .feature {{ margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 5px; }}
                .endpoint {{ margin: 10px 0; padding: 10px; background: #e9ecef; border-radius: 3px; }}
                .method {{ color: #007bff; font-weight: bold; }}
                .status {{ color: #28a745; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🌪️ {settings.APP_NAME}</h1>
                    <p>版本: {settings.VERSION} | 作者: {settings.AUTHOR}</p>
                    <div class="status">✅ 框架测试环境已启动</div>
                </div>
                
                <div class="feature">
                    <h2>📋 可用的测试端点</h2>
                    
                    <div class="endpoint">
                        <span class="method">GET</span> <code>/</code> - 首页（当前页面）
                    </div>
                    
                    <div class="endpoint">
                        <span class="method">GET</span> <code>/api/status</code> - 系统状态 (需要API密钥)
                    </div>
                    
                    <div class="endpoint">
                        <span class="method">GET</span> <code>/api/users</code> - 用户列表 (需要API密钥)
                    </div>
                    
                    <div class="endpoint">
                        <span class="method">POST</span> <code>/api/users</code> - 创建用户 (需要API密钥)
                    </div>
                    
                    <div class="endpoint">
                        <span class="method">GET</span> <code>/api/users/&lt;user_id&gt;</code> - 用户详情 (需要API密钥)
                    </div>
                    
                    <div class="endpoint">
                        <span class="method">GET</span> <code>/posts</code> - 文章列表
                    </div>
                    
                    <div class="endpoint">
                        <span class="method">POST</span> <code>/posts</code> - 创建文章
                    </div>
                    
                    <div class="endpoint">
                        <span class="method">GET</span> <code>/config</code> - 配置信息
                    </div>
                    
                    <div class="endpoint">
                        <span class="method">GET</span> <code>/test/middleware</code> - 中间件测试
                    </div>
                </div>
                
                <div class="feature">
                    <h2>🔑 API使用说明</h2>
                    <p>所有 <code>/api/</code> 端点需要在请求头中包含:</p>
                    <pre>X-API-Key: test-api-key-123</pre>
                </div>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(html_content)

class APIStatusView(JSONView):
    """API状态视图"""
    
    async def get(self, request, **kwargs):
        settings = get_settings()
        
        status_data = {
            'status': 'ok',
            'app_name': settings.APP_NAME,
            'version': settings.VERSION,
            'timestamp': datetime.now().isoformat(),
            'features': settings.FEATURE_FLAGS,
            'authenticated': hasattr(request, 'user'),
            'user_info': getattr(request, 'user', None),
            'database': {
                'engine': settings.DATABASE['ENGINE'],
                'name': settings.DATABASE['NAME'],
                'pool_size': settings.DATABASE['POOL_SIZE'],
            }
        }
        
        return JSONResponse(status_data)

class UserAPIView(View):
    """用户API视图"""
    
    async def get(self, request, **kwargs):
        """获取用户列表或单个用户"""
        user_id = kwargs.get('user_id')
        
        if user_id:
            # 返回单个用户（模拟数据）
            user_data = {
                'id': user_id,
                'username': f'user_{user_id}',
                'email': f'user_{user_id}@example.com',
                'is_active': True,
                'created_at': datetime.now().isoformat()
            }
            return JSONResponse(user_data)
        else:
            # 返回用户列表（模拟数据）
            users = [
                {
                    'id': i,
                    'username': f'user_{i}',
                    'email': f'user_{i}@example.com',
                    'is_active': True,
                    'created_at': datetime.now().isoformat()
                }
                for i in range(1, 6)
            ]
            
            return JSONResponse({
                'users': users,
                'total': len(users),
                'page': 1
            })
    
    async def post(self, request, **kwargs):
        """创建用户"""
        try:
            data = await request.json()
            
            # 验证必需字段
            if not data.get('username') or not data.get('email'):
                return JSONResponse(
                    {'error': '用户名和邮箱不能为空'}, 
                    status=400
                )
            
            # 模拟创建用户
            new_user = {
                'id': 999,  # 模拟生成的ID
                'username': data['username'],
                'email': data['email'],
                'is_active': True,
                'created_at': datetime.now().isoformat()
            }
            
            return JSONResponse(new_user, status=201)
            
        except Exception as e:
            return JSONResponse(
                {'error': f'创建用户失败: {str(e)}'}, 
                status=400
            )

# ================================
# 5. 函数视图测试
# ================================

@route('/config', methods=['GET'])
async def config_view(request):
    """配置信息视图"""
    settings = get_settings()
    
    # 获取所有配置（隐藏敏感信息）
    config_dict = settings.to_dict()
    
    # 隐藏敏感信息
    if 'SECRET_KEY' in config_dict:
        config_dict['SECRET_KEY'] = '***隐藏***'
    
    if 'DATABASE' in config_dict and 'PASSWORD' in config_dict['DATABASE']:
        config_dict['DATABASE']['PASSWORD'] = '***隐藏***'
    
    return JSONResponse({
        'config': config_dict,
        'total_items': len(config_dict)
    }, indent=2)

@route('/test/middleware', methods=['GET'])
async def middleware_test(request):
    """中间件测试视图"""
    
    response_data = {
        'message': '中间件测试成功',
        'request_info': {
            'method': request.method,
            'path': request.path,
            'headers': dict(request.headers),
            'client_ip': request.client_ip,
            'user_agent': request.user_agent,
        },
        'middleware_data': {
            'has_start_time': hasattr(request, 'start_time'),
            'is_authenticated': hasattr(request, 'user'),
            'user_info': getattr(request, 'user', None),
        },
        'timestamp': datetime.now().isoformat()
    }
    
    return JSONResponse(response_data, indent=2)

# ================================
# 6. 测试函数
# ================================

def run_configuration_tests():
    """运行配置测试"""
    print("\n" + "="*50)
    print("🧪 运行配置系统测试...")
    print("="*50)
    
    settings = get_settings()
    
    # 测试配置获取
    assert settings.APP_NAME == 'Cyclone综合测试应用'
    assert settings.VERSION == '1.0.0'
    assert settings.DATABASE['ENGINE'] == 'aiomysql'
    
    # 测试配置验证
    settings.add_validator('PORT', lambda x: isinstance(x, int) and 1 <= x <= 65535)
    
    try:
        settings.set('PORT', 99999)  # 应该失败
        assert False, "端口验证应该失败"
    except ValueError:
        print("✅ 配置验证器工作正常")
    
    # 测试配置钩子
    hook_called = []
    def test_hook(key, value):
        hook_called.append((key, value))
    
    settings.add_config_hook(test_hook)
    settings.set('TEST_VALUE', 'test')
    
    assert hook_called, "配置钩子应该被调用"
    print("✅ 配置钩子工作正常")
    
    print("✅ 所有配置测试通过!")

def run_model_tests():
    """运行模型测试"""
    print("\n" + "="*50)
    print("🧪 运行数据模型测试...")
    print("="*50)
    
    # 测试用户模型
    user = User(username='testuser', email='test@example.com')
    
    assert user.username == 'testuser', f"预期 'testuser'，实际得到 '{user.username}'"
    assert user.email == 'test@example.com', f"预期 'test@example.com'，实际得到 '{user.email}'"
    assert user.is_active == True, f"预期 True，实际得到 {user.is_active}"  # 默认值
    print("✅ 用户模型创建成功")
    
    # 测试文章模型
    post = Post(title='测试文章', content='这是测试内容', author_id=1)
    
    assert post.title == '测试文章', f"预期 '测试文章'，实际得到 '{post.title}'"
    assert post.content == '这是测试内容', f"预期 '这是测试内容'，实际得到 '{post.content}'"
    assert post.is_published == False, f"预期 False，实际得到 {post.is_published}"  # 默认值
    print("✅ 文章模型创建成功")
    
    print("✅ 所有模型测试通过!")

async def run_integration_tests():
    """运行集成测试"""
    print("\n" + "="*50)
    print("🧪 运行集成测试...")
    print("="*50)
    
    app = create_test_app()
    
    # 测试路由解析
    try:
        view_func, route_params, middleware = app.router.resolve('/', 'GET')
        print("✅ 根路由解析成功")
        
        view_func, route_params, middleware = app.router.resolve('/api/users/123', 'GET')
        assert route_params['user_id'] == 123
        print("✅ 动态路由解析成功")
        
    except Exception as e:
        print(f"❌ 路由测试失败: {e}")
        return False
    
    print("✅ 所有集成测试通过!")
    return True

def create_test_app():
    """创建测试应用"""
    print("🚀 正在创建Cyclone测试应用...")
    
    # 获取当前设置（应该已经通过setup_custom_config设置了）
    settings = get_settings()
    
    # 创建应用实例
    app = Application(settings)
    
    # 添加自定义中间件
    print("🔧 正在添加中间件...")
    app.add_middleware(RequestTimingMiddleware())
    app.add_middleware(CORSMiddleware(
        allow_origins=["*"],
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"]
    ))
    app.add_middleware(CustomAuthMiddleware())
    app.add_middleware(RequestLoggingMiddleware())
    app.add_middleware(ResponseHeaderMiddleware())
    
    # 注册路由
    print("🛣️ 正在注册路由...")
    
    # 类视图路由
    app.add_route('/', HomeView, name='home')
    app.add_route('/api/status', APIStatusView, name='api_status')
    app.add_route('/api/users', UserAPIView, name='user_list')
    app.add_route('/api/users/<user_id:int>', UserAPIView, name='user_detail')
    
    # 添加应用生命周期钩子
    @app.on_startup
    async def startup():
        print("✅ 应用启动完成!")
        if not ('--test-only' in sys.argv):
            print(f"🌐 访问地址: http://{settings.HOST}:{settings.PORT}")
            print("📖 查看完整测试说明请访问首页")
    
    @app.on_shutdown
    async def shutdown():
        print("👋 应用已关闭")
    
    print(f"✅ 应用创建完成 - 共注册 {len(app.get_routes())} 个路由")
    
    return app

def main():
    """主测试函数"""
    print("🌪️ Cyclone Framework 综合测试")
    print("=" * 60)
    
    # 检查命令行参数
    test_only = '--test-only' in sys.argv
    
    try:
        # 首先设置自定义配置
        setup_custom_config()
        
        # 运行各项测试
        run_configuration_tests()
        run_model_tests()
        
        # 运行集成测试
        success = asyncio.run(run_integration_tests())
        
        if success:
            print("\n" + "="*60)
            print("🎉 所有测试通过!")
            
            if test_only:
                print("✅ CI测试模式 - 测试完成，不启动服务器")
                return
            
            print("准备启动测试服务器...")
            print("="*60)
            
            # 创建并运行应用
            app = create_test_app()
            
            print("\n🔥 启动测试服务器...")
            print("💡 提示: 按 Ctrl+C 停止服务器")
            print("-" * 60)
            
            app.run()
        
    except KeyboardInterrupt:
        print("\n⏹️ 测试被中断")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        if test_only:
            sys.exit(1)

if __name__ == "__main__":
    main()
