"""
核心框架模块

提供接口自动化测试的核心功能组件：

主要组件：
- BaseTest: 测试基类，提供通用的测试方法和断言功能
- RequestHandler: HTTP请求处理器，负责发送请求和处理响应
- TestExecutor: 测试执行器，负责执行测试用例和收集结果

该模块是整个测试框架的核心，为上层应用提供稳定可靠的测试能力。
所有测试类都应继承自BaseTest，使用RequestHandler发送HTTP请求。

示例:
    from src.core import BaseTest, RequestHandler
    
    class MyAPITest(BaseTest):
        def test_login(self):
            result = self.make_request('POST', '/login', json={'user': 'test'})
            self.assert_status_code(result, 200)

版本: 1.0.0
作者: Interface AutoTest Framework Team
"""

__version__ = "1.0.0"
__author__ = "Interface AutoTest Framework Team"

from .base_test import BaseTest
from .request_handler import RequestHandler
from .test_executor import TestExecutor

__all__ = ["BaseTest", "RequestHandler", "TestExecutor"]