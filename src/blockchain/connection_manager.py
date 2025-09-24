"""
=============================================================================
接口自动化测试框架 - 区块链连接管理器模块
=============================================================================

本模块提供了区块链长连接管理功能，支持WebSocket连接、连接池管理、
自动重连、心跳检测等高级连接特性。

主要功能：
1. 长连接管理 - WebSocket和HTTP长连接支持
2. 连接池管理 - 高效的连接池和负载均衡
3. 自动重连 - 智能重连机制和故障恢复
4. 心跳检测 - 实时连接状态监控
5. 事件订阅 - 实时区块链事件订阅
6. 性能优化 - 连接复用和批处理

支持的长连接类型：
- WebSocket连接 - 实时事件订阅
- HTTP Keep-Alive - HTTP长连接
- 连接池 - 多连接并发处理
- 自动故障转移 - 多节点备份

技术特性：
- 异步连接管理 - 高性能异步连接处理
- 智能重连策略 - 指数退避重连算法
- 连接健康检查 - 实时连接状态监控
- 事件驱动架构 - 基于事件的异步处理
- 内存优化 - 高效的连接池管理
- 监控集成 - 连接状态监控和告警

使用示例：
    # 创建连接管理器
    conn_manager = BlockchainConnectionManager()
    
    # 建立WebSocket连接
    await conn_manager.connect_websocket("wss://sepolia.infura.io/ws/v3/YOUR_KEY")
    
    # 订阅区块链事件
    await conn_manager.subscribe_events("newHeads")
    
    # 监听事件
    async for event in conn_manager.listen_events():
        print(f"收到事件: {event}")

作者: 接口自动化测试框架团队
版本: 1.0.0
更新日期: 2024年12月
=============================================================================
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Optional, Any, Union, Callable, AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
import websockets
import aiohttp
from aiohttp import ClientSession, ClientWebSocketResponse
import ssl


class ConnectionType(Enum):
    """连接类型枚举"""
    WEBSOCKET = "websocket"
    HTTP_KEEPALIVE = "http_keepalive"
    HTTP_POOL = "http_pool"


class ConnectionStatus(Enum):
    """连接状态枚举"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


@dataclass
class ConnectionConfig:
    """连接配置数据类"""
    url: str
    connection_type: ConnectionType
    timeout: int = 30
    max_retries: int = 5
    retry_delay: float = 1.0
    heartbeat_interval: int = 30
    max_connections: int = 10
    headers: Dict[str, str] = field(default_factory=dict)
    auth: Optional[tuple] = None
    ssl_context: Optional[ssl.SSLContext] = None


@dataclass
class ConnectionInfo:
    """连接信息数据类"""
    id: str
    config: ConnectionConfig
    status: ConnectionStatus
    created_at: float
    last_heartbeat: float
    retry_count: int = 0
    websocket: Optional[ClientWebSocketResponse] = None
    session: Optional[ClientSession] = None
    subscriptions: List[str] = field(default_factory=list)


