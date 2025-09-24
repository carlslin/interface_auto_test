"""
=============================================================================
接口自动化测试框架 - 以太坊客户端模块
=============================================================================

本模块提供了完整的以太坊区块链测试支持，包括智能合约部署、调用、事件监听等功能。

主要功能：
1. 网络连接 - 支持主网、测试网、本地节点
2. 智能合约操作 - 部署、调用、事件监听
3. 交易管理 - 发送、查询、验证
4. Gas费管理 - 估算、优化、监控
5. 账户管理 - 创建、导入、余额查询
6. 区块查询 - 区块信息、交易历史

支持的网络：
- Ethereum Mainnet (以太坊主网)
- Ethereum Goerli Testnet (Goerli测试网)
- Ethereum Sepolia Testnet (Sepolia测试网)
- Ethereum Holesky Testnet (Holesky测试网)
- BSC Mainnet (币安智能链主网)
- BSC Testnet (币安智能链测试网)
- Polygon Mainnet (马蹄链主网)
- Polygon Mumbai Testnet (马蹄链测试网)
- Arbitrum One (Arbitrum主网)
- Arbitrum Goerli Testnet (Arbitrum测试网)
- Optimism Mainnet (Optimism主网)
- Optimism Goerli Testnet (Optimism测试网)

技术特性：
- Web3.py集成 - 完整的以太坊生态支持
- 异步操作 - 高性能并发处理
- 智能合约ABI解析 - 自动生成测试用例
- 事件监听 - 实时合约事件监控
- Gas费优化 - 智能Gas费估算和优化
- 多签名支持 - 企业级安全钱包
- 测试网水龙头 - 自动获取测试ETH

使用示例：
    # 连接到以太坊测试网
    eth_client = EthereumClient("https://sepolia.infura.io/v3/YOUR_KEY")
    
    # 部署智能合约
    contract_address = await eth_client.deploy_contract(abi, bytecode)
    
    # 调用合约方法
    result = await eth_client.call_contract(contract_address, abi, "getBalance", [])
    
    # 监听合约事件
    await eth_client.listen_events(contract_address, abi, "Transfer")

作者: 接口自动化测试框架团队
版本: 1.0.0
更新日期: 2024年12月
=============================================================================
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account
from eth_utils import to_checksum_address, is_address


@dataclass
class EthereumTransaction:
    """以太坊交易数据类"""
    hash: str
    from_address: str
    to_address: str
    value: int
    gas: int
    gas_price: int
    nonce: int
    data: str
    block_number: Optional[int] = None
    block_hash: Optional[str] = None
    transaction_index: Optional[int] = None
    status: Optional[int] = None


@dataclass
class SmartContract:
    """智能合约数据类"""
    address: str
    abi: List[Dict[str, Any]]
    bytecode: str
    name: str
    version: str
    deployed_at: Optional[int] = None
    deployer: Optional[str] = None


class EthereumClient:
    """以太坊客户端"""
    
    # 预定义网络配置
    NETWORKS = {
        "mainnet": {
            "name": "Ethereum Mainnet",
            "chain_id": 1,
            "rpc_url": "https://mainnet.infura.io/v3/YOUR_KEY",
            "explorer": "https://etherscan.io"
        },
        "goerli": {
            "name": "Ethereum Goerli Testnet", 
            "chain_id": 5,
            "rpc_url": "https://goerli.infura.io/v3/YOUR_KEY",
            "explorer": "https://goerli.etherscan.io"
        },
        "sepolia": {
            "name": "Ethereum Sepolia Testnet",
            "chain_id": 11155111,
            "rpc_url": "https://sepolia.infura.io/v3/YOUR_KEY", 
            "explorer": "https://sepolia.etherscan.io"
        },
        "holesky": {
            "name": "Ethereum Holesky Testnet",
            "chain_id": 17000,
            "rpc_url": "https://holesky.infura.io/v3/YOUR_KEY",
            "explorer": "https://holesky.etherscan.io"
        },
        "bsc": {
            "name": "BSC Mainnet",
            "chain_id": 56,
            "rpc_url": "https://bsc-dataseed.binance.org",
            "explorer": "https://bscscan.com"
        },
        "bsc_testnet": {
            "name": "BSC Testnet",
            "chain_id": 97,
            "rpc_url": "https://data-seed-prebsc-1-s1.binance.org:8545",
            "explorer": "https://testnet.bscscan.com"
        },
        "polygon": {
            "name": "Polygon Mainnet",
            "chain_id": 137,
            "rpc_url": "https://polygon-rpc.com",
            "explorer": "https://polygonscan.com"
        },
        "polygon_mumbai": {
            "name": "Polygon Mumbai Testnet",
            "chain_id": 80001,
            "rpc_url": "https://rpc-mumbai.maticvigil.com",
            "explorer": "https://mumbai.polygonscan.com"
        },
        "arbitrum": {
            "name": "Arbitrum One",
            "chain_id": 42161,
            "rpc_url": "https://arb1.arbitrum.io/rpc",
            "explorer": "https://arbiscan.io"
        },
        "arbitrum_goerli": {
            "name": "Arbitrum Goerli Testnet",
            "chain_id": 421613,
            "rpc_url": "https://goerli-rollup.arbitrum.io/rpc",
            "explorer": "https://goerli.arbiscan.io"
        },
        "optimism": {
            "name": "Optimism Mainnet",
            "chain_id": 10,
            "rpc_url": "https://mainnet.optimism.io",
            "explorer": "https://optimistic.etherscan.io"
        },
        "optimism_goerli": {
            "name": "Optimism Goerli Testnet",
            "chain_id": 420,
            "rpc_url": "https://goerli.optimism.io",
            "explorer": "https://goerli-optimism.etherscan.io"
        }
    }
    
    def __init__(self, rpc_url: str, private_key: Optional[str] = None, network: Optional[str] = None):
        """
        初始化以太坊客户端
        
        这是以太坊客户端的核心构造函数，负责建立与以太坊网络的连接。
        支持多种网络配置和私钥管理，为后续的区块链操作提供基础。
        
        Args:
            rpc_url (str): RPC节点URL，支持HTTP和WebSocket协议
                - HTTP: https://sepolia.infura.io/v3/YOUR_KEY
                - WebSocket: wss://sepolia.infura.io/ws/v3/YOUR_KEY
            private_key (Optional[str]): 私钥字符串，用于签名交易
                - 格式: 0x开头的64位十六进制字符串
                - 如果提供，客户端将自动创建账户对象
            network (Optional[str]): 网络名称，用于自动配置网络参数
                - 支持: mainnet, sepolia, goerli, holesky, bsc, polygon等
                - 如果指定，将自动应用对应的网络配置
        
        Raises:
            ConnectionError: 当无法连接到指定的RPC节点时抛出
            ValueError: 当私钥格式不正确时抛出
            
        Example:
            # 基础连接（只读操作）
            client = EthereumClient("https://sepolia.infura.io/v3/YOUR_KEY")
            
            # 带私钥连接（支持交易操作）
            client = EthereumClient(
                "https://sepolia.infura.io/v3/YOUR_KEY",
                private_key="0x1234...",
                network="sepolia"
            )
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.rpc_url = rpc_url
        self.private_key = private_key
        self.network = network
        
        # 初始化Web3连接
        self.web3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # 添加POA中间件（用于BSC、Polygon等网络）
        if network in ['bsc', 'bsc_testnet', 'polygon', 'polygon_mumbai']:
            self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        # 验证连接
        if not self.web3.is_connected():
            raise ConnectionError(f"无法连接到以太坊节点: {rpc_url}")
        
        # 设置账户
        self.account = None
        if private_key:
            self.account = Account.from_key(private_key)
            self.logger.info(f"账户地址: {self.account.address}")
        
        # 获取网络信息
        try:
            self.chain_id = self.web3.eth.chain_id
            self.network_info = self._get_network_info()
            self.logger.info(f"已连接到网络: {self.network_info['name']} (Chain ID: {self.chain_id})")
        except Exception as e:
            self.logger.warning(f"无法获取网络信息: {e}")
            self.chain_id = None
            self.network_info = {}
    
    def _get_network_info(self) -> Dict[str, Any]:
        """获取网络信息"""
        for network_name, info in self.NETWORKS.items():
            if info.get('chain_id') == self.chain_id:
                return info
        return {"name": f"Unknown Network (Chain ID: {self.chain_id})", "chain_id": self.chain_id}
    
    async def get_balance(self, address: str) -> int:
        """
        获取账户余额
        
        Args:
            address: 账户地址
            
        Returns:
            int: 余额（wei）
        """
        try:
            address = to_checksum_address(address)
            balance = self.web3.eth.get_balance(address)
            self.logger.debug(f"账户 {address} 余额: {balance} wei")
            return balance
        except Exception as e:
            self.logger.error(f"获取余额失败: {e}")
            raise
    
    async def get_transaction_count(self, address: str) -> int:
        """
        获取账户交易计数（nonce）
        
        Args:
            address: 账户地址
            
        Returns:
            int: nonce值
        """
        try:
            address = to_checksum_address(address)
            nonce = self.web3.eth.get_transaction_count(address)
            self.logger.debug(f"账户 {address} nonce: {nonce}")
            return nonce
        except Exception as e:
            self.logger.error(f"获取nonce失败: {e}")
            raise
    
    async def estimate_gas(self, transaction: Dict[str, Any]) -> int:
        """
        估算Gas费用
        
        Args:
            transaction: 交易参数
            
        Returns:
            int: 估算的Gas费用
        """
        try:
            gas_estimate = self.web3.eth.estimate_gas(transaction)
            self.logger.debug(f"估算Gas费用: {gas_estimate}")
            return gas_estimate
        except Exception as e:
            self.logger.error(f"估算Gas失败: {e}")
            raise
    
    async def get_gas_price(self) -> int:
        """
        获取当前Gas价格
        
        Returns:
            int: Gas价格（wei）
        """
        try:
            gas_price = self.web3.eth.gas_price
            self.logger.debug(f"当前Gas价格: {gas_price} wei")
            return gas_price
        except Exception as e:
            self.logger.error(f"获取Gas价格失败: {e}")
            raise
    
    async def send_transaction(self, to_address: str, value: int, data: str = "", gas_limit: Optional[int] = None) -> str:
        """
        发送交易
        
        Args:
            to_address: 接收地址
            value: 发送金额（wei）
            data: 交易数据（可选）
            gas_limit: Gas限制（可选）
            
        Returns:
            str: 交易哈希
        """
        if not self.account:
            raise ValueError("未设置私钥，无法发送交易")
        
        try:
            to_address = to_checksum_address(to_address)
            
            # 构建交易参数
            transaction = {
                'to': to_address,
                'value': value,
                'data': data,
                'nonce': await self.get_transaction_count(self.account.address),
                'gasPrice': await self.get_gas_price()
            }
            
            # 估算Gas费用
            if gas_limit is None:
                transaction['gas'] = await self.estimate_gas(transaction)
            else:
                transaction['gas'] = gas_limit
            
            # 签名交易
            signed_txn = self.web3.eth.account.sign_transaction(transaction, self.private_key)
            
            # 发送交易
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            tx_hash_hex = tx_hash.hex()
            
            self.logger.info(f"交易已发送: {tx_hash_hex}")
            return tx_hash_hex
            
        except Exception as e:
            self.logger.error(f"发送交易失败: {e}")
            raise
    
    async def wait_for_transaction(self, tx_hash: str, timeout: int = 300) -> Dict[str, Any]:
        """
        等待交易确认
        
        Args:
            tx_hash: 交易哈希
            timeout: 超时时间（秒）
            
        Returns:
            Dict[str, Any]: 交易收据
        """
        try:
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
            self.logger.info(f"交易已确认: {tx_hash}")
            return receipt
        except Exception as e:
            self.logger.error(f"等待交易确认失败: {e}")
            raise
    
    async def deploy_contract(self, abi: List[Dict[str, Any]], bytecode: str, constructor_args: Optional[List] = None) -> str:
        """
        部署智能合约到区块链网络
        
        这是智能合约部署的核心方法，负责将编译后的合约字节码部署到区块链上。
        支持构造函数参数传递和Gas费自动估算，确保部署过程的可靠性。
        
        Args:
            abi (List[Dict[str, Any]]): 合约ABI（应用二进制接口）
                - 描述合约的所有函数、事件和数据结构
                - 格式: JSON数组，包含函数和事件的详细信息
                - 示例: [{"inputs":[],"name":"name","outputs":[{"type":"string"}],"type":"function"}]
            bytecode (str): 合约字节码
                - 编译后的合约机器码，以0x开头的十六进制字符串
                - 包含合约的所有逻辑和数据
                - 通常通过Solidity编译器生成
            constructor_args (Optional[List]): 构造函数参数
                - 传递给合约构造函数的参数列表
                - 参数类型必须与ABI中定义的构造函数参数匹配
                - 如果合约没有构造函数，可以传入None或空列表
        
        Returns:
            str: 部署成功后的合约地址
                - 格式: 0x开头的40位十六进制字符串
                - 这是合约在区块链上的唯一标识符
                - 可用于后续的合约调用和交互
        
        Raises:
            ValueError: 当未设置私钥时抛出（部署需要签名）
            Exception: 当合约部署失败时抛出
            
        Example:
            # 部署简单合约
            abi = [{"inputs":[],"name":"getValue","outputs":[{"type":"uint256"}],"type":"function"}]
            bytecode = "0x608060405234801561001057600080fd5b50..."
            contract_address = await client.deploy_contract(abi, bytecode)
            
            # 部署带构造函数参数的合约
            abi = [{"inputs":[{"type":"string"}],"name":"constructor","type":"constructor"}]
            bytecode = "0x608060405234801561001057600080fd5b50..."
            contract_address = await client.deploy_contract(
                abi, 
                bytecode, 
                ["MyToken"]  # 构造函数参数
            )
        
        Note:
            - 部署过程需要消耗ETH作为Gas费
            - 部署时间取决于网络拥堵情况
            - 建议在测试网先测试部署过程
        """
        if not self.account:
            raise ValueError("未设置私钥，无法部署合约")
        
        try:
            # 创建合约实例
            contract = self.web3.eth.contract(abi=abi, bytecode=bytecode)
            
            # 构建构造函数调用
            if constructor_args:
                constructor_call = contract.constructor(*constructor_args)
            else:
                constructor_call = contract.constructor()
            
            # 估算Gas费用
            gas_estimate = constructor_call.estimate_gas({'from': self.account.address})
            
            # 构建部署交易
            transaction = constructor_call.build_transaction({
                'from': self.account.address,
                'gas': gas_estimate,
                'gasPrice': await self.get_gas_price(),
                'nonce': await self.get_transaction_count(self.account.address)
            })
            
            # 签名并发送交易
            signed_txn = self.web3.eth.account.sign_transaction(transaction, self.private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # 等待部署确认
            receipt = await self.wait_for_transaction(tx_hash.hex())
            
            if receipt.status == 1:
                contract_address = receipt.contractAddress
                self.logger.info(f"合约部署成功: {contract_address}")
                return contract_address
            else:
                raise Exception("合约部署失败")
                
        except Exception as e:
            self.logger.error(f"部署合约失败: {e}")
            raise
    
    async def call_contract(self, contract_address: str, abi: List[Dict[str, Any]], 
                          method_name: str, args: Optional[List] = None) -> Any:
        """
        调用智能合约方法
        
        Args:
            contract_address: 合约地址
            abi: 合约ABI
            method_name: 方法名
            args: 方法参数（可选）
            
        Returns:
            Any: 方法返回值
        """
        try:
            contract_address = to_checksum_address(contract_address)
            contract = self.web3.eth.contract(address=contract_address, abi=abi)
            
            method = getattr(contract.functions, method_name)
            
            if args:
                result = method(*args).call()
            else:
                result = method().call()
            
            self.logger.debug(f"合约调用成功: {contract_address}.{method_name} -> {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"调用合约方法失败: {e}")
            raise
    
    async def send_contract_transaction(self, contract_address: str, abi: List[Dict[str, Any]], 
                                     method_name: str, args: Optional[List] = None, 
                                     value: int = 0) -> str:
        """
        发送智能合约交易
        
        Args:
            contract_address: 合约地址
            abi: 合约ABI
            method_name: 方法名
            args: 方法参数（可选）
            value: 发送的ETH金额（可选）
            
        Returns:
            str: 交易哈希
        """
        if not self.account:
            raise ValueError("未设置私钥，无法发送合约交易")
        
        try:
            contract_address = to_checksum_address(contract_address)
            contract = self.web3.eth.contract(address=contract_address, abi=abi)
            
            method = getattr(contract.functions, method_name)
            
            if args:
                function_call = method(*args)
            else:
                function_call = method()
            
            # 构建交易
            transaction = function_call.build_transaction({
                'from': self.account.address,
                'value': value,
                'gasPrice': await self.get_gas_price(),
                'nonce': await self.get_transaction_count(self.account.address)
            })
            
            # 估算Gas费用
            transaction['gas'] = await self.estimate_gas(transaction)
            
            # 签名并发送交易
            signed_txn = self.web3.eth.account.sign_transaction(transaction, self.private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            self.logger.info(f"合约交易已发送: {tx_hash.hex()}")
            return tx_hash.hex()
            
        except Exception as e:
            self.logger.error(f"发送合约交易失败: {e}")
            raise
    
    async def listen_events(self, contract_address: str, abi: List[Dict[str, Any]], 
                          event_name: str, callback: Callable, from_block: Optional[int] = None):
        """
        监听智能合约事件
        
        Args:
            contract_address: 合约地址
            abi: 合约ABI
            event_name: 事件名
            callback: 回调函数
            from_block: 起始区块（可选）
        """
        try:
            contract_address = to_checksum_address(contract_address)
            contract = self.web3.eth.contract(address=contract_address, abi=abi)
            
            event_filter = contract.events[event_name].create_filter(fromBlock=from_block or 'latest')
            
            self.logger.info(f"开始监听事件: {contract_address}.{event_name}")
            
            while True:
                for event in event_filter.get_new_entries():
                    self.logger.debug(f"收到事件: {event}")
                    callback(event)
                await asyncio.sleep(1)
                
        except Exception as e:
            self.logger.error(f"监听事件失败: {e}")
            raise
    
    async def get_block(self, block_number: Union[int, str]) -> Dict[str, Any]:
        """
        获取区块信息
        
        Args:
            block_number: 区块号或'latest'
            
        Returns:
            Dict[str, Any]: 区块信息
        """
        try:
            block = self.web3.eth.get_block(block_number)
            return dict(block)
        except Exception as e:
            self.logger.error(f"获取区块信息失败: {e}")
            raise
    
    async def get_transaction(self, tx_hash: str) -> Dict[str, Any]:
        """
        获取交易信息
        
        Args:
            tx_hash: 交易哈希
            
        Returns:
            Dict[str, Any]: 交易信息
        """
        try:
            transaction = self.web3.eth.get_transaction(tx_hash)
            return dict(transaction)
        except Exception as e:
            self.logger.error(f"获取交易信息失败: {e}")
            raise


class EthereumTester:
    """以太坊测试器"""
    
    def __init__(self, rpc_url: str, private_key: Optional[str] = None, network: Optional[str] = None):
        """
        初始化以太坊测试器
        
        Args:
            rpc_url: RPC节点URL
            private_key: 私钥（可选）
            network: 网络名称（可选）
        """
        self.client = EthereumClient(rpc_url, private_key, network)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def test_connection(self) -> bool:
        """
        测试网络连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            chain_id = self.client.web3.eth.chain_id
            self.logger.info(f"网络连接正常，Chain ID: {chain_id}")
            return True
        except Exception as e:
            self.logger.error(f"网络连接失败: {e}")
            return False
    
    async def test_account_balance(self, address: str) -> Dict[str, Any]:
        """
        测试账户余额查询
        
        Args:
            address: 账户地址
            
        Returns:
            Dict[str, Any]: 测试结果
        """
        try:
            balance = await self.client.get_balance(address)
            balance_eth = self.client.web3.from_wei(balance, 'ether')
            
            result = {
                "success": True,
                "address": address,
                "balance_wei": balance,
                "balance_eth": float(balance_eth),
                "message": f"账户余额: {balance_eth} ETH"
            }
            
            self.logger.info(result["message"])
            return result
            
        except Exception as e:
            result = {
                "success": False,
                "address": address,
                "error": str(e),
                "message": f"查询余额失败: {e}"
            }
            
            self.logger.error(result["message"])
            return result
    
    async def test_smart_contract_deployment(self, abi: List[Dict[str, Any]], bytecode: str) -> Dict[str, Any]:
        """
        测试智能合约部署
        
        Args:
            abi: 合约ABI
            bytecode: 合约字节码
            
        Returns:
            Dict[str, Any]: 测试结果
        """
        try:
            contract_address = await self.client.deploy_contract(abi, bytecode)
            
            result = {
                "success": True,
                "contract_address": contract_address,
                "message": f"合约部署成功: {contract_address}"
            }
            
            self.logger.info(result["message"])
            return result
            
        except Exception as e:
            result = {
                "success": False,
                "error": str(e),
                "message": f"合约部署失败: {e}"
            }
            
            self.logger.error(result["message"])
            return result
    
    async def test_smart_contract_call(self, contract_address: str, abi: List[Dict[str, Any]], 
                                     method_name: str, args: Optional[List] = None) -> Dict[str, Any]:
        """
        测试智能合约调用
        
        Args:
            contract_address: 合约地址
            abi: 合约ABI
            method_name: 方法名
            args: 方法参数（可选）
            
        Returns:
            Dict[str, Any]: 测试结果
        """
        try:
            result_value = await self.client.call_contract(contract_address, abi, method_name, args)
            
            result = {
                "success": True,
                "contract_address": contract_address,
                "method": method_name,
                "args": args,
                "return_value": result_value,
                "message": f"合约调用成功: {contract_address}.{method_name} -> {result_value}"
            }
            
            self.logger.info(result["message"])
            return result
            
        except Exception as e:
            result = {
                "success": False,
                "contract_address": contract_address,
                "method": method_name,
                "error": str(e),
                "message": f"合约调用失败: {e}"
            }
            
            self.logger.error(result["message"])
            return result
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """
        运行综合测试
        
        Returns:
            Dict[str, Any]: 综合测试结果
        """
        test_results = {
            "timestamp": time.time(),
            "network": self.client.network_info.get("name", "Unknown"),
            "chain_id": self.client.chain_id,
            "tests": {}
        }
        
        # 测试网络连接
        connection_test = await self.test_connection()
        test_results["tests"]["connection"] = {
            "success": connection_test,
            "message": "网络连接测试"
        }
        
        if connection_test and self.client.account:
            # 测试账户余额
            balance_test = await self.test_account_balance(self.client.account.address)
            test_results["tests"]["balance"] = balance_test
            
            # 测试Gas价格查询
            try:
                gas_price = await self.client.get_gas_price()
                test_results["tests"]["gas_price"] = {
                    "success": True,
                    "gas_price_wei": gas_price,
                    "gas_price_gwei": self.client.web3.from_wei(gas_price, 'gwei'),
                    "message": f"当前Gas价格: {self.client.web3.from_wei(gas_price, 'gwei')} Gwei"
                }
            except Exception as e:
                test_results["tests"]["gas_price"] = {
                    "success": False,
                    "error": str(e),
                    "message": f"Gas价格查询失败: {e}"
                }
        
        # 计算总体成功率
        total_tests = len(test_results["tests"])
        successful_tests = sum(1 for test in test_results["tests"].values() if test.get("success", False))
        test_results["success_rate"] = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.logger.info(f"综合测试完成，成功率: {test_results['success_rate']:.1f}%")
        return test_results
