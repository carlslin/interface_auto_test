#!/usr/bin/env python3
"""
=============================================================================
Redis和MySQL协同工作测试脚本
=============================================================================

本脚本专门测试Redis缓存和MySQL数据库的协同工作，验证：
- 缓存作为数据库的前置层
- 缓存失效和数据库回填
- 数据一致性保证
- 性能优化效果
- 故障转移机制

使用方法：
    python3 scripts/redis_mysql_integration_test.py [--verbose]

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

from src.utils.database_manager import DatabaseManager
from src.utils.cache_manager import CacheManager


class RedisMySQLIntegrationTester:
    """Redis和MySQL协同工作测试器"""
    
    def __init__(self, verbose: bool = False):
        """
        初始化测试器
        
        Args:
            verbose: 是否详细输出
        """
        self.verbose = verbose
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 初始化数据库管理器
        self.db_manager = DatabaseManager({
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
        
        # 初始化缓存管理器
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
        
        # 测试结果
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': []
        }
    
    def _compare_user_data(self, data1: dict, data2: dict) -> bool:
        """比较用户数据，处理datetime序列化差异"""
        if not data1 or not data2:
            return False
        
        # 比较主要字段
        for key in ['id', 'username', 'email', 'name']:
            if data1.get(key) != data2.get(key):
                return False
        
        # 对于时间字段，比较字符串形式
        if 'created_at' in data1 and 'created_at' in data2:
            created_at1 = str(data1['created_at'])
            created_at2 = str(data2['created_at'])
            if created_at1 != created_at2:
                return False
        
        if 'updated_at' in data1 and 'updated_at' in data2:
            updated_at1 = str(data1['updated_at'])
            updated_at2 = str(data2['updated_at'])
            if updated_at1 != updated_at2:
                return False
        
        return True
    
    def log_test_result(self, test_name: str, success: bool, message: str = "", execution_time: float = 0):
        """记录测试结果"""
        self.test_results['total_tests'] += 1
        if success:
            self.test_results['passed_tests'] += 1
            status = "✅"
        else:
            self.test_results['failed_tests'] += 1
            status = "❌"
        
        self.logger.info(f"{status} {test_name}: {'通过' if success else '失败'} ({execution_time:.3f}s)")
        if message and not success:
            self.logger.error(f"   错误: {message}")
        
        self.test_results['test_details'].append({
            'name': test_name,
            'success': success,
            'message': message,
            'execution_time': execution_time
        })
    
    def setup_test_data(self) -> bool:
        """设置测试数据"""
        try:
            # 连接数据库
            if not self.db_manager.connect():
                return False
            
            # 创建测试表
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS cache_test_users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(100),
                name VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
            
            result = self.db_manager.execute_query(create_table_sql)
            if not result.success:
                return False
            
            # 插入测试数据
            test_users = [
                ("user1", "user1@example.com", "用户1"),
                ("user2", "user2@example.com", "用户2"),
                ("user3", "user3@example.com", "用户3"),
                ("user4", "user4@example.com", "用户4"),
                ("user5", "user5@example.com", "用户5")
            ]
            
            insert_sql = "INSERT IGNORE INTO cache_test_users (username, email, name) VALUES (%s, %s, %s)"
            for user_data in test_users:
                result = self.db_manager.execute_query(insert_sql, user_data)
                if not result.success:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"设置测试数据失败: {e}")
            return False
    
    def cleanup_test_data(self) -> bool:
        """清理测试数据"""
        try:
            if self.db_manager:
                self.db_manager.execute_query("DROP TABLE IF EXISTS cache_test_users")
                self.db_manager.disconnect()
            
            if self.cache_manager:
                # 清理缓存
                self.cache_manager.delete("user:user1")
                self.cache_manager.delete("user:user2")
                self.cache_manager.delete("user:user3")
                self.cache_manager.delete("user:user4")
                self.cache_manager.delete("user:user5")
                self.cache_manager.delete("users:all")
            
            return True
            
        except Exception as e:
            self.logger.error(f"清理测试数据失败: {e}")
            return False
    
    def test_cache_aside_pattern(self) -> bool:
        """测试Cache-Aside模式"""
        start_time = time.time()
        
        try:
            # 1. 从缓存获取数据（应该失败，因为缓存中没有）
            cached_user = self.cache_manager.get("user:user1")
            if cached_user is not None:
                self.log_test_result("Cache-Aside模式测试", False, "缓存中不应该有数据", time.time() - start_time)
                return False
            
            # 2. 从数据库获取数据
            result = self.db_manager.execute_query(
                "SELECT * FROM cache_test_users WHERE username = %s", ("user1",)
            )
            
            if not result.success or not result.data:
                self.log_test_result("Cache-Aside模式测试", False, "数据库查询失败", time.time() - start_time)
                return False
            
            user_data = result.data[0]
            
            # 3. 将数据存储到缓存
            cache_success = self.cache_manager.set("user:user1", user_data, expire_time=300)
            if not cache_success:
                self.log_test_result("Cache-Aside模式测试", False, "缓存存储失败", time.time() - start_time)
                return False
            
            # 4. 再次从缓存获取数据（应该成功）
            cached_user = self.cache_manager.get("user:user1")
            if not self._compare_user_data(cached_user, user_data):
                self.log_test_result("Cache-Aside模式测试", False, "缓存数据不匹配", time.time() - start_time)
                return False
            
            self.log_test_result("Cache-Aside模式测试", True, "", time.time() - start_time)
            return True
            
        except Exception as e:
            self.log_test_result("Cache-Aside模式测试", False, str(e), time.time() - start_time)
            return False
    
    def test_cache_invalidation(self) -> bool:
        """测试缓存失效"""
        start_time = time.time()
        
        try:
            # 1. 先在缓存中设置数据
            original_data = {"id": 1, "username": "user1", "name": "原始用户1"}
            self.cache_manager.set("user:user1", original_data, expire_time=300)
            
            # 2. 验证缓存中有数据
            cached_data = self.cache_manager.get("user:user1")
            if cached_data != original_data:
                self.log_test_result("缓存失效测试", False, "初始缓存设置失败", time.time() - start_time)
                return False
            
            # 3. 更新数据库中的数据
            update_sql = "UPDATE cache_test_users SET name = %s WHERE username = %s"
            result = self.db_manager.execute_query(update_sql, ("更新后的用户1", "user1"))
            
            if not result.success:
                self.log_test_result("缓存失效测试", False, "数据库更新失败", time.time() - start_time)
                return False
            
            # 4. 失效缓存
            self.cache_manager.delete("user:user1")
            
            # 5. 验证缓存已被删除
            cached_data = self.cache_manager.get("user:user1")
            if cached_data is not None:
                self.log_test_result("缓存失效测试", False, "缓存删除失败", time.time() - start_time)
                return False
            
            # 6. 从数据库获取更新后的数据
            result = self.db_manager.execute_query(
                "SELECT * FROM cache_test_users WHERE username = %s", ("user1",)
            )
            
            if not result.success or not result.data:
                self.log_test_result("缓存失效测试", False, "获取更新后数据失败", time.time() - start_time)
                return False
            
            updated_data = result.data[0]
            if updated_data["name"] != "更新后的用户1":
                self.log_test_result("缓存失效测试", False, "数据库更新未生效", time.time() - start_time)
                return False
            
            self.log_test_result("缓存失效测试", True, "", time.time() - start_time)
            return True
            
        except Exception as e:
            self.log_test_result("缓存失效测试", False, str(e), time.time() - start_time)
            return False
    
    def test_write_through_pattern(self) -> bool:
        """测试Write-Through模式"""
        start_time = time.time()
        
        try:
            # 1. 准备新用户数据
            new_user = {
                "username": "newuser",
                "email": "newuser@example.com",
                "name": "新用户"
            }
            
            # 2. 同时写入数据库和缓存
            # 先写入数据库
            insert_sql = "INSERT INTO cache_test_users (username, email, name) VALUES (%s, %s, %s)"
            result = self.db_manager.execute_query(insert_sql, (
                new_user["username"], 
                new_user["email"], 
                new_user["name"]
            ))
            
            if not result.success:
                self.log_test_result("Write-Through模式测试", False, "数据库写入失败", time.time() - start_time)
                return False
            
            # 获取插入后的完整数据（包括ID和时间戳）
            select_sql = "SELECT * FROM cache_test_users WHERE username = %s"
            result = self.db_manager.execute_query(select_sql, (new_user["username"],))
            
            if not result.success or not result.data:
                self.log_test_result("Write-Through模式测试", False, "获取插入数据失败", time.time() - start_time)
                return False
            
            full_user_data = result.data[0]
            
            # 写入缓存
            cache_success = self.cache_manager.set("user:newuser", full_user_data, expire_time=300)
            if not cache_success:
                self.log_test_result("Write-Through模式测试", False, "缓存写入失败", time.time() - start_time)
                return False
            
            # 3. 验证数据一致性
            cached_data = self.cache_manager.get("user:newuser")
            if not self._compare_user_data(cached_data, full_user_data):
                self.log_test_result("Write-Through模式测试", False, "缓存数据不一致", time.time() - start_time)
                return False
            
            # 4. 验证数据库中的数据
            db_data = self.db_manager.execute_query(select_sql, (new_user["username"],))
            if not db_data.success or not db_data.data:
                self.log_test_result("Write-Through模式测试", False, "数据库数据验证失败", time.time() - start_time)
                return False
            
            if db_data.data[0] != full_user_data:
                self.log_test_result("Write-Through模式测试", False, "数据库数据不一致", time.time() - start_time)
                return False
            
            self.log_test_result("Write-Through模式测试", True, "", time.time() - start_time)
            return True
            
        except Exception as e:
            self.log_test_result("Write-Through模式测试", False, str(e), time.time() - start_time)
            return False
    
    def test_performance_comparison(self) -> bool:
        """测试性能对比"""
        start_time = time.time()
        
        try:
            # 1. 测试数据库直接查询性能
            db_start = time.time()
            for i in range(100):
                result = self.db_manager.execute_query(
                    "SELECT * FROM cache_test_users WHERE username = %s", ("user1",)
                )
            db_time = time.time() - db_start
            
            # 2. 测试缓存查询性能
            # 先确保缓存中有数据
            result = self.db_manager.execute_query(
                "SELECT * FROM cache_test_users WHERE username = %s", ("user1",)
            )
            if result.success and result.data:
                self.cache_manager.set("user:user1", result.data[0], expire_time=300)
            
            cache_start = time.time()
            for i in range(100):
                cached_data = self.cache_manager.get("user:user1")
            cache_time = time.time() - cache_start
            
            # 3. 计算性能提升
            if cache_time > 0:
                speedup = db_time / cache_time
                self.log_test_result(
                    "性能对比测试", 
                    True, 
                    f"数据库: {db_time:.3f}s, 缓存: {cache_time:.3f}s, 提升: {speedup:.1f}x", 
                    time.time() - start_time
                )
            else:
                self.log_test_result("性能对比测试", False, "缓存时间计算错误", time.time() - start_time)
                return False
            
            return True
            
        except Exception as e:
            self.log_test_result("性能对比测试", False, str(e), time.time() - start_time)
            return False
    
    def test_cache_warming(self) -> bool:
        """测试缓存预热"""
        start_time = time.time()
        
        try:
            # 1. 获取所有用户数据
            result = self.db_manager.execute_query("SELECT * FROM cache_test_users")
            if not result.success or not result.data:
                self.log_test_result("缓存预热测试", False, "获取用户数据失败", time.time() - start_time)
                return False
            
            all_users = result.data
            
            # 2. 预热缓存
            cache_keys = []
            for user in all_users:
                cache_key = f"user:{user['username']}"
                cache_keys.append(cache_key)
                success = self.cache_manager.set(cache_key, user, expire_time=300)
                if not success:
                    self.log_test_result("缓存预热测试", False, f"缓存预热失败: {cache_key}", time.time() - start_time)
                    return False
            
            # 3. 验证所有数据都在缓存中
            for i, user in enumerate(all_users):
                cache_key = cache_keys[i]
                cached_data = self.cache_manager.get(cache_key)
                if not self._compare_user_data(cached_data, user):
                    self.log_test_result("缓存预热测试", False, f"缓存数据不匹配: {cache_key}", time.time() - start_time)
                    return False
            
            # 4. 存储用户列表到缓存
            self.cache_manager.set("users:all", all_users, expire_time=300)
            
            # 5. 验证用户列表缓存
            cached_list = self.cache_manager.get("users:all")
            if not cached_list or len(cached_list) != len(all_users):
                self.log_test_result("缓存预热测试", False, "用户列表缓存不匹配", time.time() - start_time)
                return False
            
            # 比较列表中的每个用户
            for i, (cached_user, original_user) in enumerate(zip(cached_list, all_users)):
                if not self._compare_user_data(cached_user, original_user):
                    self.log_test_result("缓存预热测试", False, f"用户列表第{i}个用户不匹配", time.time() - start_time)
                    return False
            
            self.log_test_result("缓存预热测试", True, f"预热了 {len(all_users)} 个用户", time.time() - start_time)
            return True
            
        except Exception as e:
            self.log_test_result("缓存预热测试", False, str(e), time.time() - start_time)
            return False
    
    def test_fault_tolerance(self) -> bool:
        """测试故障容错"""
        start_time = time.time()
        
        try:
            # 1. 测试缓存不可用时的降级
            # 先确保缓存中有数据
            result = self.db_manager.execute_query(
                "SELECT * FROM cache_test_users WHERE username = %s", ("user1",)
            )
            if result.success and result.data:
                self.cache_manager.set("user:user1", result.data[0], expire_time=300)
            
            # 2. 模拟缓存不可用（删除缓存数据）
            self.cache_manager.delete("user:user1")
            
            # 3. 尝试从缓存获取（应该失败）
            cached_data = self.cache_manager.get("user:user1")
            if cached_data is not None:
                self.log_test_result("故障容错测试", False, "缓存删除失败", time.time() - start_time)
                return False
            
            # 4. 降级到数据库查询
            db_result = self.db_manager.execute_query(
                "SELECT * FROM cache_test_users WHERE username = %s", ("user1",)
            )
            
            if not db_result.success or not db_result.data:
                self.log_test_result("故障容错测试", False, "数据库降级失败", time.time() - start_time)
                return False
            
            # 5. 验证数据正确性
            user_data = db_result.data[0]
            if user_data["username"] != "user1":
                self.log_test_result("故障容错测试", False, "降级数据不正确", time.time() - start_time)
                return False
            
            self.log_test_result("故障容错测试", True, "", time.time() - start_time)
            return True
            
        except Exception as e:
            self.log_test_result("故障容错测试", False, str(e), time.time() - start_time)
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        self.logger.info("开始Redis和MySQL协同工作测试...")
        
        try:
            # 设置测试数据
            if not self.setup_test_data():
                self.log_test_result("测试环境设置", False, "无法设置测试数据", 0)
                return self.test_results
            
            # 运行所有测试
            tests = [
                self.test_cache_aside_pattern,
                self.test_cache_invalidation,
                self.test_write_through_pattern,
                self.test_performance_comparison,
                self.test_cache_warming,
                self.test_fault_tolerance
            ]
            
            for test in tests:
                try:
                    test()
                except Exception as e:
                    self.logger.error(f"测试执行异常: {e}")
            
            # 清理测试数据
            self.cleanup_test_data()
            
        except Exception as e:
            self.logger.error(f"测试执行异常: {e}")
        finally:
            self.cleanup_test_data()
        
        # 计算成功率
        success_rate = (self.test_results['passed_tests'] / 
                       self.test_results['total_tests'] * 100) if self.test_results['total_tests'] > 0 else 0
        
        self.test_results['success_rate'] = success_rate
        
        return self.test_results
    
    def print_summary(self):
        """打印测试总结"""
        print("\n" + "="*70)
        print("Redis和MySQL协同工作测试总结")
        print("="*70)
        print(f"总测试数: {self.test_results['total_tests']}")
        print(f"通过测试: {self.test_results['passed_tests']}")
        print(f"失败测试: {self.test_results['failed_tests']}")
        print(f"成功率: {self.test_results['success_rate']:.1f}%")
        
        if self.test_results['failed_tests'] > 0:
            print("\n失败的测试:")
            for test in self.test_results['test_details']:
                if not test['success']:
                    print(f"  - {test['name']}: {test['message']}")
        
        print("\n通过的测试:")
        for test in self.test_results['test_details']:
            if test['success']:
                print(f"  ✅ {test['name']}: {test['message']}")
        
        print("="*70)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Redis和MySQL协同工作测试脚本')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    # 设置日志级别
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建测试器
    tester = RedisMySQLIntegrationTester(verbose=args.verbose)
    
    # 运行测试
    results = tester.run_all_tests()
    
    # 打印总结
    tester.print_summary()
    
    # 返回退出码
    sys.exit(0 if results['failed_tests'] == 0 else 1)


if __name__ == "__main__":
    main()
