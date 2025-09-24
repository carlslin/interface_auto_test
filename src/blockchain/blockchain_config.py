"""
=============================================================================
接口自动化测试框架 - 区块链配置模块
=============================================================================

本模块提供了区块链相关的配置管理功能，支持多种区块链网络的配置。

主要功能：
1. 网络配置 - 预定义主流区块链网络配置
2. 环境配置 - 支持开发、测试、生产环境配置
3. 动态配置 - 支持配置的动态更新
4. 配置验证 - 配置参数验证和错误检查
5. 配置导出 - 支持配置的导出和导入

支持的配置类型：
- RPC节点配置
- 私钥配置
- Gas费配置
- 网络参数配置
- 测试参数配置

使用示例：
    # 加载区块链配置
    config = BlockchainConfig.load_config()
    
    # 获取网络配置
    ethereum_config = config.get_network_config("ethereum", "sepolia")
    
    # 更新配置
    config.update_network_config("ethereum", "sepolia", {"rpc_url": "new_url"})

作者: 接口自动化测试框架团队
版本: 1.0.0
更新日期: 2024年12月
=============================================================================
"""

import json
import logging
import os
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class NetworkConfig:
    """网络配置数据类"""
    name: str
    rpc_url: str
    chain_id: Optional[int] = None
    explorer_url: Optional[str] = None
    is_testnet: bool = False
    gas_price_gwei: float = 20.0
    gas_limit: int = 21000
    timeout: int = 30
    retry_count: int = 3
    username: Optional[str] = None
    password: Optional[str] = None
    custom_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BlockchainConfig:
    """区块链配置数据类"""
    networks: Dict[str, Dict[str, NetworkConfig]] = field(default_factory=dict)
    default_network: str = "ethereum"
    default_env: str = "testnet"
    encryption_key: Optional[str] = None
    test_settings: Dict[str, Any] = field(default_factory=dict)
    
    # 预定义网络配置
    PREDEFINED_NETWORKS = {
        "ethereum": {
            "mainnet": NetworkConfig(
                name="Ethereum Mainnet",
                rpc_url="https://mainnet.infura.io/v3/YOUR_KEY",
                chain_id=1,
                explorer_url="https://etherscan.io",
                is_testnet=False,
                gas_price_gwei=20.0
            ),
            "sepolia": NetworkConfig(
                name="Ethereum Sepolia Testnet",
                rpc_url="https://sepolia.infura.io/v3/YOUR_KEY",
                chain_id=11155111,
                explorer_url="https://sepolia.etherscan.io",
                is_testnet=True,
                gas_price_gwei=1.0
            ),
            "goerli": NetworkConfig(
                name="Ethereum Goerli Testnet",
                rpc_url="https://goerli.infura.io/v3/YOUR_KEY",
                chain_id=5,
                explorer_url="https://goerli.etherscan.io",
                is_testnet=True,
                gas_price_gwei=1.0
            ),
            "holesky": NetworkConfig(
                name="Ethereum Holesky Testnet",
                rpc_url="https://holesky.infura.io/v3/YOUR_KEY",
                chain_id=17000,
                explorer_url="https://holesky.etherscan.io",
                is_testnet=True,
                gas_price_gwei=1.0
            )
        },
        "bsc": {
            "mainnet": NetworkConfig(
                name="BSC Mainnet",
                rpc_url="https://bsc-dataseed.binance.org",
                chain_id=56,
                explorer_url="https://bscscan.com",
                is_testnet=False,
                gas_price_gwei=5.0
            ),
            "testnet": NetworkConfig(
                name="BSC Testnet",
                rpc_url="https://data-seed-prebsc-1-s1.binance.org:8545",
                chain_id=97,
                explorer_url="https://testnet.bscscan.com",
                is_testnet=True,
                gas_price_gwei=10.0
            )
        },
        "polygon": {
            "mainnet": NetworkConfig(
                name="Polygon Mainnet",
                rpc_url="https://polygon-rpc.com",
                chain_id=137,
                explorer_url="https://polygonscan.com",
                is_testnet=False,
                gas_price_gwei=30.0
            ),
            "mumbai": NetworkConfig(
                name="Polygon Mumbai Testnet",
                rpc_url="https://rpc-mumbai.maticvigil.com",
                chain_id=80001,
                explorer_url="https://mumbai.polygonscan.com",
                is_testnet=True,
                gas_price_gwei=1.0
            )
        },
        "arbitrum": {
            "mainnet": NetworkConfig(
                name="Arbitrum One",
                rpc_url="https://arb1.arbitrum.io/rpc",
                chain_id=42161,
                explorer_url="https://arbiscan.io",
                is_testnet=False,
                gas_price_gwei=0.1
            ),
            "goerli": NetworkConfig(
                name="Arbitrum Goerli Testnet",
                rpc_url="https://goerli-rollup.arbitrum.io/rpc",
                chain_id=421613,
                explorer_url="https://goerli.arbiscan.io",
                is_testnet=True,
                gas_price_gwei=0.1
            )
        },
        "optimism": {
            "mainnet": NetworkConfig(
                name="Optimism Mainnet",
                rpc_url="https://mainnet.optimism.io",
                chain_id=10,
                explorer_url="https://optimistic.etherscan.io",
                is_testnet=False,
                gas_price_gwei=0.001
            ),
            "goerli": NetworkConfig(
                name="Optimism Goerli Testnet",
                rpc_url="https://goerli.optimism.io",
                chain_id=420,
                explorer_url="https://goerli-optimism.etherscan.io",
                is_testnet=True,
                gas_price_gwei=0.001
            )
        },
        "bitcoin": {
            "mainnet": NetworkConfig(
                name="Bitcoin Mainnet",
                rpc_url="http://localhost:8332",
                explorer_url="https://blockstream.info",
                is_testnet=False,
                timeout=60
            ),
            "testnet": NetworkConfig(
                name="Bitcoin Testnet",
                rpc_url="http://localhost:18332",
                explorer_url="https://blockstream.info/testnet",
                is_testnet=True,
                timeout=60
            ),
            "regtest": NetworkConfig(
                name="Bitcoin Regtest",
                rpc_url="http://localhost:18443",
                explorer_url="Local",
                is_testnet=True,
                timeout=60
            )
        }
    }
    
    @classmethod
    def load_config(cls, config_path: Optional[str] = None) -> 'BlockchainConfig':
        """
        加载区块链配置
        
        Args:
            config_path: 配置文件路径（可选）
            
        Returns:
            BlockchainConfig: 区块链配置对象
        """
        logger = logging.getLogger(cls.__name__)
        
        try:
            # 确定配置文件路径
            if config_path is None:
                # 默认配置文件路径
                current_dir = Path(__file__).parent.parent.parent
                config_path = current_dir / "config" / "blockchain.yaml"
            
            config_path = Path(config_path)
            
            # 加载配置文件
            if config_path.exists():
                if config_path.suffix.lower() == '.json':
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                else:
                    # 尝试加载YAML
                    try:
                        import yaml
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config_data = yaml.safe_load(f)
                    except ImportError:
                        logger.warning("PyYAML未安装，使用默认配置")
                        config_data = {}
            else:
                logger.info(f"配置文件不存在: {config_path}，使用默认配置")
                config_data = {}
            
            # 创建配置对象
            config = cls()
            
            # 加载网络配置
            if 'networks' in config_data:
                for blockchain, environments in config_data['networks'].items():
                    config.networks[blockchain] = {}
                    for env, network_data in environments.items():
                        config.networks[blockchain][env] = NetworkConfig(**network_data)
            else:
                # 使用预定义配置
                config.networks = cls.PREDEFINED_NETWORKS.copy()
            
            # 加载其他配置
            config.default_network = config_data.get('default_network', 'ethereum')
            config.default_env = config_data.get('default_env', 'testnet')
            config.encryption_key = config_data.get('encryption_key')
            config.test_settings = config_data.get('test_settings', {})
            
            # 应用环境变量覆盖
            config._apply_env_overrides()
            
            logger.info(f"区块链配置已加载: {config_path}")
            return config
            
        except Exception as e:
            logger.error(f"加载区块链配置失败: {e}")
            # 返回默认配置
            config = cls()
            config.networks = cls.PREDEFINED_NETWORKS.copy()
            return config
    
    def _apply_env_overrides(self) -> None:
        """应用环境变量覆盖"""
        try:
            # 常见的环境变量覆盖
            env_overrides = {
                'ETHEREUM_RPC_URL': ('ethereum', 'sepolia', 'rpc_url'),
                'BSC_RPC_URL': ('bsc', 'testnet', 'rpc_url'),
                'POLYGON_RPC_URL': ('polygon', 'mumbai', 'rpc_url'),
                'ARBITRUM_RPC_URL': ('arbitrum', 'goerli', 'rpc_url'),
                'OPTIMISM_RPC_URL': ('optimism', 'goerli', 'rpc_url'),
                'BITCOIN_RPC_URL': ('bitcoin', 'testnet', 'rpc_url'),
                'BITCOIN_RPC_USER': ('bitcoin', 'testnet', 'username'),
                'BITCOIN_RPC_PASS': ('bitcoin', 'testnet', 'password'),
                'BLOCKCHAIN_ENCRYPTION_KEY': ('', '', 'encryption_key')
            }
            
            for env_var, (blockchain, env, param) in env_overrides.items():
                env_value = os.getenv(env_var)
                if env_value is not None:
                    if blockchain and env:
                        # 网络参数覆盖
                        if blockchain in self.networks and env in self.networks[blockchain]:
                            setattr(self.networks[blockchain][env], param, env_value)
                    elif param == 'encryption_key':
                        # 全局参数覆盖
                        self.encryption_key = env_value
                        
        except Exception as e:
            self.logger.error(f"应用环境变量覆盖失败: {e}")
    
    def get_network_config(self, blockchain: str, environment: str) -> Optional[NetworkConfig]:
        """
        获取网络配置
        
        Args:
            blockchain: 区块链名称
            environment: 环境名称
            
        Returns:
            Optional[NetworkConfig]: 网络配置
        """
        try:
            if blockchain in self.networks and environment in self.networks[blockchain]:
                return self.networks[blockchain][environment]
            return None
        except Exception as e:
            self.logger.error(f"获取网络配置失败: {e}")
            return None
    
    def update_network_config(self, blockchain: str, environment: str, 
                            updates: Dict[str, Any]) -> bool:
        """
        更新网络配置
        
        Args:
            blockchain: 区块链名称
            environment: 环境名称
            updates: 更新参数
            
        Returns:
            bool: 是否更新成功
        """
        try:
            if blockchain not in self.networks:
                self.networks[blockchain] = {}
            
            if environment not in self.networks[blockchain]:
                # 创建新的网络配置
                self.networks[blockchain][environment] = NetworkConfig(
                    name=f"{blockchain} {environment}",
                    rpc_url=updates.get('rpc_url', ''),
                    **updates
                )
            else:
                # 更新现有配置
                config = self.networks[blockchain][environment]
                for key, value in updates.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
                    else:
                        config.custom_params[key] = value
            
            self.logger.info(f"网络配置已更新: {blockchain}.{environment}")
            return True
            
        except Exception as e:
            self.logger.error(f"更新网络配置失败: {e}")
            return False
    
    def list_networks(self) -> Dict[str, List[str]]:
        """
        列出所有网络
        
        Returns:
            Dict[str, List[str]]: 网络列表
        """
        try:
            result = {}
            for blockchain, environments in self.networks.items():
                result[blockchain] = list(environments.keys())
            return result
        except Exception as e:
            self.logger.error(f"列出网络失败: {e}")
            return {}
    
    def get_supported_blockchains(self) -> List[str]:
        """
        获取支持的区块链列表
        
        Returns:
            List[str]: 支持的区块链列表
        """
        return list(self.networks.keys())
    
    def get_testnet_configs(self) -> Dict[str, NetworkConfig]:
        """
        获取所有测试网配置
        
        Returns:
            Dict[str, NetworkConfig]: 测试网配置
        """
        try:
            testnet_configs = {}
            for blockchain, environments in self.networks.items():
                for env, config in environments.items():
                    if config.is_testnet:
                        key = f"{blockchain}_{env}"
                        testnet_configs[key] = config
            return testnet_configs
        except Exception as e:
            self.logger.error(f"获取测试网配置失败: {e}")
            return {}
    
    def get_mainnet_configs(self) -> Dict[str, NetworkConfig]:
        """
        获取所有主网配置
        
        Returns:
            Dict[str, NetworkConfig]: 主网配置
        """
        try:
            mainnet_configs = {}
            for blockchain, environments in self.networks.items():
                for env, config in environments.items():
                    if not config.is_testnet:
                        key = f"{blockchain}_{env}"
                        mainnet_configs[key] = config
            return mainnet_configs
        except Exception as e:
            self.logger.error(f"获取主网配置失败: {e}")
            return {}
    
    def save_config(self, config_path: Optional[str] = None) -> bool:
        """
        保存配置到文件
        
        Args:
            config_path: 配置文件路径（可选）
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 确定配置文件路径
            if config_path is None:
                current_dir = Path(__file__).parent.parent.parent
                config_path = current_dir / "config" / "blockchain.yaml"
            
            config_path = Path(config_path)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 准备配置数据
            config_data = {
                'default_network': self.default_network,
                'default_env': self.default_env,
                'encryption_key': self.encryption_key,
                'test_settings': self.test_settings,
                'networks': {}
            }
            
            # 添加网络配置
            for blockchain, environments in self.networks.items():
                config_data['networks'][blockchain] = {}
                for env, config in environments.items():
                    config_dict = {
                        'name': config.name,
                        'rpc_url': config.rpc_url,
                        'chain_id': config.chain_id,
                        'explorer_url': config.explorer_url,
                        'is_testnet': config.is_testnet,
                        'gas_price_gwei': config.gas_price_gwei,
                        'gas_limit': config.gas_limit,
                        'timeout': config.timeout,
                        'retry_count': config.retry_count,
                        'username': config.username,
                        'password': config.password,
                        'custom_params': config.custom_params
                    }
                    config_data['networks'][blockchain][env] = config_dict
            
            # 保存配置文件
            if config_path.suffix.lower() == '.json':
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
            else:
                # 保存为YAML
                try:
                    import yaml
                    with open(config_path, 'w', encoding='utf-8') as f:
                        yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
                except ImportError:
                    self.logger.warning("PyYAML未安装，保存为JSON格式")
                    config_path = config_path.with_suffix('.json')
                    with open(config_path, 'w', encoding='utf-8') as f:
                        json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"配置已保存: {config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            return False
    
    def validate_config(self) -> Dict[str, Any]:
        """
        验证配置
        
        Returns:
            Dict[str, Any]: 验证结果
        """
        try:
            validation_result = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "network_count": 0,
                "testnet_count": 0,
                "mainnet_count": 0
            }
            
            # 验证网络配置
            for blockchain, environments in self.networks.items():
                for env, config in environments.items():
                    validation_result["network_count"] += 1
                    
                    if config.is_testnet:
                        validation_result["testnet_count"] += 1
                    else:
                        validation_result["mainnet_count"] += 1
                    
                    # 检查必要字段
                    if not config.rpc_url:
                        validation_result["errors"].append(f"{blockchain}.{env}: RPC URL为空")
                        validation_result["valid"] = False
                    
                    if config.chain_id is None and blockchain != 'bitcoin':
                        validation_result["warnings"].append(f"{blockchain}.{env}: 未设置Chain ID")
                    
                    if config.gas_price_gwei <= 0:
                        validation_result["warnings"].append(f"{blockchain}.{env}: Gas价格设置异常")
            
            # 检查默认网络
            if self.default_network not in self.networks:
                validation_result["errors"].append(f"默认网络不存在: {self.default_network}")
                validation_result["valid"] = False
            
            if (self.default_network in self.networks and 
                self.default_env not in self.networks[self.default_network]):
                validation_result["errors"].append(f"默认环境不存在: {self.default_network}.{self.default_env}")
                validation_result["valid"] = False
            
            self.logger.info(f"配置验证完成: {'通过' if validation_result['valid'] else '失败'}")
            return validation_result
            
        except Exception as e:
            self.logger.error(f"配置验证失败: {e}")
            return {
                "valid": False,
                "errors": [str(e)],
                "warnings": [],
                "network_count": 0,
                "testnet_count": 0,
                "mainnet_count": 0
            }
