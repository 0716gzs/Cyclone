# 🌪️ Cyclone 异步Web后端框架

Cyclone是一个现代化的异步Web后端框架，基于Python的协程(coroutine)和异步I/O模型构建，提供高性能的Web服务开发体验。

## ✨ 核心特性

- 🚀 **纯异步架构** - 基于asyncio，支持高并发处理
- 🎯 **简洁易用** - 清晰的API设计，易于学习和使用
- 🔧 **模块化设计** - 路由、中间件、视图、模型完全解耦
- 🛡️ **内置安全** - CORS、安全头部、输入验证等安全特性
- 📊 **ORM支持** - 异步数据库操作，支持多种数据库
- 🎨 **灵活响应** - 支持JSON、HTML、文件等多种响应类型
- 🔀 **中间件系统** - 强大的中间件支持，易于扩展
- 📝 **类型提示** - 完整的类型注解，更好的开发体验

## 🏗️ 框架架构

```
┌─────────────────────────────────────────────┐
│                客户端请求                      │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│            异步HTTP服务器                     │
│         (基于asyncio.Protocol)              │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│              中间件栈                        │
│   CORS → 安全 → 日志 → 认证 → 自定义          │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│              路由系统                        │
│        URL解析 → 视图匹配                     │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│              视图层                          │
│      函数视图 / 类视图 / 装饰器视图             │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│             模型层(ORM)                      │
│       异步数据库操作 → 连接池管理               │
└─────────────────────────────────────────────┘
```

## 🚀 快速开始

### 安装

```bash
# 克隆项目
git clone <repository-url>
cd Cyclone

# 安装MySQL依赖
pip install aiomysql
```

### Hello World

```python
from cyclone import Application, JSONResponse

# 创建应用
app = Application()

# 定义视图
@app.get("/")
async def hello(request):
    return JSONResponse({"message": "Hello, Cyclone!"})

# 运行应用
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
```

### 完整示例

```python
from cyclone import (
    Application, JSONResponse, HTMLResponse,
    View, Model, CharField, IntegerField,
    CORSMiddleware, require_POST
)

# 1. 定义模型
class User(Model):
    __table__ = 'users'
    
    id = IntegerField(primary_key=True)
    name = CharField(max_length=100, nullable=False)
    email = CharField(max_length=255, unique=True)

# 2. 定义视图
class UserView(View):
    async def get(self, request, **kwargs):
        users = await User.objects().all()
        return JSONResponse([user.to_dict() for user in users])
    
    @require_POST
    async def post(self, request, **kwargs):
        data = await request.json()
        user = await User.create(**data)
        return JSONResponse(user.to_dict(), status=201)

# 3. 创建应用
app = Application()

# 4. 添加中间件
app.add_middleware(CORSMiddleware(allow_origins=["*"]))

# 5. 注册路由
app.add_route("/users", UserView)
app.add_route("/users/<user_id:int>", UserView)

# 6. 运行应用
app.run()
```

## 📋 详细文档

### 路由系统

```python
# 基础路由
@app.get("/hello")
async def hello(request):
    return JSONResponse({"message": "Hello"})

# 带参数的路由
@app.get("/users/<user_id:int>")
async def get_user(request, user_id):
    return JSONResponse({"user_id": user_id})

# 支持的参数类型
@app.get("/path/<str_param>")           # 字符串
@app.get("/path/<int_param:int>")       # 整数
@app.get("/path/<float_param:float>")   # 浮点数
@app.get("/path/<uuid_param:uuid>")     # UUID
@app.get("/path/<path_param:path>")     # 路径（包含/）

# 路由组
api_group = app.group("/api/v1")
api_group.get("/users", user_list_view)
api_group.post("/users", create_user_view)
```

### 视图系统

#### 函数视图

```python
# 基础函数视图
async def my_view(request):
    return JSONResponse({"status": "ok"})

# 装饰器视图
@route("/api/data", methods=["GET", "POST"])
@require_POST  # 只允许POST
@csrf_exempt   # CSRF豁免
async def data_view(request):
    data = await request.json()
    return JSONResponse(data)
```

#### 类视图

