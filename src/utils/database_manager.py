#!/usr/bin/env python3
"""
=============================================================================
数据库管理器
=============================================================================

本模块提供统一的数据库管理功能，支持MySQL、PostgreSQL、SQLite等多种数据库。
主要功能包括：
- 数据库连接管理
- 连接池管理
- 事务管理
- 查询构建器
- 数据模型管理
- 迁移管理

使用方法：
    from src.utils.database_manager import DatabaseManager, MySQLManager
    
    # 创建数据库管理器
    db_manager = DatabaseManager({
        'database': {
            'type': 'mysql',
            'mysql': {
                'host': 'localhost',
                'port': 3306,
                'database': 'autotest',
                'username': 'autotest',
                'password': 'autotest123'
            }
        }
    })
    
    # 执行查询
    results = db_manager.execute_query("SELECT * FROM test_cases")
    
    # 使用查询构建器
    results = db_manager.table('test_cases').where('status', 'active').get()

作者: 接口自动化测试框架团队
版本: 1.0.0
更新日期: 2024年12月
=============================================================================
"""

import sys
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
from contextlib import contextmanager
from dataclasses import dataclass
from abc import ABC, abstractmethod

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class DatabaseConfig:
    """数据库配置类"""
    host: str = 'localhost'
    port: int = 3306
    database: str = 'autotest'
    username: str = 'autotest'
    password: str = ''
    charset: str = 'utf8mb4'
    max_connections: int = 20
    connect_timeout: int = 10
    read_timeout: int = 30
    write_timeout: int = 30
    autocommit: bool = True
    pool_size: int = 10
    pool_recycle: int = 3600
    pool_pre_ping: bool = True


@dataclass
class QueryResult:
    """查询结果类"""
    data: List[Dict[str, Any]]
    row_count: int
    execution_time: float
    success: bool
    error: Optional[str] = None


