"""
=============================================================================
接口自动化测试框架 - 测试基类模块
=============================================================================

本模块提供了接口自动化测试的基础功能，包括：
- 测试基类定义和通用测试方法
- 测试结果数据结构和处理
- 断言方法和验证逻辑
- 测试执行流程控制
- 错误处理和日志记录

主要组件：
1. TestResult: 测试结果数据结构
2. BaseTest: 测试基类，提供通用测试功能
3. 断言方法: 各种验证和断言功能
4. 测试执行: 统一的测试执行流程

使用示例：
    class MyAPITest(BaseTest):
        def test_user_login(self):
            result = self.make_request('POST', '/api/login', 
                                     json={'username': 'test', 'password': 'test'})
            self.assert_status_code(result, 200)
            self.assert_response_time(result.response_time, 'POST')
            return result

作者: 接口自动化测试框架团队
版本: 1.0.0
更新日期: 2024年12月
=============================================================================
"""

import time
import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum

from ..utils.config_loader import ConfigLoader
from ..utils.validator import ResponseValidator
from .request_handler import RequestHandler


class TestStatus(Enum):
    """测试状态枚举"""
    PENDING = "pending"      # 等待执行
    RUNNING = "running"      # 正在执行
    PASSED = "passed"        # 测试通过
    FAILED = "failed"        # 测试失败
    SKIPPED = "skipped"      # 测试跳过
    ERROR = "error"          # 测试错误


