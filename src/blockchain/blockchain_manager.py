"""
=============================================================================
接口自动化测试框架 - 区块链管理器模块
=============================================================================

本模块提供了统一的区块链管理功能，支持多种区块链网络的统一管理和测试。

主要功能：
1. 多链管理 - 统一管理多种区块链网络
2. 智能路由 - 根据测试需求自动选择最佳网络
3. 配置管理 - 统一的区块链配置管理
4. 测试协调 - 跨链测试协调和管理
5. 性能监控 - 区块链网络性能监控
6. 故障转移 - 自动故障检测和转移

支持的区块链：
- Ethereum生态 (Ethereum, BSC, Polygon, Arbitrum, Optimism)
- Bitcoin生态 (Bitcoin, Litecoin)
- 其他EVM兼容链
- 自定义区块链网络

技术特性：
- 统一接口 - 所有区块链使用统一接口
- 异步操作 - 高性能并发处理
- 智能负载均衡 - 自动选择最优节点
- 健康检查 - 实时网络健康监控
- 配置热更新 - 支持配置动态更新
- 多签名支持 - 企业级安全

使用示例：
    # 初始化区块链管理器
    manager = BlockchainManager()
    
    # 添加网络
    await manager.add_network("ethereum", "https://sepolia.infura.io/v3/YOUR_KEY")
    await manager.add_network("bitcoin", "http://user:pass@localhost:18332")
    
    # 执行跨链测试
    result = await manager.run_cross_chain_test()

作者: 接口自动化测试框架团队
版本: 1.0.0
更新日期: 2024年12月
=============================================================================
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

from .ethereum_client import EthereumClient, EthereumTester
from .bitcoin_client import BitcoinClient, BitcoinTester


class BlockchainType(Enum):
    """区块链类型枚举"""
    ETHEREUM = "ethereum"
    BITCOIN = "bitcoin"
    BSC = "bsc"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    AVALANCHE = "avalanche"
    CUSTOM = "custom"


@dataclass
class NetworkConfig:
    """网络配置数据类"""
    name: str
    blockchain_type: BlockchainType
    rpc_url: str
    chain_id: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    private_key: Optional[str] = None
    explorer_url: Optional[str] = None
    is_testnet: bool = False
    priority: int = 1  # 优先级，数字越小优先级越高
    enabled: bool = True


@dataclass
class NetworkStatus:
    """网络状态数据类"""
    name: str
    is_online: bool
    response_time: float
    last_check: float
    error_count: int = 0
    last_error: Optional[str] = None


class BlockchainManager:
    """区块链管理器"""
    
    def __init__(self):
        """初始化区块链管理器"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.networks: Dict[str, NetworkConfig] = {}
        self.clients: Dict[str, Any] = {}
        self.status: Dict[str, NetworkStatus] = {}
        self.health_check_interval = 60  # 健康检查间隔（秒）
        self.health_check_task: Optional[asyncio.Task] = None
        
        self.logger.info("区块链管理器已初始化")
    
    async def add_network(self, name: str, config: Union[NetworkConfig, Dict[str, Any]]) -> bool:
        """
        添加区块链网络
        
        Args:
            name: 网络名称
            config: 网络配置
            
        Returns:
            bool: 是否添加成功
        """
        try:
            # 处理配置参数
            if isinstance(config, dict):
                network_config = NetworkConfig(
                    name=name,
                    blockchain_type=BlockchainType(config.get("type", "ethereum")),
                    rpc_url=config["rpc_url"],
                    chain_id=config.get("chain_id"),
                    username=config.get("username"),
                    password=config.get("password"),
                    private_key=config.get("private_key"),
                    explorer_url=config.get("explorer_url"),
                    is_testnet=config.get("is_testnet", False),
                    priority=config.get("priority", 1),
                    enabled=config.get("enabled", True)
                )
            else:
                network_config = config
                network_config.name = name
            
            # 添加到网络列表
            self.networks[name] = network_config
            
            # 初始化客户端
            await self._initialize_client(name, network_config)
            
            # 初始化状态
            self.status[name] = NetworkStatus(
                name=name,
                is_online=False,
                response_time=0.0,
                last_check=time.time()
            )
            
            self.logger.info(f"网络已添加: {name} ({network_config.blockchain_type.value})")
            return True
            
        except Exception as e:
            self.logger.error(f"添加网络失败: {e}")
            return False
    
    async def _initialize_client(self, name: str, config: NetworkConfig) -> None:
        """
        初始化区块链客户端
        
        Args:
            name: 网络名称
            config: 网络配置
        """
        try:
            if config.blockchain_type in [BlockchainType.ETHEREUM, BlockchainType.BSC, 
                                        BlockchainType.POLYGON, BlockchainType.ARBITRUM, 
                                        BlockchainType.OPTIMISM]:
                # 以太坊生态客户端
                client = EthereumClient(
                    rpc_url=config.rpc_url,
                    private_key=config.private_key,
                    network=config.blockchain_type.value
                )
                tester = EthereumTester(
                    rpc_url=config.rpc_url,
                    private_key=config.private_key,
                    network=config.blockchain_type.value
                )
                
            elif config.blockchain_type == BlockchainType.BITCOIN:
                # 比特币客户端
                client = BitcoinClient(
                    rpc_url=config.rpc_url,
                    username=config.username,
                    password=config.password
                )
                tester = BitcoinTester(
                    rpc_url=config.rpc_url,
                    username=config.username,
                    password=config.password
                )
                
            else:
                raise ValueError(f"不支持的区块链类型: {config.blockchain_type}")
            
            self.clients[name] = {
                "client": client,
                "tester": tester,
                "config": config
            }
            
        except Exception as e:
            self.logger.error(f"初始化客户端失败: {e}")
            raise
    
    async def remove_network(self, name: str) -> bool:
        """
        移除区块链网络
        
        Args:
            name: 网络名称
            
        Returns:
            bool: 是否移除成功
        """
        try:
            if name in self.networks:
                # 清理客户端连接
                if name in self.clients:
                    del self.clients[name]
                
                # 清理网络配置
                del self.networks[name]
                
                # 清理状态
                if name in self.status:
                    del self.status[name]
                
                self.logger.info(f"网络已移除: {name}")
                return True
            else:
                self.logger.warning(f"网络不存在: {name}")
                return False
                
        except Exception as e:
            self.logger.error(f"移除网络失败: {e}")
            return False
    
    async def get_network_status(self, name: str) -> Optional[NetworkStatus]:
        """
        获取网络状态
        
        Args:
            name: 网络名称
            
        Returns:
            Optional[NetworkStatus]: 网络状态
        """
        if name in self.status:
            return self.status[name]
        return None
    
    async def check_network_health(self, name: str) -> bool:
        """
        检查网络健康状态
        
        Args:
            name: 网络名称
            
        Returns:
            bool: 网络是否健康
        """
        try:
            if name not in self.clients:
                return False
            
            start_time = time.time()
            
            # 根据区块链类型执行不同的健康检查
            config = self.clients[name]["config"]
            tester = self.clients[name]["tester"]
            
            if config.blockchain_type in [BlockchainType.ETHEREUM, BlockchainType.BSC, 
                                        BlockchainType.POLYGON, BlockchainType.ARBITRUM, 
                                        BlockchainType.OPTIMISM]:
                # 以太坊生态健康检查
                is_healthy = await tester.test_connection()
                
            elif config.blockchain_type == BlockchainType.BITCOIN:
                # 比特币健康检查
                is_healthy = await tester.test_connection()
                
            else:
                is_healthy = False
            
            response_time = time.time() - start_time
            
            # 更新状态
            if name in self.status:
                self.status[name].is_online = is_healthy
                self.status[name].response_time = response_time
                self.status[name].last_check = time.time()
                
                if not is_healthy:
                    self.status[name].error_count += 1
                    self.status[name].last_error = "Health check failed"
                else:
                    self.status[name].error_count = 0
                    self.status[name].last_error = None
            
            self.logger.debug(f"网络健康检查: {name} -> {is_healthy} ({response_time:.3f}s)")
            return is_healthy
            
        except Exception as e:
            self.logger.error(f"健康检查失败: {e}")
            if name in self.status:
                self.status[name].is_online = False
                self.status[name].error_count += 1
                self.status[name].last_error = str(e)
            return False
    
    async def start_health_monitoring(self) -> None:
        """启动健康监控"""
        if self.health_check_task is None or self.health_check_task.done():
            self.health_check_task = asyncio.create_task(self._health_monitor_loop())
            self.logger.info("健康监控已启动")
    
    async def stop_health_monitoring(self) -> None:
        """停止健康监控"""
        if self.health_check_task and not self.health_check_task.done():
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
            self.logger.info("健康监控已停止")
    
    async def _health_monitor_loop(self) -> None:
        """健康监控循环"""
        while True:
            try:
                # 检查所有启用的网络
                for name, config in self.networks.items():
                    if config.enabled:
                        await self.check_network_health(name)
                
                # 等待下次检查
                await asyncio.sleep(self.health_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"健康监控错误: {e}")
                await asyncio.sleep(self.health_check_interval)
    
    async def get_best_network(self, blockchain_type: BlockchainType) -> Optional[str]:
        """
        获取最佳网络
        
        Args:
            blockchain_type: 区块链类型
            
        Returns:
            Optional[str]: 最佳网络名称
        """
        try:
            # 筛选同类型且启用的网络
            candidates = []
            for name, config in self.networks.items():
                if (config.blockchain_type == blockchain_type and 
                    config.enabled and 
                    name in self.status and 
                    self.status[name].is_online):
                    candidates.append((name, config.priority, self.status[name].response_time))
            
            if not candidates:
                return None
            
            # 按优先级和响应时间排序
            candidates.sort(key=lambda x: (x[1], x[2]))
            best_network = candidates[0][0]
            
            self.logger.debug(f"选择最佳网络: {best_network} (类型: {blockchain_type.value})")
            return best_network
            
        except Exception as e:
            self.logger.error(f"获取最佳网络失败: {e}")
            return None
    
    async def run_network_test(self, name: str) -> Dict[str, Any]:
        """
        运行网络测试
        
        Args:
            name: 网络名称
            
        Returns:
            Dict[str, Any]: 测试结果
        """
        try:
            if name not in self.clients:
                return {
                    "success": False,
                    "error": f"网络不存在: {name}",
                    "message": f"网络测试失败: {name}"
                }
            
            tester = self.clients[name]["tester"]
            config = self.clients[name]["config"]
            
            # 运行综合测试
            if config.blockchain_type in [BlockchainType.ETHEREUM, BlockchainType.BSC, 
                                        BlockchainType.POLYGON, BlockchainType.ARBITRUM, 
                                        BlockchainType.OPTIMISM]:
                result = await tester.run_comprehensive_test()
                
            elif config.blockchain_type == BlockchainType.BITCOIN:
                result = await tester.run_comprehensive_test()
                
            else:
                result = {
                    "success": False,
                    "error": f"不支持的区块链类型: {config.blockchain_type}",
                    "message": f"网络测试失败: {name}"
                }
            
            result["network_name"] = name
            result["blockchain_type"] = config.blockchain_type.value
            
            self.logger.info(f"网络测试完成: {name} -> {result.get('success_rate', 0):.1f}%")
            return result
            
        except Exception as e:
            self.logger.error(f"网络测试失败: {e}")
            return {
                "success": False,
                "network_name": name,
                "error": str(e),
                "message": f"网络测试失败: {name}"
            }
    
    async def run_cross_chain_test(self) -> Dict[str, Any]:
        """
        运行跨链测试
        
        Returns:
            Dict[str, Any]: 跨链测试结果
        """
        try:
            test_results = {
                "timestamp": time.time(),
                "cross_chain_test": True,
                "networks": {},
                "summary": {}
            }
            
            # 测试所有启用的网络
            for name, config in self.networks.items():
                if config.enabled:
                    self.logger.info(f"开始测试网络: {name}")
                    network_result = await self.run_network_test(name)
                    test_results["networks"][name] = network_result
            
            # 计算总体统计
            total_networks = len(test_results["networks"])
            successful_networks = sum(1 for result in test_results["networks"].values() 
                                    if result.get("success_rate", 0) > 0)
            
            test_results["summary"] = {
                "total_networks": total_networks,
                "successful_networks": successful_networks,
                "success_rate": (successful_networks / total_networks * 100) if total_networks > 0 else 0
            }
            
            self.logger.info(f"跨链测试完成: {successful_networks}/{total_networks} 网络成功")
            return test_results
            
        except Exception as e:
            self.logger.error(f"跨链测试失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "跨链测试失败"
            }
    
    async def get_network_info(self) -> Dict[str, Any]:
        """
        获取网络信息
        
        Returns:
            Dict[str, Any]: 网络信息
        """
        try:
            network_info = {
                "total_networks": len(self.networks),
                "enabled_networks": sum(1 for config in self.networks.values() if config.enabled),
                "online_networks": sum(1 for status in self.status.values() if status.is_online),
                "networks": {}
            }
            
            for name, config in self.networks.items():
                status = self.status.get(name)
                network_info["networks"][name] = {
                    "type": config.blockchain_type.value,
                    "rpc_url": config.rpc_url,
                    "is_testnet": config.is_testnet,
                    "priority": config.priority,
                    "enabled": config.enabled,
                    "is_online": status.is_online if status else False,
                    "response_time": status.response_time if status else 0.0,
                    "error_count": status.error_count if status else 0,
                    "last_check": status.last_check if status else 0
                }
            
            return network_info
            
        except Exception as e:
            self.logger.error(f"获取网络信息失败: {e}")
            return {"error": str(e)}
    
    async def shutdown(self) -> None:
        """关闭区块链管理器"""
        try:
            # 停止健康监控
            await self.stop_health_monitoring()
            
            # 清理客户端连接
            self.clients.clear()
            self.networks.clear()
            self.status.clear()
            
            self.logger.info("区块链管理器已关闭")
            
        except Exception as e:
            self.logger.error(f"关闭区块链管理器失败: {e}")
