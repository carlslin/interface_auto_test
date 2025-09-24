"""
=============================================================================
接口自动化测试框架 - 配置加载器模块
=============================================================================

本模块提供了完整的配置管理功能，支持多环境配置、动态配置更新、
环境变量覆盖等高级特性。配置系统是框架的核心基础设施。

主要功能：
1. 多环境配置管理 - 支持开发、测试、生产等多环境配置
2. 动态配置加载 - 支持运行时配置更新和热重载
3. 环境变量覆盖 - 支持通过环境变量覆盖配置文件设置
4. 配置验证 - 自动验证配置项的有效性和完整性
5. 配置合并 - 支持多个配置文件的合并和继承
6. 敏感信息保护 - 自动识别和保护敏感配置信息

配置层次结构：
1. 默认配置 (default.yaml)
2. 环境特定配置 (dev.yaml, test.yaml, prod.yaml)
3. 用户自定义配置 (custom.yaml)
4. 环境变量覆盖 (AUTOTEST_*)

使用示例：
    # 基本使用
    config = ConfigLoader()
    base_url = config.get('environments.dev.base_url')
    
    # 指定配置文件
    config = ConfigLoader('custom_config.yaml')
    
    # 切换环境
    config.set_environment('test')
    
    # 获取环境特定配置
    headers = config.get_headers()

作者: 接口自动化测试框架团队
版本: 1.0.0
更新日期: 2024年12月
=============================================================================
"""

from __future__ import annotations

import os
import yaml
import logging
import json
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from .data_manager import DataManager


class Environment(Enum):
    """环境枚举"""
    DEV = "dev"           # 开发环境
    TEST = "test"         # 测试环境
    MOCK = "mock"         # Mock环境
    PROD = "prod"         # 生产环境