```python
class APIView(View):
    async def get(self, request, **kwargs):
        return JSONResponse({"method": "GET"})
    
    async def post(self, request, **kwargs):
        data = await request.json()
        return JSONResponse({"received": data})

# 特殊视图类
class MyTemplateView(TemplateView):
    template_name = "my_template.html"
    
    async def get_context_data(self, **kwargs):
        return {"title": "My Page"}

class UserListView(ListView):
    model = User
    
    async def get_queryset(self):
        return await User.objects().filter(active=True)
```

### 请求处理

```python
async def handle_request(request):
    # 基础属性
    method = request.method        # HTTP方法
    path = request.path           # 请求路径
    headers = request.headers     # 请求头部
    
    # 查询参数
    param = request.get_query_param("param", "default")
    
    # 路由参数
    user_id = request.get_route_param("user_id")
    
    # 请求体
    json_data = await request.json()      # JSON数据
    form_data = await request.form()      # 表单数据
    files = await request.files()         # 文件上传
    text = await request.text()           # 文本数据
    bytes_data = await request.bytes()    # 字节数据
    
    # 客户端信息
    ip = request.client_ip
    user_agent = request.user_agent
    is_ajax = request.is_ajax
    is_secure = request.is_secure
```

### 响应类型

```python
# JSON响应
return JSONResponse({"data": "value"})
return JSONResponse(data, status=201, headers={"Custom": "Header"})

# HTML响应
return HTMLResponse("<h1>Hello</h1>")

# 文本响应
return PlainTextResponse("Hello World")

# 文件响应
return FileResponse("path/to/file.pdf")

# 重定向响应
return RedirectResponse("/new-url", status=302)

# 流响应（大文件）
async def file_generator():
    with open("large_file.txt", "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            yield chunk

return StreamResponse(file_generator())

# 错误响应
return ErrorResponse("Something went wrong", status=500)
```

### 中间件系统

#### 内置中间件

```python
from cyclone import (
    CORSMiddleware, SecurityMiddleware, 
    RequestLoggingMiddleware, RateLimitMiddleware,
    CompressionMiddleware, AuthenticationMiddleware
)

app.add_middleware(CORSMiddleware(
    allow_origins=["https://example.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization"]
))

app.add_middleware(SecurityMiddleware(
    force_https=True,
    hsts_max_age=31536000
))

app.add_middleware(RequestLoggingMiddleware())
app.add_middleware(RateLimitMiddleware(max_requests=100, window_seconds=60))
app.add_middleware(CompressionMiddleware())
```

#### 自定义中间件

```python
class CustomMiddleware:
    def __init__(self, app=None):
        self.app = app
    
    async def __call__(self, request):
        # 请求处理前
        start_time = time.time()
        
        # 调用下一个中间件/视图
        response = await self.app(request)
        
        # 响应处理后
        process_time = time.time() - start_time
        response.set_header("X-Process-Time", str(process_time))
        
        return response

app.add_middleware(CustomMiddleware())
```

### 数据模型

```python
from cyclone import (
    Model, CharField, IntegerField, FloatField,
    BooleanField, DateTimeField, JSONField, ForeignKey
)

class User(Model):
    __table__ = 'users'
    
    id = IntegerField(primary_key=True)
    username = CharField(max_length=50, unique=True, nullable=False)
    email = CharField(max_length=100, unique=True, nullable=False)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    profile = JSONField(default=dict)

class Post(Model):
    __table__ = 'posts'
    
    id = IntegerField(primary_key=True)
    title = CharField(max_length=200, nullable=False)
    content = CharField(max_length=10000)
    author = ForeignKey(User, on_delete='CASCADE')
    is_published = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)

# 使用模型
async def user_operations():
    # 创建用户
    user = await User.create(
        username="john",
        email="john@example.com"
    )
    
    # 查询用户
    user = await User.get(id=1)
    users = await User.filter(is_active=True)
    
    # 更新用户
    user.email = "newemail@example.com"
    await user.save()
    
    # 删除用户
    await user.delete()
    
    # 复杂查询
    active_users = await User.objects().filter(
        is_active=True
    ).order_by("created_at").limit(10)
```

### 数据库配置

```python
from cyclone import Settings, Application

# 配置设置
settings = Settings()
settings.DATABASE = {
    'ENGINE': 'aiomysql',
    'NAME': 'mydb',
    'USER': 'root',
    'PASSWORD': 'password',
    'HOST': 'localhost',
    'PORT': 3306,
    'POOL_SIZE': 10,
    'MAX_OVERFLOW': 20,
}

app = Application(settings)

# 或使用连接URL
settings.DATABASE = {
    'URL': 'mysql://root:password@localhost:3306/mydb'
}
```

