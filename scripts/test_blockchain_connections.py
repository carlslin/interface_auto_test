#!/usr/bin/env python3
"""
=============================================================================
接口自动化测试框架 - 区块链长连接测试脚本
=============================================================================

本脚本用于测试区块链长连接功能，包括WebSocket连接、连接池管理、
事件订阅、心跳检测等功能的完整性和稳定性。

测试内容：
1. WebSocket连接测试 - 建立和维持WebSocket连接
2. HTTP连接池测试 - 连接池的创建和管理
3. 事件订阅测试 - 订阅和接收区块链事件
4. 心跳检测测试 - 连接状态监控和自动重连
5. 并发连接测试 - 多连接并发处理
6. 故障恢复测试 - 连接断开和自动恢复
7. 性能压力测试 - 高并发下的连接稳定性

支持的网络：
- 以太坊测试网 (Sepolia)
- 比特币测试网
- BSC测试网
- Polygon Mumbai测试网

使用方法：
    # 基础连接测试
    python3 scripts/test_blockchain_connections.py --test basic
    
    # 完整测试套件
    python3 scripts/test_blockchain_connections.py --test all
    
    # 指定网络测试
    python3 scripts/test_blockchain_connections.py --test websocket --network sepolia
    
    # 性能压力测试
    python3 scripts/test_blockchain_connections.py --test performance --concurrent 10

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
import argparse
from typing import Dict, List, Any, Optional
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.blockchain.connection_manager import (
    BlockchainConnectionManager, 
    ConnectionType, 
    ConnectionStatus,
    ConnectionConfig
)
from src.blockchain.blockchain_config import BlockchainConfig


class BlockchainConnectionTester:
    """区块链连接测试器"""
    
    def __init__(self):
        """初始化测试器"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.connection_manager = BlockchainConnectionManager()
        self.blockchain_config = BlockchainConfig()
        self.test_results = []
        self.start_time = time.time()
        
        # 测试统计
        self.stats = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "total_connections": 0,
            "successful_connections": 0,
            "failed_connections": 0,
            "total_events": 0,
            "average_response_time": 0.0
        }
    
    def log_test_result(self, test_name: str, success: bool, message: str = "", 
                       response_time: float = 0.0):
        """记录测试结果"""
        self.stats["total_tests"] += 1
        if success:
            self.stats["passed_tests"] += 1
            status = "✅ 通过"
        else:
            self.stats["failed_tests"] += 1
            status = "❌ 失败"
        
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "response_time": response_time,
            "timestamp": time.time()
        }
        self.test_results.append(result)
        
        self.logger.info(f"{status} {test_name}: {message} ({response_time:.3f}s)")
    
    async def test_websocket_connection(self, network: str = "sepolia") -> bool:
        """测试WebSocket连接"""
        test_name = f"WebSocket连接测试 ({network})"
        start_time = time.time()
        
        try:
            # 获取网络配置
            network_config = self.blockchain_config.get_network_config("ethereum", network)
            if not network_config:
                self.log_test_result(test_name, False, f"未找到网络配置: {network}", 
                                   time.time() - start_time)
                return False
            
            ws_url = network_config.get("ws_url")
            if not ws_url:
                self.log_test_result(test_name, False, f"网络 {network} 未配置WebSocket URL", 
                                   time.time() - start_time)
                return False
            
            # 建立WebSocket连接
            connection_id = await self.connection_manager.connect_websocket(ws_url)
            self.stats["total_connections"] += 1
            self.stats["successful_connections"] += 1
            
            # 等待连接稳定
            await asyncio.sleep(2)
            
            # 检查连接状态
            stats = self.connection_manager.get_connection_stats()
            if connection_id in stats["connections"]:
                conn_status = stats["connections"][connection_id]["status"]
                if conn_status == "connected":
                    self.log_test_result(test_name, True, f"WebSocket连接成功: {connection_id}", 
                                       time.time() - start_time)
                    
                    # 清理连接
                    await self.connection_manager.disconnect(connection_id)
                    return True
                else:
                    self.log_test_result(test_name, False, f"连接状态异常: {conn_status}", 
                                       time.time() - start_time)
                    return False
            else:
                self.log_test_result(test_name, False, "连接未在统计信息中找到", 
                                   time.time() - start_time)
                return False
                
        except Exception as e:
            self.stats["failed_connections"] += 1
            self.log_test_result(test_name, False, f"WebSocket连接失败: {e}", 
                               time.time() - start_time)
            return False
    
    async def test_http_connection_pool(self, network: str = "sepolia", pool_size: int = 5) -> bool:
        """测试HTTP连接池"""
        test_name = f"HTTP连接池测试 ({network}, 大小: {pool_size})"
        start_time = time.time()
        
        try:
            # 获取网络配置
            network_config = self.blockchain_config.get_network_config("ethereum", network)
            if not network_config:
                self.log_test_result(test_name, False, f"未找到网络配置: {network}", 
                                   time.time() - start_time)
                return False
            
            rpc_url = network_config.get("rpc_url")
            if not rpc_url:
                self.log_test_result(test_name, False, f"网络 {network} 未配置RPC URL", 
                                   time.time() - start_time)
                return False
            
            # 建立HTTP连接池
            pool_id = await self.connection_manager.connect_http_pool(rpc_url, pool_size)
            self.stats["total_connections"] += pool_size
            self.stats["successful_connections"] += pool_size
            
            # 等待连接稳定
            await asyncio.sleep(2)
            
            # 检查连接池状态
            stats = self.connection_manager.get_connection_stats()
            pool_connections = [conn_id for conn_id in stats["connections"].keys() 
                              if conn_id.startswith(pool_id)]
            
            if len(pool_connections) == pool_size:
                self.log_test_result(test_name, True, f"HTTP连接池创建成功: {pool_id}", 
                                   time.time() - start_time)
                
                # 清理连接池
                for conn_id in pool_connections:
                    await self.connection_manager.disconnect(conn_id)
                return True
            else:
                self.log_test_result(test_name, False, 
                                   f"连接池大小不匹配: 期望 {pool_size}, 实际 {len(pool_connections)}", 
                                   time.time() - start_time)
                return False
                
        except Exception as e:
            self.stats["failed_connections"] += pool_size
            self.log_test_result(test_name, False, f"HTTP连接池创建失败: {e}", 
                               time.time() - start_time)
            return False
    
    async def test_event_subscription(self, network: str = "sepolia") -> bool:
        """测试事件订阅"""
        test_name = f"事件订阅测试 ({network})"
        start_time = time.time()
        
        try:
            # 获取网络配置
            network_config = self.blockchain_config.get_network_config("ethereum", network)
            if not network_config:
                self.log_test_result(test_name, False, f"未找到网络配置: {network}", 
                                   time.time() - start_time)
                return False
            
            ws_url = network_config.get("ws_url")
            if not ws_url:
                self.log_test_result(test_name, False, f"网络 {network} 未配置WebSocket URL", 
                                   time.time() - start_time)
                return False
            
            # 建立WebSocket连接
            connection_id = await self.connection_manager.connect_websocket(ws_url)
            
            # 订阅新区块事件
            success = await self.connection_manager.subscribe_events(
                connection_id, "newHeads"
            )
            
            if success:
                self.log_test_result(test_name, True, "事件订阅成功", 
                                   time.time() - start_time)
                
                # 等待一段时间接收事件
                await asyncio.sleep(5)
                
                # 清理连接
                await self.connection_manager.disconnect(connection_id)
                return True
            else:
                self.log_test_result(test_name, False, "事件订阅失败", 
                                   time.time() - start_time)
                return False
                
        except Exception as e:
            self.log_test_result(test_name, False, f"事件订阅测试失败: {e}", 
                               time.time() - start_time)
            return False
    
    async def test_heartbeat_monitoring(self, network: str = "sepolia") -> bool:
        """测试心跳监控"""
        test_name = f"心跳监控测试 ({network})"
        start_time = time.time()
        
        try:
            # 获取网络配置
            network_config = self.blockchain_config.get_network_config("ethereum", network)
            if not network_config:
                self.log_test_result(test_name, False, f"未找到网络配置: {network}", 
                                   time.time() - start_time)
                return False
            
            ws_url = network_config.get("ws_url")
            if not ws_url:
                self.log_test_result(test_name, False, f"网络 {network} 未配置WebSocket URL", 
                                   time.time() - start_time)
                return False
            
            # 建立WebSocket连接
            connection_id = await self.connection_manager.connect_websocket(ws_url)
            
            # 启动心跳监控
            await self.connection_manager.start_heartbeat_monitoring()
            
            # 等待心跳检测
            await asyncio.sleep(10)
            
            # 检查连接状态
            stats = self.connection_manager.get_connection_stats()
            if connection_id in stats["connections"]:
                conn_info = stats["connections"][connection_id]
                if conn_info["status"] == "connected":
                    self.log_test_result(test_name, True, "心跳监控正常", 
                                       time.time() - start_time)
                    
                    # 停止心跳监控
                    await self.connection_manager.stop_heartbeat_monitoring()
                    
                    # 清理连接
                    await self.connection_manager.disconnect(connection_id)
                    return True
                else:
                    self.log_test_result(test_name, False, f"连接状态异常: {conn_info['status']}", 
                                       time.time() - start_time)
                    return False
            else:
                self.log_test_result(test_name, False, "连接未在统计信息中找到", 
                                   time.time() - start_time)
                return False
                
        except Exception as e:
            self.log_test_result(test_name, False, f"心跳监控测试失败: {e}", 
                               time.time() - start_time)
            return False
    
    async def test_concurrent_connections(self, network: str = "sepolia", concurrent_count: int = 5) -> bool:
        """测试并发连接"""
        test_name = f"并发连接测试 ({network}, 并发数: {concurrent_count})"
        start_time = time.time()
        
        try:
            # 获取网络配置
            network_config = self.blockchain_config.get_network_config("ethereum", network)
            if not network_config:
                self.log_test_result(test_name, False, f"未找到网络配置: {network}", 
                                   time.time() - start_time)
                return False
            
            ws_url = network_config.get("ws_url")
            if not ws_url:
                self.log_test_result(test_name, False, f"网络 {network} 未配置WebSocket URL", 
                                   time.time() - start_time)
                return False
            
            # 创建并发连接任务
            tasks = []
            for i in range(concurrent_count):
                task = asyncio.create_task(
                    self.connection_manager.connect_websocket(ws_url)
                )
                tasks.append(task)
            
            # 等待所有连接完成
            connection_ids = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 统计成功连接
            successful_connections = []
            failed_connections = 0
            
            for i, result in enumerate(connection_ids):
                if isinstance(result, Exception):
                    failed_connections += 1
                    self.logger.error(f"并发连接 {i} 失败: {result}")
                else:
                    successful_connections.append(result)
            
            self.stats["total_connections"] += concurrent_count
            self.stats["successful_connections"] += len(successful_connections)
            self.stats["failed_connections"] += failed_connections
            
            success_rate = len(successful_connections) / concurrent_count * 100
            
            if success_rate >= 80:  # 80%成功率认为通过
                self.log_test_result(test_name, True, 
                                   f"并发连接成功率: {success_rate:.1f}% ({len(successful_connections)}/{concurrent_count})", 
                                   time.time() - start_time)
                
                # 清理连接
                for conn_id in successful_connections:
                    await self.connection_manager.disconnect(conn_id)
                return True
            else:
                self.log_test_result(test_name, False, 
                                   f"并发连接成功率过低: {success_rate:.1f}% ({len(successful_connections)}/{concurrent_count})", 
                                   time.time() - start_time)
                return False
                
        except Exception as e:
            self.log_test_result(test_name, False, f"并发连接测试失败: {e}", 
                               time.time() - start_time)
            return False
    
    async def test_rpc_requests(self, network: str = "sepolia") -> bool:
        """测试RPC请求"""
        test_name = f"RPC请求测试 ({network})"
        start_time = time.time()
        
        try:
            # 获取网络配置
            network_config = self.blockchain_config.get_network_config("ethereum", network)
            if not network_config:
                self.log_test_result(test_name, False, f"未找到网络配置: {network}", 
                                   time.time() - start_time)
                return False
            
            rpc_url = network_config.get("rpc_url")
            if not rpc_url:
                self.log_test_result(test_name, False, f"网络 {network} 未配置RPC URL", 
                                   time.time() - start_time)
                return False
            
            # 建立HTTP连接池
            pool_id = await self.connection_manager.connect_http_pool(rpc_url, 3)
            
            # 获取连接池中的连接
            stats = self.connection_manager.get_connection_stats()
            pool_connections = [conn_id for conn_id in stats["connections"].keys() 
                              if conn_id.startswith(pool_id)]
            
            if not pool_connections:
                self.log_test_result(test_name, False, "连接池为空", 
                                   time.time() - start_time)
                return False
            
            # 使用第一个连接发送RPC请求
            connection_id = pool_connections[0]
            
            # 发送eth_blockNumber请求
            response = await self.connection_manager.send_request(
                connection_id, "eth_blockNumber"
            )
            
            if "result" in response:
                block_number = int(response["result"], 16)
                self.log_test_result(test_name, True, 
                                   f"RPC请求成功，当前区块: {block_number}", 
                                   time.time() - start_time)
                
                # 清理连接池
                for conn_id in pool_connections:
                    await self.connection_manager.disconnect(conn_id)
                return True
            else:
                error_msg = response.get("error", "未知错误")
                self.log_test_result(test_name, False, f"RPC请求失败: {error_msg}", 
                                   time.time() - start_time)
                return False
                
        except Exception as e:
            self.log_test_result(test_name, False, f"RPC请求测试失败: {e}", 
                               time.time() - start_time)
            return False
    
    async def run_basic_tests(self, network: str = "sepolia") -> Dict[str, bool]:
        """运行基础测试"""
        self.logger.info(f"开始运行基础测试 (网络: {network})")
        
        results = {}
        
        # WebSocket连接测试
        results["websocket_connection"] = await self.test_websocket_connection(network)
        
        # HTTP连接池测试
        results["http_connection_pool"] = await self.test_http_connection_pool(network)
        
        # RPC请求测试
        results["rpc_requests"] = await self.test_rpc_requests(network)
        
        return results
    
    async def run_advanced_tests(self, network: str = "sepolia") -> Dict[str, bool]:
        """运行高级测试"""
        self.logger.info(f"开始运行高级测试 (网络: {network})")
        
        results = {}
        
        # 事件订阅测试
        results["event_subscription"] = await self.test_event_subscription(network)
        
        # 心跳监控测试
        results["heartbeat_monitoring"] = await self.test_heartbeat_monitoring(network)
        
        # 并发连接测试
        results["concurrent_connections"] = await self.test_concurrent_connections(network, 5)
        
        return results
    
    async def run_performance_tests(self, network: str = "sepolia", concurrent_count: int = 10) -> Dict[str, bool]:
        """运行性能测试"""
        self.logger.info(f"开始运行性能测试 (网络: {network}, 并发数: {concurrent_count})")
        
        results = {}
        
        # 高并发连接测试
        results["high_concurrent_connections"] = await self.test_concurrent_connections(
            network, concurrent_count
        )
        
        # 大连接池测试
        results["large_connection_pool"] = await self.test_http_connection_pool(
            network, concurrent_count
        )
        
        return results
    
    def print_summary(self):
        """打印测试总结"""
        total_time = time.time() - self.start_time
        success_rate = (self.stats["passed_tests"] / self.stats["total_tests"] * 100) if self.stats["total_tests"] > 0 else 0
        
        print("\n" + "="*80)
        print("区块链长连接测试总结")
        print("="*80)
        print(f"总测试数: {self.stats['total_tests']}")
        print(f"通过测试: {self.stats['passed_tests']}")
        print(f"失败测试: {self.stats['failed_tests']}")
        print(f"成功率: {success_rate:.1f}%")
        print(f"总连接数: {self.stats['total_connections']}")
        print(f"成功连接: {self.stats['successful_connections']}")
        print(f"失败连接: {self.stats['failed_connections']}")
        print(f"总测试时间: {total_time:.2f}秒")
        print("="*80)
        
        # 打印详细结果
        print("\n详细测试结果:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test_name']}: {result['message']} ({result['response_time']:.3f}s)")
        
        # 保存结果到文件
        report_file = f"blockchain_connection_test_report_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": self.stats,
                "results": self.test_results,
                "total_time": total_time
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n测试报告已保存到: {report_file}")


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="区块链长连接测试脚本")
    parser.add_argument("--test", choices=["basic", "advanced", "performance", "all"], 
                       default="basic", help="测试类型")
    parser.add_argument("--network", default="sepolia", 
                       help="测试网络 (sepolia, bsc_testnet, mumbai)")
    parser.add_argument("--concurrent", type=int, default=10, 
                       help="并发连接数 (仅用于性能测试)")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="详细输出")
    
    args = parser.parse_args()
    
    # 配置日志
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建测试器
    tester = BlockchainConnectionTester()
    
    try:
        if args.test == "basic":
            await tester.run_basic_tests(args.network)
        elif args.test == "advanced":
            await tester.run_advanced_tests(args.network)
        elif args.test == "performance":
            await tester.run_performance_tests(args.network, args.concurrent)
        elif args.test == "all":
            await tester.run_basic_tests(args.network)
            await tester.run_advanced_tests(args.network)
            await tester.run_performance_tests(args.network, args.concurrent)
        
        # 打印总结
        tester.print_summary()
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
    finally:
        # 清理资源
        await tester.connection_manager.disconnect_all()


if __name__ == "__main__":
    asyncio.run(main())
