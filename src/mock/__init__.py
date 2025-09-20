"""
Mock服务器模块

提供轻量Mock服务器功能，用于测试环境：
- HTTP/HTTPS Mock服务器
- 动态路由配置
- 响应数据模拟
- 请求日志记录

主要组件：
- MockServer: Mock服务器实现，基于Flask
- MockDataManager: Mock数据管理器，管理响应数据

主要特性：
- 支持RESTful API模拟
- 可配置响应延迟
- CORS跨域支持
- JSON/XML响应格式
- 状态码和头部自定义

使用示例:
    from src.mock import MockServer, MockDataManager
    
    # 创建Mock服务器
    server = MockServer({
        'host': 'localhost',
        'port': 5000,
        'debug': True
    })
    
    # 添加Mock路由
    server.add_route('GET', '/api/users', {'users': []})
    server.start()
"""

from .mock_server import MockServer
from .mock_data import MockDataManager

__all__ = ["MockServer", "MockDataManager"]