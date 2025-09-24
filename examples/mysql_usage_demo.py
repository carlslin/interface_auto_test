#!/usr/bin/env python3
"""
=============================================================================
MySQL数据库使用示例
=============================================================================

本示例展示了如何在接口自动化测试框架中使用MySQL数据库功能，包括：
- 基本数据库操作
- 查询构建器使用
- 事务管理示例
- 性能优化示例
- 错误处理示例
- 与测试框架集成示例

运行方法：
    python3 examples/mysql_usage_demo.py

前提条件：
    1. MySQL服务器已启动
    2. 已安装pymysql包: pip install pymysql
    3. 已配置MySQL连接信息

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

from src.utils.database_manager import DatabaseManager, DatabaseConfig


class MySQLUsageDemo:
    """MySQL使用示例类"""
    
    def __init__(self):
        """初始化示例"""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 创建数据库管理器
        self.db_manager = DatabaseManager({
            'database': {
                'type': 'mysql',
                'mysql': {
                    'host': 'localhost',
                    'port': 3306,
                    'database': 'autotest',
                    'username': 'autotest',
                    'password': 'autotest123',
                    'charset': 'utf8mb4'
                }
            }
        })
    
    def demo_basic_operations(self):
        """演示基本数据库操作"""
        print("\n" + "="*50)
        print("1. 基本数据库操作演示")
        print("="*50)
        
        # 创建测试表
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS demo_users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE,
            age INT,
            status ENUM('active', 'inactive') DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
        
        print("创建测试表...")
        result = self.db_manager.execute_query(create_table_sql)
        print(f"创建表结果: {'成功' if result.success else '失败'}")
        
        # 插入数据
        print("插入测试数据...")
        insert_sql = "INSERT INTO demo_users (name, email, age) VALUES (%s, %s, %s)"
        test_data = [
            ("张三", "zhangsan@example.com", 25),
            ("李四", "lisi@example.com", 30),
            ("王五", "wangwu@example.com", 35)
        ]
        
        for data in test_data:
            result = self.db_manager.execute_query(insert_sql, data)
            print(f"插入 {data[0]}: {'成功' if result.success else '失败'}")
        
        # 查询数据
        print("查询所有用户...")
        result = self.db_manager.execute_query("SELECT * FROM demo_users")
        if result.success:
            print(f"查询到 {len(result.data)} 条记录:")
            for user in result.data:
                print(f"  - {user['name']} ({user['email']}) - {user['age']}岁")
        
        # 更新数据
        print("更新用户年龄...")
        update_sql = "UPDATE demo_users SET age = %s WHERE name = %s"
        result = self.db_manager.execute_query(update_sql, (26, "张三"))
        print(f"更新结果: {'成功' if result.success else '失败'}")
        
        # 删除数据
        print("删除测试数据...")
        delete_sql = "DELETE FROM demo_users WHERE name = %s"
        result = self.db_manager.execute_query(delete_sql, ("王五",))
        print(f"删除结果: {'成功' if result.success else '失败'}")
        
        # 清理测试表
        self.db_manager.execute_query("DROP TABLE IF EXISTS demo_users")
        print("✅ 基本操作演示完成")
    
    def demo_query_builder(self):
        """演示查询构建器使用"""
        print("\n" + "="*50)
        print("2. 查询构建器演示")
        print("="*50)
        
        # 创建测试表
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS demo_products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            category VARCHAR(50),
            price DECIMAL(10,2),
            stock INT DEFAULT 0,
            status ENUM('active', 'inactive', 'discontinued') DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
        
        self.db_manager.execute_query(create_table_sql)
        
        # 插入测试数据
        products_data = [
            ("iPhone 15", "手机", 7999.00, 100, "active"),
            ("MacBook Pro", "电脑", 15999.00, 50, "active"),
            ("iPad Air", "平板", 4999.00, 75, "active"),
            ("AirPods Pro", "耳机", 1999.00, 200, "active"),
            ("旧款iPhone", "手机", 2999.00, 10, "discontinued")
        ]
        
        insert_sql = "INSERT INTO demo_products (name, category, price, stock, status) VALUES (%s, %s, %s, %s, %s)"
        for data in products_data:
            self.db_manager.execute_query(insert_sql, data)
        
        print("插入产品数据完成")
        
        # 基本查询
        print("\n查询所有产品:")
        result = self.db_manager.table('demo_products').get()
        if result.success:
            for product in result.data:
                print(f"  - {product['name']}: ¥{product['price']}")
        
        # WHERE条件查询
        print("\n查询手机类产品:")
        result = self.db_manager.table('demo_products').where('category', '=', '手机').get()
        if result.success:
            for product in result.data:
                print(f"  - {product['name']}: ¥{product['price']}")
        
        # 复合条件查询
        print("\n查询价格大于5000的活跃产品:")
        result = (self.db_manager.table('demo_products')
                 .where('price', '>', 5000)
                 .where('status', '=', 'active')
                 .get())
        if result.success:
            for product in result.data:
                print(f"  - {product['name']}: ¥{product['price']}")
        
        # 排序查询
        print("\n按价格降序排列:")
        result = self.db_manager.table('demo_products').order_by('price', 'DESC').get()
        if result.success:
            for product in result.data:
                print(f"  - {product['name']}: ¥{product['price']}")
        
        # 限制查询
        print("\n查询前3个产品:")
        result = self.db_manager.table('demo_products').limit(3).get()
        if result.success:
            for product in result.data:
                print(f"  - {product['name']}: ¥{product['price']}")
        
        # 计数查询
        print("\n统计信息:")
        total_count = self.db_manager.table('demo_products').count()
        active_count = self.db_manager.table('demo_products').where('status', '=', 'active').count()
        print(f"  总产品数: {total_count}")
        print(f"  活跃产品数: {active_count}")
        
        # 获取第一条记录
        print("\n获取第一个产品:")
        first_product = self.db_manager.table('demo_products').first()
        if first_product:
            print(f"  - {first_product['name']}: ¥{first_product['price']}")
        
        # 清理测试表
        self.db_manager.execute_query("DROP TABLE IF EXISTS demo_products")
        print("✅ 查询构建器演示完成")
    
    def demo_transaction_management(self):
        """演示事务管理"""
        print("\n" + "="*50)
        print("3. 事务管理演示")
        print("="*50)
        
        # 创建测试表
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS demo_accounts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            balance DECIMAL(10,2) DEFAULT 0.00,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
        
        self.db_manager.execute_query(create_table_sql)
        
        # 插入测试账户
        accounts_data = [
            ("账户A", 1000.00),
            ("账户B", 500.00),
            ("账户C", 2000.00)
        ]
        
        insert_sql = "INSERT INTO demo_accounts (name, balance) VALUES (%s, %s)"
        for data in accounts_data:
            self.db_manager.execute_query(insert_sql, data)
        
        print("创建测试账户完成")
        
        # 显示初始余额
        print("\n初始账户余额:")
        result = self.db_manager.execute_query("SELECT name, balance FROM demo_accounts ORDER BY name")
        if result.success:
            for account in result.data:
                print(f"  {account['name']}: ¥{account['balance']}")
        
        # 成功事务示例：转账
        print("\n执行转账事务 (账户A -> 账户B: ¥200):")
        try:
            with self.db_manager.transaction():
                # 从账户A扣除200
                self.db_manager.execute_query(
                    "UPDATE demo_accounts SET balance = balance - %s WHERE name = %s",
                    (200.00, "账户A")
                )
                # 向账户B增加200
                self.db_manager.execute_query(
                    "UPDATE demo_accounts SET balance = balance + %s WHERE name = %s",
                    (200.00, "账户B")
                )
                print("  转账事务执行成功")
        except Exception as e:
            print(f"  转账事务执行失败: {e}")
        
        # 显示转账后余额
        print("\n转账后账户余额:")
        result = self.db_manager.execute_query("SELECT name, balance FROM demo_accounts ORDER BY name")
        if result.success:
            for account in result.data:
                print(f"  {account['name']}: ¥{account['balance']}")
        
        # 失败事务示例：回滚
        print("\n执行失败事务 (账户B -> 不存在的账户: ¥100):")
        try:
            with self.db_manager.transaction():
                # 从账户B扣除100
                self.db_manager.execute_query(
                    "UPDATE demo_accounts SET balance = balance - %s WHERE name = %s",
                    (100.00, "账户B")
                )
                # 向不存在的账户增加100（这会失败）
                self.db_manager.execute_query(
                    "UPDATE demo_accounts SET balance = balance + %s WHERE name = %s",
                    (100.00, "不存在的账户")
                )
        except Exception as e:
            print(f"  事务执行失败，已回滚: {e}")
        
        # 显示回滚后余额
        print("\n回滚后账户余额:")
        result = self.db_manager.execute_query("SELECT name, balance FROM demo_accounts ORDER BY name")
        if result.success:
            for account in result.data:
                print(f"  {account['name']}: ¥{account['balance']}")
        
        # 清理测试表
        self.db_manager.execute_query("DROP TABLE IF EXISTS demo_accounts")
        print("✅ 事务管理演示完成")
    
    def demo_batch_operations(self):
        """演示批量操作"""
        print("\n" + "="*50)
        print("4. 批量操作演示")
        print("="*50)
        
        # 创建测试表
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS demo_orders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            order_no VARCHAR(50) NOT NULL,
            customer_name VARCHAR(100),
            amount DECIMAL(10,2),
            status ENUM('pending', 'paid', 'shipped', 'delivered') DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
        
        self.db_manager.execute_query(create_table_sql)
        
        # 准备批量数据
        batch_data = []
        for i in range(1, 101):  # 100条订单
            batch_data.append((
                f"ORD{i:06d}",
                f"客户{i}",
                round(100.00 + i * 10, 2),
                "pending"
            ))
        
        print(f"准备批量插入 {len(batch_data)} 条订单数据...")
        
        # 批量插入
        start_time = time.time()
        insert_sql = "INSERT INTO demo_orders (order_no, customer_name, amount, status) VALUES (%s, %s, %s, %s)"
        result = self.db_manager.execute_many(insert_sql, batch_data)
        insert_time = time.time() - start_time
        
        print(f"批量插入结果: {'成功' if result.success else '失败'}")
        print(f"插入时间: {insert_time:.3f}秒")
        print(f"插入速度: {len(batch_data)/insert_time:.0f} 条/秒")
        
        # 验证插入结果
        count_result = self.db_manager.execute_query("SELECT COUNT(*) as count FROM demo_orders")
        if count_result.success:
            print(f"验证结果: 插入了 {count_result.data[0]['count']} 条记录")
        
        # 批量更新
        print("\n执行批量更新 (更新前50条订单状态为paid)...")
        update_data = [("paid", f"ORD{i:06d}") for i in range(1, 51)]
        
        start_time = time.time()
        update_sql = "UPDATE demo_orders SET status = %s WHERE order_no = %s"
        result = self.db_manager.execute_many(update_sql, update_data)
        update_time = time.time() - start_time
        
        print(f"批量更新结果: {'成功' if result.success else '失败'}")
        print(f"更新时间: {update_time:.3f}秒")
        print(f"更新速度: {len(update_data)/update_time:.0f} 条/秒")
        
        # 验证更新结果
        paid_count = self.db_manager.table('demo_orders').where('status', '=', 'paid').count()
        print(f"验证结果: {paid_count} 条订单状态为paid")
        
        # 清理测试表
        self.db_manager.execute_query("DROP TABLE IF EXISTS demo_orders")
        print("✅ 批量操作演示完成")
    
    def demo_performance_comparison(self):
        """演示性能对比"""
        print("\n" + "="*50)
        print("5. 性能对比演示")
        print("="*50)
        
        # 创建测试表
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS demo_performance (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100),
            value INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
        
        self.db_manager.execute_query(create_table_sql)
        
        # 测试数据
        test_count = 1000
        
        # 单条插入性能测试
        print(f"单条插入性能测试 ({test_count} 条记录):")
        start_time = time.time()
        for i in range(test_count):
            self.db_manager.execute_query(
                "INSERT INTO demo_performance (name, value) VALUES (%s, %s)",
                (f"记录{i}", i)
            )
        single_insert_time = time.time() - start_time
        
        # 批量插入性能测试
        print(f"批量插入性能测试 ({test_count} 条记录):")
        batch_data = [(f"批量记录{i}", i) for i in range(test_count)]
        start_time = time.time()
        self.db_manager.execute_many(
            "INSERT INTO demo_performance (name, value) VALUES (%s, %s)",
            batch_data
        )
        batch_insert_time = time.time() - start_time
        
        # 查询性能测试
        print("查询性能测试:")
        start_time = time.time()
        for i in range(100):
            self.db_manager.execute_query(
                "SELECT * FROM demo_performance WHERE value = %s", (i,)
            )
        select_time = time.time() - start_time
        
        # 输出性能对比
        print(f"\n性能对比结果:")
        print(f"单条插入: {single_insert_time:.3f}秒 ({test_count/single_insert_time:.0f} ops/sec)")
        print(f"批量插入: {batch_insert_time:.3f}秒 ({test_count/batch_insert_time:.0f} ops/sec)")
        print(f"查询操作: {select_time:.3f}秒 ({100/select_time:.0f} ops/sec)")
        
        # 计算性能提升
        if batch_insert_time > 0:
            speedup = single_insert_time / batch_insert_time
            print(f"批量插入性能提升: {speedup:.1f}x")
        
        # 清理测试表
        self.db_manager.execute_query("DROP TABLE IF EXISTS demo_performance")
        print("✅ 性能对比演示完成")
    
    def demo_integration_with_tests(self):
        """演示与测试框架集成"""
        print("\n" + "="*50)
        print("6. 与测试框架集成演示")
        print("="*50)
        
        # 创建测试用例表
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS demo_test_cases (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            api_endpoint VARCHAR(500),
            method ENUM('GET', 'POST', 'PUT', 'DELETE') DEFAULT 'GET',
            expected_status INT DEFAULT 200,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
        
        self.db_manager.execute_query(create_table_sql)
        
        # 创建测试执行记录表
        create_executions_sql = """
        CREATE TABLE IF NOT EXISTS demo_test_executions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            test_case_id INT,
            execution_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status ENUM('passed', 'failed', 'skipped') NOT NULL,
            response_time DECIMAL(10,3),
            error_message TEXT,
            FOREIGN KEY (test_case_id) REFERENCES demo_test_cases(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
        
        self.db_manager.execute_query(create_executions_sql)
        
        # 插入测试用例
        test_cases_data = [
            ("获取用户列表", "/api/users", "GET", 200),
            ("创建用户", "/api/users", "POST", 201),
            ("更新用户", "/api/users/1", "PUT", 200),
            ("删除用户", "/api/users/1", "DELETE", 204)
        ]
        
        insert_sql = "INSERT INTO demo_test_cases (name, api_endpoint, method, expected_status) VALUES (%s, %s, %s, %s)"
        test_case_ids = []
        
        for data in test_cases_data:
            result = self.db_manager.execute_query(insert_sql, data)
            if result.success:
                # 获取插入的ID
                id_result = self.db_manager.execute_query("SELECT LAST_INSERT_ID() as id")
                if id_result.success:
                    test_case_ids.append(id_result.data[0]['id'])
        
        print(f"插入了 {len(test_case_ids)} 个测试用例")
        
        # 模拟测试执行
        print("\n模拟测试执行:")
        execution_data = []
        
        for i, test_case_id in enumerate(test_case_ids):
            # 模拟不同的执行结果
            if i == 0:  # 第一个测试通过
                status = "passed"
                response_time = 0.150
                error_message = None
            elif i == 1:  # 第二个测试失败
                status = "failed"
                response_time = 0.200
                error_message = "用户已存在"
            else:  # 其他测试通过
                status = "passed"
                response_time = 0.100 + i * 0.050
                error_message = None
            
            execution_data.append((test_case_id, status, response_time, error_message))
            print(f"  测试用例 {test_case_id}: {status} ({response_time:.3f}s)")
        
        # 批量插入执行记录
        insert_execution_sql = "INSERT INTO demo_test_executions (test_case_id, status, response_time, error_message) VALUES (%s, %s, %s, %s)"
        result = self.db_manager.execute_many(insert_execution_sql, execution_data)
        
        if result.success:
            print(f"插入了 {len(execution_data)} 条执行记录")
        
        # 查询测试报告
        print("\n生成测试报告:")
        report_sql = """
        SELECT 
            tc.name,
            tc.api_endpoint,
            tc.method,
            tc.expected_status,
            te.status as actual_status,
            te.response_time,
            te.error_message,
            te.execution_time
        FROM demo_test_cases tc
        LEFT JOIN demo_test_executions te ON tc.id = te.test_case_id
        ORDER BY tc.id
        """
        
        result = self.db_manager.execute_query(report_sql)
        if result.success:
            print("测试报告:")
            for row in result.data:
                status_icon = "✅" if row['actual_status'] == 'passed' else "❌"
                print(f"  {status_icon} {row['name']} ({row['method']} {row['api_endpoint']})")
                print(f"     期望状态: {row['expected_status']}, 实际状态: {row['actual_status']}")
                print(f"     响应时间: {row['response_time']}s")
                if row['error_message']:
                    print(f"     错误信息: {row['error_message']}")
        
        # 统计信息
        print("\n测试统计:")
        total_tests = self.db_manager.table('demo_test_cases').count()
        passed_tests = self.db_manager.table('demo_test_executions').where('status', '=', 'passed').count()
        failed_tests = self.db_manager.table('demo_test_executions').where('status', '=', 'failed').count()
        
        print(f"  总测试数: {total_tests}")
        print(f"  通过测试: {passed_tests}")
        print(f"  失败测试: {failed_tests}")
        print(f"  成功率: {(passed_tests/total_tests*100):.1f}%")
        
        # 清理测试表
        self.db_manager.execute_query("DROP TABLE IF EXISTS demo_test_executions")
        self.db_manager.execute_query("DROP TABLE IF EXISTS demo_test_cases")
        print("✅ 集成演示完成")
    
    def demo_error_handling(self):
        """演示错误处理"""
        print("\n" + "="*50)
        print("7. 错误处理演示")
        print("="*50)
        
        # 测试无效SQL
        print("测试无效SQL语句:")
        result = self.db_manager.execute_query("INVALID SQL STATEMENT")
        print(f"  结果: {'成功' if result.success else '失败'}")
        if not result.success:
            print(f"  错误信息: {result.error}")
        
        # 测试不存在的表
        print("\n测试查询不存在的表:")
        result = self.db_manager.execute_query("SELECT * FROM non_existent_table")
        print(f"  结果: {'成功' if result.success else '失败'}")
        if not result.success:
            print(f"  错误信息: {result.error}")
        
        # 测试无效连接
        print("\n测试无效数据库连接:")
        invalid_db_manager = DatabaseManager({
            'database': {
                'type': 'mysql',
                'mysql': {
                    'host': 'invalid-host',
                    'port': 9999,
                    'database': 'non_existent_database',
                    'username': 'invalid_user',
                    'password': 'invalid_password'
                }
            }
        })
        
        result = invalid_db_manager.execute_query("SELECT 1")
        print(f"  结果: {'成功' if result.success else '失败'}")
        if not result.success:
            print(f"  错误信息: {result.error}")
        
        # 测试事务回滚
        print("\n测试事务回滚:")
        try:
            with self.db_manager.transaction():
                # 正常操作
                self.db_manager.execute_query("SELECT 1")
                # 故意引发错误
                self.db_manager.execute_query("SELECT * FROM non_existent_table")
        except Exception as e:
            print(f"  事务回滚成功: {e}")
        
        print("✅ 错误处理演示完成")
    
    def run_all_demos(self):
        """运行所有演示"""
        print("MySQL数据库使用示例")
        print("="*50)
        
        try:
            # 测试MySQL连接
            if not self.db_manager.connect():
                print("❌ MySQL连接失败")
                print("请确保MySQL服务器已启动并配置正确")
                return
            
            print("✅ MySQL连接正常")
            
            # 运行所有演示
            self.demo_basic_operations()
            self.demo_query_builder()
            self.demo_transaction_management()
            self.demo_batch_operations()
            self.demo_performance_comparison()
            self.demo_integration_with_tests()
            self.demo_error_handling()
            
            # 断开连接
            self.db_manager.disconnect()
            
        except Exception as e:
            print(f"❌ 演示执行异常: {e}")
        
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
    demo = MySQLUsageDemo()
    demo.run_all_demos()


if __name__ == "__main__":
    main()
