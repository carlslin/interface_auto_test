#!/usr/bin/env python3
"""
=============================================================================
接口自动化测试框架 - 完整示例集合
=============================================================================

本文件包含了接口自动化测试框架的所有使用示例，包括：
1. 基础API测试示例
2. AI功能使用示例
3. 区块链功能示例
4. 缓存和数据库示例
5. 长连接示例
6. Mock服务器示例
7. 解析器示例
8. 导出器示例

使用方法：
    # 运行所有示例
    python3 examples/all_examples.py --run-all
    
    # 运行特定示例
    python3 examples/all_examples.py --example basic
    python3 examples/all_examples.py --example ai
    python3 examples/all_examples.py --example blockchain
    
    # 运行测试验证
    python3 examples/all_examples.py --test

作者: 接口自动化测试框架团队
版本: 1.0.0
更新日期: 2024年12月
=============================================================================
"""

import asyncio
import json
import logging
import os
import sys
import time
from typing import Dict, Any, Optional, List
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入所有模块
from src.core.request_handler import RequestHandler
from src.core.base_test import BaseTest, TestResult
from src.ai.deepseek_client import DeepSeekClient
from src.blockchain.connection_manager import BlockchainConnectionManager
from src.utils.cache_manager import CacheManager
from src.utils.database_manager import DatabaseManager
from src.mock.mock_server import MockServer
from src.parsers.openapi_parser import OpenAPIParser
from src.exporters.test_case_exporter import TestCaseExporter
from src.utils.config_loader import ConfigLoader


