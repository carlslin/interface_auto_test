"""
=============================================================================
接口自动化测试框架 - 区块链CLI命令模块
=============================================================================

本模块提供了区块链功能的命令行接口，支持各种区块链操作和测试功能。

主要功能：
1. 区块链连接管理 - 建立和管理区块链连接
2. 钱包操作 - 生成、导入和管理钱包
3. 交易操作 - 发送和查询交易
4. 智能合约测试 - 部署和测试智能合约
5. 事件监听 - 实时监听区块链事件
6. 长连接管理 - WebSocket和HTTP长连接支持

支持的区块链：
- 以太坊 (Ethereum) - 主网、测试网、L2网络
- 比特币 (Bitcoin) - 主网、测试网、回归测试网
- EVM兼容链 - BSC、Polygon、Arbitrum等

CLI命令结构：
- blockchain connect - 连接区块链网络
- blockchain wallet - 钱包管理操作
- blockchain transaction - 交易操作
- blockchain contract - 智能合约操作
- blockchain listen - 事件监听
- blockchain pool - 连接池管理

使用示例：
    # 连接以太坊测试网
    python3 -m src.cli.main blockchain connect ethereum --network sepolia
    
    # 生成新钱包
    python3 -m src.cli.main blockchain wallet generate --type ethereum
    
    # 监听新区块事件
    python3 -m src.cli.main blockchain listen --type newHeads --connection-id conn_123

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
import click
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.blockchain.blockchain_manager import BlockchainManager
from src.blockchain.wallet_manager import WalletManager
from src.blockchain.smart_contract_tester import SmartContractTester
from src.blockchain.connection_manager import BlockchainConnectionManager, ConnectionType
from src.blockchain.blockchain_config import BlockchainConfig
from src.utils.config_loader import ConfigLoader


class BlockchainCLI:
    """区块链CLI管理器"""
    
    def __init__(self):
        """初始化区块链CLI"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config_loader = ConfigLoader()
        self.blockchain_config = BlockchainConfig()
        self.wallet_manager = WalletManager()
        self.connection_manager = BlockchainConnectionManager()
        self.blockchain_manager = None
        
        # 初始化区块链管理器
        try:
            blockchain_config = self.blockchain_config.get_config()
            self.blockchain_manager = BlockchainManager(blockchain_config)
            self.logger.info("区块链CLI初始化成功")
        except Exception as e:
            self.logger.warning(f"区块链管理器初始化失败: {e}")
    
    async def connect_ethereum(self, network: str, rpc_url: Optional[str] = None, 
                             private_key: Optional[str] = None) -> str:
        """
        连接以太坊网络
        
        Args:
            network: 网络名称
            rpc_url: RPC URL
            private_key: 私钥
            
        Returns:
            str: 连接ID
        """
        try:
            # 获取网络配置
            network_config = self.blockchain_config.get_network_config("ethereum", network)
            if not network_config:
                raise ValueError(f"未找到网络配置: {network}")
            
            # 使用提供的RPC URL或配置中的URL
            url = rpc_url or network_config.get("rpc_url")
            if not url:
                raise ValueError(f"网络 {network} 未配置RPC URL")
            
            # 使用提供的私钥或配置中的私钥
            key = private_key or network_config.get("private_key")
            
            # 创建以太坊客户端
            from src.blockchain.ethereum_client import EthereumClient
            client = EthereumClient(url, private_key=key, network=network)
            
            # 添加到区块链管理器
            connection_id = f"ethereum_{network}_{int(time.time())}"
            if not hasattr(self.blockchain_manager, 'clients'):
                self.blockchain_manager.clients = {}
            self.blockchain_manager.clients[connection_id] = client
            
            self.logger.info(f"以太坊网络连接成功: {network} ({connection_id})")
            return connection_id
            
        except Exception as e:
            self.logger.error(f"连接以太坊网络失败: {e}")
            raise
    
    async def connect_websocket(self, url: str, connection_type: str = "websocket") -> str:
        """
        建立WebSocket长连接
        
        Args:
            url: WebSocket URL
            connection_type: 连接类型
            
        Returns:
            str: 连接ID
        """
        try:
            conn_type = ConnectionType.WEBSOCKET if connection_type == "websocket" else ConnectionType.HTTP_POOL
            
            if conn_type == ConnectionType.WEBSOCKET:
                connection_id = await self.connection_manager.connect_websocket(url)
            else:
                connection_id = await self.connection_manager.connect_http_pool(url)
            
            self.logger.info(f"WebSocket连接建立成功: {connection_id}")
            return connection_id
            
        except Exception as e:
            self.logger.error(f"建立WebSocket连接失败: {e}")
            raise
    
    async def generate_wallet(self, wallet_type: str) -> Dict[str, str]:
        """
        生成新钱包
        
        Args:
            wallet_type: 钱包类型 (ethereum/bitcoin)
            
        Returns:
            Dict[str, str]: 钱包信息
        """
        try:
            if wallet_type.lower() == "ethereum":
                wallet_info = self.wallet_manager.generate_ethereum_wallet()
            elif wallet_type.lower() == "bitcoin":
                wallet_info = self.wallet_manager.generate_bitcoin_wallet()
            else:
                raise ValueError(f"不支持的钱包类型: {wallet_type}")
            
            self.logger.info(f"{wallet_type}钱包生成成功: {wallet_info.get('address', 'N/A')}")
            return wallet_info
            
        except Exception as e:
            self.logger.error(f"生成钱包失败: {e}")
            raise
    
    async def send_transaction(self, connection_id: str, to_address: str, 
                            amount: float, currency: str = "ETH") -> str:
        """
        发送交易
        
        Args:
            connection_id: 连接ID
            to_address: 接收地址
            amount: 金额
            currency: 货币类型
            
        Returns:
            str: 交易哈希
        """
        try:
            if connection_id not in self.blockchain_manager.clients:
                raise ValueError(f"连接不存在: {connection_id}")
            
            client = self.blockchain_manager.clients[connection_id]
            
            if currency.upper() == "ETH":
                # 以太坊交易
                tx_hash = client.send_transaction(to_address, amount)
            else:
                raise ValueError(f"不支持的货币类型: {currency}")
            
            self.logger.info(f"交易发送成功: {tx_hash}")
            return tx_hash
            
        except Exception as e:
            self.logger.error(f"发送交易失败: {e}")
            raise
    
    async def deploy_contract(self, connection_id: str, abi_file: str, 
                            bytecode_file: str) -> str:
        """
        部署智能合约
        
        Args:
            connection_id: 连接ID
            abi_file: ABI文件路径
            bytecode_file: 字节码文件路径
            
        Returns:
            str: 合约地址
        """
        try:
            if connection_id not in self.blockchain_manager.clients:
                raise ValueError(f"连接不存在: {connection_id}")
            
            client = self.blockchain_manager.clients[connection_id]
            
            # 读取ABI和字节码
            with open(abi_file, 'r') as f:
                abi = json.load(f)
            
            with open(bytecode_file, 'r') as f:
                bytecode = f.read().strip()
            
            # 部署合约
            contract_address = await client.deploy_contract(abi, bytecode)
            
            self.logger.info(f"合约部署成功: {contract_address}")
            return contract_address
            
        except Exception as e:
            self.logger.error(f"部署合约失败: {e}")
            raise
    
    async def listen_events(self, connection_id: str, event_type: str) -> None:
        """
        监听区块链事件
        
        Args:
            connection_id: 连接ID
            event_type: 事件类型
        """
        try:
            # 订阅事件
            await self.connection_manager.subscribe_events(connection_id, event_type)
            
            # 监听事件
            self.logger.info(f"开始监听事件: {event_type}")
            async for event in self.connection_manager.listen_events(connection_id):
                click.echo(f"收到事件: {json.dumps(event, indent=2)}")
                
        except Exception as e:
            self.logger.error(f"监听事件失败: {e}")
            raise
    
    async def get_connection_stats(self) -> Dict[str, Any]:
        """
        获取连接统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            stats = self.connection_manager.get_connection_stats()
            
            # 添加区块链管理器统计
            if self.blockchain_manager:
                stats["blockchain_clients"] = len(self.blockchain_manager.clients)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"获取统计信息失败: {e}")
            raise
    
    async def cleanup(self):
        """清理资源"""
        try:
            await self.connection_manager.disconnect_all()
            self.logger.info("区块链CLI资源清理完成")
        except Exception as e:
            self.logger.error(f"清理资源失败: {e}")


# CLI命令定义
@click.group()
@click.pass_context
def blockchain(ctx):
    """区块链操作命令"""
    ctx.ensure_object(dict)
    ctx.obj['blockchain_cli'] = BlockchainCLI()


@blockchain.command()
@click.option('--network', '-n', required=True, help='网络名称 (sepolia, mainnet, bsc, polygon等)')
@click.option('--rpc-url', help='RPC URL (可选，使用配置中的默认值)')
@click.option('--private-key', help='私钥 (可选，用于交易操作)')
@click.option('--connection-type', type=click.Choice(['websocket', 'http']), default='http', help='连接类型')
@click.pass_context
def connect(ctx, network: str, rpc_url: Optional[str], private_key: Optional[str], connection_type: str):
    """连接区块链网络"""
    blockchain_cli = ctx.obj['blockchain_cli']
    
    async def _connect():
        try:
            if connection_type == 'websocket' and rpc_url:
                # WebSocket连接
                connection_id = await blockchain_cli.connect_websocket(rpc_url)
            else:
                # 以太坊连接
                connection_id = await blockchain_cli.connect_ethereum(network, rpc_url, private_key)
            
            click.echo(f"连接成功: {connection_id}")
            
        except Exception as e:
            click.echo(f"连接失败: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_connect())


@blockchain.command()
@click.option('--type', '-t', type=click.Choice(['ethereum', 'bitcoin']), required=True, help='钱包类型')
@click.option('--output', '-o', help='输出文件路径 (可选)')
@click.pass_context
def wallet(ctx, type: str, output: Optional[str]):
    """生成新钱包"""
    blockchain_cli = ctx.obj['blockchain_cli']
    
    async def _generate_wallet():
        try:
            wallet_info = await blockchain_cli.generate_wallet(type)
            
            # 输出钱包信息
            click.echo("钱包生成成功:")
            click.echo(f"地址: {wallet_info.get('address', 'N/A')}")
            click.echo(f"私钥: {wallet_info.get('private_key', wallet_info.get('private_key_wif', 'N/A'))}")
            if 'mnemonic' in wallet_info:
                click.echo(f"助记词: {wallet_info['mnemonic']}")
            
            # 保存到文件
            if output:
                with open(output, 'w') as f:
                    json.dump(wallet_info, f, indent=2)
                click.echo(f"钱包信息已保存到: {output}")
            
        except Exception as e:
            click.echo(f"生成钱包失败: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_generate_wallet())


@blockchain.command()
@click.option('--connection-id', '-c', required=True, help='连接ID')
@click.option('--to', required=True, help='接收地址')
@click.option('--amount', '-a', type=float, required=True, help='发送金额')
@click.option('--currency', default='ETH', help='货币类型')
@click.pass_context
def transaction(ctx, connection_id: str, to: str, amount: float, currency: str):
    """发送交易"""
    blockchain_cli = ctx.obj['blockchain_cli']
    
    async def _send_transaction():
        try:
            tx_hash = await blockchain_cli.send_transaction(connection_id, to, amount, currency)
            click.echo(f"交易发送成功: {tx_hash}")
            
        except Exception as e:
            click.echo(f"发送交易失败: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_send_transaction())


@blockchain.command()
@click.option('--connection-id', '-c', required=True, help='连接ID')
@click.option('--abi-file', '-a', required=True, help='ABI文件路径')
@click.option('--bytecode-file', '-b', required=True, help='字节码文件路径')
@click.pass_context
def contract(ctx, connection_id: str, abi_file: str, bytecode_file: str):
    """部署智能合约"""
    blockchain_cli = ctx.obj['blockchain_cli']
    
    async def _deploy_contract():
        try:
            contract_address = await blockchain_cli.deploy_contract(connection_id, abi_file, bytecode_file)
            click.echo(f"合约部署成功: {contract_address}")
            
        except Exception as e:
            click.echo(f"部署合约失败: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_deploy_contract())


@blockchain.command()
@click.option('--connection-id', '-c', required=True, help='连接ID')
@click.option('--type', '-t', required=True, help='事件类型 (newHeads, logs等)')
@click.pass_context
def listen(ctx, connection_id: str, type: str):
    """监听区块链事件"""
    blockchain_cli = ctx.obj['blockchain_cli']
    
    async def _listen_events():
        try:
            await blockchain_cli.listen_events(connection_id, type)
            
        except KeyboardInterrupt:
            click.echo("\n监听已停止")
        except Exception as e:
            click.echo(f"监听事件失败: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_listen_events())


@blockchain.command()
@click.pass_context
def stats(ctx):
    """显示连接统计信息"""
    blockchain_cli = ctx.obj['blockchain_cli']
    
    async def _show_stats():
        try:
            stats = await blockchain_cli.get_connection_stats()
            click.echo("连接统计信息:")
            click.echo(json.dumps(stats, indent=2, ensure_ascii=False))
            
        except Exception as e:
            click.echo(f"获取统计信息失败: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_show_stats())


@blockchain.command()
@click.pass_context
def cleanup(ctx):
    """清理所有连接"""
    blockchain_cli = ctx.obj['blockchain_cli']
    
    async def _cleanup():
        try:
            await blockchain_cli.cleanup()
            click.echo("资源清理完成")
            
        except Exception as e:
            click.echo(f"清理失败: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(_cleanup())


if __name__ == "__main__":
    blockchain()
