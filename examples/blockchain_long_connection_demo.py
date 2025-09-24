#!/usr/bin/env python3
"""
=============================================================================
接口自动化测试框架 - 区块链长连接使用示例
=============================================================================

本示例演示了如何使用区块链长连接功能，包括WebSocket连接、事件订阅、
连接池管理、心跳检测等高级特性。

主要功能演示：
1. WebSocket长连接 - 建立和维护WebSocket连接
2. 事件实时订阅 - 订阅新区块、交易等事件
3. 连接池管理 - HTTP连接池的创建和使用
4. 心跳监控 - 自动连接状态检测和重连
5. 并发处理 - 多连接并发操作
6. 错误处理 - 连接失败和自动恢复
7. 性能监控 - 连接性能和统计信息

使用场景：
- 实时监控区块链状态
- 智能合约事件监听
- 高频交易数据获取
- 区块链网络健康检查
- 多链数据同步

使用方法：
    # 基础WebSocket连接
    python3 examples/blockchain_long_connection_demo.py --mode websocket
    
    # 事件订阅演示
    python3 examples/blockchain_long_connection_demo.py --mode events
    
    # 连接池演示
    python3 examples/blockchain_long_connection_demo.py --mode pool
    
    # 完整功能演示
    python3 examples/blockchain_long_connection_demo.py --mode full

作者: 接口自动化测试框架团队
版本: 1.0.0
更新日期: 2024年12月
=============================================================================
"""

import asyncio
import json
import logging
import sys
import time
from typing import Dict, List, Any, Optional
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.blockchain.connection_manager import (
    BlockchainConnectionManager, 
    ConnectionType, 
    ConnectionStatus
)
from src.blockchain.blockchain_config import BlockchainConfig


