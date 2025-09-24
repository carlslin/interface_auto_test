"""
=============================================================================
接口自动化测试框架 - 区块链测试示例
=============================================================================

本示例展示了如何使用区块链模块进行各种区块链测试。

主要功能演示：
1. 以太坊网络连接测试
2. 智能合约部署和测试
3. 钱包管理功能
4. 跨链测试
5. 性能测试

运行示例：
    python3 examples/blockchain_test_demo.py

作者: 接口自动化测试框架团队
版本: 1.0.0
更新日期: 2024年12月
=============================================================================
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入区块链模块
from src.blockchain import (
    EthereumClient, EthereumTester,
    BitcoinClient, BitcoinTester,
    BlockchainManager, SmartContractTester,
    WalletManager, BlockchainConfig
)


class BlockchainTestDemo:
    """区块链测试演示类"""
    
    def __init__(self):
        """初始化演示类"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.results = {}
    
    async def demo_ethereum_connection(self):
        """演示以太坊连接测试"""
        self.logger.info("=== 以太坊连接测试演示 ===")
        
        try:
            # 使用公共RPC节点（仅用于演示）
            rpc_url = "https://sepolia.infura.io/v3/YOUR_KEY"  # 需要替换为真实的API密钥
            
            # 创建以太坊客户端
            eth_client = EthereumClient(rpc_url)
            
            # 测试连接
            tester = EthereumTester(rpc_url)
            result = await tester.run_comprehensive_test()
            
            self.results["ethereum_connection"] = result
            self.logger.info(f"以太坊连接测试完成: {result.get('success_rate', 0):.1f}%")
            
        except Exception as e:
            self.logger.error(f"以太坊连接测试失败: {e}")
            self.results["ethereum_connection"] = {"error": str(e)}
    
    async def demo_smart_contract_test(self):
        """演示智能合约测试"""
        self.logger.info("=== 智能合约测试演示 ===")
        
        try:
            # 示例ERC20合约ABI（简化版）
            erc20_abi = [
                {
                    "inputs": [],
                    "name": "name",
                    "outputs": [{"internalType": "string", "name": "", "type": "string"}],
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "inputs": [],
                    "name": "symbol",
                    "outputs": [{"internalType": "string", "name": "", "type": "string"}],
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "inputs": [],
                    "name": "decimals",
                    "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "inputs": [],
                    "name": "totalSupply",
                    "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                    "stateMutability": "view",
                    "type": "function"
                }
            ]
            
            # 示例合约字节码（简化版）
            erc20_bytecode = "0x608060405234801561001057600080fd5b50..."
            
            # 创建以太坊客户端（需要私钥才能部署合约）
            rpc_url = "https://sepolia.infura.io/v3/YOUR_KEY"
            private_key = "YOUR_PRIVATE_KEY"  # 需要替换为真实的私钥
            
            eth_client = EthereumClient(rpc_url, private_key)
            contract_tester = SmartContractTester(eth_client)
            
            # 运行智能合约综合测试
            report = await contract_tester.run_comprehensive_test(
                abi=erc20_abi,
                bytecode=erc20_bytecode
            )
            
            self.results["smart_contract_test"] = contract_tester.generate_test_report()
            self.logger.info(f"智能合约测试完成: {report.passed_tests}/{report.total_tests} 测试通过")
            
        except Exception as e:
            self.logger.error(f"智能合约测试失败: {e}")
            self.results["smart_contract_test"] = {"error": str(e)}
    
    async def demo_wallet_management(self):
        """演示钱包管理功能"""
        self.logger.info("=== 钱包管理演示 ===")
        
        try:
            # 创建钱包管理器
            wallet_manager = WalletManager()
            
            # 创建以太坊钱包
            eth_wallet = await wallet_manager.create_wallet("ethereum", "测试以太坊钱包")
            self.logger.info(f"创建以太坊钱包: {eth_wallet.address}")
            
            # 创建比特币钱包
            btc_wallet = await wallet_manager.create_wallet("bitcoin", "测试比特币钱包")
            self.logger.info(f"创建比特币钱包: {btc_wallet.address}")
            
            # 验证地址
            eth_valid = await wallet_manager.validate_address(eth_wallet.address, "ethereum")
            btc_valid = await wallet_manager.validate_address(btc_wallet.address, "bitcoin")
            
            self.logger.info(f"以太坊地址验证: {eth_valid}")
            self.logger.info(f"比特币地址验证: {btc_valid}")
            
            # 获取钱包信息
            wallet_info = await wallet_manager.get_wallet_info()
            
            self.results["wallet_management"] = {
                "ethereum_wallet": {
                    "address": eth_wallet.address,
                    "valid": eth_valid
                },
                "bitcoin_wallet": {
                    "address": btc_wallet.address,
                    "valid": btc_valid
                },
                "wallet_info": wallet_info
            }
            
            self.logger.info("钱包管理演示完成")
            
        except Exception as e:
            self.logger.error(f"钱包管理演示失败: {e}")
            self.results["wallet_management"] = {"error": str(e)}
    
    async def demo_blockchain_manager(self):
        """演示区块链管理器"""
        self.logger.info("=== 区块链管理器演示 ===")
        
        try:
            # 创建区块链管理器
            manager = BlockchainManager()
            
            # 添加多个网络
            networks_to_add = [
                {
                    "name": "ethereum_sepolia",
                    "type": "ethereum",
                    "rpc_url": "https://sepolia.infura.io/v3/YOUR_KEY",
                    "is_testnet": True
                },
                {
                    "name": "bsc_testnet",
                    "type": "bsc",
                    "rpc_url": "https://data-seed-prebsc-1-s1.binance.org:8545",
                    "is_testnet": True
                }
            ]
            
            # 添加网络
            for network_config in networks_to_add:
                success = await manager.add_network(network_config["name"], network_config)
                if success:
                    self.logger.info(f"网络添加成功: {network_config['name']}")
                else:
                    self.logger.warning(f"网络添加失败: {network_config['name']}")
            
            # 启动健康监控
            await manager.start_health_monitoring()
            
            # 等待健康检查
            await asyncio.sleep(5)
            
            # 获取网络信息
            network_info = await manager.get_network_info()
            
            # 运行跨链测试
            cross_chain_result = await manager.run_cross_chain_test()
            
            # 停止健康监控
            await manager.stop_health_monitoring()
            
            self.results["blockchain_manager"] = {
                "network_info": network_info,
                "cross_chain_test": cross_chain_result
            }
            
            self.logger.info("区块链管理器演示完成")
            
        except Exception as e:
            self.logger.error(f"区块链管理器演示失败: {e}")
            self.results["blockchain_manager"] = {"error": str(e)}
    
    async def demo_config_management(self):
        """演示配置管理"""
        self.logger.info("=== 配置管理演示 ===")
        
        try:
            # 加载区块链配置
            config = BlockchainConfig.load_config()
            
            # 获取网络配置
            ethereum_config = config.get_network_config("ethereum", "sepolia")
            if ethereum_config:
                self.logger.info(f"以太坊配置: {ethereum_config.name}")
            
            # 列出所有网络
            networks = config.list_networks()
            self.logger.info(f"支持的区块链: {list(networks.keys())}")
            
            # 获取测试网配置
            testnet_configs = config.get_testnet_configs()
            self.logger.info(f"测试网数量: {len(testnet_configs)}")
            
            # 验证配置
            validation_result = config.validate_config()
            
            self.results["config_management"] = {
                "networks": networks,
                "testnet_count": len(testnet_configs),
                "validation": validation_result
            }
            
            self.logger.info("配置管理演示完成")
            
        except Exception as e:
            self.logger.error(f"配置管理演示失败: {e}")
            self.results["config_management"] = {"error": str(e)}
    
    async def demo_performance_test(self):
        """演示性能测试"""
        self.logger.info("=== 性能测试演示 ===")
        
        try:
            # 测试钱包创建性能
            wallet_manager = WalletManager()
            
            start_time = time.time()
            wallets = []
            
            # 创建多个钱包测试性能
            for i in range(10):
                wallet = await wallet_manager.create_wallet("ethereum", f"性能测试钱包{i}")
                wallets.append(wallet)
            
            creation_time = time.time() - start_time
            
            # 测试地址验证性能
            start_time = time.time()
            validations = []
            
            for wallet in wallets:
                is_valid = await wallet_manager.validate_address(wallet.address, "ethereum")
                validations.append(is_valid)
            
            validation_time = time.time() - start_time
            
            self.results["performance_test"] = {
                "wallet_creation": {
                    "count": len(wallets),
                    "total_time": creation_time,
                    "avg_time_per_wallet": creation_time / len(wallets)
                },
                "address_validation": {
                    "count": len(validations),
                    "total_time": validation_time,
                    "avg_time_per_validation": validation_time / len(validations)
                }
            }
            
            self.logger.info(f"性能测试完成: 创建{len(wallets)}个钱包耗时{creation_time:.3f}秒")
            
        except Exception as e:
            self.logger.error(f"性能测试失败: {e}")
            self.results["performance_test"] = {"error": str(e)}
    
    async def run_all_demos(self):
        """运行所有演示"""
        self.logger.info("开始区块链功能演示...")
        
        start_time = time.time()
        
        # 运行各个演示
        await self.demo_config_management()
        await self.demo_wallet_management()
        await self.demo_ethereum_connection()
        await self.demo_smart_contract_test()
        await self.demo_blockchain_manager()
        await self.demo_performance_test()
        
        total_time = time.time() - start_time
        
        # 生成总结报告
        self.generate_summary_report(total_time)
        
        self.logger.info("区块链功能演示完成!")
    
    def generate_summary_report(self, total_time: float):
        """生成总结报告"""
        self.logger.info("=== 演示总结报告 ===")
        
        total_demos = len(self.results)
        successful_demos = sum(1 for result in self.results.values() 
                             if not result.get("error"))
        
        self.logger.info(f"总演示数: {total_demos}")
        self.logger.info(f"成功演示数: {successful_demos}")
        self.logger.info(f"成功率: {successful_demos/total_demos*100:.1f}%")
        self.logger.info(f"总耗时: {total_time:.3f}秒")
        
        # 详细结果
        for demo_name, result in self.results.items():
            if result.get("error"):
                self.logger.error(f"{demo_name}: 失败 - {result['error']}")
            else:
                self.logger.info(f"{demo_name}: 成功")
        
        # 保存结果到文件
        try:
            with open("blockchain_demo_results.json", "w", encoding="utf-8") as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            self.logger.info("演示结果已保存到 blockchain_demo_results.json")
        except Exception as e:
            self.logger.error(f"保存结果失败: {e}")


async def main():
    """主函数"""
    demo = BlockchainTestDemo()
    await demo.run_all_demos()


if __name__ == "__main__":
    # 运行演示
    asyncio.run(main())
