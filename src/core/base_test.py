"""
测试基类模块
提供基础的测试功能和通用方法
"""

import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from abc import ABC, abstractmethod

from ..utils.config_loader import ConfigLoader
from ..utils.validator import ResponseValidator
from .request_handler import RequestHandler


@dataclass
class TestResult:
    """测试结果数据类"""
    test_name: str
    method: str
    url: str
    status_code: int
    response_time: float
    success: bool
    error_message: Optional[str] = None
    request_data: Optional[Dict[str, Any]] = None
    response_data: Optional[Dict[str, Any]] = None


class BaseTest(ABC):
    """
    测试基类
    提供通用的测试方法和断言功能
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化测试基类
        
        Args:
            config_path: 配置文件路径
        """
        self.config = ConfigLoader(config_path)
        self.request_handler = RequestHandler(self.config)
        self.validator = ResponseValidator()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.test_results: List[TestResult] = []
        
    def setup_method(self):
        """测试方法执行前的准备工作"""
        pass
        
    def teardown_method(self):
        """测试方法执行后的清理工作"""
        pass
        
    def teardown_class(self):
        """
        测试类执行后的清理工作
        关闭连接池释放资源
        """
        if hasattr(self, 'request_handler'):
            self.request_handler.close_session()
        
    def assert_status_code(self, response, expected_status: int):
        """断言状态码"""
        actual_status = response.status_code
        assert actual_status == expected_status, \
            f"期望状态码 {expected_status}, 实际状态码 {actual_status}"
            
    def assert_response_time(self, response_time: float, method: str = "GET"):
        """
        断言响应时间（使用差异化超时策略）
        
        Args:
            response_time: 实际响应时间
            method: HTTP方法，用于确定合理的超时阈值
        """
        # 使用差异化超时策略
        timeout_thresholds = {
            'GET': 3.0,
            'POST': 5.0,
            'PUT': 8.0,
            'DELETE': 4.0
        }
        
        max_time = timeout_thresholds.get(method.upper(), 5.0)
        assert response_time <= max_time, \
            f"{method}响应时间 {response_time}s 超过最大允许时间 {max_time}s"
            
    def assert_json_schema(self, response_data: Dict[str, Any], schema: Dict[str, Any]):
        """断言JSON结构"""
        self.validator.validate_json_schema(response_data, schema)
        
    def assert_contains(self, response_data: Dict[str, Any], field: str, expected_value: Any):
        """断言响应包含指定字段和值"""
        assert field in response_data, f"响应中不包含字段 {field}"
        actual_value = response_data[field]
        assert actual_value == expected_value, \
            f"字段 {field} 期望值 {expected_value}, 实际值 {actual_value}"
            
    def make_request(self, method: str, url: str, **kwargs) -> TestResult:
        """
        发送HTTP请求并记录结果
        
        Args:
            method: HTTP方法
            url: 请求URL
            **kwargs: 其他请求参数
            
        Returns:
            TestResult: 测试结果
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