class BlockchainConnectionManager:
    """区块链连接管理器"""
    
    def __init__(self, max_connections: int = 50):
        """
        初始化区块链连接管理器
        
        Args:
            max_connections: 最大连接数
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.max_connections = max_connections
        self.connections: Dict[str, ConnectionInfo] = {}
        self.connection_pools: Dict[str, List[ConnectionInfo]] = {}
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.running = False
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        
        # 连接统计
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "failed_connections": 0,
            "total_events": 0,
            "last_cleanup": time.time()
        }
        
        self.logger.info("区块链连接管理器已初始化")
    
    async def connect_websocket(self, url: str, config: Optional[ConnectionConfig] = None) -> str:
        """
        建立WebSocket连接
        
        Args:
            url: WebSocket URL
            config: 连接配置
            
        Returns:
            str: 连接ID
        """
        try:
            connection_id = str(uuid.uuid4())
            
            if config is None:
                config = ConnectionConfig(
                    url=url,
                    connection_type=ConnectionType.WEBSOCKET
                )
            
            # 创建连接信息
            conn_info = ConnectionInfo(
                id=connection_id,
                config=config,
                status=ConnectionStatus.CONNECTING,
                created_at=time.time(),
                last_heartbeat=time.time()
            )
            
            self.connections[connection_id] = conn_info
            
            # 建立WebSocket连接
            await self._establish_websocket_connection(conn_info)
            
            # 启动心跳检测
            if not self.running:
                await self.start_heartbeat_monitoring()
            
            self.logger.info(f"WebSocket连接已建立: {connection_id}")
            return connection_id
            
        except Exception as e:
            self.logger.error(f"建立WebSocket连接失败: {e}")
            raise
    
    async def connect_http_pool(self, url: str, pool_size: int = 5, 
                              config: Optional[ConnectionConfig] = None) -> str:
        """
        建立HTTP连接池
        
        Args:
            url: HTTP URL
            pool_size: 连接池大小
            config: 连接配置
            
        Returns:
            str: 连接池ID
        """
        try:
            pool_id = str(uuid.uuid4())
            
            if config is None:
                config = ConnectionConfig(
                    url=url,
                    connection_type=ConnectionType.HTTP_POOL,
                    max_connections=pool_size
                )
            
            # 创建连接池
            pool = []
            for i in range(pool_size):
                connection_id = f"{pool_id}_{i}"
                
                conn_info = ConnectionInfo(
                    id=connection_id,
                    config=config,
                    status=ConnectionStatus.CONNECTING,
                    created_at=time.time(),
                    last_heartbeat=time.time()
                )
                
                # 建立HTTP会话
                await self._establish_http_connection(conn_info)
                
                pool.append(conn_info)
                self.connections[connection_id] = conn_info
            
            self.connection_pools[pool_id] = pool
            
            self.logger.info(f"HTTP连接池已建立: {pool_id} (大小: {pool_size})")
            return pool_id
            
        except Exception as e:
            self.logger.error(f"建立HTTP连接池失败: {e}")
            raise
    
    async def _establish_websocket_connection(self, conn_info: ConnectionInfo):
        """建立WebSocket连接"""
        try:
            # 创建WebSocket连接
            websocket = await aiohttp.ClientSession().ws_connect(
                conn_info.config.url,
                timeout=conn_info.config.timeout,
                headers=conn_info.config.headers,
                auth=conn_info.config.auth,
                ssl=conn_info.config.ssl_context
            )
            
            conn_info.websocket = websocket
            conn_info.status = ConnectionStatus.CONNECTED
            conn_info.last_heartbeat = time.time()
            
            self.stats["total_connections"] += 1
            self.stats["active_connections"] += 1
            
        except Exception as e:
            conn_info.status = ConnectionStatus.FAILED
            self.stats["failed_connections"] += 1
            raise
    
    async def _establish_http_connection(self, conn_info: ConnectionInfo):
        """建立HTTP连接"""
        try:
            # 创建HTTP会话
            session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=conn_info.config.timeout),
                headers=conn_info.config.headers,
                auth=conn_info.config.auth,
                connector=aiohttp.TCPConnector(
                    limit=100,
                    limit_per_host=30,
                    keepalive_timeout=30,
                    enable_cleanup_closed=True
                )
            )
            
            conn_info.session = session
            conn_info.status = ConnectionStatus.CONNECTED
            conn_info.last_heartbeat = time.time()
            
            self.stats["total_connections"] += 1
            self.stats["active_connections"] += 1
            
        except Exception as e:
            conn_info.status = ConnectionStatus.FAILED
            self.stats["failed_connections"] += 1
            raise
    
    async def subscribe_events(self, connection_id: str, subscription_type: str, 
                             params: Optional[List] = None) -> bool:
        """
        订阅区块链事件
        
        Args:
            connection_id: 连接ID
            subscription_type: 订阅类型
            params: 订阅参数
            
        Returns:
            bool: 是否订阅成功
        """
        try:
            if connection_id not in self.connections:
                raise ValueError(f"连接不存在: {connection_id}")
            
            conn_info = self.connections[connection_id]
            
            if conn_info.config.connection_type != ConnectionType.WEBSOCKET:
                raise ValueError("只有WebSocket连接支持事件订阅")
            
            if not conn_info.websocket or conn_info.status != ConnectionStatus.CONNECTED:
                raise ValueError("WebSocket连接未建立")
            
            # 构建订阅消息
            subscription_id = str(uuid.uuid4())
            message = {
                "id": subscription_id,
                "method": "eth_subscribe",
                "params": [subscription_type] + (params or [])
            }
            
            # 发送订阅消息
            await conn_info.websocket.send_str(json.dumps(message))
            
            # 等待订阅确认
            response = await conn_info.websocket.receive_str()
            response_data = json.loads(response)
            
            if "error" in response_data:
                self.logger.error(f"订阅失败: {response_data['error']}")
                return False
            
            # 记录订阅
            subscription_key = f"{subscription_type}_{subscription_id}"
            conn_info.subscriptions.append(subscription_key)
            
            self.logger.info(f"事件订阅成功: {subscription_type} (连接: {connection_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"订阅事件失败: {e}")
            return False
    
    async def listen_events(self, connection_id: str) -> AsyncIterator[Dict[str, Any]]:
        """
        监听区块链事件
        
        Args:
            connection_id: 连接ID
            
        Yields:
            Dict[str, Any]: 事件数据
        """
        try:
            if connection_id not in self.connections:
                raise ValueError(f"连接不存在: {connection_id}")
            
            conn_info = self.connections[connection_id]
            
            if conn_info.config.connection_type != ConnectionType.WEBSOCKET:
                raise ValueError("只有WebSocket连接支持事件监听")
            
            if not conn_info.websocket:
                raise ValueError("WebSocket连接未建立")
            
            self.logger.info(f"开始监听事件 (连接: {connection_id})")
            
            while conn_info.status == ConnectionStatus.CONNECTED:
                try:
                    # 接收消息
                    message = await conn_info.websocket.receive_str()
                    event_data = json.loads(message)
                    
                    # 更新心跳时间
                    conn_info.last_heartbeat = time.time()
                    
                    # 统计事件
                    self.stats["total_events"] += 1
                    
                    # 触发事件处理器
                    await self._trigger_event_handlers(event_data)
                    
                    yield event_data
                    
                except websockets.exceptions.ConnectionClosed:
                    self.logger.warning(f"WebSocket连接已关闭: {connection_id}")
                    conn_info.status = ConnectionStatus.DISCONNECTED
                    break
                except Exception as e:
                    self.logger.error(f"接收事件失败: {e}")
                    await asyncio.sleep(1)
            
        except Exception as e:
            self.logger.error(f"监听事件失败: {e}")
            raise
    
    async def send_request(self, connection_id: str, method: str, params: List[Any] = None) -> Dict[str, Any]:
        """
        发送RPC请求
        
        Args:
            connection_id: 连接ID
            method: RPC方法
            params: 参数
            
        Returns:
            Dict[str, Any]: 响应数据
        """
        try:
            if connection_id not in self.connections:
                raise ValueError(f"连接不存在: {connection_id}")
            
            conn_info = self.connections[connection_id]
            
            # 构建请求
            request_id = str(uuid.uuid4())
            request_data = {
                "id": request_id,
                "method": method,
                "params": params or []
            }
            
            if conn_info.config.connection_type == ConnectionType.WEBSOCKET:
                # WebSocket请求
                if not conn_info.websocket:
                    raise ValueError("WebSocket连接未建立")
                
                await conn_info.websocket.send_str(json.dumps(request_data))
                response = await conn_info.websocket.receive_str()
                response_data = json.loads(response)
                
            else:
                # HTTP请求
                if not conn_info.session:
                    raise ValueError("HTTP会话未建立")
                
                async with conn_info.session.post(
                    conn_info.config.url,
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    response_data = await response.json()
            
            # 更新心跳时间
            conn_info.last_heartbeat = time.time()
            
            return response_data
            
        except Exception as e:
            self.logger.error(f"发送RPC请求失败: {e}")
            raise
    
    async def start_heartbeat_monitoring(self):
        """启动心跳监控"""
        if self.running:
            return
        
        self.running = True
        self.heartbeat_task = asyncio.create_task(self._heartbeat_monitor_loop())
        self.cleanup_task = asyncio.create_task(self._cleanup_monitor_loop())
        
        self.logger.info("心跳监控已启动")
    
    async def stop_heartbeat_monitoring(self):
        """停止心跳监控"""
        self.running = False
        
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("心跳监控已停止")
    
    async def _heartbeat_monitor_loop(self):
        """心跳监控循环"""
        while self.running:
            try:
                current_time = time.time()
                
                for conn_info in self.connections.values():
                    # 检查连接状态
                    if conn_info.status == ConnectionStatus.CONNECTED:
                        # 检查心跳超时
                        if current_time - conn_info.last_heartbeat > conn_info.config.heartbeat_interval * 2:
                            self.logger.warning(f"连接心跳超时: {conn_info.id}")
                            await self._reconnect_connection(conn_info)
                    
                    # 检查重连状态
                    elif conn_info.status == ConnectionStatus.RECONNECTING:
                        await self._reconnect_connection(conn_info)
                
                await asyncio.sleep(5)  # 每5秒检查一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"心跳监控错误: {e}")
                await asyncio.sleep(5)
    
    async def _cleanup_monitor_loop(self):
        """清理监控循环"""
        while self.running:
            try:
                current_time = time.time()
                
                # 清理无效连接
                to_remove = []
                for conn_id, conn_info in self.connections.items():
                    # 清理超过1小时的失败连接
                    if (conn_info.status == ConnectionStatus.FAILED and 
                        current_time - conn_info.created_at > 3600):
                        to_remove.append(conn_id)
                
                for conn_id in to_remove:
                    await self.disconnect(conn_id)
                
                # 更新统计
                self.stats["active_connections"] = sum(
                    1 for conn in self.connections.values() 
                    if conn.status == ConnectionStatus.CONNECTED
                )
                self.stats["last_cleanup"] = current_time
                
                await asyncio.sleep(60)  # 每分钟清理一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"清理监控错误: {e}")
                await asyncio.sleep(60)
    
    async def _reconnect_connection(self, conn_info: ConnectionInfo):
        """重连连接"""
        try:
            if conn_info.retry_count >= conn_info.config.max_retries:
                conn_info.status = ConnectionStatus.FAILED
                self.logger.error(f"连接重试次数超限: {conn_info.id}")
                return
            
            conn_info.status = ConnectionStatus.RECONNECTING
            conn_info.retry_count += 1
            
            # 计算重连延迟（指数退避）
            delay = conn_info.config.retry_delay * (2 ** conn_info.retry_count)
            await asyncio.sleep(delay)
            
            # 重新建立连接
            if conn_info.config.connection_type == ConnectionType.WEBSOCKET:
                await self._establish_websocket_connection(conn_info)
            else:
                await self._establish_http_connection(conn_info)
            
            # 重新订阅事件
            for subscription in conn_info.subscriptions:
                subscription_type = subscription.split('_')[0]
                await self.subscribe_events(conn_info.id, subscription_type)
            
            self.logger.info(f"连接重连成功: {conn_info.id}")
            
        except Exception as e:
            self.logger.error(f"连接重连失败: {e}")
            conn_info.status = ConnectionStatus.FAILED
    
    async def _trigger_event_handlers(self, event_data: Dict[str, Any]):
        """触发事件处理器"""
        try:
            # 根据事件类型触发处理器
            if "method" in event_data:
                method = event_data["method"]
                if method in self.event_handlers:
                    for handler in self.event_handlers[method]:
                        try:
                            if asyncio.iscoroutinefunction(handler):
                                await handler(event_data)
                            else:
                                handler(event_data)
                        except Exception as e:
                            self.logger.error(f"事件处理器错误: {e}")
            
        except Exception as e:
            self.logger.error(f"触发事件处理器失败: {e}")
    
    def add_event_handler(self, event_type: str, handler: Callable):
        """
        添加事件处理器
        
        Args:
            event_type: 事件类型
            handler: 处理器函数
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
        self.logger.info(f"事件处理器已添加: {event_type}")
    
    async def disconnect(self, connection_id: str) -> bool:
        """
        断开连接
        
        Args:
            connection_id: 连接ID
            
        Returns:
            bool: 是否断开成功
        """
        try:
            if connection_id not in self.connections:
                return False
            
            conn_info = self.connections[connection_id]
            
            # 关闭WebSocket连接
            if conn_info.websocket:
                await conn_info.websocket.close()
            
            # 关闭HTTP会话
            if conn_info.session:
                await conn_info.session.close()
            
            # 更新状态
            conn_info.status = ConnectionStatus.DISCONNECTED
            del self.connections[connection_id]
            
            # 从连接池中移除
            for pool_id, pool in self.connection_pools.items():
                if any(conn.id == connection_id for conn in pool):
                    pool[:] = [conn for conn in pool if conn.id != connection_id]
                    if not pool:
                        del self.connection_pools[pool_id]
                    break
            
            self.logger.info(f"连接已断开: {connection_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"断开连接失败: {e}")
            return False
    
    async def disconnect_all(self):
        """断开所有连接"""
        try:
            connection_ids = list(self.connections.keys())
            for connection_id in connection_ids:
                await self.disconnect(connection_id)
            
            # 停止监控
            await self.stop_heartbeat_monitoring()
            
            self.logger.info("所有连接已断开")
            
        except Exception as e:
            self.logger.error(f"断开所有连接失败: {e}")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """
        获取连接统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            **self.stats,
            "connection_count": len(self.connections),
            "pool_count": len(self.connection_pools),
            "event_handler_count": sum(len(handlers) for handlers in self.event_handlers.values()),
            "connections": {
                conn_id: {
                    "status": conn_info.status.value,
                    "type": conn_info.config.connection_type.value,
                    "created_at": conn_info.created_at,
                    "last_heartbeat": conn_info.last_heartbeat,
                    "retry_count": conn_info.retry_count,
                    "subscription_count": len(conn_info.subscriptions)
                }
                for conn_id, conn_info in self.connections.items()
            }
        }
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.disconnect_all()