class BlockchainLongConnectionDemo:
    """区块链长连接演示类"""
    
    def __init__(self):
        """初始化演示"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.connection_manager = BlockchainConnectionManager()
        self.blockchain_config = BlockchainConfig()
        self.connections = []
        self.event_count = 0
        self.start_time = time.time()
    
    async def demo_websocket_connection(self, network: str = "sepolia"):
        """演示WebSocket长连接"""
        print(f"\n🔗 WebSocket长连接演示 (网络: {network})")
        print("="*60)
        
        try:
            # 获取网络配置
            network_config = self.blockchain_config.get_network_config("ethereum", network)
            if not network_config:
                print(f"❌ 未找到网络配置: {network}")
                return
            
            ws_url = network_config.get("ws_url")
            if not ws_url:
                print(f"❌ 网络 {network} 未配置WebSocket URL")
                return
            
            print(f"📡 连接到WebSocket: {ws_url}")
            
            # 建立WebSocket连接
            connection_id = await self.connection_manager.connect_websocket(ws_url)
            self.connections.append(connection_id)
            
            print(f"✅ WebSocket连接建立成功: {connection_id}")
            
            # 显示连接统计
            stats = self.connection_manager.get_connection_stats()
            print(f"📊 连接统计: {stats['connection_count']} 个连接")
            
            # 保持连接一段时间
            print("⏳ 保持连接30秒...")
            await asyncio.sleep(30)
            
            print("✅ WebSocket长连接演示完成")
            
        except Exception as e:
            print(f"❌ WebSocket连接演示失败: {e}")
            self.logger.error(f"WebSocket连接演示失败: {e}")
    
    async def demo_event_subscription(self, network: str = "sepolia"):
        """演示事件订阅"""
        print(f"\n📡 事件订阅演示 (网络: {network})")
        print("="*60)
        
        try:
            # 获取网络配置
            network_config = self.blockchain_config.get_network_config("ethereum", network)
            if not network_config:
                print(f"❌ 未找到网络配置: {network}")
                return
            
            ws_url = network_config.get("ws_url")
            if not ws_url:
                print(f"❌ 网络 {network} 未配置WebSocket URL")
                return
            
            print(f"📡 建立WebSocket连接...")
            
            # 建立WebSocket连接
            connection_id = await self.connection_manager.connect_websocket(ws_url)
            self.connections.append(connection_id)
            
            print(f"✅ 连接建立成功: {connection_id}")
            
            # 订阅新区块事件
            print("📋 订阅新区块事件...")
            success = await self.connection_manager.subscribe_events(connection_id, "newHeads")
            
            if success:
                print("✅ 事件订阅成功")
                
                # 监听事件
                print("👂 开始监听事件 (60秒)...")
                print("按 Ctrl+C 停止监听")
                
                try:
                    event_count = 0
                    async for event in self.connection_manager.listen_events(connection_id):
                        event_count += 1
                        self.event_count += 1
                        
                        if event.get("method") == "eth_subscription":
                            # 处理新区块事件
                            params = event.get("params", {})
                            result = params.get("result", {})
                            
                            if "number" in result:
                                block_number = int(result["number"], 16)
                                print(f"🆕 新区块 #{block_number}")
                                print(f"   📅 时间戳: {int(result.get('timestamp', '0'), 16)}")
                                print(f"   ⛏️  矿工: {result.get('miner', 'N/A')}")
                                print(f"   ⛽ Gas限制: {int(result.get('gasLimit', '0'), 16)}")
                                print(f"   📊 Gas使用: {int(result.get('gasUsed', '0'), 16)}")
                                print("-" * 40)
                        
                        # 限制监听时间
                        if event_count >= 10:
                            print("⏰ 已监听10个事件，演示结束")
                            break
                            
                except KeyboardInterrupt:
                    print("\n⏹️ 监听已停止")
                
                print(f"📊 总共接收到 {event_count} 个事件")
            else:
                print("❌ 事件订阅失败")
            
            print("✅ 事件订阅演示完成")
            
        except Exception as e:
            print(f"❌ 事件订阅演示失败: {e}")
            self.logger.error(f"事件订阅演示失败: {e}")
    
    async def demo_connection_pool(self, network: str = "sepolia"):
        """演示连接池管理"""
        print(f"\n🏊 连接池管理演示 (网络: {network})")
        print("="*60)
        
        try:
            # 获取网络配置
            network_config = self.blockchain_config.get_network_config("ethereum", network)
            if not network_config:
                print(f"❌ 未找到网络配置: {network}")
                return
            
            rpc_url = network_config.get("rpc_url")
            if not rpc_url:
                print(f"❌ 网络 {network} 未配置RPC URL")
                return
            
            print(f"📡 创建HTTP连接池...")
            
            # 创建连接池
            pool_size = 5
            pool_id = await self.connection_manager.connect_http_pool(rpc_url, pool_size)
            
            print(f"✅ 连接池创建成功: {pool_id} (大小: {pool_size})")
            
            # 获取连接池统计
            stats = self.connection_manager.get_connection_stats()
            pool_connections = [conn_id for conn_id in stats["connections"].keys() 
                              if conn_id.startswith(pool_id)]
            
            print(f"📊 连接池统计:")
            print(f"   - 连接数: {len(pool_connections)}")
            print(f"   - 活跃连接: {stats['active_connections']}")
            
            # 使用连接池发送RPC请求
            print("📤 使用连接池发送RPC请求...")
            
            # 并发发送多个请求
            tasks = []
            for i in range(10):
                connection_id = pool_connections[i % len(pool_connections)]
                task = asyncio.create_task(
                    self._send_rpc_request(connection_id, "eth_blockNumber", f"请求 #{i+1}")
                )
                tasks.append(task)
            
            # 等待所有请求完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 统计结果
            successful_requests = sum(1 for result in results if not isinstance(result, Exception))
            print(f"📊 RPC请求统计:")
            print(f"   - 总请求数: {len(results)}")
            print(f"   - 成功请求: {successful_requests}")
            print(f"   - 成功率: {successful_requests/len(results)*100:.1f}%")
            
            print("✅ 连接池管理演示完成")
            
        except Exception as e:
            print(f"❌ 连接池管理演示失败: {e}")
            self.logger.error(f"连接池管理演示失败: {e}")
    
    async def _send_rpc_request(self, connection_id: str, method: str, request_name: str):
        """发送RPC请求"""
        try:
            start_time = time.time()
            response = await self.connection_manager.send_request(connection_id, method)
            response_time = time.time() - start_time
            
            if "result" in response:
                result = response["result"]
                print(f"✅ {request_name} 成功 ({response_time:.3f}s): {result[:20]}...")
                return True
            else:
                error = response.get("error", "未知错误")
                print(f"❌ {request_name} 失败: {error}")
                return False
                
        except Exception as e:
            print(f"❌ {request_name} 异常: {e}")
            return False
    
    async def demo_heartbeat_monitoring(self, network: str = "sepolia"):
        """演示心跳监控"""
        print(f"\n💓 心跳监控演示 (网络: {network})")
        print("="*60)
        
        try:
            # 获取网络配置
            network_config = self.blockchain_config.get_network_config("ethereum", network)
            if not network_config:
                print(f"❌ 未找到网络配置: {network}")
                return
            
            ws_url = network_config.get("ws_url")
            if not ws_url:
                print(f"❌ 网络 {network} 未配置WebSocket URL")
                return
            
            print(f"📡 建立WebSocket连接...")
            
            # 建立WebSocket连接
            connection_id = await self.connection_manager.connect_websocket(ws_url)
            self.connections.append(connection_id)
            
            print(f"✅ 连接建立成功: {connection_id}")
            
            # 启动心跳监控
            print("💓 启动心跳监控...")
            await self.connection_manager.start_heartbeat_monitoring()
            
            # 监控连接状态
            print("👀 监控连接状态 (60秒)...")
            
            for i in range(12):  # 每5秒检查一次，共60秒
                await asyncio.sleep(5)
                
                stats = self.connection_manager.get_connection_stats()
                if connection_id in stats["connections"]:
                    conn_info = stats["connections"][connection_id]
                    status = conn_info["status"]
                    last_heartbeat = conn_info["last_heartbeat"]
                    retry_count = conn_info["retry_count"]
                    
                    print(f"📊 心跳检查 #{i+1}: 状态={status}, 重试次数={retry_count}, "
                          f"最后心跳={time.time() - last_heartbeat:.1f}s前")
                else:
                    print(f"❌ 连接 {connection_id} 未找到")
                    break
            
            # 停止心跳监控
            print("⏹️ 停止心跳监控...")
            await self.connection_manager.stop_heartbeat_monitoring()
            
            print("✅ 心跳监控演示完成")
            
        except Exception as e:
            print(f"❌ 心跳监控演示失败: {e}")
            self.logger.error(f"心跳监控演示失败: {e}")
    
    async def demo_concurrent_operations(self, network: str = "sepolia"):
        """演示并发操作"""
        print(f"\n⚡ 并发操作演示 (网络: {network})")
        print("="*60)
        
        try:
            # 获取网络配置
            network_config = self.blockchain_config.get_network_config("ethereum", network)
            if not network_config:
                print(f"❌ 未找到网络配置: {network}")
                return
            
            rpc_url = network_config.get("rpc_url")
            if not rpc_url:
                print(f"❌ 网络 {network} 未配置RPC URL")
                return
            
            print(f"📡 创建多个连接池...")
            
            # 创建多个连接池
            pool_count = 3
            pool_size = 5
            pools = []
            
            for i in range(pool_count):
                pool_id = await self.connection_manager.connect_http_pool(rpc_url, pool_size)
                pools.append(pool_id)
                print(f"✅ 连接池 {i+1} 创建成功: {pool_id}")
            
            # 并发操作
            print(f"⚡ 开始并发操作 ({pool_count} 个连接池)...")
            
            # 每个连接池发送多个请求
            all_tasks = []
            for pool_id in pools:
                # 获取连接池中的连接
                stats = self.connection_manager.get_connection_stats()
                pool_connections = [conn_id for conn_id in stats["connections"].keys() 
                                  if conn_id.startswith(pool_id)]
                
                # 为每个连接创建任务
                for conn_id in pool_connections:
                    for i in range(3):  # 每个连接发送3个请求
                        task = asyncio.create_task(
                            self._send_rpc_request(conn_id, "eth_blockNumber", 
                                                f"{pool_id}-{conn_id}-#{i+1}")
                        )
                        all_tasks.append(task)
            
            print(f"📤 发送 {len(all_tasks)} 个并发请求...")
            
            # 等待所有任务完成
            start_time = time.time()
            results = await asyncio.gather(*all_tasks, return_exceptions=True)
            total_time = time.time() - start_time
            
            # 统计结果
            successful_requests = sum(1 for result in results if result is True)
            print(f"📊 并发操作统计:")
            print(f"   - 总请求数: {len(results)}")
            print(f"   - 成功请求: {successful_requests}")
            print(f"   - 成功率: {successful_requests/len(results)*100:.1f}%")
            print(f"   - 总耗时: {total_time:.2f}秒")
            print(f"   - 平均响应时间: {total_time/len(results)*1000:.1f}ms")
            
            print("✅ 并发操作演示完成")
            
        except Exception as e:
            print(f"❌ 并发操作演示失败: {e}")
            self.logger.error(f"并发操作演示失败: {e}")
    
    async def demo_performance_monitoring(self):
        """演示性能监控"""
        print(f"\n📊 性能监控演示")
        print("="*60)
        
        try:
            # 获取连接统计
            stats = self.connection_manager.get_connection_stats()
            
            print(f"📊 连接管理器统计:")
            print(f"   - 总连接数: {stats['connection_count']}")
            print(f"   - 活跃连接: {stats['active_connections']}")
            print(f"   - 失败连接: {stats['failed_connections']}")
            print(f"   - 连接池数: {stats['pool_count']}")
            print(f"   - 事件处理器数: {stats['event_handler_count']}")
            print(f"   - 总事件数: {stats['total_events']}")
            
            # 显示连接详情
            if stats['connections']:
                print(f"\n📋 连接详情:")
                for conn_id, conn_info in stats['connections'].items():
                    print(f"   🔗 {conn_id}:")
                    print(f"      - 状态: {conn_info['status']}")
                    print(f"      - 类型: {conn_info['type']}")
                    print(f"      - 创建时间: {time.ctime(conn_info['created_at'])}")
                    print(f"      - 最后心跳: {time.ctime(conn_info['last_heartbeat'])}")
                    print(f"      - 重试次数: {conn_info['retry_count']}")
                    print(f"      - 订阅数: {conn_info['subscription_count']}")
            
            # 计算运行时间
            total_time = time.time() - self.start_time
            print(f"\n⏱️ 运行时间: {total_time:.2f}秒")
            print(f"📈 事件接收率: {self.event_count/total_time:.2f} 事件/秒")
            
            print("✅ 性能监控演示完成")
            
        except Exception as e:
            print(f"❌ 性能监控演示失败: {e}")
            self.logger.error(f"性能监控演示失败: {e}")
    
    async def run_full_demo(self, network: str = "sepolia"):
        """运行完整演示"""
        print(f"\n🚀 区块链长连接完整功能演示")
        print(f"网络: {network}")
        print("="*80)
        
        try:
            # 1. WebSocket长连接演示
            await self.demo_websocket_connection(network)
            await asyncio.sleep(2)
            
            # 2. 事件订阅演示
            await self.demo_event_subscription(network)
            await asyncio.sleep(2)
            
            # 3. 连接池管理演示
            await self.demo_connection_pool(network)
            await asyncio.sleep(2)
            
            # 4. 心跳监控演示
            await self.demo_heartbeat_monitoring(network)
            await asyncio.sleep(2)
            
            # 5. 并发操作演示
            await self.demo_concurrent_operations(network)
            await asyncio.sleep(2)
            
            # 6. 性能监控演示
            await self.demo_performance_monitoring()
            
            print("\n🎉 完整功能演示完成！")
            
        except Exception as e:
            print(f"❌ 完整演示失败: {e}")
            self.logger.error(f"完整演示失败: {e}")
    
    async def cleanup(self):
        """清理资源"""
        try:
            print("\n🧹 清理资源...")
            await self.connection_manager.disconnect_all()
            print("✅ 资源清理完成")
        except Exception as e:
            print(f"❌ 资源清理失败: {e}")
            self.logger.error(f"资源清理失败: {e}")


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="区块链长连接使用示例")
    parser.add_argument("--mode", choices=["websocket", "events", "pool", "heartbeat", "concurrent", "full"], 
                       default="full", help="演示模式")
    parser.add_argument("--network", default="sepolia", 
                       help="测试网络 (sepolia, bsc_testnet, mumbai)")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="详细输出")
    
    args = parser.parse_args()
    
    # 配置日志
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建演示实例
    demo = BlockchainLongConnectionDemo()
    
    try:
        if args.mode == "websocket":
            await demo.demo_websocket_connection(args.network)
        elif args.mode == "events":
            await demo.demo_event_subscription(args.network)
        elif args.mode == "pool":
            await demo.demo_connection_pool(args.network)
        elif args.mode == "heartbeat":
            await demo.demo_heartbeat_monitoring(args.network)
        elif args.mode == "concurrent":
            await demo.demo_concurrent_operations(args.network)
        elif args.mode == "full":
            await demo.run_full_demo(args.network)
        
        # 性能监控
        await demo.demo_performance_monitoring()
        
    except KeyboardInterrupt:
        print("\n⏹️ 演示被用户中断")
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")
    finally:
        # 清理资源
        await demo.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
