"""
Cyclone 模型模块

提供ORM基类和数据库模型定义
"""

import asyncio
from typing import Dict, Any, List, Optional, Type, Union, Callable
from datetime import datetime
from .exceptions import DatabaseError, ValidationError


class Field:
    """字段基类"""
    
    def __init__(self, primary_key: bool = False, nullable: bool = True, 
                 default: Any = None, unique: bool = False,
                 max_length: int = None, db_column: str = None):
        self.primary_key = primary_key
        self.nullable = nullable
        self.default = default
        self.unique = unique
        self.max_length = max_length
        self.db_column = db_column
        self.name = None
    
    def validate(self, value: Any) -> Any:
        if value is None:
            if not self.nullable and self.default is None:
                raise ValidationError(f"字段 {self.name} 不能为空")
            return self.default
        return self.to_python(value)
    
    def to_python(self, value: Any) -> Any:
        return value
    
    def to_db(self, value: Any) -> Any:
        return value
    
    def get_db_column(self) -> str:
        return self.db_column or self.name


class CharField(Field):
    """字符串字段"""
    
    def __init__(self, max_length: int = 255, **kwargs):
        super().__init__(max_length=max_length, **kwargs)
    
    def validate(self, value: Any) -> Any:
        value = super().validate(value)
        if value is not None:
            if not isinstance(value, str):
                value = str(value)
            if self.max_length and len(value) > self.max_length:
                raise ValidationError(f"字段 {self.name} 长度不能超过 {self.max_length}")
        return value


class IntegerField(Field):
    """整数字段"""
    
    def to_python(self, value: Any) -> int:
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"无法将 {value} 转换为整数")


class FloatField(Field):
    """浮点数字段"""
    
    def to_python(self, value: Any) -> float:
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            raise ValidationError(f"无法将 {value} 转换为浮点数")


class BooleanField(Field):
    """布尔字段"""
    
    def to_python(self, value: Any) -> bool:
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)