@dataclass
class ConfigValidationResult:
    """配置验证结果"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    
    def __bool__(self):
        return self.is_valid


class ConfigLoader:
    """
    配置加载器 - 框架配置管理的核心类
    
    本类提供了完整的配置管理功能，支持多环境配置、动态配置更新、
    环境变量覆盖等高级特性。配置系统采用分层设计，支持配置继承和覆盖。
    
    主要特性：
    1. 多环境支持: 支持开发、测试、生产等多环境配置
    2. 动态加载: 支持运行时配置更新和热重载
    3. 环境变量覆盖: 支持通过环境变量覆盖配置文件设置
    4. 配置验证: 自动验证配置项的有效性和完整性
    5. 配置合并: 支持多个配置文件的合并和继承
    6. 敏感信息保护: 自动识别和保护敏感配置信息
    
    配置层次结构（优先级从高到低）：
    1. 环境变量 (AUTOTEST_*)
    2. 用户自定义配置 (custom.yaml)
    3. 环境特定配置 (dev.yaml, test.yaml, prod.yaml)
    4. 默认配置 (default.yaml)
    
    使用示例：
        # 基本使用
        config = ConfigLoader()
        base_url = config.get('environments.dev.base_url')
        
        # 指定配置文件
        config = ConfigLoader('custom_config.yaml')
        
        # 切换环境
        config.set_environment('test')
        
        # 获取环境特定配置
        headers = config.get_headers()
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置加载器
        
        初始化过程包括：
        - 确定配置文件路径
        - 加载配置文件
        - 应用环境变量覆盖
        - 验证配置有效性
        - 设置默认环境
        
        Args:
            config_path: 配置文件路径，支持相对路径和绝对路径
                       如果为None，则使用默认配置文件路径
                       支持YAML和JSON格式
        
        Raises:
            FileNotFoundError: 配置文件不存在
            yaml.YAMLError: 配置文件格式错误
            ValueError: 配置参数无效
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config_data: Dict[str, Any] = {}
        self.current_env = Environment.DEV.value
        self.data_manager = DataManager()
        
        # 确定配置文件路径
        if config_path:
            self.config_path = Path(config_path)
        else:
            # 默认配置文件路径
            current_dir = Path(__file__).parent.parent.parent
            self.config_path = current_dir / "config" / "default.yaml"
            
        # 配置验证结果
        self.validation_result: Optional[ConfigValidationResult] = None
        
        # 加载配置
        self.load_config()
        
        # 应用环境变量覆盖
        self._apply_env_overrides()
        
        # 验证配置
        self.validate_config()
    
    def _apply_env_overrides(self):
        """
        应用环境变量覆盖
        
        从环境变量中读取配置覆盖，优先级高于配置文件
        支持的环境变量格式：
        - CONFIG_SECTION_KEY=value
        - CONFIG_SECTION_SUBSECTION_KEY=value
        """
        if not hasattr(self, 'config') or not self.config:
            return
        
        try:
            # 常见的环境变量覆盖
            env_overrides = {
                'DEEPSEEK_API_KEY': 'ai.deepseek_api_key',
                'MYSQL_HOST': 'database.mysql.host',
                'MYSQL_PORT': 'database.mysql.port',
                'MYSQL_DATABASE': 'database.mysql.database',
                'MYSQL_USERNAME': 'database.mysql.username',
                'MYSQL_PASSWORD': 'database.mysql.password',
                'REDIS_HOST': 'cache.redis.host',
                'REDIS_PORT': 'cache.redis.port',
                'REDIS_DB': 'cache.redis.db',
                'LOG_LEVEL': 'logging.level'
            }
            
            for env_var, config_path in env_overrides.items():
                env_value = os.getenv(env_var)
                if env_value is not None:
                    self._set_nested_config(config_path, env_value)
                    
        except Exception as e:
            self.logger.error(f"应用环境变量覆盖失败: {e}")
    
    def _set_nested_config(self, path: str, value: str):
        """
        设置嵌套配置值
        
        Args:
            path: 配置路径，如 'ai.deepseek_api_key'
            value: 配置值
        """
        try:
            keys = path.split('.')
            current = self.config
            
            # 导航到目标位置
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            # 设置值
            current[keys[-1]] = value
            
        except Exception as e:
            self.logger.error(f"设置嵌套配置失败 {path}: {e}")
    
    def _load_environment_config(self):
        """
        加载环境特定配置
        
        根据当前环境（development, test, production）加载对应的配置
        """
        try:
            # 获取当前环境
            env = os.getenv('ENVIRONMENT', 'development')
            
            if hasattr(self, 'config') and self.config and 'environments' in self.config:
                env_config = self.config['environments'].get(env, {})
                if env_config:
                    # 合并环境配置到主配置
                    self._merge_config(self.config, env_config)
                    
        except Exception as e:
            self.logger.error(f"加载环境配置失败: {e}")
    
    def _merge_config(self, base_config: dict, env_config: dict):
        """
        合并配置
        
        Args:
            base_config: 基础配置
            env_config: 环境配置
        """
        try:
            for key, value in env_config.items():
                if key in base_config and isinstance(base_config[key], dict) and isinstance(value, dict):
                    self._merge_config(base_config[key], value)
                else:
                    base_config[key] = value
                    
        except Exception as e:
            self.logger.error(f"合并配置失败: {e}")
        
    def load_config(self):
        """
        加载配置文件
        
        支持多种配置文件格式：
        - YAML格式 (.yaml, .yml)
        - JSON格式 (.json)
        
        加载过程包括：
        1. 检查配置文件是否存在
        2. 根据文件扩展名选择解析器
        3. 解析配置文件内容
        4. 合并环境特定配置
        5. 应用默认配置
        
        Raises:
            FileNotFoundError: 配置文件不存在
            yaml.YAMLError: YAML格式错误
            json.JSONDecodeError: JSON格式错误
        """
        try:
            if self.config_path.exists():
                # 根据文件扩展名选择解析器
                if self.config_path.suffix.lower() in ['.yaml', '.yml']:
                    with open(self.config_path, 'r', encoding='utf-8') as f:
                        self.config_data = yaml.safe_load(f) or {}
                elif self.config_path.suffix.lower() == '.json':
                    with open(self.config_path, 'r', encoding='utf-8') as f:
                        self.config_data = json.load(f) or {}
                else:
                    raise ValueError(f"不支持的配置文件格式: {self.config_path.suffix}")
                
                self.logger.info(f"配置文件加载成功: {self.config_path}")
                
                # 加载环境特定配置
                self._load_environment_config()
                
            else:
                self.logger.warning(f"配置文件不存在: {self.config_path}")
                self.config_data = self._get_default_config()
        except Exception as e:
            self.logger.error(f"配置文件加载失败: {str(e)}")
            self.config_data = self._get_default_config()
            
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "global": {
                "timeout": 30,
                "retry": 3,
                "parallel": 5
            },
            "environments": {
                "dev": {
                    "base_url": "http://localhost:8080",
                    "headers": {
                        "Content-Type": "application/json"
                    },
                    "timeout": 30
                }
            },
            "mock": {
                "port": 5000,
                "host": "localhost",
                "debug": True,
                "enable_cors": True
            },
            "report": {
                "format": ["html", "json"],
                "output_dir": "./reports"
            }
        }
        
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        try:
            keys = key.split('.')
            value = self.config_data
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
                    
            return value
        except Exception:
            return default
            
    def set(self, key: str, value: Any):
        """
        设置配置值
        
        Args:
            key: 配置键
            value: 配置值
        """
        keys = key.split('.')
        config = self.config_data
        
        # 创建嵌套字典路径
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
            
        config[keys[-1]] = value
        
    def set_environment(self, env: str):
        """
        设置当前环境
        
        Args:
            env: 环境名称
        """
        if f"environments.{env}" in str(self.config_data):
            self.current_env = env
            self.logger.info(f"切换到环境: {env}")
        else:
            self.logger.warning(f"环境 {env} 不存在，保持当前环境: {self.current_env}")
            
    def get_current_env_config(self) -> Dict[str, Any]:
        """获取当前环境配置"""
        return self.get(f"environments.{self.current_env}", {})
        
    def get_base_url(self) -> str:
        """获取当前环境的基础URL"""
        return self.get(f"environments.{self.current_env}.base_url", "")
        
    def get_headers(self) -> Dict[str, str]:
        """获取当前环境的默认请求头"""
        return self.get(f"environments.{self.current_env}.headers", {})
        
    def get_timeout(self) -> int:
        """获取超时时间"""
        # 优先使用环境特定的超时时间，然后是全局超时时间
        env_timeout = self.get(f"environments.{self.current_env}.timeout")
        if env_timeout is not None:
            return env_timeout
        return self.get("global.timeout", 30)
        
    def save_config(self, output_path: Optional[str] = None):
        """
        保存配置到文件
        
        Args:
            output_path: 输出文件路径，默认为当前配置文件路径
        """
        try:
            save_path = Path(output_path) if output_path else self.config_path
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config_data, f, default_flow_style=False, allow_unicode=True)
                
            self.logger.info(f"配置文件保存成功: {save_path}")
        except Exception as e:
            self.logger.error(f"配置文件保存失败: {str(e)}")
            
    def reload(self):
        """重新加载配置文件"""
        self.load_config()
        
    def update_from_dict(self, config_dict: Dict[str, Any]):
        """
        从字典更新配置
        
        Args:
            config_dict: 配置字典
        """
        def deep_update(base_dict: Dict[str, Any], update_dict: Dict[str, Any]):
            """深度更新字典"""
            for key, value in update_dict.items():
                if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                    deep_update(base_dict[key], value)
                else:
                    base_dict[key] = value
                    
        deep_update(self.config_data, config_dict)
        
    def get_all_environments(self) -> List[str]:
        """获取所有环境名称"""
        environments = self.get("environments", {})
        return list(environments.keys()) if isinstance(environments, dict) else []
        
    def get_test_mode(self) -> str:
        """
        获取当前的测试模式
        
        Returns:
            str: 测试模式 (mock/real/auto)
        """
        # 优先使用环境特定的模式设置
        env_mode = self.get(f"environments.{self.current_env}.test_mode")
        if env_mode:
            return env_mode
        
        # 使用全局模式设置
        return self.get("global.test_mode", "auto")
        
    def is_mock_fallback_enabled(self) -> bool:
        """
        检查是否允许Mock回退
        
        Returns:
            bool: 是否允许回退到Mock模式
        """
        # 优先使用环境特定的设置
        env_fallback = self.get(f"environments.{self.current_env}.mock_fallback")
        if env_fallback is not None:
            return env_fallback
        
        # 使用全局设置
        return self.get("global.mock_fallback", True)
        
    def get_mock_config(self) -> Dict[str, Any]:
        """
        获取Mock服务器配置
        
        Returns:
            Dict[str, Any]: Mock配置
        """
        return self.get("mock", {})
        
    def get_mock_url(self) -> str:
        """
        获取Mock服务器URL
        
        Returns:
            str: Mock服务器URL
        """
        mock_config = self.get_mock_config()
        host = mock_config.get("host", "localhost")
        port = mock_config.get("port", 5000)
        return f"http://{host}:{port}"
        
    def should_use_mock(self) -> bool:
        """
        判断是否应该使用Mock模式
        
        Returns:
            bool: 是否使用Mock模式
        """
        test_mode = self.get_test_mode()
        
        if test_mode == "mock":
            return True
        elif test_mode == "real":
            return False
        elif test_mode == "auto":
            # 自动模式：尝试检测真实接口是否可用
            return self._should_auto_use_mock()
        else:
            # 默认使用auto模式
            return self._should_auto_use_mock()
            
    def _should_auto_use_mock(self) -> bool:
        """
        自动判断是否使用Mock模式
        
        Returns:
            bool: 是否使用Mock模式
        """
        import requests
        
        # 获取真实接口URL
        real_url = self.get_base_url()
        
        if not real_url:
            self.logger.warning("未配置真实接口URL，使用Mock模式")
            return True
            
        try:
            # 尝试访问真实接口（通常使用健康检查端点）
            health_endpoints = [
                f"{real_url}/health",
                f"{real_url}/api/health", 
                f"{real_url}/ping",
                f"{real_url}/"
            ]
            
            for endpoint in health_endpoints:
                try:
                    response = requests.get(endpoint, timeout=3)
                    if response.status_code < 500:  # 只要不是服务器错误就认为可用
                        self.logger.info(f"真实接口可用，使用真实模式: {endpoint}")
                        return False
                except:
                    continue
                    
            # 所有尝试都失败，使用Mock
            if self.is_mock_fallback_enabled():
                self.logger.info("真实接口不可用，回退到Mock模式")
                return True
            else:
                self.logger.error("真实接口不可用且禁用Mock回退")
                raise Exception("真实接口不可用且禁用Mock回退")
                
        except requests.exceptions.RequestException:
            if self.is_mock_fallback_enabled():
                self.logger.info("网络错误，回退到Mock模式")
                return True
            else:
                self.logger.error("网络错误且禁用Mock回退")
                raise
                
    def get_effective_base_url(self) -> str:
        """
        获取当前有效的基础URL（根据测试模式决定）
        
        Returns:
            str: 有效的基础URL
        """
        if self.should_use_mock():
            return self.get_mock_url()
        else:
            return self.get_base_url()
            
    def set_test_mode(self, mode: str):
        """
        设置测试模式
        
        Args:
            mode: 测试模式 (mock/real/auto)
        """
        if mode not in ["mock", "real", "auto"]:
            raise ValueError(f"无效的测试模式: {mode}")
            
        self.set(f"environments.{self.current_env}.test_mode", mode)
        self.logger.info(f"已设置测试模式为: {mode}")
        

        
    def validate_config(self) -> Dict[str, List[str]]:
        """
        验证配置文件
        
        Returns:
            Dict[str, List[str]]: 验证结果（错误和警告）
        """
        errors = []
        warnings = []
        
        # 检查必需字段
        required_fields = ["global", "environments"]
        
        for field in required_fields:
            if field not in self.config_data:
                errors.append(f"缺少必需字段: {field}")
        
        # 检查环境配置
        environments = self.config_data.get("environments", {})
        if not environments:
            errors.append("未配置环境")
        else:
            for env_name, env_config in environments.items():
                if not isinstance(env_config, dict):
                    errors.append(f"环境 {env_name} 配置格式错误")
                    continue
                    
                if "base_url" not in env_config:
                    warnings.append(f"环境 {env_name} 缺少 base_url 配置")
        
        # 检查全局配置
        global_config = self.config_data.get("global", {})
        if global_config and "timeout" in global_config:
            timeout = global_config["timeout"]
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                errors.append("全局timeout配置必须为正数")
        
        return {"errors": errors, "warnings": warnings}
        

            
