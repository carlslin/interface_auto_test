"""
配置加载器模块
负责加载和管理配置文件
"""

from __future__ import annotations

import os
import yaml
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from .data_manager import DataManager


class ConfigLoader:
    """配置加载器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置加载器
        
        Args:
            config_path: 配置文件路径
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config_data: Dict[str, Any] = {}
        self.current_env = "dev"
        self.data_manager = DataManager()
        
        # 确定配置文件路径
        if config_path:
            self.config_path = Path(config_path)
        else:
            # 默认配置文件路径
            current_dir = Path(__file__).parent.parent.parent
            self.config_path = current_dir / "config" / "default.yaml"
            
        self.load_config()
        
    def load_config(self):
        """加载配置文件"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config_data = yaml.safe_load(f) or {}
                self.logger.info(f"配置文件加载成功: {self.config_path}")
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
        

            
