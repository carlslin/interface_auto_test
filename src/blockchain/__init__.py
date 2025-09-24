"""
=============================================================================
接口自动化测试框架 - 区块链支持模块
=============================================================================

本模块提供了完整的区块链测试支持功能，支持主流区块链网络和智能合约测试。

主要功能：
1. 多链支持 - 以太坊、比特币、BSC、Polygon等
2. 智能合约测试 - 部署、调用、事件监听
3. 交易测试 - 发送、查询、验证
4. 网络监控 - 节点状态、区块同步
5. 钱包管理 - 账户创建、余额查询
6. 测试数据生成 - 模拟交易、合约调用

支持的区块链：
- Ethereum (以太坊主网/测试网)
- Bitcoin (比特币主网/测试网)
- BSC (币安智能链)
- Polygon (马蹄链)
- Arbitrum
- Optimism
- Avalanche
- Solana (计划中)

技术特性：
- Web3.py集成 - 以太坊生态支持
- Bitcoin Core集成 - 比特币网络支持
- 异步操作支持 - 高性能并发测试
- 智能合约ABI解析 - 自动生成测试用例
- 事件监听 - 实时合约事件监控
- Gas费优化 - 智能Gas费估算
- 多签名钱包支持 - 企业级安全
- 测试网水龙头集成 - 自动获取测试币

使用示例：
    # 以太坊测试
    from src.blockchain import EthereumTester
    eth_tester = EthereumTester()
    await eth_tester.deploy_contract(abi, bytecode)
    
    # 比特币测试
    from src.blockchain import BitcoinTester
    btc_tester = BitcoinTester()
    await btc_tester.send_transaction(to_address, amount)

作者: 接口自动化测试框架团队
版本: 1.0.0
更新日期: 2024年12月
=============================================================================
"""

from .ethereum_client import EthereumClient, EthereumTester
from .bitcoin_client import BitcoinClient, BitcoinTester
from .blockchain_manager import BlockchainManager
from .smart_contract_tester import SmartContractTester
from .wallet_manager import WalletManager
from .blockchain_config import BlockchainConfig
from .connection_manager import BlockchainConnectionManager, ConnectionType, ConnectionStatus, ConnectionConfig, ConnectionInfo

__all__ = [
    'EthereumClient',
    'EthereumTester', 
    'BitcoinClient',
    'BitcoinTester',
    'BlockchainManager',
    'SmartContractTester',
    'WalletManager',
    'BlockchainConfig',
    'BlockchainConnectionManager',
    'ConnectionType',
    'ConnectionStatus',
    'ConnectionConfig', 
    'ConnectionInfo'
]