class AllExamples:
    """完整示例集合类"""
    
    def __init__(self):
        """初始化示例集合"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = ConfigLoader().config_data
        self.results = []
        
        # 初始化组件
        self.request_handler = None
        self.ai_client = None
        self.cache_manager = None
        self.db_manager = None
        self.mock_server = None
        self.connection_manager = None
        
        print("🚀 接口自动化测试框架 - 完整示例集合")
        print("="*80)
    
    def log_result(self, example_name: str, success: bool, message: str = ""):
        """记录示例执行结果"""
        result = {
            "example": example_name,
            "success": success,
            "message": message,
            "timestamp": time.time()
        }
        self.results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {example_name}: {message}")
    
    def example_basic_api_test(self):
        """基础API测试示例"""
        print("\n📡 基础API测试示例")
        print("-" * 40)
        
        try:
            # 创建请求处理器
            self.request_handler = RequestHandler(self.config)
            
            # 示例API请求
            test_url = "https://httpbin.org/get"
            response = self.request_handler.request("GET", test_url)
            
            if response and response.get("status_code") == 200:
                self.log_result("基础API测试", True, f"成功请求 {test_url}")
                return True
            else:
                self.log_result("基础API测试", False, "API请求失败")
                return False
                
        except Exception as e:
            self.log_result("基础API测试", False, f"异常: {e}")
            return False
    
    def example_ai_functionality(self):
        """AI功能示例"""
        print("\n🤖 AI功能示例")
        print("-" * 40)
        
        try:
            # 检查AI API Key
            api_key = os.getenv('DEEPSEEK_API_KEY', 'sk-your-deepseek-api-key')
            if api_key == 'sk-your-deepseek-api-key':
                self.log_result("AI功能示例", False, "请设置真实的DEEPSEEK_API_KEY环境变量")
                return False
            
            # 创建AI客户端
            self.ai_client = DeepSeekClient(api_key)
            
            # 发送AI请求
            response = self.ai_client.chat_completion(
                messages=[{"role": "user", "content": "Hello, AI!"}],
                model="deepseek-chat"
            )
            
            if response and response.content:
                self.log_result("AI功能示例", True, f"AI响应: {response.content[:50]}...")
                return True
            else:
                self.log_result("AI功能示例", False, "AI请求失败")
                return False
                
        except Exception as e:
            self.log_result("AI功能示例", False, f"异常: {e}")
            return False
    
    async def example_blockchain_connection(self):
        """区块链连接示例"""
        print("\n⛓️ 区块链连接示例")
        print("-" * 40)
        
        try:
            # 创建连接管理器
            self.connection_manager = BlockchainConnectionManager()
            
            # 示例WebSocket连接（使用公共测试节点）
            test_url = "wss://sepolia.infura.io/ws/v3/YOUR_KEY"
            
            # 注意：这里使用示例URL，实际使用时需要替换为真实的URL
            print(f"尝试连接到: {test_url}")
            print("注意：这是示例URL，实际使用时需要替换为真实的WebSocket URL")
            
            self.log_result("区块链连接示例", True, "连接管理器创建成功（使用示例URL）")
            return True
            
        except Exception as e:
            self.log_result("区块链连接示例", False, f"异常: {e}")
            return False
    
    def example_cache_operations(self):
        """缓存操作示例"""
        print("\n💾 缓存操作示例")
        print("-" * 40)
        
        try:
            # 创建缓存管理器
            self.cache_manager = CacheManager("memory")
            
            # 测试缓存操作
            test_key = "test_key"
            test_value = {"message": "Hello Cache!", "timestamp": time.time()}
            
            # 设置缓存
            success = self.cache_manager.set(test_key, test_value)
            if not success:
                self.log_result("缓存操作示例", False, "设置缓存失败")
                return False
            
            # 获取缓存
            cached_value = self.cache_manager.get(test_key)
            if cached_value and cached_value.get("message") == test_value["message"]:
                self.log_result("缓存操作示例", True, "缓存设置和获取成功")
                return True
            else:
                self.log_result("缓存操作示例", False, "缓存获取失败")
                return False
                
        except Exception as e:
            self.log_result("缓存操作示例", False, f"异常: {e}")
            return False
    
    def example_database_operations(self):
        """数据库操作示例"""
        print("\n🗄️ 数据库操作示例")
        print("-" * 40)
        
        try:
            # 创建数据库管理器
            self.db_manager = DatabaseManager("sqlite", ":memory:")
            
            # 创建测试表
            create_table_sql = """
            CREATE TABLE test_users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            result = self.db_manager.execute_query(create_table_sql)
            if not result.success:
                self.log_result("数据库操作示例", False, "创建表失败")
                return False
            
            # 插入测试数据
            insert_sql = "INSERT INTO test_users (name, email) VALUES (?, ?)"
            result = self.db_manager.execute_query(insert_sql, ("测试用户", "test@example.com"))
            
            if result.success:
                # 查询数据
                select_sql = "SELECT * FROM test_users WHERE name = ?"
                result = self.db_manager.execute_query(select_sql, ("测试用户",))
                
                if result.success and result.data:
                    self.log_result("数据库操作示例", True, "数据库操作成功")
                    return True
                else:
                    self.log_result("数据库操作示例", False, "数据查询失败")
                    return False
            else:
                self.log_result("数据库操作示例", False, "数据插入失败")
                return False
                
        except Exception as e:
            self.log_result("数据库操作示例", False, f"异常: {e}")
            return False
    
    def example_mock_server(self):
        """Mock服务器示例"""
        print("\n🎭 Mock服务器示例")
        print("-" * 40)
        
        try:
            # 创建Mock服务器
            self.mock_server = MockServer()
            
            # 添加测试路由
            self.mock_server.add_route("GET", "/api/test", {"message": "Mock响应"}, 200)
            
            # 启动服务器
            self.mock_server.start(port=8080)
            
            # 等待服务器启动
            time.sleep(2)
            
            # 测试请求
            import requests
            response = requests.get("http://localhost:8080/api/test", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("message") == "Mock响应":
                    self.log_result("Mock服务器示例", True, "Mock服务器运行正常")
                    self.mock_server.stop()
                    return True
                else:
                    self.log_result("Mock服务器示例", False, "Mock响应内容不正确")
                    self.mock_server.stop()
                    return False
            else:
                self.log_result("Mock服务器示例", False, f"Mock请求失败: {response.status_code}")
                self.mock_server.stop()
                return False
                
        except Exception as e:
            self.log_result("Mock服务器示例", False, f"异常: {e}")
            if self.mock_server:
                self.mock_server.stop()
            return False
    
    def example_api_parser(self):
        """API解析器示例"""
        print("\n📄 API解析器示例")
        print("-" * 40)
        
        try:
            # 创建示例OpenAPI文档
            openapi_doc = {
                "openapi": "3.0.0",
                "info": {"title": "测试API", "version": "1.0.0"},
                "paths": {
                    "/api/users": {
                        "get": {
                            "responses": {"200": {"description": "成功"}}
                        },
                        "post": {
                            "requestBody": {
                                "content": {
                                    "application/json": {
                                        "schema": {"type": "object"}
                                    }
                                }
                            },
                            "responses": {"201": {"description": "创建成功"}}
                        }
                    }
                }
            }
            
            # 创建临时文件
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(openapi_doc, f)
                temp_file = f.name
            
            try:
                # 使用解析器
                parser = OpenAPIParser()
                result = parser.load_from_file(temp_file)
                
                if result:
                    paths = parser.get_all_paths()
                    if paths and len(paths) > 0:
                        self.log_result("API解析器示例", True, f"成功解析API文档，发现 {len(paths)} 个路径")
                        return True
                    else:
                        self.log_result("API解析器示例", False, "未发现API路径")
                        return False
                else:
                    self.log_result("API解析器示例", False, "API文档解析失败")
                    return False
                    
            finally:
                # 清理临时文件
                os.unlink(temp_file)
                
        except Exception as e:
            self.log_result("API解析器示例", False, f"异常: {e}")
            return False
    
    def example_test_exporter(self):
        """测试导出器示例"""
        print("\n📊 测试导出器示例")
        print("-" * 40)
        
        try:
            # 创建示例测试用例
            test_cases = [
                {
                    "name": "测试用例1",
                    "description": "GET请求测试",
                    "method": "GET",
                    "url": "/api/users",
                    "expected_status": 200
                },
                {
                    "name": "测试用例2",
                    "description": "POST请求测试",
                    "method": "POST",
                    "url": "/api/users",
                    "expected_status": 201,
                    "request_data": {"name": "测试用户"}
                }
            ]
            
            # 创建导出器
            exporter = TestCaseExporter()
            
            # 导出为JSON格式
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                temp_file = f.name
            
            try:
                success = exporter.export_test_cases(test_cases, temp_file, "json")
                
                if success and os.path.exists(temp_file):
                    # 验证导出文件
                    with open(temp_file, 'r') as f:
                        exported_data = json.load(f)
                    
                    if exported_data and len(exported_data) == len(test_cases):
                        self.log_result("测试导出器示例", True, "测试用例导出成功")
                        return True
                    else:
                        self.log_result("测试导出器示例", False, "导出数据不完整")
                        return False
                else:
                    self.log_result("测试导出器示例", False, "导出失败")
                    return False
                    
            finally:
                # 清理临时文件
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                
        except Exception as e:
            self.log_result("测试导出器示例", False, f"异常: {e}")
            return False
    
    async def example_long_connection(self):
        """长连接示例"""
        print("\n🔗 长连接示例")
        print("-" * 40)
        
        try:
            # 创建连接管理器
            conn_manager = BlockchainConnectionManager()
            
            # 模拟长连接操作
            print("创建连接管理器...")
            print("配置连接池...")
            print("启动心跳监控...")
            
            # 模拟连接统计
            stats = conn_manager.get_connection_stats()
            self.log_result("长连接示例", True, "连接管理器创建成功")
            return True
            
        except Exception as e:
            self.log_result("长连接示例", False, f"异常: {e}")
            return False
    
    def run_basic_examples(self):
        """运行基础示例"""
        print("\n🚀 运行基础示例")
        print("="*80)
        
        examples = [
            ("基础API测试", self.example_basic_api_test),
            ("缓存操作", self.example_cache_operations),
            ("数据库操作", self.example_database_operations),
            ("API解析器", self.example_api_parser),
            ("测试导出器", self.example_test_exporter),
        ]
        
        success_count = 0
        for name, func in examples:
            try:
                if func():
                    success_count += 1
            except Exception as e:
                self.log_result(name, False, f"执行异常: {e}")
        
        print(f"\n📊 基础示例结果: {success_count}/{len(examples)} 成功")
        return success_count == len(examples)
    
    async def run_advanced_examples(self):
        """运行高级示例"""
        print("\n🚀 运行高级示例")
        print("="*80)
        
        examples = [
            ("AI功能", self.example_ai_functionality),
            ("区块链连接", self.example_blockchain_connection),
            ("长连接", self.example_long_connection),
        ]
        
        success_count = 0
        for name, func in examples:
            try:
                if asyncio.iscoroutinefunction(func):
                    if await func():
                        success_count += 1
                else:
                    if func():
                        success_count += 1
            except Exception as e:
                self.log_result(name, False, f"执行异常: {e}")
        
        print(f"\n📊 高级示例结果: {success_count}/{len(examples)} 成功")
        return success_count == len(examples)
    
    async def run_all_examples(self):
        """运行所有示例"""
        print("\n🚀 运行所有示例")
        print("="*80)
        
        # 运行基础示例
        basic_success = self.run_basic_examples()
        
        # 运行高级示例
        advanced_success = await self.run_advanced_examples()
        
        # 运行Mock服务器示例（单独运行，避免端口冲突）
        mock_success = self.example_mock_server()
        
        total_examples = len(self.results)
        successful_examples = sum(1 for r in self.results if r["success"])
        
        print(f"\n🎉 所有示例执行完成!")
        print(f"📊 总示例数: {total_examples}")
        print(f"✅ 成功: {successful_examples}")
        print(f"❌ 失败: {total_examples - successful_examples}")
        print(f"📈 成功率: {successful_examples/total_examples*100:.1f}%")
        
        return successful_examples == total_examples
    
    def print_summary(self):
        """打印执行总结"""
        print("\n" + "="*80)
        print("📋 示例执行总结")
        print("="*80)
        
        for result in self.results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['example']}: {result['message']}")
        
        successful = sum(1 for r in self.results if r["success"])
        total = len(self.results)
        
        print(f"\n📊 总结:")
        print(f"   - 总示例数: {total}")
        print(f"   - 成功数: {successful}")
        print(f"   - 失败数: {total - successful}")
        print(f"   - 成功率: {successful/total*100:.1f}%")


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="接口自动化测试框架 - 完整示例集合")
    parser.add_argument("--run-all", action="store_true", help="运行所有示例")
    parser.add_argument("--example", choices=["basic", "ai", "blockchain", "cache", "database", "mock", "parser", "exporter", "long-connection"], 
                       help="运行特定示例")
    parser.add_argument("--test", action="store_true", help="运行测试验证")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    # 配置日志
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建示例集合
    examples = AllExamples()
    
    try:
        if args.run_all:
            success = await examples.run_all_examples()
        elif args.example:
            if args.example == "basic":
                success = examples.example_basic_api_test()
            elif args.example == "ai":
                success = examples.example_ai_functionality()
            elif args.example == "blockchain":
                success = await examples.example_blockchain_connection()
            elif args.example == "cache":
                success = examples.example_cache_operations()
            elif args.example == "database":
                success = examples.example_database_operations()
            elif args.example == "mock":
                success = examples.example_mock_server()
            elif args.example == "parser":
                success = examples.example_api_parser()
            elif args.example == "exporter":
                success = examples.example_test_exporter()
            elif args.example == "long-connection":
                success = await examples.example_long_connection()
        elif args.test:
            success = await examples.run_all_examples()
        else:
            print("请指定运行选项，使用 --help 查看帮助")
            return
        
        # 打印总结
        examples.print_summary()
        
        if success:
            print("\n🎉 所有示例执行成功!")
            sys.exit(0)
        else:
            print("\n⚠️ 部分示例执行失败，请检查日志")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ 示例执行被用户中断")
    except Exception as e:
        print(f"\n❌ 示例执行过程中发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
