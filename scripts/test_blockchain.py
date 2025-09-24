#!/usr/bin/env python3
"""
=============================================================================
接口自动化测试框架 - 区块链测试脚本
=============================================================================

本脚本用于测试区块链模块的各项功能。

使用方法：
    python3 scripts/test_blockchain.py --network ethereum --env sepolia
    python3 scripts/test_blockchain.py --all
    python3 scripts/test_blockchain.py --wallet-test

作者: 接口自动化测试框架团队
版本: 1.0.0
更新日期: 2024年12月
=============================================================================
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.blockchain import (
    EthereumClient, EthereumTester,
    BitcoinClient, BitcoinTester,
    BlockchainManager, SmartContractTester,
    WalletManager, BlockchainConfig
)


class BlockchainTester:
    """区块链测试器"""
    
    def __init__(self, verbose: bool = False):
        """
        初始化区块链测试器
        
        Args:
            verbose: 是否显示详细日志
        """
        self.verbose = verbose
        self.setup_logging()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.results = {}
    
    def setup_logging(self):
        """设置日志"""
        level = logging.DEBUG if self.verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('blockchain_test.log')
            ]
        )
    
    async def test_config_loading(self) -> bool:
        """测试配置加载"""
        self.logger.info("测试配置加载...")
        
        try:
            config = BlockchainConfig.load_config()
            networks = config.list_networks()
            
            self.results["config_loading"] = {
                "success": True,
                "supported_blockchains": list(networks.keys()),
                "network_count": sum(len(envs) for envs in networks.values())
            }
            
            self.logger.info(f"配置加载成功，支持 {len(networks)} 种区块链")
            return True
            
        except Exception as e:
            self.results["config_loading"] = {
                "success": False,
                "error": str(e)
            }
            self.logger.error(f"配置加载失败: {e}")
            return False
    
    async def test_wallet_management(self) -> bool:
        """测试钱包管理"""
        self.logger.info("测试钱包管理...")
        
        try:
            wallet_manager = WalletManager()
            
            # 创建钱包
            eth_wallet = await wallet_manager.create_wallet("ethereum", "测试钱包")
            btc_wallet = await wallet_manager.create_wallet("bitcoin", "测试钱包")
            
            # 验证地址
            eth_valid = await wallet_manager.validate_address(eth_wallet.address, "ethereum")
            btc_valid = await wallet_manager.validate_address(btc_wallet.address, "bitcoin")
            
            # 获取钱包信息
            wallet_info = await wallet_manager.get_wallet_info()
            
            self.results["wallet_management"] = {
                "success": True,
                "ethereum_wallet": eth_wallet.address,
                "bitcoin_wallet": btc_wallet.address,
                "ethereum_valid": eth_valid,
                "bitcoin_valid": btc_valid,
                "total_wallets": wallet_info["total_wallets"]
            }
            
            self.logger.info("钱包管理测试成功")
            return True
            
        except Exception as e:
            self.results["wallet_management"] = {
                "success": False,
                "error": str(e)
            }
            self.logger.error(f"钱包管理测试失败: {e}")
            return False
    
    async def test_ethereum_connection(self, rpc_url: str) -> bool:
        """测试以太坊连接"""
        self.logger.info(f"测试以太坊连接: {rpc_url}")
        
        try:
            tester = EthereumTester(rpc_url)
            
            # 测试连接
            connection_test = await tester.test_connection()
            
            if connection_test:
                # 运行综合测试
                result = await tester.run_comprehensive_test()
                
                self.results["ethereum_connection"] = {
                    "success": True,
                    "connection": True,
                    "success_rate": result.get("success_rate", 0),
                    "network": result.get("network", "Unknown")
                }
                
                self.logger.info(f"以太坊连接测试成功，成功率: {result.get('success_rate', 0):.1f}%")
                return True
            else:
                self.results["ethereum_connection"] = {
                    "success": False,
                    "connection": False,
                    "error": "连接失败"
                }
                self.logger.error("以太坊连接失败")
                return False
                
        except Exception as e:
            self.results["ethereum_connection"] = {
                "success": False,
                "error": str(e)
            }
            self.logger.error(f"以太坊连接测试失败: {e}")
            return False
    
    async def test_bitcoin_connection(self, rpc_url: str, username: str = None, password: str = None) -> bool:
        """测试比特币连接"""
        self.logger.info(f"测试比特币连接: {rpc_url}")
        
        try:
            tester = BitcoinTester(rpc_url, username, password)
            
            # 测试连接
            connection_test = await tester.test_connection()
            
            if connection_test:
                # 运行综合测试
                result = await tester.run_comprehensive_test()
                
                self.results["bitcoin_connection"] = {
                    "success": True,
                    "connection": True,
                    "success_rate": result.get("success_rate", 0)
                }
                
                self.logger.info(f"比特币连接测试成功，成功率: {result.get('success_rate', 0):.1f}%")
                return True
            else:
                self.results["bitcoin_connection"] = {
                    "success": False,
                    "connection": False,
                    "error": "连接失败"
                }
                self.logger.error("比特币连接失败")
                return False
                
        except Exception as e:
            self.results["bitcoin_connection"] = {
                "success": False,
                "error": str(e)
            }
            self.logger.error(f"比特币连接测试失败: {e}")
            return False
    
    async def test_blockchain_manager(self) -> bool:
        """测试区块链管理器"""
        self.logger.info("测试区块链管理器...")
        
        try:
            manager = BlockchainManager()
            
            # 添加测试网络
            test_networks = [
                {
                    "name": "ethereum_sepolia",
                    "type": "ethereum",
                    "rpc_url": "https://sepolia.infura.io/v3/YOUR_KEY",
                    "is_testnet": True
                }
            ]
            
            # 添加网络
            added_count = 0
            for network_config in test_networks:
                success = await manager.add_network(network_config["name"], network_config)
                if success:
                    added_count += 1
            
            # 获取网络信息
            network_info = await manager.get_network_info()
            
            self.results["blockchain_manager"] = {
                "success": True,
                "networks_added": added_count,
                "total_networks": network_info["total_networks"],
                "enabled_networks": network_info["enabled_networks"]
            }
            
            self.logger.info(f"区块链管理器测试成功，添加了 {added_count} 个网络")
            return True
            
        except Exception as e:
            self.results["blockchain_manager"] = {
                "success": False,
                "error": str(e)
            }
            self.logger.error(f"区块链管理器测试失败: {e}")
            return False
    
    async def test_smart_contract(self, rpc_url: str, private_key: str = None) -> bool:
        """测试智能合约功能"""
        self.logger.info("测试智能合约功能...")
        
        try:
            if not private_key:
                self.logger.warning("未提供私钥，跳过智能合约测试")
                self.results["smart_contract"] = {
                    "success": False,
                    "error": "未提供私钥"
                }
                return False
            
            # 创建以太坊客户端
            eth_client = EthereumClient(rpc_url, private_key)
            contract_tester = SmartContractTester(eth_client)
            
            # 示例ERC20合约ABI
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
                }
            ]
            
            # 示例字节码（简化）
            bytecode = "0x608060405234801561001057600080fd5b50..."
            
            # 运行合约测试
            report = await contract_tester.run_comprehensive_test(erc20_abi, bytecode)
            
            self.results["smart_contract"] = {
                "success": True,
                "deployment_success": report.deployment_result.success if report.deployment_result else False,
                "total_tests": report.total_tests,
                "passed_tests": report.passed_tests,
                "success_rate": (report.passed_tests / report.total_tests * 100) if report.total_tests > 0 else 0
            }
            
            self.logger.info(f"智能合约测试成功: {report.passed_tests}/{report.total_tests} 测试通过")
            return True
            
        except Exception as e:
            self.results["smart_contract"] = {
                "success": False,
                "error": str(e)
            }
            self.logger.error(f"智能合约测试失败: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        self.logger.info("开始运行所有区块链测试...")
        
        start_time = time.time()
        
        # 运行基础测试
        config_test = await self.test_config_loading()
        wallet_test = await self.test_wallet_management()
        manager_test = await self.test_blockchain_manager()
        
        # 运行网络连接测试（使用公共节点）
        ethereum_test = await self.test_ethereum_connection("https://sepolia.infura.io/v3/YOUR_KEY")
        
        total_time = time.time() - start_time
        
        # 计算总体结果
        total_tests = len(self.results)
        successful_tests = sum(1 for result in self.results.values() if result.get("success"))
        
        summary = {
            "timestamp": time.time(),
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": total_tests - successful_tests,
            "success_rate": (successful_tests / total_tests * 100) if total_tests > 0 else 0,
            "total_time": total_time,
            "results": self.results
        }
        
        self.logger.info(f"所有测试完成: {successful_tests}/{total_tests} 成功 ({summary['success_rate']:.1f}%)")
        
        return summary
    
    async def run_network_test(self, network: str, env: str, rpc_url: str = None, 
                             private_key: str = None, username: str = None, password: str = None) -> Dict[str, Any]:
        """运行特定网络测试"""
        self.logger.info(f"运行 {network}.{env} 网络测试...")
        
        start_time = time.time()
        
        # 获取网络配置
        config = BlockchainConfig.load_config()
        network_config = config.get_network_config(network, env)
        
        if network_config and rpc_url is None:
            rpc_url = network_config.rpc_url
        
        if not rpc_url:
            self.logger.error(f"未找到 {network}.{env} 的RPC URL")
            return {"error": f"未找到 {network}.{env} 的RPC URL"}
        
        # 根据网络类型运行测试
        if network in ["ethereum", "bsc", "polygon", "arbitrum", "optimism"]:
            await self.test_ethereum_connection(rpc_url)
            if private_key:
                await self.test_smart_contract(rpc_url, private_key)
        elif network == "bitcoin":
            await self.test_bitcoin_connection(rpc_url, username, password)
        
        total_time = time.time() - start_time
        
        # 生成结果
        result = {
            "network": f"{network}.{env}",
            "rpc_url": rpc_url,
            "test_time": total_time,
            "results": {k: v for k, v in self.results.items() if k in ["ethereum_connection", "bitcoin_connection", "smart_contract"]}
        }
        
        return result
    
    def save_results(self, results: Dict[str, Any], filename: str = "blockchain_test_results.json"):
        """保存测试结果"""
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            self.logger.info(f"测试结果已保存到: {filename}")
        except Exception as e:
            self.logger.error(f"保存测试结果失败: {e}")


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="区块链测试脚本")
    parser.add_argument("--all", action="store_true", help="运行所有测试")
    parser.add_argument("--wallet-test", action="store_true", help="只运行钱包测试")
    parser.add_argument("--network", type=str, help="指定网络类型")
    parser.add_argument("--env", type=str, help="指定环境")
    parser.add_argument("--rpc-url", type=str, help="RPC URL")
    parser.add_argument("--private-key", type=str, help="私钥")
    parser.add_argument("--username", type=str, help="RPC用户名")
    parser.add_argument("--password", type=str, help="RPC密码")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    # 创建测试器
    tester = BlockchainTester(verbose=args.verbose)
    
    try:
        if args.all:
            # 运行所有测试
            results = await tester.run_all_tests()
            tester.save_results(results)
            
        elif args.wallet_test:
            # 只运行钱包测试
            await tester.test_wallet_management()
            tester.save_results(tester.results, "wallet_test_results.json")
            
        elif args.network and args.env:
            # 运行特定网络测试
            results = await tester.run_network_test(
                args.network, args.env, args.rpc_url, 
                args.private_key, args.username, args.password
            )
            tester.save_results(results, f"{args.network}_{args.env}_test_results.json")
            
        else:
            print("请指定测试类型: --all, --wallet-test, 或 --network + --env")
            return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        return 1
    except Exception as e:
        print(f"测试失败: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
