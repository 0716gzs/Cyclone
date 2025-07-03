"""
Cyclone 数据库连接池模块

提供MySQL数据库连接池管理
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
from ..exceptions import DatabaseError


class DatabasePool:
    """MySQL数据库连接池"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pool = None
        self.engine = 'aiomysql'
        self.logger = logging.getLogger(__name__)
        
        # 验证配置
        self._validate_config()
    
    def _validate_config(self):
        """验证数据库配置"""
        if 'URL' not in self.config:
            required_fields = ['NAME', 'USER', 'PASSWORD', 'HOST', 'PORT']
            for field in required_fields:
                if field not in self.config:
                    raise DatabaseError(f"数据库配置缺少必需字段: {field}")
        
        # 确保引擎是MySQL
        if self.config.get('ENGINE') and self.config['ENGINE'] != 'aiomysql':
            self.logger.warning(f"不支持的数据库引擎: {self.config['ENGINE']}, 将使用aiomysql")
        
        self.config['ENGINE'] = 'aiomysql'
    
    async def initialize(self):
        """初始化连接池"""
        try:
            import aiomysql
        except ImportError:
            raise DatabaseError("请安装aiomysql: pip install aiomysql")
        
        try:
            if 'URL' in self.config:
                # 解析URL
                url = self.config['URL']
                if not url.startswith('mysql://'):
                    raise DatabaseError("数据库URL必须以mysql://开头")
                
                # 使用URL创建连接池
                self.pool = await aiomysql.create_pool(
                    host=self._extract_host_from_url(url),
                    port=self._extract_port_from_url(url),
                    user=self._extract_user_from_url(url),
                    password=self._extract_password_from_url(url),
                    db=self._extract_db_from_url(url),
                    minsize=self.config.get('POOL_SIZE', 10),
                    maxsize=self.config.get('POOL_SIZE', 10) + self.config.get('MAX_OVERFLOW', 10),
                    charset='utf8mb4',
                    autocommit=False
                )
            else:
                # 使用配置参数创建连接池
                self.pool = await aiomysql.create_pool(
                    host=self.config['HOST'],
                    port=self.config['PORT'],
                    user=self.config['USER'],
                    password=self.config['PASSWORD'],
                    db=self.config['NAME'],
                    minsize=self.config.get('POOL_SIZE', 10),
                    maxsize=self.config.get('POOL_SIZE', 10) + self.config.get('MAX_OVERFLOW', 10),
                    charset='utf8mb4',
                    autocommit=False
                )
            
            self.logger.info("MySQL数据库连接池初始化成功")
            
        except Exception as e:
            raise DatabaseError(f"数据库连接池初始化失败: {e}")
    
    def _extract_host_from_url(self, url: str) -> str:
        """从URL提取主机"""
        # mysql://user:password@host:port/database
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        return parsed.hostname or 'localhost'
    
    def _extract_port_from_url(self, url: str) -> int:
        """从URL提取端口"""
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        return parsed.port or 3306
    
    def _extract_user_from_url(self, url: str) -> str:
        """从URL提取用户名"""
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        return parsed.username or 'root'
    
    def _extract_password_from_url(self, url: str) -> str:
        """从URL提取密码"""
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        return parsed.password or ''
    
    def _extract_db_from_url(self, url: str) -> str:
        """从URL提取数据库名"""
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        return parsed.path.lstrip('/') if parsed.path else 'test'
    
    async def close(self):
        """关闭连接池"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            self.logger.info("MySQL数据库连接池已关闭")
    
    async def execute(self, query: str, *args) -> int:
        """执行SQL语句（INSERT、UPDATE、DELETE）"""
        if not self.pool:
            raise DatabaseError("数据库连接池未初始化")
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    affected_rows = await cursor.execute(query, args)
                    await conn.commit()
                    return affected_rows
                except Exception as e:
                    await conn.rollback()
                    raise DatabaseError(f"SQL执行失败: {e}")
    
    async def fetchone(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """获取单行结果"""
        if not self.pool:
            raise DatabaseError("数据库连接池未初始化")
        
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                try:
                    await cursor.execute(query, args)
                    result = await cursor.fetchone()
                    return dict(result) if result else None
                except Exception as e:
                    raise DatabaseError(f"SQL查询失败: {e}")
    
    async def fetchall(self, query: str, *args) -> List[Dict[str, Any]]:
        """获取所有结果"""
        return await self.fetch(query, *args)
    
    async def fetch(self, query: str, *args) -> List[Dict[str, Any]]:
        """获取查询结果"""
        if not self.pool:
            raise DatabaseError("数据库连接池未初始化")
        
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                try:
                    await cursor.execute(query, args)
                    results = await cursor.fetchall()
                    return [dict(row) for row in results]
                except Exception as e:
                    raise DatabaseError(f"SQL查询失败: {e}")
    
    async def fetchval(self, query: str, *args) -> Any:
        """获取单个值"""
        if not self.pool:
            raise DatabaseError("数据库连接池未初始化")
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(query, args)
                    result = await cursor.fetchone()
                    return result[0] if result else None
                except Exception as e:
                    raise DatabaseError(f"SQL查询失败: {e}")
    
    async def transaction(self):
        """获取事务上下文管理器"""
        return DatabaseTransaction(self.pool)
    
    def is_connected(self) -> bool:
        """检查连接池是否已连接"""
        return self.pool is not None and not self.pool._closed


class DatabaseTransaction:
    """数据库事务管理器"""
    
    def __init__(self, pool):
        self.pool = pool
        self.conn = None
        self.cursor = None
    
    async def __aenter__(self):
        if not self.pool:
            raise DatabaseError("数据库连接池未初始化")
        
        self.conn = await self.pool.acquire()
        await self.conn.begin()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            if exc_type is None:
                await self.conn.commit()
            else:
                await self.conn.rollback()
            
            self.pool.release(self.conn)
    
    async def execute(self, query: str, *args) -> int:
        """在事务中执行SQL"""
        if not self.conn:
            raise DatabaseError("事务未启动")
        
        async with self.conn.cursor() as cursor:
            return await cursor.execute(query, args)
    
    async def fetchone(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """在事务中获取单行"""
        if not self.conn:
            raise DatabaseError("事务未启动")
        
        async with self.conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, args)
            result = await cursor.fetchone()
            return dict(result) if result else None
    
    async def fetchall(self, query: str, *args) -> List[Dict[str, Any]]:
        """在事务中获取所有行"""
        if not self.conn:
            raise DatabaseError("事务未启动")
        
        async with self.conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, args)
            results = await cursor.fetchall()
            return [dict(row) for row in results]


# 全局连接池实例
_db_pool: Optional[DatabasePool] = None


def get_db_pool() -> Optional[DatabasePool]:
    """获取全局数据库连接池"""
    return _db_pool


def set_db_pool(pool: DatabasePool):
    """设置全局数据库连接池"""
    global _db_pool
    _db_pool = pool


async def init_db_pool(config: Dict[str, Any]) -> DatabasePool:
    """初始化全局数据库连接池"""
    pool = DatabasePool(config)
    await pool.initialize()
    set_db_pool(pool)
    return pool


async def close_db_pool():
    """关闭全局数据库连接池"""
    global _db_pool
    if _db_pool:
        await _db_pool.close()
        _db_pool = None
