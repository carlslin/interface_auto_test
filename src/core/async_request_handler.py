#!/usr/bin/env python3
"""
异步HTTP请求处理器模块
提供高性能的异步HTTP请求处理能力
"""

import asyncio
import aiohttp
import time
import logging
from typing import Dict, Any, Optional, Union
from urllib.parse import urljoin, urlparse
from .request_handler import RequestHandler
from ..utils.security_manager import SecurityManager


class AsyncRequestHandler:
    """异步HTTP请求处理器"""
    
    def __init__(self, config, max_concurrent_requests: int = 100):
        """
        初始化异步请求处理器
        
        Args:
            config: 配置对象
            max_concurrent_requests: 最大并发请求数
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.security_manager = SecurityManager()
        self.max_concurrent_requests = max_concurrent_requests
        
        # 不同HTTP方法的差异化超时配置
        self.method_timeouts = {
            'GET': 3.0,
            'POST': 5.0,
            'PUT': 8.0,
            'DELETE': 4.0
        }
        
        # 请求大小限制
        self.max_request_size = config.get('global.max_request_size', 10 * 1024 * 1024)
        
        # 连接器配置
        self.connector_config = {
            'limit': max_concurrent_requests,
            'limit_per_host': 30,
            'ttl_dns_cache': 300,
            'use_dns_cache': True,
            'keepalive_timeout': 30,
            'enable_cleanup_closed': True
        }
        
        # 会话配置
        self.session_config = {
            'timeout': aiohttp.ClientTimeout(total=30),
            'connector': aiohttp.TCPConnector(**self.connector_config),
            'headers': {
                'User-Agent': 'Interface-AutoTest-Framework/1.0.0',
                'Accept': 'application/json',
                'Accept-Encoding': 'gzip, deflate'
            }
        }
        
        self._session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
    
    async def start(self):
        """启动异步会话"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(**self.session_config)
            self.logger.info("异步HTTP会话已启动")
    
    async def close(self):
        """关闭异步会话"""
        if self._session and not self._session.closed:
            await self._session.close()
            self.logger.info("异步HTTP会话已关闭")
    
    def _validate_request_inputs(self, method: str, url: str, **kwargs) -> None:
        """
        验证请求输入参数（复用同步版本的验证逻辑）
        
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
        if 'data' in kwargs or 'json' in kwargs:
            data = kwargs.get('data') or kwargs.get('json')
            if isinstance(data, str):
                data_size = len(data.encode('utf-8'))
            elif isinstance(data, (dict, list)):
                import json
                data_size = len(json.dumps(data).encode('utf-8'))
            else:
                data_size = len(str(data).encode('utf-8'))
            
            if data_size > self.max_request_size:
                raise ValueError(f"请求体大小超过限制: {data_size} > {self.max_request_size}")
    
    async def request(self, method: str, url: str, **kwargs) -> aiohttp.ClientResponse:
        """
        发送异步HTTP请求
        
        Args:
            method: HTTP方法
            url: 请求URL
            **kwargs: 其他请求参数
            
        Returns:
            aiohttp.ClientResponse: 响应对象
        """
        if self._session is None or self._session.closed:
            await self.start()
        
        # 验证输入参数
        self._validate_request_inputs(method, url, **kwargs)
        
        # 构建完整URL
        base_url = self.config.get('environments.dev.base_url', '')
        if not url.startswith('http'):
            url = urljoin(base_url, url)
        
        # 设置超时
        method_upper = method.upper()
        timeout = kwargs.pop('timeout', self.method_timeouts.get(method_upper, 30))
        
        # 设置请求参数
        request_kwargs = {
            'timeout': aiohttp.ClientTimeout(total=timeout),
            **kwargs
        }
        
        # 发送请求
        start_time = time.time()
        try:
            self.logger.info(f"发送异步请求: {method} {url}")
            async with self._session.request(method, url, **request_kwargs) as response:
                response_time = time.time() - start_time
                self.logger.info(f"异步请求完成: {method} {url} - {response.status} ({response_time:.3f}s)")
                
                # 读取响应内容（如果需要）
                if not response.content.at_eof():
                    await response.read()
                
                return response
                
        except asyncio.TimeoutError:
            self.logger.error(f"异步请求超时: {method} {url}")
            raise
        except Exception as e:
            self.logger.error(f"异步请求失败: {method} {url} - {e}")
            raise
    
    async def get(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """发送异步GET请求"""
        return await self.request('GET', url, **kwargs)
    
    async def post(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """发送异步POST请求"""
        return await self.request('POST', url, **kwargs)
    
    async def put(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """发送异步PUT请求"""
        return await self.request('PUT', url, **kwargs)
    
    async def delete(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """发送异步DELETE请求"""
        return await self.request('DELETE', url, **kwargs)
    
    async def batch_request(self, requests: list) -> list:
        """
        批量发送异步请求
        
        Args:
            requests: 请求列表，每个元素包含 (method, url, kwargs)
            
        Returns:
            list: 响应列表
        """
        if not requests:
            return []
        
        # 限制并发数量
        semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        
        async def single_request(method: str, url: str, **kwargs):
            async with semaphore:
                return await self.request(method, url, **kwargs)
        
        # 创建任务
        tasks = [
            single_request(method, url, **kwargs)
            for method, url, kwargs in requests
        ]
        
        # 并发执行
        self.logger.info(f"开始批量异步请求: {len(requests)} 个请求")
        start_time = time.time()
        
        try:
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time
            
            # 统计结果
            success_count = sum(1 for r in responses if not isinstance(r, Exception))
            error_count = len(responses) - success_count
            
            self.logger.info(f"批量异步请求完成: {success_count} 成功, {error_count} 失败, 总用时: {total_time:.3f}s")
            
            return responses
            
        except Exception as e:
            self.logger.error(f"批量异步请求失败: {e}")
            raise
    
    async def health_check(self, url: str) -> Dict[str, Any]:
        """
        健康检查
        
        Args:
            url: 检查的URL
            
        Returns:
            Dict[str, Any]: 健康检查结果
        """
        start_time = time.time()
        try:
            response = await self.get(url)
            response_time = time.time() - start_time
            
            return {
                'status': 'healthy' if response.status < 400 else 'unhealthy',
                'status_code': response.status,
                'response_time': response_time,
                'url': url,
                'timestamp': time.time()
            }
        except Exception as e:
            response_time = time.time() - start_time
            return {
                'status': 'error',
                'error': str(e),
                'response_time': response_time,
                'url': url,
                'timestamp': time.time()
            }
    
    async def get_connection_info(self) -> Dict[str, Any]:
        """获取连接信息"""
        if self._session is None or self._session.closed:
            return {'status': 'disconnected'}
        
        connector = self._session.connector
        return {
            'status': 'connected',
            'max_connections': connector.limit,
            'max_connections_per_host': connector.limit_per_host,
            'dns_cache_enabled': connector.use_dns_cache,
            'keepalive_timeout': connector.keepalive_timeout
        }
