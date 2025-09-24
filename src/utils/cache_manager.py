#!/usr/bin/env python3
"""
缓存管理器模块
提供内存缓存和Redis缓存支持
"""

import json
import time
import hashlib
import logging
from typing import Dict, Any, Optional, Union, Callable
from functools import wraps
from pathlib import Path


class MemoryCache:
    """内存缓存实现"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        初始化内存缓存
        
        Args:
            max_size: 最大缓存条目数
            default_ttl: 默认TTL（秒）
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, float] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _generate_key(self, key: Union[str, tuple, dict]) -> str:
        """生成缓存键"""
        if isinstance(key, str):
            return key
        elif isinstance(key, (tuple, list)):
            return hashlib.md5(str(key).encode()).hexdigest()
        elif isinstance(key, dict):
            return hashlib.md5(json.dumps(key, sort_keys=True).encode()).hexdigest()
        else:
            return str(key)
    
    def _is_expired(self, key: str) -> bool:
        """检查缓存是否过期"""
        if key not in self.cache:
            return True
        
        entry = self.cache[key]
        if 'expires_at' in entry:
            return time.time() > entry['expires_at']
        return False
    
    def _evict_lru(self):
        """淘汰最近最少使用的条目"""
        if len(self.cache) >= self.max_size:
            # 找到最久未访问的条目
            oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
            del self.cache[oldest_key]
            del self.access_times[oldest_key]
            self.logger.debug(f"淘汰LRU缓存条目: {oldest_key}")
    
    def get(self, key: Union[str, tuple, dict]) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            Any: 缓存值，如果不存在或过期则返回None
        """
        cache_key = self._generate_key(key)
        
        if self._is_expired(cache_key):
            if cache_key in self.cache:
                del self.cache[cache_key]
                if cache_key in self.access_times:
                    del self.access_times[cache_key]
            return None
        
        # 更新访问时间
        self.access_times[cache_key] = time.time()
        return self.cache[cache_key]['value']
    
    def set(self, key: Union[str, tuple, dict], value: Any, ttl: Optional[int] = None, 
            expire_time: Optional[int] = None) -> None:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: TTL（秒），如果为None则使用默认TTL
            expire_time: 过期时间（秒），兼容参数名
        """
        cache_key = self._generate_key(key)
        # 兼容expire_time参数名
        ttl = ttl or expire_time or self.default_ttl
        
        # 检查是否需要淘汰
        if cache_key not in self.cache and len(self.cache) >= self.max_size:
            self._evict_lru()
        
        # 设置缓存条目
        self.cache[cache_key] = {
            'value': value,
            'expires_at': time.time() + ttl,
            'created_at': time.time()
        }
        self.access_times[cache_key] = time.time()
    
    def delete(self, key: Union[str, tuple, dict]) -> bool:
        """
        删除缓存条目
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否删除成功
        """
        cache_key = self._generate_key(key)
        if cache_key in self.cache:
            del self.cache[cache_key]
            if cache_key in self.access_times:
                del self.access_times[cache_key]
            return True
        return False
    
    def clear(self) -> None:
        """清空所有缓存"""
        self.cache.clear()
        self.access_times.clear()
        self.logger.info("内存缓存已清空")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        current_time = time.time()
        expired_count = sum(1 for entry in self.cache.values() 
                           if 'expires_at' in entry and current_time > entry['expires_at'])
        
        return {
            'total_entries': len(self.cache),
            'expired_entries': expired_count,
            'active_entries': len(self.cache) - expired_count,
            'max_size': self.max_size,
            'usage_percentage': (len(self.cache) / self.max_size) * 100
        }


class RedisCache:
    """Redis缓存实现"""
    
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0, 
                 password: Optional[str] = None, default_ttl: int = 3600):
        """
        初始化Redis缓存
        
        Args:
            host: Redis主机
            port: Redis端口
            db: Redis数据库
            password: Redis密码
            default_ttl: 默认TTL（秒）
        """
        self.host = host
        self.port = port
        self.db = db
        self.redis_password = password
        self.default_ttl = default_ttl
        self.logger = logging.getLogger(self.__class__.__name__)
        self._redis = None
        
    def _get_redis(self):
        """获取Redis连接"""
        if self._redis is None:
            try:
                import redis
                self._redis = redis.Redis(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    password=self.redis_password,
                    decode_responses=True
                )
                # 测试连接
                self._redis.ping()
                self.logger.info(f"Redis连接成功: {self.host}:{self.port}")
            except ImportError:
                raise ImportError("请安装redis包: pip install redis")
            except Exception as e:
                self.logger.error(f"Redis连接失败: {e}")
                raise
        
        return self._redis
    
    def _generate_key(self, key: Union[str, tuple, dict]) -> str:
        """生成缓存键"""
        if isinstance(key, str):
            return f"autotest:{key}"
        elif isinstance(key, (tuple, list)):
            return f"autotest:{hashlib.md5(str(key).encode()).hexdigest()}"
        elif isinstance(key, dict):
            return f"autotest:{hashlib.md5(json.dumps(key, sort_keys=True).encode()).hexdigest()}"
        else:
            return f"autotest:{str(key)}"
    
    def get(self, key: Union[str, tuple, dict]) -> Optional[Any]:
        """获取缓存值"""
        try:
            redis_client = self._get_redis()
            cache_key = self._generate_key(key)
            value = redis_client.get(cache_key)
            
            if value is not None:
                return json.loads(value)
            return None
            
        except Exception as e:
            self.logger.error(f"Redis获取失败: {e}")
            return None
    
    def set(self, key: Union[str, tuple, dict], value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        try:
            redis_client = self._get_redis()
            cache_key = self._generate_key(key)
            ttl = ttl or self.default_ttl
            
            redis_client.setex(cache_key, ttl, json.dumps(value, ensure_ascii=False, default=str))
            return True
            
        except Exception as e:
            self.logger.error(f"Redis设置失败: {e}")
            return False
    
    def delete(self, key: Union[str, tuple, dict]) -> bool:
        """删除缓存条目"""
        try:
            redis_client = self._get_redis()
            cache_key = self._generate_key(key)
            return bool(redis_client.delete(cache_key))
            
        except Exception as e:
            self.logger.error(f"Redis删除失败: {e}")
            return False
    
    def clear(self) -> bool:
        """清空所有缓存"""
        try:
            redis_client = self._get_redis()
            keys = redis_client.keys("autotest:*")
            if keys:
                redis_client.delete(*keys)
            return True
            
        except Exception as e:
            self.logger.error(f"Redis清空失败: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            redis_client = self._get_redis()
            keys = redis_client.keys("autotest:*")
            
            return {
                'total_entries': len(keys),
                'redis_info': redis_client.info(),
                'memory_usage': redis_client.memory_usage()
            }
            
        except Exception as e:
            self.logger.error(f"获取Redis统计信息失败: {e}")
            return {'error': str(e)}


class CacheManager:
    """缓存管理器 - 统一管理不同类型的缓存"""
    
    def __init__(self, config: Union[str, Dict[str, Any]] = 'memory', **kwargs):
        """
        初始化缓存管理器
        
        Args:
            config: 缓存配置，可以是字符串类型或配置字典
            **kwargs: 额外的缓存配置参数
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 处理配置参数
        if isinstance(config, str):
            # 如果config是字符串，直接作为缓存类型
            cache_type = config
            cache_config = kwargs
        elif isinstance(config, dict):
            # 如果config是字典，解析配置
            cache_type = config.get('cache', {}).get('type', 'memory')
            cache_config = config.get('cache', {}).get('redis', {}) if cache_type == 'redis' else {}
            cache_config.update(kwargs)
        else:
            raise ValueError(f"不支持的配置类型: {type(config)}")
        
        self.cache_type = cache_type
        
        if cache_type == 'memory':
            self.cache = MemoryCache(**cache_config)
        elif cache_type == 'redis':
            self.cache = RedisCache(**cache_config)
        else:
            raise ValueError(f"不支持的缓存类型: {cache_type}")
        
        self.logger.info(f"缓存管理器已初始化: {cache_type}")
    
    def get(self, key: Union[str, tuple, dict]) -> Optional[Any]:
        """获取缓存值"""
        return self.cache.get(key)
    
    def set(self, key: Union[str, tuple, dict], value: Any, ttl: Optional[int] = None, 
            expire_time: Optional[int] = None) -> bool:
        """设置缓存值"""
        # 兼容expire_time参数名
        ttl = ttl or expire_time
        return self.cache.set(key, value, ttl)
    
    def delete(self, key: Union[str, tuple, dict]) -> bool:
        """删除缓存条目"""
        return self.cache.delete(key)
    
    def clear(self) -> bool:
        """清空所有缓存"""
        return self.cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return self.cache.get_stats()
    
    def cache_result(self, expire_time: Optional[int] = None):
        """
        缓存结果装饰器
        
        Args:
            expire_time: 过期时间（秒）
            
        Returns:
            装饰器函数
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                # 生成缓存键
                cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
                
                # 尝试从缓存获取
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # 执行函数
                result = func(*args, **kwargs)
                
                # 缓存结果
                self.set(cache_key, result, expire_time=expire_time)
                
                return result
            return wrapper
        return decorator
    
    def cached(self, ttl: Optional[int] = None, key_prefix: str = ""):
        """
        缓存装饰器
        
        Args:
            ttl: TTL（秒）
            key_prefix: 键前缀
            
        Returns:
            装饰器函数
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # 生成缓存键
                cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
                
                # 尝试从缓存获取
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    self.logger.debug(f"缓存命中: {cache_key}")
                    return cached_result
                
                # 执行函数并缓存结果
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl)
                self.logger.debug(f"缓存设置: {cache_key}")
                
                return result
            
            return wrapper
        return decorator
