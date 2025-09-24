#!/usr/bin/env python3
"""
认证管理器 - 处理各种认证方式和依赖场景
"""

import os
import json
import yaml
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pathlib import Path
import requests
from datetime import datetime, timedelta


class AuthStrategy(ABC):
    """认证策略抽象基类"""
    
    @abstractmethod
    def authenticate(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """执行认证，返回认证信息"""
        pass
    
    @abstractmethod
    def is_valid(self, auth_data: Dict[str, Any]) -> bool:
        """检查认证是否有效"""
        pass
    
    @abstractmethod
    def refresh_if_needed(self, auth_data: Dict[str, Any]) -> Dict[str, Any]:
        """如果需要，刷新认证"""
        pass


class BearerTokenAuth(AuthStrategy):
    """Bearer Token认证策略"""
    
    def authenticate(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """执行Bearer Token认证"""
        login_url = config.get('login_url')
        username = config.get('username')
        user_password = config.get('password')
        
        if not all([login_url, username, password]):
            raise ValueError("Bearer Token认证缺少必要参数: login_url, username, password")
        
        # 类型检查
        if not isinstance(login_url, str):
            raise ValueError("login_url 必须是字符串")
        
        try:
            response = requests.post(login_url, json={
                'username': username,
                'password': password
            }, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                token = result.get('token') or result.get('access_token')
                if not token:
                    raise ValueError("认证响应中未找到token字段")
                
                return {
                    'type': 'bearer',
                    'token': token,
                    'expires_at': datetime.now() + timedelta(hours=config.get('token_ttl', 24)),
                    'refresh_token': result.get('refresh_token'),
                    'headers': {'Authorization': f'Bearer {token}'}
                }
            else:
                raise ValueError(f"认证失败: HTTP {response.status_code} - {response.text}")
                
        except Exception as e:
            raise ValueError(f"Bearer Token认证失败: {str(e)}")
    
    def is_valid(self, auth_data: Dict[str, Any]) -> bool:
        """检查Token是否有效"""
        if not auth_data.get('token'):
            return False
        
        expires_at = auth_data.get('expires_at')
        if expires_at and datetime.now() > expires_at:
            return False
        
        return True
    
    def refresh_if_needed(self, auth_data: Dict[str, Any]) -> Dict[str, Any]:
        """刷新Token"""
        if self.is_valid(auth_data):
            return auth_data
        
        refresh_token = auth_data.get('refresh_token')
        if not refresh_token:
            raise ValueError("无法刷新Token: 缺少refresh_token")
        
        # 这里应该实现Token刷新逻辑
        # 返回新的认证数据
        return auth_data


class BasicAuth(AuthStrategy):
    """Basic认证策略"""
    
    def authenticate(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """执行Basic认证"""
        username = config.get('username')
        user_password = config.get('password')
        
        if not all([username, password]):
            raise ValueError("Basic认证缺少必要参数: username, password")
        
        import base64
        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
        
        return {
            'type': 'basic',
            'username': username,
            'password': password,
            'headers': {'Authorization': f'Basic {credentials}'}
        }
    
    def is_valid(self, auth_data: Dict[str, Any]) -> bool:
        """Basic认证通常不会过期"""
        return bool(auth_data.get('username') and auth_data.get('password'))
    
    def refresh_if_needed(self, auth_data: Dict[str, Any]) -> Dict[str, Any]:
        """Basic认证不需要刷新"""
        return auth_data


class ApiKeyAuth(AuthStrategy):
    """API Key认证策略"""
    
    def authenticate(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """执行API Key认证"""
        api_key = config.get('api_key')
        header_name = config.get('header_name', 'X-API-Key')
        
        if not api_key:
            raise ValueError("API Key认证缺少必要参数: api_key")
        
        return {
            'type': 'api_key',
            'api_key': api_key,
            'header_name': header_name,
            'headers': {header_name: api_key}
        }
    
    def is_valid(self, auth_data: Dict[str, Any]) -> bool:
        """检查API Key是否存在"""
        return bool(auth_data.get('api_key'))
    
    def refresh_if_needed(self, auth_data: Dict[str, Any]) -> Dict[str, Any]:
        """API Key通常不需要刷新"""
        return auth_data


class OAuth2Auth(AuthStrategy):
    """OAuth2认证策略"""
    
    def authenticate(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """执行OAuth2认证"""
        client_id = config.get('client_id')
        client_secret = config.get('client_secret')
        token_url = config.get('token_url')
        grant_type = config.get('grant_type', 'client_credentials')
        
        if not all([client_id, client_secret, token_url]):
            raise ValueError("OAuth2认证缺少必要参数: client_id, client_secret, token_url")
        
        # 类型检查
        if not isinstance(token_url, str):
            raise ValueError("token_url 必须是字符串")
        
        try:
            data = {
                'grant_type': grant_type,
                'client_id': client_id,
                'client_secret': client_secret
            }
            
            # 如果是密码模式，添加用户名密码
            if grant_type == 'password':
                data.update({
                    'username': config.get('username'),
                    'password': config.get('password')
                })
            
            response = requests.post(token_url, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                access_token = result.get('access_token')
                if not access_token:
                    raise ValueError("OAuth2响应中未找到access_token字段")
                
                expires_in = result.get('expires_in', 3600)  # 默认1小时
                
                return {
                    'type': 'oauth2',
                    'access_token': access_token,
                    'token_type': result.get('token_type', 'Bearer'),
                    'expires_at': datetime.now() + timedelta(seconds=expires_in),
                    'refresh_token': result.get('refresh_token'),
                    'headers': {'Authorization': f"Bearer {access_token}"}
                }
            else:
                raise ValueError(f"OAuth2认证失败: HTTP {response.status_code} - {response.text}")
                
        except Exception as e:
            raise ValueError(f"OAuth2认证失败: {str(e)}")
    
    def is_valid(self, auth_data: Dict[str, Any]) -> bool:
        """检查OAuth2 Token是否有效"""
        if not auth_data.get('access_token'):
            return False
        
        expires_at = auth_data.get('expires_at')
        if expires_at and datetime.now() > expires_at:
            return False
        
        return True
    
    def refresh_if_needed(self, auth_data: Dict[str, Any]) -> Dict[str, Any]:
        """刷新OAuth2 Token"""
        if self.is_valid(auth_data):
            return auth_data
        
        refresh_token = auth_data.get('refresh_token')
        if not refresh_token:
            raise ValueError("无法刷新OAuth2 Token: 缺少refresh_token")
        
        # 实现Token刷新逻辑
        return auth_data


class AuthManager:
    """认证管理器 - 统一管理各种认证方式"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path
        self.auth_cache = {}
        
        # 注册认证策略
        self.strategies = {
            'bearer': BearerTokenAuth(),
            'basic': BasicAuth(),
            'api_key': ApiKeyAuth(),
            'oauth2': OAuth2Auth()
        }
    
    def get_auth_config(self, auth_name: str) -> Dict[str, Any]:
        """获取认证配置"""
        if self.config_path and Path(self.config_path).exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                if self.config_path.endswith('.yaml') or self.config_path.endswith('.yml'):
                    config = yaml.safe_load(f)
                else:
                    config = json.load(f)
            
            auth_configs = config.get('authentication', {})
            if auth_name in auth_configs:
                return auth_configs[auth_name]
        
        # 从环境变量获取
        env_prefix = f"AUTH_{auth_name.upper()}"
        env_config = {}
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                config_key = key[len(env_prefix)+1:].lower()
                env_config[config_key] = value
        
        if env_config:
            return env_config
        
        raise ValueError(f"未找到认证配置: {auth_name}")
    
    def authenticate(self, auth_name: str, force_refresh: bool = False) -> Dict[str, Any]:
        """执行认证"""
        # 检查缓存
        if not force_refresh and auth_name in self.auth_cache:
            cached_auth = self.auth_cache[auth_name]
            auth_type = cached_auth.get('type')
            if auth_type in self.strategies:
                strategy = self.strategies[auth_type]
                if strategy.is_valid(cached_auth):
                    self.logger.info(f"使用缓存的认证信息: {auth_name}")
                    return strategy.refresh_if_needed(cached_auth)
        
        # 获取认证配置
        config = self.get_auth_config(auth_name)
        auth_type = config.get('type')
        
        if auth_type not in self.strategies:
            raise ValueError(f"不支持的认证类型: {auth_type}")
        
        # 执行认证
        strategy = self.strategies[auth_type]
        auth_data = strategy.authenticate(config)
        
        # 缓存认证信息
        self.auth_cache[auth_name] = auth_data
        
        self.logger.info(f"认证成功: {auth_name} ({auth_type})")
        return auth_data
    
    def get_auth_headers(self, auth_name: str) -> Dict[str, str]:
        """获取认证请求头"""
        auth_data = self.authenticate(auth_name)
        return auth_data.get('headers', {})
    
    def is_authenticated(self, auth_name: str) -> bool:
        """检查是否已认证"""
        if auth_name not in self.auth_cache:
            return False
        
        auth_data = self.auth_cache[auth_name]
        auth_type = auth_data.get('type')
        
        if auth_type in self.strategies:
            strategy = self.strategies[auth_type]
            return strategy.is_valid(auth_data)
        
        return False
    
    def clear_auth_cache(self, auth_name: Optional[str] = None):
        """清除认证缓存"""
        if auth_name:
            self.auth_cache.pop(auth_name, None)
            self.logger.info(f"已清除认证缓存: {auth_name}")
        else:
            self.auth_cache.clear()
            self.logger.info("已清除所有认证缓存")
    
    def get_authentication_guide(self) -> str:
        """获取认证配置指南"""
        guide = """
🔐 认证配置指南

支持的认证类型：
1. Bearer Token 认证
2. Basic 认证  
3. API Key 认证
4. OAuth2 认证

配置方式：
1. 配置文件方式（推荐）
2. 环境变量方式

## 配置文件示例 (config/auth.yaml)

```yaml
authentication:
  # Bearer Token认证
  api_auth:
    type: bearer
    login_url: "https://api.example.com/auth/login"
    username: "your_username"
    password: "your_password"
    token_ttl: 24  # Token有效期（小时）
  
  # Basic认证
  basic_auth:
    type: basic
    username: "admin"
    password: "your-password-here"
  
  # API Key认证
  key_auth:
    type: api_key
    api_key: "your-api-key-here"
    header_name: "X-API-Key"  # 可选，默认X-API-Key
  
  # OAuth2认证
  oauth_auth:
    type: oauth2
    client_id: "your_client_id"
    client_secret: "your_client_secret"
    token_url: "https://api.example.com/oauth/token"
    grant_type: "client_credentials"  # 或 password
```

## 环境变量方式

```bash
# Bearer Token认证
export AUTH_API_AUTH_TYPE=bearer
export AUTH_API_AUTH_LOGIN_URL=https://api.example.com/auth/login
export AUTH_API_AUTH_USERNAME=your_username
export AUTH_API_AUTH_PASSWORD=your_password

# API Key认证
export AUTH_KEY_AUTH_TYPE=api_key
export AUTH_KEY_AUTH_API_KEY=your-api-key-here
export AUTH_KEY_AUTH_HEADER_NAME=X-API-Key
```

## 使用示例

```python
# 初始化认证管理器
auth_manager = AuthManager("config/auth.yaml")

# 执行认证
auth_data = auth_manager.authenticate("api_auth")

# 获取认证请求头
headers = auth_manager.get_auth_headers("api_auth")

# 检查认证状态
is_auth = auth_manager.is_authenticated("api_auth")
```
"""
        return guide