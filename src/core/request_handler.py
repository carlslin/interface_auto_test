"""
HTTP请求处理器模块
负责发送HTTP请求和处理响应
"""

from __future__ import annotations

import requests
import time
import logging
import re
from typing import Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from ..utils.security_manager import SecurityManager


class RequestHandler:
    """HTTP请求处理器"""
    
    def __init__(self, config):
        """
        初始化请求处理器
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.session = requests.Session()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.security_manager = SecurityManager()
        
        # 不同HTTP方法的差异化超时配置（基于用户记忆的经验）
        self.method_timeouts = {
            'GET': 3.0,      # GET请求3秒超时
            'POST': 5.0,     # POST请求5秒超时  
            'PUT': 8.0,      # PUT请求8秒超时
            'DELETE': 4.0    # DELETE请求4秒超时
        }
        
        # 请求大小限制（字节）
        self.max_request_size = config.get('global.max_request_size', 10 * 1024 * 1024)  # 10MB
        
        self._setup_session()
        
    def _setup_session(self):
        """设置会话默认参数"""
        # 设置默认超时（通过请求时传递）
        self.default_timeout = self.config.get('global.timeout', 30)
        
        # 设置默认请求头
        default_headers = self.config.get('environments.dev.headers', {})
        self.session.headers.update(default_headers)
        
        # 设置长连接支持
        keep_alive = self.config.get('global.keep_alive', True)
        if keep_alive:
            self.session.headers['Connection'] = 'keep-alive'
            # 设置连接池参数
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry
            
            # 配置连接池大小
            pool_connections = self.config.get('global.pool_connections', 10)
            pool_maxsize = self.config.get('global.pool_maxsize', 10)
            
            adapter = HTTPAdapter(
                pool_connections=pool_connections,
                pool_maxsize=pool_maxsize,
                max_retries=0  # 重试由我们自己处理
            )
            
            self.session.mount('http://', adapter)
            self.session.mount('https://', adapter)
        
        # 禁用代理，防止代理导致的连接问题
        self.session.proxies = {}
    
    def _validate_request_inputs(self, method: str, url: str, **kwargs) -> None:
        """
        验证请求输入参数
        
        Args:
            method: HTTP方法
            url: 请求URL
            **kwargs: 其他请求参数
            
        Raises:
            ValueError: 如果输入验证失败
        """
        # 验证HTTP方法
        valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
        if method.upper() not in valid_methods:
            raise ValueError(f"不支持的HTTP方法: {method}")
        
        # 验证URL
        if not url or not isinstance(url, str):
            raise ValueError("URL不能为空")
        
        # 验证URL格式
        if not self.security_manager.validate_url(url) and not url.startswith('/'):
            raise ValueError(f"无效的URL格式: {url}")
        
        # 验证请求体大小
        if 'data' in kwargs:
            data = kwargs['data']
            if isinstance(data, str):
                data_size = len(data.encode('utf-8'))
            elif isinstance(data, (dict, list)):
                import json
                data_size = len(json.dumps(data).encode('utf-8'))
            else:
                data_size = len(str(data).encode('utf-8'))
            
            if data_size > self.max_request_size:
                raise ValueError(f"请求体大小超过限制: {data_size} > {self.max_request_size}")
        
        # 验证JSON数据
        if 'json' in kwargs:
            json_data = kwargs['json']
            if isinstance(json_data, str):
                if not self.security_manager.validate_json_input(json_data):
                    raise ValueError("无效的JSON格式")
            elif isinstance(json_data, (dict, list)):
                import json
                try:
                    json.dumps(json_data)
                except (TypeError, ValueError) as e:
                    raise ValueError(f"JSON序列化失败: {e}")
        
        # 清理和验证请求头
        if 'headers' in kwargs:
            headers = kwargs['headers']
            if isinstance(headers, dict):
                # 清理请求头
                cleaned_headers = {}
                for key, value in headers.items():
                    if isinstance(key, str) and isinstance(value, str):
                        cleaned_key = self.security_manager.sanitize_input(key)
                        cleaned_value = self.security_manager.sanitize_input(value)
                        cleaned_headers[cleaned_key] = cleaned_value
                kwargs['headers'] = cleaned_headers
        
        # 验证参数
        if 'params' in kwargs:
            params = kwargs['params']
            if isinstance(params, dict):
                cleaned_params = {}
                for key, value in params.items():
                    if isinstance(key, str) and isinstance(value, str):
                        cleaned_key = self.security_manager.sanitize_input(key)
                        cleaned_value = self.security_manager.sanitize_input(value)
                        cleaned_params[cleaned_key] = cleaned_value
                kwargs['params'] = cleaned_params
        
    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        发送HTTP请求
        
        Args:
            method: HTTP方法
            url: 请求URL
            **kwargs: 其他请求参数
            
        Returns:
            requests.Response: 响应对象
        """
        # 验证输入参数
        self._validate_request_inputs(method, url, **kwargs)
        
        # 构建完整URL
        base_url = self.config.get('environments.dev.base_url', '')
        if not url.startswith('http'):
            url = urljoin(base_url, url)
            
        # 使用差异化超时策略
        method_upper = method.upper()
        default_timeout = self.method_timeouts.get(method_upper, self.default_timeout)
        
        # 设置请求参数
        request_kwargs = {
            'timeout': kwargs.pop('timeout', default_timeout),
            **kwargs
        }
        
        # 重试机制
        max_retries = self.config.get('global.retry', 3)
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                self.logger.info(f"发送请求: {method} {url} (尝试 {attempt + 1}/{max_retries + 1}, 超时: {request_kwargs['timeout']}s)")
                response = self.session.request(method, url, **request_kwargs)
                self.logger.info(f"响应状态码: {response.status_code}")
                return response
                
            except Exception as e:
                last_exception = e
                self.logger.warning(f"请求失败 (尝试 {attempt + 1}/{max_retries + 1}): {str(e)}")
                if attempt < max_retries:
                    time.sleep(1)  # 重试前等待1秒
                    
        if last_exception:
            raise last_exception
        else:
            raise Exception("未知错误")
        
    def get(self, url: str, **kwargs) -> requests.Response:
        """发送GET请求"""
        return self.request('GET', url, **kwargs)
        
    def post(self, url: str, **kwargs) -> requests.Response:
        """发送POST请求"""
        return self.request('POST', url, **kwargs)
        
    def put(self, url: str, **kwargs) -> requests.Response:
        """发送PUT请求"""
        return self.request('PUT', url, **kwargs)
        
    def delete(self, url: str, **kwargs) -> requests.Response:
        """发送DELETE请求"""
        return self.request('DELETE', url, **kwargs)
        
    def patch(self, url: str, **kwargs) -> requests.Response:
        """发送PATCH请求"""
        return self.request('PATCH', url, **kwargs)
        
    def set_auth(self, auth_type: str, **auth_params):
        """
        设置认证信息
        
        Args:
            auth_type: 认证类型 (bearer, basic, api_key)
            **auth_params: 认证参数
        """
        if auth_type == 'bearer':
            token = auth_params.get('token')
            self.session.headers['Authorization'] = f'Bearer {token}'
        elif auth_type == 'basic':
            username = auth_params.get('username', '')
            user_password = auth_params.get('password', '')
            from requests.auth import HTTPBasicAuth
            self.session.auth = HTTPBasicAuth(username, user_password)
        elif auth_type == 'api_key':
            key = auth_params.get('key', '')
            header = auth_params.get('header', 'X-API-Key')
            self.session.headers[header] = key
            
    def clear_auth(self):
        """清除认证信息"""
        if 'Authorization' in self.session.headers:
            del self.session.headers['Authorization']
        self.session.auth = None
        
    def close_session(self):
        """
        关闭会话和连接池
        在测试完成后调用以释放资源
        """
        if hasattr(self, 'session'):
            self.session.close()
            self.logger.info("会话已关闭，连接池已释放")
            
    def get_connection_info(self) -> Dict[str, Any]:
        """
        获取连接信息
        
        Returns:
            Dict[str, Any]: 连接状态信息
        """
        info = {
            'keep_alive_enabled': 'Connection' in self.session.headers and 
                                self.session.headers['Connection'] == 'keep-alive',
            'session_headers': dict(self.session.headers),
            'timeout': self.default_timeout
        }
        
        # 获取连接池信息
        try:
            adapter = self.session.get_adapter('http://')
            if hasattr(adapter, '_pool_connections'):
                info['pool_connections'] = getattr(adapter, '_pool_connections', 'N/A')
                info['pool_maxsize'] = getattr(adapter, '_pool_maxsize', 'N/A')
            else:
                info['pool_info'] = '连接池信息不可用'
        except Exception:
            info['pool_info'] = '无法获取连接池信息'
            
        return info