#!/usr/bin/env python3
"""
安全管理器模块
负责处理敏感信息加密、输入验证和安全配置
"""

import os
import re
import json
import base64
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class SecurityManager:
    """安全管理器 - 处理敏感信息和安全配置"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        初始化安全管理器
        
        Args:
            encryption_key: 加密密钥，如果为None则从环境变量获取或生成
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.encryption_key = encryption_key or self._get_or_generate_key()
        self.cipher = Fernet(self.encryption_key)
        
    def _get_or_generate_key(self) -> str:
        """获取或生成加密密钥"""
        # 首先尝试从环境变量获取
        key = os.environ.get('AUTOTEST_ENCRYPTION_KEY')
        if key:
            return key
            
        # 尝试从配置文件获取
        config_file = Path.home() / '.autotest' / 'security.key'
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    return f.read().strip()
            except Exception as e:
                self.logger.warning(f"读取安全密钥失败: {e}")
        
        # 生成新的密钥
        new_key = Fernet.generate_key().decode()
        
        # 保存到配置文件
        try:
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w') as f:
                f.write(new_key)
            # 设置文件权限为仅所有者可读
            os.chmod(config_file, 0o600)
            self.logger.info("已生成新的安全密钥")
        except Exception as e:
            self.logger.warning(f"保存安全密钥失败: {e}")
            
        return new_key
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """
        加密敏感数据
        
        Args:
            data: 要加密的敏感数据
            
        Returns:
            str: 加密后的数据（base64编码）
        """
        try:
            encrypted_data = self.cipher.encrypt(data.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            self.logger.error(f"加密数据失败: {e}")
            raise ValueError(f"加密失败: {e}")
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """
        解密敏感数据
        
        Args:
            encrypted_data: 加密的数据（base64编码）
            
        Returns:
            str: 解密后的原始数据
        """
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            decrypted_data = self.cipher.decrypt(encrypted_bytes)
            return decrypted_data.decode()
        except Exception as e:
            self.logger.error(f"解密数据失败: {e}")
            raise ValueError(f"解密失败: {e}")
    
    def validate_api_endpoint(self, endpoint: str) -> bool:
        """
        验证API端点格式，防止路径遍历攻击
        
        Args:
            endpoint: API端点路径
            
        Returns:
            bool: 是否有效
        """
        if not endpoint or not isinstance(endpoint, str):
            return False
            
        # 防止路径遍历攻击
        if '..' in endpoint or '//' in endpoint:
            return False
            
        # 验证路径格式
        pattern = r'^/[a-zA-Z0-9\-_/{}]*$'
        return bool(re.match(pattern, endpoint))
    
    def sanitize_input(self, data: Union[str, dict, list]) -> Union[str, dict, list]:
        """
        清理输入数据，防止XSS和注入攻击
        
        Args:
            data: 输入数据
            
        Returns:
            Union[str, dict, list]: 清理后的数据
        """
        if isinstance(data, str):
            # 移除潜在的危险字符
            sanitized = re.sub(r'[<>"\']', '', data)
            # 移除控制字符
            sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)
            return sanitized
        elif isinstance(data, dict):
            return {k: self.sanitize_input(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_input(item) for item in data]
        return data
    
    def validate_json_input(self, json_str: str) -> bool:
        """
        验证JSON输入格式
        
        Args:
            json_str: JSON字符串
            
        Returns:
            bool: 是否有效
        """
        try:
            json.loads(json_str)
            return True
        except json.JSONDecodeError:
            return False
    
    def validate_url(self, url: str) -> bool:
        """
        验证URL格式
        
        Args:
            url: URL字符串
            
        Returns:
            bool: 是否有效
        """
        pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$'
        return bool(re.match(pattern, url))
    
    def mask_sensitive_info(self, data: str, sensitive_keys: list = None) -> str:
        """
        遮蔽敏感信息
        
        Args:
            data: 包含敏感信息的数据
            sensitive_keys: 敏感字段名列表
            
        Returns:
            str: 遮蔽后的数据
        """
        if sensitive_keys is None:
            sensitive_keys = ['password', 'token', 'key', 'secret', 'api_key']
        
        # 如果是JSON字符串，解析后遮蔽
        try:
            json_data = json.loads(data)
            masked_data = self._mask_json_sensitive_info(json_data, sensitive_keys)
            return json.dumps(masked_data, ensure_ascii=False, indent=2)
        except json.JSONDecodeError:
            # 如果不是JSON，直接遮蔽字符串
            return self._mask_string_sensitive_info(data, sensitive_keys)
    
    def _mask_json_sensitive_info(self, data: Any, sensitive_keys: list) -> Any:
        """递归遮蔽JSON中的敏感信息"""
        if isinstance(data, dict):
            masked = {}
            for key, value in data.items():
                if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
                    masked[key] = "***MASKED***"
                else:
                    masked[key] = self._mask_json_sensitive_info(value, sensitive_keys)
            return masked
        elif isinstance(data, list):
            return [self._mask_json_sensitive_info(item, sensitive_keys) for item in data]
        else:
            return data
    
    def _mask_string_sensitive_info(self, data: str, sensitive_keys: list) -> str:
        """遮蔽字符串中的敏感信息"""
        masked_data = data
        for key in sensitive_keys:
            # 使用正则表达式匹配并遮蔽敏感信息
            pattern = rf'({key}[=:]\s*)([^\s,}}]+)'
            masked_data = re.sub(pattern, r'\1***MASKED***', masked_data, flags=re.IGNORECASE)
        return masked_data
    
    def generate_secure_token(self, length: int = 32) -> str:
        """
        生成安全令牌
        
        Args:
            length: 令牌长度
            
        Returns:
            str: 安全令牌
        """
        import secrets
        import string
        
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def hash_password(self, password: str, salt: Optional[str] = None) -> tuple:
        """
        哈希密码
        
        Args:
            password: 原始密码
            salt: 盐值，如果为None则生成新的
            
        Returns:
            tuple: (哈希值, 盐值)
        """
        if salt is None:
            salt = os.urandom(16)
        else:
            salt = salt.encode() if isinstance(salt, str) else salt
            
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key.decode(), salt.hex()
    
    def verify_password(self, password: str, hashed_password: str, salt: str) -> bool:
        """
        验证密码
        
        Args:
            password: 原始密码
            hashed_password: 哈希后的密码
            salt: 盐值
            
        Returns:
            bool: 是否匹配
        """
        try:
            new_hash, _ = self.hash_password(password, bytes.fromhex(salt))
            return new_hash == hashed_password
        except Exception as e:
            self.logger.error(f"密码验证失败: {e}")
            return False


class SecureConfigManager:
    """安全配置管理器 - 处理配置文件中的敏感信息"""
    
    def __init__(self, config_path: str, security_manager: Optional[SecurityManager] = None):
        """
        初始化安全配置管理器
        
        Args:
            config_path: 配置文件路径
            security_manager: 安全管理器实例
        """
        self.config_path = Path(config_path)
        self.security_manager = security_manager or SecurityManager()
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def load_secure_config(self) -> Dict[str, Any]:
        """
        加载安全配置文件
        
        Returns:
            Dict[str, Any]: 配置数据
        """
        try:
            if not self.config_path.exists():
                self.logger.warning(f"配置文件不存在: {self.config_path}")
                return {}
                
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                
            # 解密敏感字段
            return self._decrypt_sensitive_fields(config_data)
            
        except Exception as e:
            self.logger.error(f"加载安全配置失败: {e}")
            return {}
    
    def save_secure_config(self, config_data: Dict[str, Any]) -> bool:
        """
        保存安全配置文件
        
        Args:
            config_data: 配置数据
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 加密敏感字段
            encrypted_config = self._encrypt_sensitive_fields(config_data)
            
            # 确保目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存配置文件
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(encrypted_config, f, ensure_ascii=False, indent=2)
                
            # 设置文件权限为仅所有者可读
            os.chmod(self.config_path, 0o600)
            
            self.logger.info(f"安全配置已保存: {self.config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存安全配置失败: {e}")
            return False
    
    def _encrypt_sensitive_fields(self, data: Any, sensitive_keys: list = None) -> Any:
        """递归加密敏感字段"""
        if sensitive_keys is None:
            sensitive_keys = ['password', 'token', 'key', 'secret', 'api_key', 'auth']
            
        if isinstance(data, dict):
            encrypted = {}
            for key, value in data.items():
                if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
                    if isinstance(value, str) and not value.startswith('ENCRYPTED:'):
                        encrypted[key] = f"ENCRYPTED:{self.security_manager.encrypt_sensitive_data(value)}"
                    else:
                        encrypted[key] = value
                else:
                    encrypted[key] = self._encrypt_sensitive_fields(value, sensitive_keys)
            return encrypted
        elif isinstance(data, list):
            return [self._encrypt_sensitive_fields(item, sensitive_keys) for item in data]
        else:
            return data
    
    def _decrypt_sensitive_fields(self, data: Any) -> Any:
        """递归解密敏感字段"""
        if isinstance(data, dict):
            decrypted = {}
            for key, value in data.items():
                if isinstance(value, str) and value.startswith('ENCRYPTED:'):
                    try:
                        encrypted_data = value[10:]  # 移除 'ENCRYPTED:' 前缀
                        decrypted[key] = self.security_manager.decrypt_sensitive_data(encrypted_data)
                    except Exception as e:
                        self.logger.warning(f"解密字段 {key} 失败: {e}")
                        decrypted[key] = value
                else:
                    decrypted[key] = self._decrypt_sensitive_fields(value)
            return decrypted
        elif isinstance(data, list):
            return [self._decrypt_sensitive_fields(item) for item in data]
        else:
            return data