### 应用配置

```python
from cyclone import Settings, configure

# 方式1: 直接设置
settings = Settings()
settings.DEBUG = True
settings.HOST = "0.0.0.0"
settings.PORT = 8080

# 方式2: 环境变量
# DEBUG=True HOST=0.0.0.0 PORT=8080 python app.py

# 方式3: 配置文件
configure('myproject.settings')

# 方式4: 字典配置
app.configure(
    DEBUG=True,
    HOST="0.0.0.0", 
    PORT=8080
)
```

## 🧪 运行示例

```bash
# 运行示例应用
python example.py
```

然后访问 http://127.0.0.1:8000 查看演示页面。

### 可用端点

- `GET /` - 首页（HTML）
- `GET /api/hello` - JSON API示例
- `POST /api/echo` - 回显JSON数据
- `GET /api/users` - 用户列表
- `POST /api/users` - 创建用户
- `GET /api/users/<user_id:int>` - 用户详情
- `GET /debug` - 调试信息

### 测试API

```bash
# 获取用户列表
curl http://127.0.0.1:8000/api/users

# 创建用户
curl -X POST http://127.0.0.1:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "测试用户", "email": "test@example.com"}'

# 回显数据
curl -X POST http://127.0.0.1:8000/api/echo \
  -H "Content-Type: application/json" \
  -d '{"test": "data", "number": 123}'

# 获取用户详情
curl http://127.0.0.1:8000/api/users/1
```

## 📁 项目结构

```
Cyclone/
├── cyclone/                    # 框架源码
│   ├── __init__.py            # 框架入口
│   ├── app.py                 # 应用类
│   ├── server.py              # 异步HTTP服务器
│   ├── router.py              # 路由系统
│   ├── views.py               # 视图系统
│   ├── request.py             # 请求对象
│   ├── response.py            # 响应对象
│   ├── middleware.py          # 中间件系统
│   ├── models.py              # ORM模型
│   ├── settings.py            # 配置管理
│   ├── exceptions.py          # 异常定义
│   ├── utils.py               # 工具函数
│   └── database/              # 数据库模块
│       ├── __init__.py
│       ├── pool.py            # 连接池
│       └── orm.py             # ORM实现
├── example.py                 # 示例应用
└── README.md                  # 项目文档
```

## 🎯 设计原则

1. **异步优先** - 所有I/O操作都是异步的
2. **简洁明了** - API设计直观，易于理解
3. **类型安全** - 完整的类型注解支持
4. **可扩展性** - 模块化设计，易于扩展
5. **性能优化** - 高效的请求处理和资源管理
6. **开发友好** - 丰富的调试信息和错误提示

## 🔧 高级功能

### 应用生命周期

```python
app = Application()

@app.on_startup
async def startup():
    """应用启动时执行"""
    print("应用启动中...")
    # 初始化数据库连接
    # 加载缓存数据
    # 启动后台任务

@app.on_shutdown
async def shutdown():
    """应用关闭时执行"""
    print("应用关闭中...")
    # 清理资源
    # 关闭数据库连接
    # 保存状态
```

### 静态文件服务

```python
# 配置静态文件
settings.STATIC_URL = '/static/'
settings.STATIC_ROOT = 'static'

# 添加静态文件路由
app.add_static_route('/static/', 'static/')
```

### 模板渲染

```python
class MyTemplateView(TemplateView):
    template_name = "index.html"
    
    async def get_context_data(self, **kwargs):
        return {
            "title": "我的页面",
            "users": await User.objects().all()
        }
```

### 信号系统

```python
# 定义信号
user_created = Signal()

# 连接信号处理器
@user_created.connect
async def send_welcome_email(user):
    # 发送欢迎邮件
    pass

# 发送信号
await user_created.send(user=new_user)
```

## 🤝 贡献指南

欢迎对Cyclone框架进行贡献！请遵循以下步骤：

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📄 许可证

本项目采用MIT许可证 - 查看[LICENSE](LICENSE)文件了解详情。

## 🙏 致谢

- 感谢Python asyncio社区的贡献
- 参考了FastAPI、Django、Flask等优秀框架的设计
- 感谢所有为开源社区做出贡献的开发者

---

**🌪️ Cyclone - 让异步Web开发变得简单而强大！** 