class DateTimeField(Field):
    """日期时间字段"""
    
    def __init__(self, auto_now: bool = False, auto_now_add: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.auto_now = auto_now
        self.auto_now_add = auto_now_add
    
    def to_python(self, value: Any) -> datetime:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                raise ValidationError(f"无法解析日期时间: {value}")
        raise ValidationError(f"无法将 {value} 转换为日期时间")


class JSONField(Field):
    """JSON字段"""
    
    def to_python(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, str):
            import json
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                raise ValidationError(f"无法解析JSON: {value}")
        return value
    
    def to_db(self, value: Any) -> str:
        if value is None:
            return None
        import json
        return json.dumps(value, ensure_ascii=False)


class ForeignKey(Field):
    """外键字段"""
    
    def __init__(self, to: Union[str, Type['Model']], on_delete: str = 'CASCADE', **kwargs):
        super().__init__(**kwargs)
        self.to = to
        self.on_delete = on_delete


class ModelMeta(type):
    """模型元类"""
    
    def __new__(cls, name, bases, attrs):
        fields = {}
        for key, value in attrs.items():
            if isinstance(value, Field):
                value.name = key
                fields[key] = value
        
        new_class = super().__new__(cls, name, bases, attrs)
        new_class._fields = fields
        new_class._table_name = attrs.get('__table__', name.lower())
        
        return new_class


class QuerySet:
    """查询集"""
    
    def __init__(self, model: Type['Model'], db_pool=None):
        self.model = model
        self.db_pool = db_pool
        self._filters = {}
        self._order_by = []
        self._limit = None
        self._offset = None
    
    def filter(self, **kwargs) -> 'QuerySet':
        new_qs = self._clone()
        new_qs._filters.update(kwargs)
        return new_qs
    
    def order_by(self, *fields) -> 'QuerySet':
        new_qs = self._clone()
        new_qs._order_by = list(fields)
        return new_qs
    
    def limit(self, count: int) -> 'QuerySet':
        new_qs = self._clone()
        new_qs._limit = count
        return new_qs
    
    def offset(self, count: int) -> 'QuerySet':
        new_qs = self._clone()
        new_qs._offset = count
        return new_qs
    
    async def all(self) -> List['Model']:
        return []
    
    async def first(self) -> Optional['Model']:
        results = await self.limit(1).all()
        return results[0] if results else None
    
    async def get(self, **kwargs) -> 'Model':
        results = await self.filter(**kwargs).all()
        if not results:
            raise DatabaseError(f"未找到匹配的 {self.model.__name__} 对象")
        if len(results) > 1:
            raise DatabaseError(f"找到多个匹配的 {self.model.__name__} 对象")
        return results[0]
    
    async def count(self) -> int:
        return 0
    
    async def exists(self) -> bool:
        return await self.count() > 0
    
    def _clone(self) -> 'QuerySet':
        new_qs = QuerySet(self.model, self.db_pool)
        new_qs._filters = self._filters.copy()
        new_qs._order_by = self._order_by.copy()
        new_qs._limit = self._limit
        new_qs._offset = self._offset
        return new_qs


class Model(metaclass=ModelMeta):
    """模型基类"""
    
    def __init__(self, **kwargs):
        self._data = {}
        self._original_data = {}
        
        for field_name, field in self._fields.items():
            if field_name in kwargs:
                value = field.validate(kwargs[field_name])
                self._data[field_name] = value
                self._original_data[field_name] = value
            elif field.default is not None:
                if callable(field.default):
                    value = field.default()
                else:
                    value = field.default
                self._data[field_name] = value
                self._original_data[field_name] = value
    
    def __getattribute__(self, name: str) -> Any:
        # 首先尝试获取特殊属性（以_开头的或者特定方法）
        if name.startswith('_') or name in ('to_dict', 'save', 'delete', 'objects', 'create', 'get', 'filter'):
            return super().__getattribute__(name)
        
        # 尝试获取字段定义
        try:
            fields = super().__getattribute__('_fields')
            if name in fields:
                data = super().__getattribute__('_data')
                return data.get(name)
        except AttributeError:
            pass
        
        # 如果不是字段，使用默认的属性访问
        return super().__getattribute__(name)
    
    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith('_') or not hasattr(self, '_fields') or name not in self._fields:
            super().__setattr__(name, value)
        else:
            field = self._fields[name]
            validated_value = field.validate(value)
            self._data[name] = validated_value
    
    @classmethod
    def objects(cls) -> QuerySet:
        return QuerySet(cls)
    
    @classmethod
    async def create(cls, **kwargs) -> 'Model':
        instance = cls(**kwargs)
        await instance.save()
        return instance
    
    @classmethod
    async def get(cls, **kwargs) -> 'Model':
        return await cls.objects().get(**kwargs)
    
    @classmethod
    async def filter(cls, **kwargs) -> List['Model']:
        return await cls.objects().filter(**kwargs).all()
    
    async def save(self) -> None:
        for field_name, field in self._fields.items():
            if isinstance(field, DateTimeField):
                if field.auto_now or (field.auto_now_add and field_name not in self._data):
                    self._data[field_name] = datetime.now()
        
        if self._is_new():
            await self._insert()
        else:
            await self._update()
        
        self._original_data = self._data.copy()
    
    async def delete(self) -> None:
        pass
    
    def _is_new(self) -> bool:
        pk_field = self._get_pk_field()
        return pk_field is None or pk_field.name not in self._data or self._data[pk_field.name] is None
    
    def _get_pk_field(self) -> Optional[Field]:
        for field in self._fields.values():
            if field.primary_key:
                return field
        return None
    
    async def _insert(self) -> None:
        pass
    
    async def _update(self) -> None:
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        result = {}
        for field_name, field in self._fields.items():
            if field_name in self._data:
                value = self._data[field_name]
                if isinstance(value, datetime):
                    result[field_name] = value.isoformat()
                else:
                    result[field_name] = value
        return result
    
    def __repr__(self) -> str:
        pk_field = self._get_pk_field()
        if pk_field and pk_field.name in self._data:
            return f"<{self.__class__.__name__}: {self._data[pk_field.name]}>"
        return f"<{self.__class__.__name__}: 未保存>"
    
    def __str__(self) -> str:
        return self.__repr__()


def create_model(name: str, fields: Dict[str, Field], table_name: str = None) -> Type[Model]:
    """动态创建模型"""
    attrs = fields.copy()
    if table_name:
        attrs['__table__'] = table_name
    
    return type(name, (Model,), attrs)
