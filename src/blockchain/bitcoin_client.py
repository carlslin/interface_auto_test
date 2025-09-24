"""
=============================================================================
接口自动化测试框架 - 比特币客户端模块
=============================================================================

本模块提供了完整的比特币区块链测试支持，包括交易发送、查询、地址生成等功能。

主要功能：
1. 网络连接 - 支持主网、测试网、本地节点
2. 交易管理 - 发送、查询、验证
3. 地址管理 - 生成、验证、余额查询
4. 区块查询 - 区块信息、交易历史
5. 钱包管理 - 私钥管理、签名
6. UTXO管理 - 未花费输出查询

支持的网络：
- Bitcoin Mainnet (比特币主网)
- Bitcoin Testnet (比特币测试网)
- Bitcoin Regtest (本地测试网络)

技术特性：
- Bitcoin Core RPC集成 - 完整的比特币网络支持
- 异步操作 - 高性能并发处理
- 地址生成 - 支持多种地址格式
- 交易构建 - 完整的交易构建和签名
- UTXO管理 - 未花费输出跟踪
- 多重签名支持 - 企业级安全

使用示例：
    # 连接到比特币测试网
    btc_client = BitcoinClient("http://user:pass@localhost:18332")
    
    # 生成新地址
    address = await btc_client.generate_address()
    
    # 查询余额
    balance = await btc_client.get_balance(address)
    
    # 发送交易
    tx_hash = await btc_client.send_transaction(to_address, amount, private_key)

作者: 接口自动化测试框架团队
版本: 1.0.0
更新日期: 2024年12月
=============================================================================
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import httpx
from bitcoin import *
from bitcoin.rpc import RawProxy


@dataclass
class BitcoinTransaction:
    """比特币交易数据类"""
    txid: str
    hash: str
    version: int
    size: int
    vsize: int
    weight: int
    locktime: int
    vin: List[Dict[str, Any]]
    vout: List[Dict[str, Any]]
    hex: str
    blockhash: Optional[str] = None
    confirmations: Optional[int] = None
    time: Optional[int] = None
    blocktime: Optional[int] = None


@dataclass
class UTXO:
    """未花费输出数据类"""
    txid: str
    vout: int
    address: str
    scriptPubKey: str
    amount: float
    confirmations: int
    spendable: bool
    solvable: bool


class BitcoinClient:
    """比特币客户端"""
    
    # 预定义网络配置
    NETWORKS = {
        "mainnet": {
            "name": "Bitcoin Mainnet",
            "rpc_port": 8332,
            "explorer": "https://blockstream.info"
        },
        "testnet": {
            "name": "Bitcoin Testnet",
            "rpc_port": 18332,
            "explorer": "https://blockstream.info/testnet"
        },
        "regtest": {
            "name": "Bitcoin Regtest",
            "rpc_port": 18443,
            "explorer": "Local"
        }
    }
    
    def __init__(self, rpc_url: str, username: Optional[str] = None, password: Optional[str] = None):
        """
        初始化比特币客户端
        
        Args:
            rpc_url: RPC节点URL
            username: RPC用户名（可选）
            password: RPC密码（可选）
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.rpc_url = rpc_url
        self.username = username
        self.password = password
        
        # 初始化RPC连接
        try:
            if username and password:
                self.rpc = RawProxy(service_url=rpc_url, user=username, password=password)
            else:
                self.rpc = RawProxy(service_url=rpc_url)
            
            # 验证连接
            self.rpc.getblockchaininfo()
            self.logger.info(f"已连接到比特币节点: {rpc_url}")
            
        except Exception as e:
            self.logger.error(f"无法连接到比特币节点: {e}")
            raise ConnectionError(f"无法连接到比特币节点: {rpc_url}")
    
    async def get_blockchain_info(self) -> Dict[str, Any]:
        """
        获取区块链信息
        
        Returns:
            Dict[str, Any]: 区块链信息
        """
        try:
            info = self.rpc.getblockchaininfo()
            self.logger.debug(f"区块链信息: {info}")
            return info
        except Exception as e:
            self.logger.error(f"获取区块链信息失败: {e}")
            raise
    
    async def get_network_info(self) -> Dict[str, Any]:
        """
        获取网络信息
        
        Returns:
            Dict[str, Any]: 网络信息
        """
        try:
            info = self.rpc.getnetworkinfo()
            self.logger.debug(f"网络信息: {info}")
            return info
        except Exception as e:
            self.logger.error(f"获取网络信息失败: {e}")
            raise
    
    async def generate_address(self, label: str = "") -> str:
        """
        生成新地址
        
        Args:
            label: 地址标签（可选）
            
        Returns:
            str: 生成的地址
        """
        try:
            address = self.rpc.getnewaddress(label)
            self.logger.info(f"生成新地址: {address}")
            return address
        except Exception as e:
            self.logger.error(f"生成地址失败: {e}")
            raise
    
    async def get_balance(self, address: Optional[str] = None, minconf: int = 1) -> float:
        """
        获取余额
        
        Args:
            address: 地址（可选，不指定则返回钱包总余额）
            minconf: 最小确认数
            
        Returns:
            float: 余额（BTC）
        """
        try:
            if address:
                # 获取特定地址余额
                utxos = await self.list_unspent(minconf=minconf, addresses=[address])
                balance = sum(utxo.amount for utxo in utxos)
            else:
                # 获取钱包总余额
                balance = self.rpc.getbalance("*", minconf)
            
            self.logger.debug(f"余额查询: {balance} BTC")
            return balance
        except Exception as e:
            self.logger.error(f"获取余额失败: {e}")
            raise
    
    async def list_unspent(self, minconf: int = 1, maxconf: int = 9999999, 
                         addresses: Optional[List[str]] = None) -> List[UTXO]:
        """
        列出未花费输出
        
        Args:
            minconf: 最小确认数
            maxconf: 最大确认数
            addresses: 地址列表（可选）
            
        Returns:
            List[UTXO]: 未花费输出列表
        """
        try:
            if addresses:
                utxos_data = self.rpc.listunspent(minconf, maxconf, addresses)
            else:
                utxos_data = self.rpc.listunspent(minconf, maxconf)
            
            utxos = []
            for utxo_data in utxos_data:
                utxo = UTXO(
                    txid=utxo_data['txid'],
                    vout=utxo_data['vout'],
                    address=utxo_data['address'],
                    scriptPubKey=utxo_data['scriptPubKey'],
                    amount=utxo_data['amount'],
                    confirmations=utxo_data['confirmations'],
                    spendable=utxo_data['spendable'],
                    solvable=utxo_data['solvable']
                )
                utxos.append(utxo)
            
            self.logger.debug(f"找到 {len(utxos)} 个未花费输出")
            return utxos
            
        except Exception as e:
            self.logger.error(f"获取未花费输出失败: {e}")
            raise
    
    async def send_to_address(self, address: str, amount: float, comment: str = "", 
                            comment_to: str = "", subtract_fee_from_amount: bool = False) -> str:
        """
        发送比特币到地址
        
        Args:
            address: 接收地址
            amount: 发送金额（BTC）
            comment: 交易备注
            comment_to: 接收方备注
            subtract_fee_from_amount: 是否从金额中扣除手续费
            
        Returns:
            str: 交易哈希
        """
        try:
            tx_hash = self.rpc.sendtoaddress(
                address, amount, comment, comment_to, subtract_fee_from_amount
            )
            
            self.logger.info(f"交易已发送: {tx_hash}")
            return tx_hash
            
        except Exception as e:
            self.logger.error(f"发送交易失败: {e}")
            raise
    
    async def send_raw_transaction(self, hexstring: str) -> str:
        """
        发送原始交易
        
        Args:
            hexstring: 十六进制交易数据
            
        Returns:
            str: 交易哈希
        """
        try:
            tx_hash = self.rpc.sendrawtransaction(hexstring)
            self.logger.info(f"原始交易已发送: {tx_hash}")
            return tx_hash
        except Exception as e:
            self.logger.error(f"发送原始交易失败: {e}")
            raise
    
    async def create_raw_transaction(self, inputs: List[Dict[str, Any]], 
                                   outputs: Dict[str, float], 
                                   locktime: int = 0) -> str:
        """
        创建原始交易
        
        Args:
            inputs: 输入列表 [{"txid": "xxx", "vout": 0}]
            outputs: 输出字典 {"address": amount}
            locktime: 锁定时间
            
        Returns:
            str: 十六进制交易数据
        """
        try:
            hex_tx = self.rpc.createrawtransaction(inputs, outputs, locktime)
            self.logger.debug(f"创建原始交易: {hex_tx}")
            return hex_tx
        except Exception as e:
            self.logger.error(f"创建原始交易失败: {e}")
            raise
    
    async def sign_raw_transaction(self, hexstring: str, prevtxs: Optional[List[Dict[str, Any]]] = None,
                                 privkeys: Optional[List[str]] = None, sighashtype: str = "ALL") -> Dict[str, Any]:
        """
        签名原始交易
        
        Args:
            hexstring: 十六进制交易数据
            prevtxs: 前一个交易信息（可选）
            privkeys: 私钥列表（可选）
            sighashtype: 签名哈希类型
            
        Returns:
            Dict[str, Any]: 签名结果
        """
        try:
            result = self.rpc.signrawtransaction(hexstring, prevtxs, privkeys, sighashtype)
            self.logger.debug(f"交易签名结果: {result}")
            return result
        except Exception as e:
            self.logger.error(f"签名交易失败: {e}")
            raise
    
    async def get_transaction(self, txid: str, verbose: bool = True, 
                            wallet: bool = False) -> Dict[str, Any]:
        """
        获取交易信息
        
        Args:
            txid: 交易哈希
            verbose: 是否返回详细信息
            wallet: 是否从钱包获取
            
        Returns:
            Dict[str, Any]: 交易信息
        """
        try:
            tx_info = self.rpc.gettransaction(txid, verbose, wallet)
            self.logger.debug(f"交易信息: {tx_info}")
            return tx_info
        except Exception as e:
            self.logger.error(f"获取交易信息失败: {e}")
            raise
    
    async def get_raw_transaction(self, txid: str, verbose: bool = True) -> Union[str, Dict[str, Any]]:
        """
        获取原始交易
        
        Args:
            txid: 交易哈希
            verbose: 是否返回详细信息
            
        Returns:
            Union[str, Dict[str, Any]]: 原始交易数据
        """
        try:
            raw_tx = self.rpc.getrawtransaction(txid, verbose)
            self.logger.debug(f"原始交易: {raw_tx}")
            return raw_tx
        except Exception as e:
            self.logger.error(f"获取原始交易失败: {e}")
            raise
    
    async def get_block(self, block_hash: str, verbosity: int = 1) -> Dict[str, Any]:
        """
        获取区块信息
        
        Args:
            block_hash: 区块哈希
            verbosity: 详细程度 (0=原始数据, 1=JSON对象, 2=包含交易)
            
        Returns:
            Dict[str, Any]: 区块信息
        """
        try:
            block_info = self.rpc.getblock(block_hash, verbosity)
            self.logger.debug(f"区块信息: {block_info}")
            return block_info
        except Exception as e:
            self.logger.error(f"获取区块信息失败: {e}")
            raise
    
    async def get_block_hash(self, height: int) -> str:
        """
        根据高度获取区块哈希
        
        Args:
            height: 区块高度
            
        Returns:
            str: 区块哈希
        """
        try:
            block_hash = self.rpc.getblockhash(height)
            self.logger.debug(f"区块哈希: {block_hash}")
            return block_hash
        except Exception as e:
            self.logger.error(f"获取区块哈希失败: {e}")
            raise
    
    async def estimate_smart_fee(self, target_blocks: int, estimate_mode: str = "CONSERVATIVE") -> Dict[str, Any]:
        """
        估算智能手续费
        
        Args:
            target_blocks: 目标确认区块数
            estimate_mode: 估算模式 (CONSERVATIVE, ECONOMICAL)
            
        Returns:
            Dict[str, Any]: 手续费估算结果
        """
        try:
            fee_estimate = self.rpc.estimatesmartfee(target_blocks, estimate_mode)
            self.logger.debug(f"手续费估算: {fee_estimate}")
            return fee_estimate
        except Exception as e:
            self.logger.error(f"估算手续费失败: {e}")
            raise
    
    async def validate_address(self, address: str) -> Dict[str, Any]:
        """
        验证地址
        
        Args:
            address: 地址
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        try:
            result = self.rpc.validateaddress(address)
            self.logger.debug(f"地址验证: {result}")
            return result
        except Exception as e:
            self.logger.error(f"验证地址失败: {e}")
            raise
    
    async def import_address(self, address: str, label: str = "", rescan: bool = True) -> None:
        """
        导入地址到钱包
        
        Args:
            address: 地址
            label: 标签
            rescan: 是否重新扫描
        """
        try:
            self.rpc.importaddress(address, label, rescan)
            self.logger.info(f"地址已导入: {address}")
        except Exception as e:
            self.logger.error(f"导入地址失败: {e}")
            raise


class BitcoinTester:
    """比特币测试器"""
    
    def __init__(self, rpc_url: str, username: Optional[str] = None, password: Optional[str] = None):
        """
        初始化比特币测试器
        
        Args:
            rpc_url: RPC节点URL
            username: RPC用户名（可选）
            password: RPC密码（可选）
        """
        self.client = BitcoinClient(rpc_url, username, password)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def test_connection(self) -> bool:
        """
        测试网络连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            blockchain_info = await self.client.get_blockchain_info()
            self.logger.info(f"网络连接正常，链: {blockchain_info.get('chain', 'Unknown')}")
            return True
        except Exception as e:
            self.logger.error(f"网络连接失败: {e}")
            return False
    
    async def test_address_generation(self) -> Dict[str, Any]:
        """
        测试地址生成
        
        Returns:
            Dict[str, Any]: 测试结果
        """
        try:
            address = await self.client.generate_address("test_address")
            
            result = {
                "success": True,
                "address": address,
                "message": f"地址生成成功: {address}"
            }
            
            self.logger.info(result["message"])
            return result
            
        except Exception as e:
            result = {
                "success": False,
                "error": str(e),
                "message": f"地址生成失败: {e}"
            }
            
            self.logger.error(result["message"])
            return result
    
    async def test_address_validation(self, address: str) -> Dict[str, Any]:
        """
        测试地址验证
        
        Args:
            address: 地址
            
        Returns:
            Dict[str, Any]: 测试结果
        """
        try:
            validation_result = await self.client.validate_address(address)
            
            result = {
                "success": True,
                "address": address,
                "is_valid": validation_result.get("isvalid", False),
                "validation_result": validation_result,
                "message": f"地址验证成功: {address} -> {validation_result.get('isvalid', False)}"
            }
            
            self.logger.info(result["message"])
            return result
            
        except Exception as e:
            result = {
                "success": False,
                "address": address,
                "error": str(e),
                "message": f"地址验证失败: {e}"
            }
            
            self.logger.error(result["message"])
            return result
    
    async def test_balance_query(self, address: Optional[str] = None) -> Dict[str, Any]:
        """
        测试余额查询
        
        Args:
            address: 地址（可选）
            
        Returns:
            Dict[str, Any]: 测试结果
        """
        try:
            balance = await self.client.get_balance(address)
            
            result = {
                "success": True,
                "address": address,
                "balance": balance,
                "message": f"余额查询成功: {balance} BTC"
            }
            
            self.logger.info(result["message"])
            return result
            
        except Exception as e:
            result = {
                "success": False,
                "address": address,
                "error": str(e),
                "message": f"余额查询失败: {e}"
            }
            
            self.logger.error(result["message"])
            return result
    
    async def test_utxo_query(self, address: Optional[str] = None) -> Dict[str, Any]:
        """
        测试UTXO查询
        
        Args:
            address: 地址（可选）
            
        Returns:
            Dict[str, Any]: 测试结果
        """
        try:
            if address:
                utxos = await self.client.list_unspent(addresses=[address])
            else:
                utxos = await self.client.list_unspent()
            
            total_amount = sum(utxo.amount for utxo in utxos)
            
            result = {
                "success": True,
                "address": address,
                "utxo_count": len(utxos),
                "total_amount": total_amount,
                "utxos": [{"txid": utxo.txid, "vout": utxo.vout, "amount": utxo.amount} for utxo in utxos],
                "message": f"UTXO查询成功: 找到 {len(utxos)} 个未花费输出，总计 {total_amount} BTC"
            }
            
            self.logger.info(result["message"])
            return result
            
        except Exception as e:
            result = {
                "success": False,
                "address": address,
                "error": str(e),
                "message": f"UTXO查询失败: {e}"
            }
            
            self.logger.error(result["message"])
            return result
    
    async def test_fee_estimation(self) -> Dict[str, Any]:
        """
        测试手续费估算
        
        Returns:
            Dict[str, Any]: 测试结果
        """
        try:
            fee_estimate = await self.client.estimate_smart_fee(6)  # 6个区块确认
            
            result = {
                "success": True,
                "fee_estimate": fee_estimate,
                "message": f"手续费估算成功: {fee_estimate}"
            }
            
            self.logger.info(result["message"])
            return result
            
        except Exception as e:
            result = {
                "success": False,
                "error": str(e),
                "message": f"手续费估算失败: {e}"
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
            "network": "Bitcoin",
            "tests": {}
        }
        
        # 测试网络连接
        connection_test = await self.test_connection()
        test_results["tests"]["connection"] = {
            "success": connection_test,
            "message": "网络连接测试"
        }
        
        if connection_test:
            # 测试地址生成
            address_test = await self.test_address_generation()
            test_results["tests"]["address_generation"] = address_test
            
            # 测试地址验证
            if address_test["success"]:
                validation_test = await self.test_address_validation(address_test["address"])
                test_results["tests"]["address_validation"] = validation_test
            
            # 测试余额查询
            balance_test = await self.test_balance_query()
            test_results["tests"]["balance_query"] = balance_test
            
            # 测试UTXO查询
            utxo_test = await self.test_utxo_query()
            test_results["tests"]["utxo_query"] = utxo_test
            
            # 测试手续费估算
            fee_test = await self.test_fee_estimation()
            test_results["tests"]["fee_estimation"] = fee_test
        
        # 计算总体成功率
        total_tests = len(test_results["tests"])
        successful_tests = sum(1 for test in test_results["tests"].values() if test.get("success", False))
        test_results["success_rate"] = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.logger.info(f"综合测试完成，成功率: {test_results['success_rate']:.1f}%")
        return test_results
