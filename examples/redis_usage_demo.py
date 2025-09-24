#!/usr/bin/env python3
"""
=============================================================================
Redis缓存使用示例
=============================================================================

本示例展示了如何在接口自动化测试框架中使用Redis缓存功能，包括：
- 基本缓存操作
- 缓存装饰器使用
- 性能优化示例
- 错误处理示例
- 与测试框架集成示例

运行方法：
    python3 examples/redis_usage_demo.py

前提条件：
    1. Redis服务器已启动
    2. 已安装redis包: pip install redis
    3. 已配置Redis连接信息

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
from typing import Dict, Any, List

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.cache_manager import RedisCache, CacheManager, MemoryCache
from src.utils.config_loader import ConfigLoader


class RedisUsageDemo:
    """Redis使用示例类"""
    
    def __init__(self):
        """初始化示例"""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 创建Redis缓存实例
        self.redis_cache = RedisCache(
            host='localhost',
            port=6379,
            db=0,
            default_ttl=3600
        )
        
        # 创建缓存管理器
        self.cache_manager = CacheManager({
            'cache': {
                'type': 'redis',
                'redis': {
                    'host': 'localhost',
                    'port': 6379,
                    'db': 0
                }
            }
        })
    
    def demo_basic_operations(self):
        """演示基本缓存操作"""
        print("\n" + "="*50)
        print("1. 基本缓存操作演示")
        print("="*50)
        
        # 设置缓存
        test_data = {
            "user_id": 123,
            "username": "test_user",
            "email": "test@example.com",
            "created_at": time.time()
        }
        
        print("设置缓存数据...")
        success = self.redis_cache.set("user:123", test_data, ttl=300)
        print(f"设置结果: {'成功' if success else '失败'}")
        
        # 获取缓存
        print("获取缓存数据...")
        cached_data = self.redis_cache.get("user:123")
        print(f"获取结果: {cached_data}")
        
        # 检查数据一致性
        if cached_data == test_data:
            print("✅ 数据一致性验证通过")
        else:
            print("❌ 数据一致性验证失败")
        
        # 删除缓存
        print("删除缓存数据...")
        success = self.redis_cache.delete("user:123")
        print(f"删除结果: {'成功' if success else '失败'}")
        
        # 验证删除
        cached_data = self.redis_cache.get("user:123")
        if cached_data is None:
            print("✅ 删除验证通过")
        else:
            print("❌ 删除验证失败")
    
    def demo_cache_decorator(self):
        """演示缓存装饰器使用"""
        print("\n" + "="*50)
        print("2. 缓存装饰器演示")
        print("="*50)
        
        # 模拟一个耗时的计算函数
        @self.cache_manager.cache_result(expire_time=60)
        def expensive_calculation(n: int) -> int:
            """模拟耗时计算"""
            print(f"执行计算: {n}")
            time.sleep(1)  # 模拟耗时操作
            return n * n
        
        # 第一次调用（会执行计算）
        print("第一次调用（会执行计算）:")
        start_time = time.time()
        result1 = expensive_calculation(5)
        time1 = time.time() - start_time
        print(f"结果: {result1}, 耗时: {time1:.2f}秒")
        
        # 第二次调用（从缓存获取）
        print("第二次调用（从缓存获取）:")
        start_time = time.time()
        result2 = expensive_calculation(5)
        time2 = time.time() - start_time
        print(f"结果: {result2}, 耗时: {time2:.2f}秒")
        
        # 验证结果
        if result1 == result2 and time2 < time1:
            print("✅ 缓存装饰器工作正常")
        else:
            print("❌ 缓存装饰器工作异常")
    
    def demo_performance_comparison(self):
        """演示性能对比"""
        print("\n" + "="*50)
        print("3. 性能对比演示")
        print("="*50)
        
        # 创建内存缓存实例用于对比
        memory_cache = MemoryCache()
        
        # 测试数据
        test_data = {"data": list(range(1000))}
        test_count = 100
        
        # Redis缓存性能测试
        print("Redis缓存性能测试...")
        start_time = time.time()
        for i in range(test_count):
            self.redis_cache.set(f"perf:redis:{i}", test_data, ttl=300)
        redis_write_time = time.time() - start_time
        
        start_time = time.time()
        for i in range(test_count):
            self.redis_cache.get(f"perf:redis:{i}")
        redis_read_time = time.time() - start_time
        
        # 内存缓存性能测试
        print("内存缓存性能测试...")
        start_time = time.time()
        for i in range(test_count):
            memory_cache.set(f"perf:memory:{i}", test_data, expire_time=300)
        memory_write_time = time.time() - start_time
        
        start_time = time.time()
        for i in range(test_count):
            memory_cache.get(f"perf:memory:{i}")
        memory_read_time = time.time() - start_time
        
        # 输出性能对比
        print(f"\n性能对比结果 (操作{test_count}次):")
        print(f"Redis写入: {redis_write_time:.3f}秒 ({test_count/redis_write_time:.0f} ops/sec)")
        print(f"Redis读取: {redis_read_time:.3f}秒 ({test_count/redis_read_time:.0f} ops/sec)")
        print(f"内存写入: {memory_write_time:.3f}秒 ({test_count/memory_write_time:.0f} ops/sec)")
        print(f"内存读取: {memory_read_time:.3f}秒 ({test_count/memory_read_time:.0f} ops/sec)")
        
        # 清理测试数据
        for i in range(test_count):
            self.redis_cache.delete(f"perf:redis:{i}")
    
    def demo_error_handling(self):
        """演示错误处理"""
        print("\n" + "="*50)
        print("4. 错误处理演示")
        print("="*50)
        
        # 测试无效连接
        print("测试无效连接...")
        invalid_cache = RedisCache(host='invalid-host', port=9999)
        
        # 尝试操作
        result = invalid_cache.get("test:key")
        print(f"无效连接获取结果: {result}")
        
        # 测试序列化错误
        print("测试序列化错误...")
        try:
            import threading
            invalid_data = threading.Lock()  # 不可序列化的对象
            success = self.redis_cache.set("test:invalid", invalid_data)
            print(f"序列化错误处理: {'成功' if not success else '失败'}")
        except Exception as e:
            print(f"序列化错误捕获: {e}")
        
        print("✅ 错误处理演示完成")
    
    def demo_integration_with_tests(self):
        """演示与测试框架集成"""
        print("\n" + "="*50)
        print("5. 与测试框架集成演示")
        print("="*50)
        
        # 模拟API响应缓存
        def mock_api_call(endpoint: str) -> Dict[str, Any]:
            """模拟API调用"""
            print(f"调用API: {endpoint}")
            time.sleep(0.5)  # 模拟网络延迟
            return {
                "endpoint": endpoint,
                "data": f"response_from_{endpoint}",
                "timestamp": time.time()
            }
        
        # 带缓存的API调用
        def cached_api_call(endpoint: str) -> Dict[str, Any]:
            """带缓存的API调用"""
            cache_key = f"api:response:{endpoint}"
            
            # 尝试从缓存获取
            cached_response = self.redis_cache.get(cache_key)
            if cached_response:
                print(f"从缓存获取: {endpoint}")
                return cached_response
            
            # 缓存未命中，调用API
            response = mock_api_call(endpoint)
            
            # 缓存响应
            self.redis_cache.set(cache_key, response, ttl=300)
            print(f"缓存响应: {endpoint}")
            
            return response
        
        # 测试缓存效果
        endpoints = ["/api/users", "/api/users", "/api/products", "/api/users"]
        
        print("测试API响应缓存:")
        for endpoint in endpoints:
            start_time = time.time()
            response = cached_api_call(endpoint)
            elapsed = time.time() - start_time
            print(f"  {endpoint}: {elapsed:.3f}秒")
        
        # 清理测试数据
        for endpoint in set(endpoints):
            self.redis_cache.delete(f"api:response:{endpoint}")
        
        print("✅ 集成演示完成")
    
    def demo_advanced_features(self):
        """演示高级功能"""
        print("\n" + "="*50)
        print("6. 高级功能演示")
        print("="*50)
        
        # 批量操作
        print("批量操作演示...")
        batch_data = {
            f"batch:item:{i}": {"id": i, "value": f"item_{i}"}
            for i in range(10)
        }
        
        # 批量设置
        for key, value in batch_data.items():
            self.redis_cache.set(key, value, ttl=300)
        
        # 批量获取
        batch_results = {}
        for key in batch_data.keys():
            batch_results[key] = self.redis_cache.get(key)
        
        # 验证批量操作
        if batch_results == batch_data:
            print("✅ 批量操作成功")
        else:
            print("❌ 批量操作失败")
        
        # 清理批量数据
        for key in batch_data.keys():
            self.redis_cache.delete(key)
        
        # TTL管理
        print("TTL管理演示...")
        ttl_key = "ttl:test"
        ttl_value = "TTL测试数据"
        
        # 设置短期TTL
        self.redis_cache.set(ttl_key, ttl_value, ttl=2)
        
        # 立即获取
        result = self.redis_cache.get(ttl_key)
        print(f"设置后立即获取: {result}")
        
        # 等待过期
        print("等待TTL过期...")
        time.sleep(3)
        
        # 过期后获取
        result = self.redis_cache.get(ttl_key)
        print(f"过期后获取: {result}")
        
        if result is None:
            print("✅ TTL管理正常")
        else:
            print("❌ TTL管理异常")
    
    def run_all_demos(self):
        """运行所有演示"""
        print("Redis缓存使用示例")
        print("="*50)
        
        try:
            # 测试Redis连接
            self.redis_cache._get_redis().ping()
            print("✅ Redis连接正常")
        except Exception as e:
            print(f"❌ Redis连接失败: {e}")
            print("请确保Redis服务器已启动")
            return
        
        # 运行所有演示
        self.demo_basic_operations()
        self.demo_cache_decorator()
        self.demo_performance_comparison()
        self.demo_error_handling()
        self.demo_integration_with_tests()
        self.demo_advanced_features()
        
        print("\n" + "="*50)
        print("所有演示完成！")
        print("="*50)


def main():
    """主函数"""
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建并运行演示
    demo = RedisUsageDemo()
    demo.run_all_demos()


if __name__ == "__main__":
    main()
