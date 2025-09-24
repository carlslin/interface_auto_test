#!/usr/bin/env python3
"""
测试datetime序列化问题
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.database_manager import DatabaseManager
from src.utils.cache_manager import CacheManager

def test_datetime_serialization():
    """测试datetime序列化"""
    print("测试datetime序列化...")
    
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
    
    # 连接数据库
    if not db_manager.connect():
        print("数据库连接失败")
        return
    
    # 创建测试表
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS datetime_test (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    
    db_manager.execute_query(create_table_sql)
    
    # 插入测试数据
    db_manager.execute_query("INSERT INTO datetime_test (name) VALUES (%s)", ("测试用户",))
    
    # 查询数据
    result = db_manager.execute_query("SELECT * FROM datetime_test WHERE name = %s", ("测试用户",))
    
    if result.success and result.data:
        original_data = result.data[0]
        print(f"原始数据: {original_data}")
        print(f"created_at类型: {type(original_data['created_at'])}")
        print(f"created_at值: {original_data['created_at']}")
        
        # 测试JSON序列化
        serialized = json.dumps(original_data, ensure_ascii=False, default=str)
        print(f"序列化后: {serialized}")
        
        # 反序列化
        deserialized = json.loads(serialized)
        print(f"反序列化后: {deserialized}")
        print(f"created_at类型: {type(deserialized['created_at'])}")
        print(f"created_at值: {deserialized['created_at']}")
        
        # 比较
        print(f"数据是否相等: {original_data == deserialized}")
        
        # 测试缓存
        cache_manager = CacheManager({
            'cache': {
                'type': 'redis',
                'redis': {
                    'host': 'localhost',
                    'port': 6379,
                    'db': 0
                }
            }
        })
        
        # 存储到缓存
        cache_manager.set("test:user", original_data, expire_time=300)
        
        # 从缓存获取
        cached_data = cache_manager.get("test:user")
        print(f"缓存数据: {cached_data}")
        print(f"缓存created_at类型: {type(cached_data['created_at'])}")
        print(f"缓存created_at值: {cached_data['created_at']}")
        
        # 清理
        cache_manager.delete("test:user")
        db_manager.execute_query("DROP TABLE IF EXISTS datetime_test")
        db_manager.disconnect()
    
    else:
        print("查询失败")

if __name__ == "__main__":
    test_datetime_serialization()
