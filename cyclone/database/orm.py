"""
Cyclone ORM模块

提供MySQL数据库的高级操作接口
"""

import asyncio
from typing import Dict, Any, List, Optional, Type, Union
from ..models import Model, QuerySet
from .pool import get_db_pool
from ..exceptions import DatabaseError


class ORM:
    """MySQL ORM操作类"""
    
    def __init__(self, db_pool=None):
        self.db_pool = db_pool or get_db_pool()
        if not self.db_pool:
            raise DatabaseError("数据库连接池未初始化")
    
    async def create_table(self, model: Type[Model]) -> None:
        """创建表"""
        sql = self._build_create_table_sql(model)
        await self.db_pool.execute(sql)
    
    async def drop_table(self, model: Type[Model]) -> None:
        """删除表"""
        sql = f"DROP TABLE IF EXISTS {model._table_name}"
        await self.db_pool.execute(sql)
    
    async def insert(self, model_instance: Model) -> Any:
        """插入数据"""
        model_class = model_instance.__class__
        fields = []
        values = []
        placeholders = []
        
        for field_name, field in model_class._fields.items():
            if field_name in model_instance._data:
                fields.append(field.get_db_column())
                values.append(field.to_db(model_instance._data[field_name]))
                placeholders.append('%s')
        
        sql = f"INSERT INTO {model_class._table_name} ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
        
        # MySQL使用LAST_INSERT_ID()获取插入的ID
        pk_field = model_instance._get_pk_field()
        if pk_field:
            await self.db_pool.execute(sql, *values)
            # 获取最后插入的ID
            last_id = await self.db_pool.fetchval("SELECT LAST_INSERT_ID()")
            if last_id:
                model_instance._data[pk_field.name] = last_id
                return last_id
        else:
            return await self.db_pool.execute(sql, *values)
    
    async def update(self, model_instance: Model) -> int:
        """更新数据"""
        model_class = model_instance.__class__
        pk_field = model_instance._get_pk_field()
        
        if not pk_field or pk_field.name not in model_instance._data:
            raise DatabaseError("无法更新没有主键的模型实例")
        
        # 检查哪些字段被修改
        set_clauses = []
        values = []
        
        for field_name, field in model_class._fields.items():
            if (field_name in model_instance._data and 
                model_instance._data[field_name] != model_instance._original_data.get(field_name)):
                
                set_clauses.append(f"{field.get_db_column()} = %s")
                values.append(field.to_db(model_instance._data[field_name]))
        
        if not set_clauses:
            return 0  # 没有修改
        
        # 添加WHERE条件
        values.append(model_instance._data[pk_field.name])
        where_clause = f"{pk_field.get_db_column()} = %s"
        
        sql = f"UPDATE {model_class._table_name} SET {', '.join(set_clauses)} WHERE {where_clause}"
        
        return await self.db_pool.execute(sql, *values)
    
    async def delete(self, model_instance: Model) -> int:
        """删除数据"""
        model_class = model_instance.__class__
        pk_field = model_instance._get_pk_field()
        
        if not pk_field or pk_field.name not in model_instance._data:
            raise DatabaseError("无法删除没有主键的模型实例")
        
        sql = f"DELETE FROM {model_class._table_name} WHERE {pk_field.get_db_column()} = %s"
        
        return await self.db_pool.execute(sql, model_instance._data[pk_field.name])
    
    async def select(self, model: Type[Model], filters: Dict[str, Any] = None,
                    order_by: List[str] = None, limit: int = None, 
                    offset: int = None) -> List[Model]:
        """查询数据"""
        sql_parts = [f"SELECT * FROM {model._table_name}"]
        values = []
        
        # WHERE条件
        if filters:
            conditions = []
            for field_name, value in filters.items():
                if field_name in model._fields:
                    field = model._fields[field_name]
                    conditions.append(f"{field.get_db_column()} = %s")
                    values.append(field.to_db(value))
            
            if conditions:
                sql_parts.append("WHERE " + " AND ".join(conditions))
        
        # ORDER BY
        if order_by:
            sql_parts.append("ORDER BY " + ", ".join(order_by))
        
        # LIMIT
        if limit:
            sql_parts.append(f"LIMIT {limit}")
        
        # OFFSET
        if offset:
            sql_parts.append(f"OFFSET {offset}")
        
        sql = " ".join(sql_parts)
        rows = await self.db_pool.fetch(sql, *values)
        
        # 转换为模型实例
        instances = []
        for row in rows:
            instance_data = {}
            for field_name, field in model._fields.items():
                db_column = field.get_db_column()
                if db_column in row:
                    instance_data[field_name] = field.to_python(row[db_column])
            
            instance = model(**instance_data)
            instance._original_data = instance_data.copy()
            instances.append(instance)
        
        return instances
    
    async def get(self, model: Type[Model], **filters) -> Model:
        """获取单个对象"""
        instances = await self.select(model, filters, limit=2)
        
        if not instances:
            raise DatabaseError(f"未找到匹配的 {model.__name__} 对象")
        
        if len(instances) > 1:
            raise DatabaseError(f"找到多个匹配的 {model.__name__} 对象")
        
        return instances[0]
    
    async def count(self, model: Type[Model], filters: Dict[str, Any] = None) -> int:
        """计算数量"""
        sql_parts = [f"SELECT COUNT(*) FROM {model._table_name}"]
        values = []
        
        # WHERE条件
        if filters:
            conditions = []
            for field_name, value in filters.items():
                if field_name in model._fields:
                    field = model._fields[field_name]
                    conditions.append(f"{field.get_db_column()} = %s")
                    values.append(field.to_db(value))
            
            if conditions:
                sql_parts.append("WHERE " + " AND ".join(conditions))
        
        sql = " ".join(sql_parts)
        return await self.db_pool.fetchval(sql, *values)
    
    async def exists(self, model: Type[Model], **filters) -> bool:
        """检查是否存在"""
        count = await self.count(model, filters)
        return count > 0
    
    def _build_create_table_sql(self, model: Type[Model]) -> str:
        """构建MySQL CREATE TABLE SQL"""
        columns = []
        
        for field_name, field in model._fields.items():
            column_def = f"{field.get_db_column()} {self._get_mysql_column_type(field)}"
            
            if field.primary_key:
                column_def += " AUTO_INCREMENT PRIMARY KEY"
            else:
                if not field.nullable:
                    column_def += " NOT NULL"
                
                if field.unique:
                    column_def += " UNIQUE"
                
                if field.default is not None:
                    if callable(field.default):
                        # 对于函数默认值，我们不在DDL中设置
                        pass
                    else:
                        column_def += f" DEFAULT {self._format_mysql_default_value(field.default)}"
            
            columns.append(column_def)
        
        return f"CREATE TABLE IF NOT EXISTS {model._table_name} ({', '.join(columns)}) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"
    
    def _get_mysql_column_type(self, field) -> str:
        """获取MySQL列类型"""
        from ..models import CharField, IntegerField, FloatField, BooleanField, DateTimeField, JSONField
        
        if isinstance(field, CharField):
            if field.max_length and field.max_length <= 255:
                return f"VARCHAR({field.max_length})"
            else:
                return "TEXT"
        
        elif isinstance(field, IntegerField):
            return "INT"
        
        elif isinstance(field, FloatField):
            return "FLOAT"
        
        elif isinstance(field, BooleanField):
            return "BOOLEAN"
        
        elif isinstance(field, DateTimeField):
            return "DATETIME"
        
        elif isinstance(field, JSONField):
            return "JSON"
        
        else:
            return "TEXT"  # 默认类型
    
    def _format_mysql_default_value(self, value) -> str:
        """格式化MySQL默认值"""
        if isinstance(value, str):
            return f"'{value}'"
        elif isinstance(value, bool):
            return 'TRUE' if value else 'FALSE'
        elif value is None:
            return 'NULL'
        else:
            return str(value)


# 全局ORM实例
_orm: Optional[ORM] = None


def get_orm() -> Optional[ORM]:
    """获取全局ORM实例"""
    return _orm


def set_orm(orm: ORM):
    """设置全局ORM实例"""
    global _orm
    _orm = orm


def init_orm(db_pool=None) -> ORM:
    """初始化全局ORM实例"""
    orm = ORM(db_pool)
    set_orm(orm)
    return orm


# 便捷函数

async def create_tables(*models: Type[Model]):
    """创建多个表"""
    orm = get_orm()
    if not orm:
        raise DatabaseError("ORM未初始化")
    
    for model in models:
        await orm.create_table(model)


async def drop_tables(*models: Type[Model]):
    """删除多个表"""
    orm = get_orm()
    if not orm:
        raise DatabaseError("ORM未初始化")
    
    for model in models:
        await orm.drop_table(model) 