@dataclass
class TestResult:
    """
    测试结果数据类
    
    用于存储单个测试用例的执行结果，包含完整的测试信息：
    - 基本信息：测试名称、HTTP方法、URL
    - 执行结果：状态码、响应时间、成功状态
    - 详细数据：请求数据、响应数据、错误信息
    - 元数据：执行时间、环境信息等
    
    Attributes:
        test_name: 测试用例名称，用于标识和报告
        method: HTTP请求方法（GET, POST, PUT, DELETE等）
        url: 请求的URL地址
        status_code: HTTP响应状态码
        response_time: 响应时间（秒）
        success: 测试是否成功
        error_message: 错误信息（如果测试失败）
        request_data: 请求数据（请求体、参数等）
        response_data: 响应数据（响应体内容）
        execution_time: 测试执行时间戳
        environment: 测试环境信息
        assertions: 断言结果列表
        performance_metrics: 性能指标
    """
    # 基本信息
    test_name: str
    method: str
    url: str
    
    # 执行结果
    status_code: int
    response_time: float
    success: bool
    
    # 详细数据
    error_message: Optional[str] = None
    request_data: Optional[Dict[str, Any]] = None
    response_data: Optional[Dict[str, Any]] = None
    
    # 元数据
    execution_time: float = field(default_factory=time.time)
    environment: Optional[str] = None
    assertions: List[Dict[str, Any]] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将测试结果转换为字典格式
        
        Returns:
            Dict[str, Any]: 测试结果的字典表示
        """
        return {
            'test_name': self.test_name,
            'method': self.method,
            'url': self.url,
            'status_code': self.status_code,
            'response_time': self.response_time,
            'success': self.success,
            'error_message': self.error_message,
            'request_data': self.request_data,
            'response_data': self.response_data,
            'execution_time': self.execution_time,
            'environment': self.environment,
            'assertions': self.assertions,
            'performance_metrics': self.performance_metrics
        }


class BaseTest(ABC):
    """
    测试基类 - 接口自动化测试的核心基类
    
    本类提供了接口自动化测试的基础功能，包括：
    - 统一的测试执行流程
    - 丰富的断言方法
    - 自动化的结果收集
    - 完善的错误处理
    - 灵活的配置管理
    
    继承此类的测试类需要实现具体的测试逻辑，框架会自动处理：
    - HTTP请求的发送和响应处理
    - 测试结果的收集和验证
    - 错误信息的记录和报告
    - 性能指标的统计和分析
    
    主要功能：
    1. 测试执行: make_request() 方法统一处理HTTP请求
    2. 断言验证: 提供多种断言方法验证响应结果
    3. 结果管理: 自动收集和管理测试结果
    4. 配置管理: 支持多环境配置和动态切换
    5. 日志记录: 完整的测试执行日志
    
    使用方式：
    1. 继承BaseTest类
    2. 实现具体的测试方法
    3. 使用make_request()发送请求
    4. 使用断言方法验证结果
    5. 框架自动处理结果收集和报告生成
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化测试基类
        
        初始化过程包括：
        - 加载配置文件
        - 初始化请求处理器
        - 设置响应验证器
        - 配置日志记录器
        - 初始化测试结果收集器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认配置
                       支持相对路径和绝对路径
                       支持YAML和JSON格式
        
        Raises:
            FileNotFoundError: 配置文件不存在
            yaml.YAMLError: 配置文件格式错误
            ValueError: 配置参数无效
        """
        # 配置管理 - 加载和管理测试配置
        self.config = ConfigLoader(config_path)
        
        # 请求处理 - 处理HTTP请求和响应
        self.request_handler = RequestHandler(self.config)
        
        # 响应验证 - 验证响应格式和内容
        self.validator = ResponseValidator()
        
        # 日志记录 - 记录测试执行过程
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 结果收集 - 存储测试执行结果
        self.test_results: List[TestResult] = []
        
        # 测试统计 - 统计测试执行情况
        self.test_stats = {
            'total': 0,      # 总测试数
            'passed': 0,     # 通过数
            'failed': 0,     # 失败数
            'skipped': 0,    # 跳过数
            'error': 0       # 错误数
        }
        
        # 初始化测试模式
        self._setup_test_mode()
        
    def _setup_test_mode(self):
        """
        设置测试模式
        
        根据配置文件中的设置确定测试模式，并执行相应的初始化工作：
        - 确定使用真实接口还是Mock服务器
        - 设置有效的API基础URL
        - 检查Mock服务器可用性（如果需要）
        - 记录测试环境信息
        
        测试模式说明：
        - auto: 自动选择，优先真实接口，失败时回退到Mock
        - real: 强制使用真实接口
        - mock: 强制使用Mock服务器
        """
        test_mode = self.config.get_test_mode()
        effective_url = self.config.get_effective_base_url()
        
        self.logger.info(f"测试模式: {test_mode}")
        self.logger.info(f"有效URL: {effective_url}")
        
        # 如果是Mock模式，检查Mock服务器是否可用
        if self.config.should_use_mock():
            self._ensure_mock_server_available()
            
    def _ensure_mock_server_available(self):
        """
        确保Mock服务器可用
        
        检查Mock服务器是否正在运行，如果不可用则根据配置决定是否自动启动。
        这个方法是测试模式为mock或auto时的关键步骤。
        
        检查流程：
        1. 尝试连接Mock服务器
        2. 如果连接失败，检查是否配置了自动启动
        3. 如果配置了自动启动，则启动Mock服务器
        4. 如果未配置自动启动，则记录警告信息
        
        Raises:
            ConnectionError: Mock服务器不可用且未配置自动启动
        """
        import requests
        
        mock_url = self.config.get_mock_url()
        mock_config = self.config.get_mock_config()
        
        try:
            # 检查Mock服务器是否运行
            response = requests.get(f"{mock_url}/", timeout=3)
            self.logger.info(f"Mock服务器已就绪: {mock_url}")
        except requests.exceptions.RequestException:
            # Mock服务器不可用
            if mock_config.get("auto_start", False):
                self.logger.info("正在自动启动Mock服务器...")
                self._start_mock_server()
            else:
                self.logger.warning(f"Mock服务器不可用: {mock_url}")
                self.logger.warning("请手动启动Mock服务器或设置 auto_start: true")
                
    def _start_mock_server(self):
        """
        自动启动Mock服务器
        
        在后台线程中启动Mock服务器，用于自动化测试场景。
        启动过程包括：
        1. 创建Mock服务器实例
        2. 在后台线程中启动服务器
        3. 等待服务器启动完成
        4. 验证服务器可用性
        
        注意：
        - 服务器在后台线程中运行，不会阻塞主线程
        - 服务器设置为daemon线程，主程序退出时会自动停止
        - 启动过程有超时保护，避免无限等待
        """
        try:
            from ..mock.mock_server import MockServer
            import threading
            
            mock_config = self.config.get_mock_config()
            server = MockServer(mock_config)
            
            # 在后台线程启动服务器
            server_thread = threading.Thread(target=server.start, daemon=True)
            server_thread.start()
            
            # 等待服务器启动
            import time
            time.sleep(2)
            
            self.logger.info(f"Mock服务器已启动: {self.config.get_mock_url()}")
            
        except ImportError:
            self.logger.error("无法导入Mock服务器模块")
        except Exception as e:
            self.logger.error(f"Mock服务器启动失败: {e}")
        
    def setup_method(self):
        """
        测试方法执行前的准备工作
        
        在每个测试方法执行前调用，用于：
        - 初始化测试数据
        - 设置测试环境
        - 准备测试资源
        - 记录测试开始信息
        
        子类可以重写此方法来实现特定的准备工作。
        """
        pass
        
    def teardown_method(self):
        """
        测试方法执行后的清理工作
        
        在每个测试方法执行后调用，用于：
        - 清理测试数据
        - 释放测试资源
        - 重置测试环境
        - 记录测试结束信息
        
        子类可以重写此方法来实现特定的清理工作。
        """
        pass
        
    def teardown_class(self):
        """
        测试类执行后的清理工作
        
        在整个测试类执行完成后调用，用于：
        - 关闭HTTP连接池
        - 释放系统资源
        - 生成测试报告
        - 清理临时文件
        
        这个方法确保测试完成后系统资源的正确释放。
        """
        if hasattr(self, 'request_handler'):
            self.request_handler.close_session()
        
    def assert_status_code(self, response, expected_status: int):
        """
        断言HTTP响应状态码
        
        验证HTTP响应的状态码是否符合预期，这是接口测试中最基本的断言。
        
        Args:
            response: HTTP响应对象，包含status_code属性
            expected_status: 期望的状态码，如200、201、400、404、500等
        
        Raises:
            AssertionError: 当实际状态码与期望状态码不匹配时抛出
        
        使用示例:
            result = self.make_request('GET', '/api/users')
            self.assert_status_code(result, 200)  # 期望返回200状态码
        """
        actual_status = response.status_code
        assert actual_status == expected_status, \
            f"期望状态码 {expected_status}, 实际状态码 {actual_status}"
            
    def assert_response_time(self, response_time: float, method: str = "GET"):
        """
        断言响应时间（使用差异化超时策略）
        
        根据不同的HTTP方法设置不同的响应时间阈值，更符合实际业务场景。
        不同方法的响应时间要求：
        - GET: 通常用于查询，响应时间要求较高
        - POST: 通常用于创建，可能涉及复杂业务逻辑
        - PUT: 通常用于更新，可能涉及数据验证和处理
        - DELETE: 通常用于删除，响应时间要求中等
        
        Args:
            response_time: 实际响应时间（秒）
            method: HTTP方法，用于确定合理的超时阈值
        
        Raises:
            AssertionError: 当响应时间超过阈值时抛出
        
        使用示例:
            result = self.make_request('GET', '/api/users')
            self.assert_response_time(result.response_time, 'GET')
        """
        # 使用差异化超时策略
        timeout_thresholds = {
            'GET': 3.0,      # GET请求通常较快，3秒内完成
            'POST': 5.0,     # POST请求可能涉及复杂逻辑，5秒内完成
            'PUT': 8.0,      # PUT请求可能涉及大量数据更新，8秒内完成
            'DELETE': 4.0    # DELETE请求通常较快，4秒内完成
        }
        
        max_time = timeout_thresholds.get(method.upper(), 5.0)
        assert response_time <= max_time, \
            f"{method}响应时间 {response_time}s 超过最大允许时间 {max_time}s"
            
    def assert_json_schema(self, response_data: Dict[str, Any], schema: Dict[str, Any]):
        """
        断言JSON响应结构
        
        验证响应数据是否符合指定的JSON Schema结构，确保API返回的数据格式正确。
        
        Args:
            response_data: 响应数据字典
            schema: JSON Schema结构定义
        
        Raises:
            ValidationError: 当响应数据不符合Schema时抛出
        
        使用示例:
            schema = {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"}
                },
                "required": ["id", "name"]
            }
            self.assert_json_schema(response.json(), schema)
        """
        self.validator.validate_json_schema(response_data, schema)
        
    def assert_contains(self, response_data: Dict[str, Any], field: str, expected_value: Any):
        """
        断言响应包含指定字段和值
        
        验证响应数据中是否包含指定的字段，并且字段值符合预期。
        
        Args:
            response_data: 响应数据字典
            field: 要检查的字段名
            expected_value: 期望的字段值
        
        Raises:
            AssertionError: 当字段不存在或值不匹配时抛出
        
        使用示例:
            response = self.make_request('GET', '/api/user/123')
            self.assert_contains(response.response_data, 'id', 123)
            self.assert_contains(response.response_data, 'name', 'John Doe')
        """
        assert field in response_data, f"响应中不包含字段 {field}"
        actual_value = response_data[field]
        assert actual_value == expected_value, \
            f"字段 {field} 期望值 {expected_value}, 实际值 {actual_value}"
            
    def make_request(self, method: str, url: str, **kwargs) -> TestResult:
        """
        发送HTTP请求并记录结果
        
        这是测试框架的核心方法，用于发送HTTP请求并自动记录测试结果。
        方法会自动处理：
        - 请求发送和响应接收
        - 响应时间统计
        - 错误处理和记录
        - 测试结果收集
        - 日志记录
        
        Args:
            method: HTTP方法（GET, POST, PUT, DELETE等）
            url: 请求URL，支持相对路径和绝对路径
            **kwargs: 其他请求参数，包括：
                - json: JSON请求体
                - data: 表单数据
                - params: URL参数
                - headers: 请求头
                - timeout: 超时时间
                - test_name: 测试名称（可选）
            
        Returns:
            TestResult: 包含完整测试信息的测试结果对象
        
        使用示例:
            # 发送GET请求
            result = self.make_request('GET', '/api/users')
            
            # 发送POST请求
            result = self.make_request('POST', '/api/users', 
                                     json={'name': 'John', 'email': 'john@example.com'})
            
            # 发送带参数的请求
            result = self.make_request('GET', '/api/users', 
                                     params={'page': 1, 'size': 10})
        """
        start_time = time.time()
        test_name = kwargs.pop('test_name', f"{method}_{url}")
        
        try:
            response = self.request_handler.request(method, url, **kwargs)
            response_time = time.time() - start_time
            
            result = TestResult(
                test_name=test_name,
                method=method,
                url=url,
                status_code=response.status_code,
                response_time=response_time,
                success=True,
                request_data=kwargs,
                response_data=response.json() if response.headers.get('content-type', '').startswith('application/json') else None
            )
        except Exception as e:
            response_time = time.time() - start_time
            result = TestResult(
                test_name=test_name,
                method=method,
                url=url,
                status_code=0,
                response_time=response_time,
                success=False,
                error_message=str(e),
                request_data=kwargs
            )
            
        self.test_results.append(result)
        return result
        
    def switch_to_mock_mode(self):
        """切换到Mock模式"""
        self.config.set_test_mode("mock")
        self.request_handler = RequestHandler(self.config)  # 重新初始化请求处理器
        self._setup_test_mode()
        self.logger.info("已切换到Mock模式")
        
    def switch_to_real_mode(self):
        """切换到真实接口模式"""
        self.config.set_test_mode("real")
        self.request_handler = RequestHandler(self.config)  # 重新初始化请求处理器
        self._setup_test_mode()
        self.logger.info("已切换到真实接口模式")
        
    def switch_to_auto_mode(self):
        """切换到自动模式"""
        self.config.set_test_mode("auto")
        self.request_handler = RequestHandler(self.config)  # 重新初始化请求处理器
        self._setup_test_mode()
        self.logger.info("已切换到自动模式")
        
    def get_current_mode_info(self) -> Dict[str, Any]:
        """
        获取当前模式信息
        
        Returns:
            Dict[str, Any]: 模式信息
        """
        return {
            "test_mode": self.config.get_test_mode(),
            "using_mock": self.config.should_use_mock(),
            "effective_url": self.config.get_effective_base_url(),
            "real_url": self.config.get_base_url(),
            "mock_url": self.config.get_mock_url(),
            "mock_fallback": self.config.is_mock_fallback_enabled()
        }
        
    def make_request_with_fallback(self, method: str, url: str, **kwargs) -> TestResult:
        """
        发送HTTP请求，支持自动回退
        
        Args:
            method: HTTP方法
            url: 请求URL
            **kwargs: 其他请求参数
            
        Returns:
            TestResult: 测试结果
        """
        start_time = time.time()
        test_name = kwargs.pop('test_name', f"{method}_{url}")
        
        # 先尝试当前配置的模式
        try:
            result = self.make_request(method, url, test_name=test_name, **kwargs)
            if result.success:
                return result
        except Exception as e:
            self.logger.warning(f"当前模式请求失败: {e}")
            
        # 如果当前是真实模式且允许回退，尝试切换到Mock
        if not self.config.should_use_mock() and self.config.is_mock_fallback_enabled():
            self.logger.info(f"尝试切换到Mock模式重试请求: {method} {url}")
            
            original_mode = self.config.get_test_mode()
            try:
                self.switch_to_mock_mode()
                result = self.make_request(method, url, test_name=f"{test_name}_mock_fallback", **kwargs)
                
                if result.success:
                    self.logger.info("使用Mock模式重试成功")
                    return result
                    
            except Exception as e:
                self.logger.error(f"Mock模式重试也失败: {e}")
            finally:
                # 恢复原模式
                self.config.set_test_mode(original_mode)
                self.request_handler = RequestHandler(self.config)
                
        # 所有尝试都失败，返回失败结果
        response_time = time.time() - start_time
        return TestResult(
            test_name=test_name,
            method=method,
            url=url,
            status_code=0,
            response_time=response_time,
            success=False,
            error_message="所有模式都尝试失败",
            request_data=kwargs
        )
        
    @abstractmethod
    def run_tests(self) -> List[Dict[str, Any]]:
        """抽象方法：运行测试用例
        
        Returns:
            List[Dict[str, Any]]: 测试结果列表
        """
        pass
        
    def get_test_summary(self) -> Dict[str, Any]:
        """获取测试汇总信息"""
        total = len(self.test_results)
        success = sum(1 for result in self.test_results if result.success)
        failed = total - success
        
        return {
            "total": total,
            "success": success,
            "failed": failed,
            "success_rate": success / total if total > 0 else 0,
            "results": self.test_results
        }