class BaseDatabaseManager(ABC):
    """数据库管理器基类"""
    
    def __init__(self, config: DatabaseConfig):
        """
        初始化数据库管理器
        
        Args:
            config: 数据库配置
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self._connection = None
        self._connection_pool = None
        
    @abstractmethod
    def connect(self) -> bool:
        """建立数据库连接"""
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """断开数据库连接"""
        pass
    
    @abstractmethod
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> QueryResult:
        """执行查询"""
        pass
    
    @abstractmethod
    def execute_many(self, query: str, params_list: List[Tuple]) -> QueryResult:
        """批量执行查询"""
        pass
    
    @abstractmethod
    def get_connection_info(self) -> Dict[str, Any]:
        """获取连接信息"""
        pass


class MySQLManager(BaseDatabaseManager):
    """MySQL数据库管理器"""
    
    def __init__(self, config: DatabaseConfig):
        """
        初始化MySQL管理器
        
        Args:
            config: MySQL配置
        """
        super().__init__(config)
        self._mysql_connection = None
        self._mysql_pool = None
        
    def connect(self) -> bool:
        """
        建立MySQL连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            import pymysql
            from pymysql.cursors import DictCursor
            
            # 创建连接
            self._mysql_connection = pymysql.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.username,
                password=self.config.password,
                database=self.config.database,
                charset=self.config.charset,
                connect_timeout=self.config.connect_timeout,
                read_timeout=self.config.read_timeout,
                write_timeout=self.config.write_timeout,
                autocommit=self.config.autocommit,
                cursorclass=DictCursor
            )
            
            # 测试连接
            with self._mysql_connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            self.logger.info(f"MySQL连接成功: {self.config.host}:{self.config.port}")
            return True
            
        except ImportError:
            self.logger.error("请安装pymysql包: pip install pymysql")
            return False
        except Exception as e:
            self.logger.error(f"MySQL连接失败: {e}")
            return False
    
    def disconnect(self) -> bool:
        """
        断开MySQL连接
        
        Returns:
            bool: 断开是否成功
        """
        try:
            if self._mysql_connection:
                self._mysql_connection.close()
                self._mysql_connection = None
                self.logger.info("MySQL连接已断开")
            return True
        except Exception as e:
            self.logger.error(f"MySQL断开连接失败: {e}")
            return False
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> QueryResult:
        """
        执行MySQL查询
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            QueryResult: 查询结果
        """
        start_time = time.time()
        
        try:
            if not self._mysql_connection:
                if not self.connect():
                    return QueryResult([], 0, 0, False, "连接失败")
            
            with self._mysql_connection.cursor() as cursor:
                cursor.execute(query, params)
                
                if query.strip().upper().startswith('SELECT'):
                    data = cursor.fetchall()
                    row_count = len(data)
                else:
                    data = []
                    row_count = cursor.rowcount
                
                execution_time = time.time() - start_time
                
                self.logger.debug(f"查询执行成功: {query[:50]}... ({execution_time:.3f}s)")
                return QueryResult(data, row_count, execution_time, True)
                
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"查询执行失败: {e}"
            self.logger.error(error_msg)
            return QueryResult([], 0, execution_time, False, error_msg)
    
    def execute_many(self, query: str, params_list: List[Tuple]) -> QueryResult:
        """
        批量执行MySQL查询
        
        Args:
            query: SQL查询语句
            params_list: 参数列表
            
        Returns:
            QueryResult: 执行结果
        """
        start_time = time.time()
        
        try:
            if not self._mysql_connection:
                if not self.connect():
                    return QueryResult([], 0, 0, False, "连接失败")
            
            with self._mysql_connection.cursor() as cursor:
                cursor.executemany(query, params_list)
                row_count = cursor.rowcount
                
                execution_time = time.time() - start_time
                
                self.logger.debug(f"批量查询执行成功: {len(params_list)}条记录 ({execution_time:.3f}s)")
                return QueryResult([], row_count, execution_time, True)
                
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"批量查询执行失败: {e}"
            self.logger.error(error_msg)
            return QueryResult([], 0, execution_time, False, error_msg)
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        获取MySQL连接信息
        
        Returns:
            Dict[str, Any]: 连接信息
        """
        try:
            if not self._mysql_connection:
                return {'error': '未连接'}
            
            with self._mysql_connection.cursor() as cursor:
                # 获取版本信息
                cursor.execute("SELECT VERSION() as version")
                version_result = cursor.fetchone()
                
                # 获取连接信息
                cursor.execute("SELECT CONNECTION_ID() as connection_id")
                connection_result = cursor.fetchone()
                
                # 获取数据库信息
                cursor.execute("SELECT DATABASE() as current_database")
                database_result = cursor.fetchone()
                
                return {
                    'version': version_result['version'] if version_result else 'Unknown',
                    'connection_id': connection_result['connection_id'] if connection_result else 'Unknown',
                    'current_database': database_result['current_database'] if database_result else 'Unknown',
                    'host': self.config.host,
                    'port': self.config.port,
                    'username': self.config.username,
                    'charset': self.config.charset
                }
                
        except Exception as e:
            return {'error': str(e)}


class SQLiteManager(BaseDatabaseManager):
    """SQLite数据库管理器"""
    
    def __init__(self, config: DatabaseConfig):
        """
        初始化SQLite管理器
        
        Args:
            config: SQLite配置
        """
        super().__init__(config)
        self._sqlite_connection = None
        
    def connect(self) -> bool:
        """
        建立SQLite连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            import sqlite3
            
            # 创建连接
            self._sqlite_connection = sqlite3.connect(
                self.config.database,  # SQLite中database字段表示文件路径
                timeout=self.config.connect_timeout
            )
            self._sqlite_connection.row_factory = sqlite3.Row
            
            # 测试连接
            cursor = self._sqlite_connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            
            self.logger.info(f"SQLite连接成功: {self.config.database}")
            return True
            
        except Exception as e:
            self.logger.error(f"SQLite连接失败: {e}")
            return False
    
    def disconnect(self) -> bool:
        """
        断开SQLite连接
        
        Returns:
            bool: 断开是否成功
        """
        try:
            if self._sqlite_connection:
                self._sqlite_connection.close()
                self._sqlite_connection = None
                self.logger.info("SQLite连接已断开")
            return True
        except Exception as e:
            self.logger.error(f"SQLite断开连接失败: {e}")
            return False
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> QueryResult:
        """
        执行SQLite查询
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            QueryResult: 查询结果
        """
        start_time = time.time()
        
        try:
            if not self._sqlite_connection:
                if not self.connect():
                    return QueryResult([], 0, 0, False, "连接失败")
            
            cursor = self._sqlite_connection.cursor()
            cursor.execute(query, params or ())
            
            if query.strip().upper().startswith('SELECT'):
                rows = cursor.fetchall()
                data = [dict(row) for row in rows]
                row_count = len(data)
            else:
                data = []
                row_count = cursor.rowcount
                self._sqlite_connection.commit()
            
            cursor.close()
            execution_time = time.time() - start_time
            
            self.logger.debug(f"查询执行成功: {query[:50]}... ({execution_time:.3f}s)")
            return QueryResult(data, row_count, execution_time, True)
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"查询执行失败: {e}"
            self.logger.error(error_msg)
            return QueryResult([], 0, execution_time, False, error_msg)
    
    def execute_many(self, query: str, params_list: List[Tuple]) -> QueryResult:
        """
        批量执行SQLite查询
        
        Args:
            query: SQL查询语句
            params_list: 参数列表
            
        Returns:
            QueryResult: 执行结果
        """
        start_time = time.time()
        
        try:
            if not self._sqlite_connection:
                if not self.connect():
                    return QueryResult([], 0, 0, False, "连接失败")
            
            cursor = self._sqlite_connection.cursor()
            cursor.executemany(query, params_list)
            row_count = cursor.rowcount
            self._sqlite_connection.commit()
            cursor.close()
            
            execution_time = time.time() - start_time
            
            self.logger.debug(f"批量查询执行成功: {len(params_list)}条记录 ({execution_time:.3f}s)")
            return QueryResult([], row_count, execution_time, True)
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"批量查询执行失败: {e}"
            self.logger.error(error_msg)
            return QueryResult([], 0, execution_time, False, error_msg)
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        获取SQLite连接信息
        
        Returns:
            Dict[str, Any]: 连接信息
        """
        try:
            if not self._sqlite_connection:
                return {'error': '未连接'}
            
            cursor = self._sqlite_connection.cursor()
            cursor.execute("SELECT sqlite_version() as version")
            version_result = cursor.fetchone()
            cursor.close()
            
            return {
                'version': version_result[0] if version_result else 'Unknown',
                'database_file': self.config.database,
                'type': 'SQLite'
            }
            
        except Exception as e:
            return {'error': str(e)}


class QueryBuilder:
    """查询构建器"""
    
    def __init__(self, db_manager: BaseDatabaseManager):
        """
        初始化查询构建器
        
        Args:
            db_manager: 数据库管理器实例
        """
        self.db_manager = db_manager
        self.table_name = None
        self.select_fields = ['*']
        self.where_conditions = []
        self.order_by_fields = []
        self.limit_count = None
        self.offset_count = None
        
    def table(self, table_name: str) -> 'QueryBuilder':
        """
        设置表名
        
        Args:
            table_name: 表名
            
        Returns:
            QueryBuilder: 查询构建器实例
        """
        self.table_name = table_name
        return self
    
    def select(self, *fields: str) -> 'QueryBuilder':
        """
        设置查询字段
        
        Args:
            *fields: 字段名列表
            
        Returns:
            QueryBuilder: 查询构建器实例
        """
        self.select_fields = list(fields) if fields else ['*']
        return self
    
    def where(self, field: str, operator: str, value: Any) -> 'QueryBuilder':
        """
        添加WHERE条件
        
        Args:
            field: 字段名
            operator: 操作符 (=, !=, >, <, >=, <=, LIKE, IN, NOT IN)
            value: 值
            
        Returns:
            QueryBuilder: 查询构建器实例
        """
        self.where_conditions.append((field, operator, value))
        return self
    
    def where_in(self, field: str, values: List[Any]) -> 'QueryBuilder':
        """
        添加IN条件
        
        Args:
            field: 字段名
            values: 值列表
            
        Returns:
            QueryBuilder: 查询构建器实例
        """
        return self.where(field, 'IN', values)
    
    def where_not_in(self, field: str, values: List[Any]) -> 'QueryBuilder':
        """
        添加NOT IN条件
        
        Args:
            field: 字段名
            values: 值列表
            
        Returns:
            QueryBuilder: 查询构建器实例
        """
        return self.where(field, 'NOT IN', values)
    
    def order_by(self, field: str, direction: str = 'ASC') -> 'QueryBuilder':
        """
        添加排序条件
        
        Args:
            field: 字段名
            direction: 排序方向 (ASC, DESC)
            
        Returns:
            QueryBuilder: 查询构建器实例
        """
        self.order_by_fields.append((field, direction.upper()))
        return self
    
    def limit(self, count: int) -> 'QueryBuilder':
        """
        设置限制数量
        
        Args:
            count: 限制数量
            
        Returns:
            QueryBuilder: 查询构建器实例
        """
        self.limit_count = count
        return self
    
    def offset(self, count: int) -> 'QueryBuilder':
        """
        设置偏移量
        
        Args:
            count: 偏移量
            
        Returns:
            QueryBuilder: 查询构建器实例
        """
        self.offset_count = count
        return self
    
    def _build_query(self) -> Tuple[str, List[Any]]:
        """
        构建SQL查询
        
        Returns:
            Tuple[str, List[Any]]: SQL查询和参数
        """
        if not self.table_name:
            raise ValueError("必须指定表名")
        
        # 构建SELECT子句
        select_clause = f"SELECT {', '.join(self.select_fields)}"
        
        # 构建FROM子句
        from_clause = f"FROM {self.table_name}"
        
        # 构建WHERE子句
        where_clause = ""
        params = []
        
        if self.where_conditions:
            where_parts = []
            for field, operator, value in self.where_conditions:
                if operator.upper() == 'IN':
                    placeholders = ', '.join(['%s'] * len(value))
                    where_parts.append(f"{field} IN ({placeholders})")
                    params.extend(value)
                elif operator.upper() == 'NOT IN':
                    placeholders = ', '.join(['%s'] * len(value))
                    where_parts.append(f"{field} NOT IN ({placeholders})")
                    params.extend(value)
                else:
                    where_parts.append(f"{field} {operator} %s")
                    params.append(value)
            
            where_clause = f"WHERE {' AND '.join(where_parts)}"
        
        # 构建ORDER BY子句
        order_clause = ""
        if self.order_by_fields:
            order_parts = [f"{field} {direction}" for field, direction in self.order_by_fields]
            order_clause = f"ORDER BY {', '.join(order_parts)}"
        
        # 构建LIMIT子句
        limit_clause = ""
        if self.limit_count is not None:
            limit_clause = f"LIMIT {self.limit_count}"
            if self.offset_count is not None:
                limit_clause = f"LIMIT {self.offset_count}, {self.limit_count}"
        
        # 组合查询
        query_parts = [select_clause, from_clause, where_clause, order_clause, limit_clause]
        query = ' '.join(filter(None, query_parts))
        
        return query, params
    
    def get(self) -> QueryResult:
        """
        执行查询并获取结果
        
        Returns:
            QueryResult: 查询结果
        """
        query, params = self._build_query()
        return self.db_manager.execute_query(query, tuple(params) if params else None)
    
    def first(self) -> Optional[Dict[str, Any]]:
        """
        获取第一条记录
        
        Returns:
            Optional[Dict[str, Any]]: 第一条记录或None
        """
        self.limit(1)
        result = self.get()
        return result.data[0] if result.data else None
    
    def count(self) -> int:
        """
        获取记录数量
        
        Returns:
            int: 记录数量
        """
        self.select_fields = ['COUNT(*) as count']
        result = self.get()
        return result.data[0]['count'] if result.data else 0


class DatabaseManager:
    """统一数据库管理器"""
    
    def __init__(self, config: Union[str, Dict[str, Any]]):
        """
        初始化数据库管理器
        
        Args:
            config: 数据库配置，可以是字符串类型或配置字典
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 处理配置参数
        if isinstance(config, str):
            # 如果config是字符串，作为数据库类型
            db_type = config
            db_config = DatabaseConfig()
        elif isinstance(config, dict):
            # 如果config是字典，解析配置
            db_type = config.get('database', {}).get('type', 'sqlite')
            db_config_dict = config.get('database', {}).get(db_type, {})
            db_config = DatabaseConfig(**db_config_dict)
        else:
            raise ValueError(f"不支持的配置类型: {type(config)}")
        
        self.db_type = db_type
        
        # 创建对应的数据库管理器
        if db_type == 'mysql':
            self.db_manager = MySQLManager(db_config)
        elif db_type == 'sqlite':
            self.db_manager = SQLiteManager(db_config)
        else:
            raise ValueError(f"不支持的数据库类型: {db_type}")
        
        self.logger.info(f"数据库管理器已初始化: {db_type}")
    
    def connect(self) -> bool:
        """
        建立数据库连接
        
        Returns:
            bool: 连接是否成功
        """
        return self.db_manager.connect()
    
    def disconnect(self) -> bool:
        """
        断开数据库连接
        
        Returns:
            bool: 断开是否成功
        """
        return self.db_manager.disconnect()
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> QueryResult:
        """
        执行查询
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            QueryResult: 查询结果
        """
        return self.db_manager.execute_query(query, params)
    
    def execute_many(self, query: str, params_list: List[Tuple]) -> QueryResult:
        """
        批量执行查询
        
        Args:
            query: SQL查询语句
            params_list: 参数列表
            
        Returns:
            QueryResult: 执行结果
        """
        return self.db_manager.execute_many(query, params_list)
    
    def table(self, table_name: str) -> QueryBuilder:
        """
        创建查询构建器
        
        Args:
            table_name: 表名
            
        Returns:
            QueryBuilder: 查询构建器实例
        """
        return QueryBuilder(self.db_manager).table(table_name)
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        获取连接信息
        
        Returns:
            Dict[str, Any]: 连接信息
        """
        return self.db_manager.get_connection_info()
    
    @contextmanager
    def transaction(self):
        """
        事务上下文管理器
        
        Yields:
            DatabaseManager: 数据库管理器实例
        """
        try:
            # 开始事务
            self.execute_query("START TRANSACTION")
            yield self
            # 提交事务
            self.execute_query("COMMIT")
        except Exception as e:
            # 回滚事务
            self.execute_query("ROLLBACK")
            raise e
    
    def create_table(self, table_name: str, columns: Dict[str, str]) -> bool:
        """
        创建表
        
        Args:
            table_name: 表名
            columns: 列定义字典 {列名: 类型}
            
        Returns:
            bool: 创建是否成功
        """
        try:
            column_definitions = []
            for column_name, column_type in columns.items():
                column_definitions.append(f"{column_name} {column_type}")
            
            create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_definitions)})"
            result = self.execute_query(create_sql)
            
            if result.success:
                self.logger.info(f"表 {table_name} 创建成功")
                return True
            else:
                self.logger.error(f"表 {table_name} 创建失败: {result.error}")
                return False
                
        except Exception as e:
            self.logger.error(f"创建表失败: {e}")
            return False
    
    def drop_table(self, table_name: str) -> bool:
        """
        删除表
        
        Args:
            table_name: 表名
            
        Returns:
            bool: 删除是否成功
        """
        try:
            drop_sql = f"DROP TABLE IF EXISTS {table_name}"
            result = self.execute_query(drop_sql)
            
            if result.success:
                self.logger.info(f"表 {table_name} 删除成功")
                return True
            else:
                self.logger.error(f"表 {table_name} 删除失败: {result.error}")
                return False
                
        except Exception as e:
            self.logger.error(f"删除表失败: {e}")
            return False
    
    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """
        获取表结构信息
        
        Args:
            table_name: 表名
            
        Returns:
            List[Dict[str, Any]]: 表结构信息
        """
        try:
            if self.db_type == 'mysql':
                query = f"SHOW COLUMNS FROM {table_name}"
            elif self.db_type == 'sqlite':
                query = f"PRAGMA table_info({table_name})"
            else:
                return []
            
            result = self.execute_query(query)
            return result.data if result.success else []
            
        except Exception as e:
            self.logger.error(f"获取表结构失败: {e}")
            return []
    
    def get_tables(self) -> List[str]:
        """
        获取所有表名
        
        Returns:
            List[str]: 表名列表
        """
        try:
            if self.db_type == 'mysql':
                query = "SHOW TABLES"
            elif self.db_type == 'sqlite':
                query = "SELECT name FROM sqlite_master WHERE type='table'"
            else:
                return []
            
            result = self.execute_query(query)
            if result.success:
                if self.db_type == 'mysql':
                    # MySQL返回的键名是动态的
                    return [list(row.values())[0] for row in result.data]
                else:
                    # SQLite返回name字段
                    return [row['name'] for row in result.data]
            return []
            
        except Exception as e:
            self.logger.error(f"获取表列表失败: {e}")
            return []


# 便捷函数
def create_database_manager(config: Union[str, Dict[str, Any]]) -> DatabaseManager:
    """
    创建数据库管理器实例
    
    Args:
        config: 数据库配置
        
    Returns:
        DatabaseManager: 数据库管理器实例
    """
    return DatabaseManager(config)


def get_database_config_from_file(config_file: str) -> Dict[str, Any]:
    """
    从配置文件加载数据库配置
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        Dict[str, Any]: 数据库配置
    """
    import yaml
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config.get('database', {})
