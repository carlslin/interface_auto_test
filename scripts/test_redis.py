#!/usr/bin/env python3
"""
=============================================================================
Redis组件测试脚本
=============================================================================

本脚本用于测试接口自动化测试框架中的Redis缓存功能，包括：
- Redis连接测试
- 缓存基本操作测试
- 性能测试
- 错误处理测试
- 与框架集成测试

使用方法：
    python3 scripts/test_redis.py [--host HOST] [--port PORT] [--db DB]

参数说明：
    --host: Redis主机地址，默认localhost
    --port: Redis端口，默认6379
    --db: Redis数据库编号，默认0

作者: 接口自动化测试框架团队
版本: 1.0.0
更新日期: 2024年12月
=============================================================================
"""

import sys
import time
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, List

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.cache_manager import RedisCache, CacheManager
from src.utils.config_loader import ConfigLoader


class RedisTester:
    """Redis测试器"""
    
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        """
        初始化Redis测试器
        
        Args:
            host: Redis主机地址
            port: Redis端口
            db: Redis数据库编号
        """
        self.host = host
        self.port = port
        self.db = db
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 测试结果
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': []
        }
    
    def log_test_result(self, test_name: str, success: bool, message: str = ""):
        """
        记录测试结果
        
        Args:
            test_name: 测试名称
            success: 测试是否成功
            message: 测试消息
        """
        self.test_results['total_tests'] += 1
        if success:
            self.test_results['passed_tests'] += 1
            self.logger.info(f"✅ {test_name}: 通过")
        else:
            self.test_results['failed_tests'] += 1
            self.logger.error(f"❌ {test_name}: 失败 - {message}")
        
        self.test_results['test_details'].append({
            'name': test_name,
            'success': success,
            'message': message
        })
    
    def test_redis_connection(self) -> bool:
        """
        测试Redis连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            cache = RedisCache(host=self.host, port=self.port, db=self.db)
            # 尝试获取连接
            redis_client = cache._get_redis()
            redis_client.ping()
            self.log_test_result("Redis连接测试", True, f"连接到 {self.host}:{self.port}")
            return True
        except Exception as e:
            self.log_test_result("Redis连接测试", False, str(e))
            return False
    
    def test_basic_operations(self) -> bool:
        """
        测试基本缓存操作
        
        Returns:
            bool: 测试是否成功
        """
        try:
            cache = RedisCache(host=self.host, port=self.port, db=self.db)
            
            # 测试设置和获取
            test_key = "test:basic:key"
            test_value = {"message": "Hello Redis", "timestamp": time.time()}
            
            # 设置值
            success = cache.set(test_key, test_value, ttl=60)
            if not success:
                self.log_test_result("基本操作测试", False, "设置缓存失败")
                return False
            
            # 获取值
            retrieved_value = cache.get(test_key)
            if retrieved_value != test_value:
                self.log_test_result("基本操作测试", False, "获取缓存值不匹配")
                return False
            
            # 删除值
            success = cache.delete(test_key)
            if not success:
                self.log_test_result("基本操作测试", False, "删除缓存失败")
                return False
            
            # 验证删除
            retrieved_value = cache.get(test_key)
            if retrieved_value is not None:
                self.log_test_result("基本操作测试", False, "删除后仍能获取到值")
                return False
            
            self.log_test_result("基本操作测试", True, "设置、获取、删除操作正常")
            return True
            
        except Exception as e:
            self.log_test_result("基本操作测试", False, str(e))
            return False
    
    def test_data_types(self) -> bool:
        """
        测试不同数据类型的缓存
        
        Returns:
            bool: 测试是否成功
        """
        try:
            cache = RedisCache(host=self.host, port=self.port, db=self.db)
            
            # 测试数据类型
            test_cases = [
                ("string", "Hello World"),
                ("number", 12345),
                ("float", 3.14159),
                ("boolean", True),
                ("list", [1, 2, 3, "test"]),
                ("dict", {"key": "value", "nested": {"inner": "data"}}),
                ("none", None)
            ]
            
            for data_type, test_value in test_cases:
                key = f"test:type:{data_type}"
                
                # 设置值
                success = cache.set(key, test_value, ttl=60)
                if not success:
                    self.log_test_result(f"数据类型测试-{data_type}", False, "设置失败")
                    continue
                
                # 获取值
                retrieved_value = cache.get(key)
                if retrieved_value != test_value:
                    self.log_test_result(f"数据类型测试-{data_type}", False, 
                                       f"值不匹配: 期望 {test_value}, 实际 {retrieved_value}")
                    continue
                
                # 清理
                cache.delete(key)
                self.log_test_result(f"数据类型测试-{data_type}", True, "类型支持正常")
            
            return True
            
        except Exception as e:
            self.log_test_result("数据类型测试", False, str(e))
            return False
    
    def test_ttl_expiration(self) -> bool:
        """
        测试TTL过期功能
        
        Returns:
            bool: 测试是否成功
        """
        try:
            cache = RedisCache(host=self.host, port=self.port, db=self.db)
            
            # 设置短期过期的键
            test_key = "test:ttl:key"
            test_value = "TTL测试值"
            short_ttl = 2  # 2秒过期
            
            success = cache.set(test_key, test_value, ttl=short_ttl)
            if not success:
                self.log_test_result("TTL过期测试", False, "设置TTL失败")
                return False
            
            # 立即获取应该成功
            retrieved_value = cache.get(test_key)
            if retrieved_value != test_value:
                self.log_test_result("TTL过期测试", False, "设置后立即获取失败")
                return False
            
            # 等待过期
            time.sleep(short_ttl + 1)
            
            # 过期后获取应该返回None
            retrieved_value = cache.get(test_key)
            if retrieved_value is not None:
                self.log_test_result("TTL过期测试", False, "过期后仍能获取到值")
                return False
            
            self.log_test_result("TTL过期测试", True, "TTL过期功能正常")
            return True
            
        except Exception as e:
            self.log_test_result("TTL过期测试", False, str(e))
            return False
    
    def test_performance(self) -> bool:
        """
        测试Redis性能
        
        Returns:
            bool: 测试是否成功
        """
        try:
            cache = RedisCache(host=self.host, port=self.port, db=self.db)
            
            # 性能测试参数
            test_count = 1000
            test_data = {"id": 1, "name": "性能测试", "data": list(range(100))}
            
            # 写入性能测试
            start_time = time.time()
            for i in range(test_count):
                key = f"perf:write:{i}"
                cache.set(key, test_data, ttl=300)
            write_time = time.time() - start_time
            
            # 读取性能测试
            start_time = time.time()
            for i in range(test_count):
                key = f"perf:write:{i}"
                cache.get(key)
            read_time = time.time() - start_time
            
            # 清理测试数据
            for i in range(test_count):
                key = f"perf:write:{i}"
                cache.delete(key)
            
            # 计算性能指标
            write_ops_per_sec = test_count / write_time
            read_ops_per_sec = test_count / read_time
            
            self.log_test_result("性能测试", True, 
                               f"写入: {write_ops_per_sec:.0f} ops/sec, "
                               f"读取: {read_ops_per_sec:.0f} ops/sec")
            return True
            
        except Exception as e:
            self.log_test_result("性能测试", False, str(e))
            return False
    
    def test_cache_manager_integration(self) -> bool:
        """
        测试与CacheManager的集成
        
        Returns:
            bool: 测试是否成功
        """
        try:
            # 创建Redis配置
            redis_config = {
                'cache': {
                    'type': 'redis',
                    'redis': {
                        'host': self.host,
                        'port': self.port,
                        'db': self.db
                    }
                }
            }
            
            # 创建CacheManager
            cache_manager = CacheManager(redis_config)
            
            # 测试基本操作
            test_key = "integration:test"
            test_value = {"integration": "test", "timestamp": time.time()}
            
            # 设置值
            cache_manager.set(test_key, test_value, expire_time=60)
            
            # 获取值
            retrieved_value = cache_manager.get(test_key)
            if retrieved_value != test_value:
                self.log_test_result("CacheManager集成测试", False, "值不匹配")
                return False
            
            # 删除值
            cache_manager.delete(test_key)
            
            # 验证删除
            retrieved_value = cache_manager.get(test_key)
            if retrieved_value is not None:
                self.log_test_result("CacheManager集成测试", False, "删除后仍能获取到值")
                return False
            
            self.log_test_result("CacheManager集成测试", True, "集成功能正常")
            return True
            
        except Exception as e:
            self.log_test_result("CacheManager集成测试", False, str(e))
            return False
    
    def test_error_handling(self) -> bool:
        """
        测试错误处理
        
        Returns:
            bool: 测试是否成功
        """
        try:
            # 测试无效连接
            invalid_cache = RedisCache(host='invalid-host', port=9999)
            
            # 尝试操作应该失败但不崩溃
            result = invalid_cache.get("test:key")
            if result is not None:
                self.log_test_result("错误处理测试", False, "无效连接应该返回None")
                return False
            
            # 测试无效数据
            cache = RedisCache(host=self.host, port=self.port, db=self.db)
            
            # 尝试设置不可序列化的数据
            try:
                import threading
                invalid_data = threading.Lock()  # 不可序列化的对象
                success = cache.set("test:invalid", invalid_data)
                if success:
                    self.log_test_result("错误处理测试", False, "应该处理序列化错误")
                    return False
            except Exception:
                pass  # 预期的异常
            
            self.log_test_result("错误处理测试", True, "错误处理正常")
            return True
            
        except Exception as e:
            self.log_test_result("错误处理测试", False, str(e))
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """
        运行所有测试
        
        Returns:
            Dict[str, Any]: 测试结果
        """
        self.logger.info("开始Redis组件测试...")
        
        # 运行所有测试
        tests = [
            self.test_redis_connection,
            self.test_basic_operations,
            self.test_data_types,
            self.test_ttl_expiration,
            self.test_performance,
            self.test_cache_manager_integration,
            self.test_error_handling
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.logger.error(f"测试执行异常: {e}")
        
        # 计算成功率
        success_rate = (self.test_results['passed_tests'] / 
                       self.test_results['total_tests'] * 100) if self.test_results['total_tests'] > 0 else 0
        
        self.test_results['success_rate'] = success_rate
        
        return self.test_results
    
    def print_summary(self):
        """打印测试总结"""
        print("\n" + "="*60)
        print("Redis组件测试总结")
        print("="*60)
        print(f"总测试数: {self.test_results['total_tests']}")
        print(f"通过测试: {self.test_results['passed_tests']}")
        print(f"失败测试: {self.test_results['failed_tests']}")
        print(f"成功率: {self.test_results['success_rate']:.1f}%")
        
        if self.test_results['failed_tests'] > 0:
            print("\n失败的测试:")
            for test in self.test_results['test_details']:
                if not test['success']:
                    print(f"  - {test['name']}: {test['message']}")
        
        print("="*60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Redis组件测试脚本')
    parser.add_argument('--host', default='localhost', help='Redis主机地址')
    parser.add_argument('--port', type=int, default=6379, help='Redis端口')
    parser.add_argument('--db', type=int, default=0, help='Redis数据库编号')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    # 设置日志级别
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建测试器
    tester = RedisTester(host=args.host, port=args.port, db=args.db)
    
    # 运行测试
    results = tester.run_all_tests()
    
    # 打印总结
    tester.print_summary()
    
    # 返回退出码
    sys.exit(0 if results['failed_tests'] == 0 else 1)


if __name__ == "__main__":
    main()
