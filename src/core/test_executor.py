"""
测试执行器模块
负责执行测试用例和管理测试流程
"""

import logging
import concurrent.futures
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass
from datetime import datetime

from .base_test import BaseTest, TestResult


@dataclass
class ExecutionConfig:
    """执行配置"""
    parallel: int = 1
    timeout: int = 300
    retry_failed: bool = False
    generate_report: bool = True
    report_format: str = "html"


class TestExecutor:
    """测试执行器"""
    
    def __init__(self, config: Optional[ExecutionConfig] = None):
        """
        初始化测试执行器
        
        Args:
            config: 执行配置
        """
        self.config = config or ExecutionConfig()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.test_instances: List[BaseTest] = []
        self.execution_results: List[Dict[str, Any]] = []
        
    def add_test(self, test_instance: BaseTest):
        """
        添加测试实例
        
        Args:
            test_instance: 测试实例
        """
        self.test_instances.append(test_instance)
        
    def execute_single_test(self, test_instance: BaseTest) -> Dict[str, Any]:
        """
        执行单个测试
        
        Args:
            test_instance: 测试实例
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        start_time = datetime.now()
        
        try:
            # 执行测试前置方法
            test_instance.setup_method()
            
            # 执行测试
            test_instance.run_tests()
            
            # 执行测试后置方法
            test_instance.teardown_method()
            
            success = True
            error_message = None
            
        except Exception as e:
            success = False
            error_message = str(e)
            self.logger.error(f"测试执行失败: {test_instance.__class__.__name__} - {error_message}")
            
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # 获取测试汇总
        summary = test_instance.get_test_summary()
        
        result = {
            "test_class": test_instance.__class__.__name__,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "execution_time": execution_time,
            "success": success,
            "error_message": error_message,
            "summary": summary
        }
        
        return result
        
    def execute_parallel(self) -> List[Dict[str, Any]]:
        """
        并行执行测试
        
        Returns:
            List[Dict[str, Any]]: 执行结果列表
        """
        self.logger.info(f"开始并行执行 {len(self.test_instances)} 个测试，并发数: {self.config.parallel}")
        
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.parallel) as executor:
            # 提交所有测试任务
            future_to_test = {
                executor.submit(self.execute_single_test, test): test 
                for test in self.test_instances
            }
            
            # 收集结果
            for future in concurrent.futures.as_completed(future_to_test, timeout=self.config.timeout):
                test = future_to_test[future]
                try:
                    result = future.result()
                    results.append(result)
                    self.logger.info(f"测试完成: {test.__class__.__name__}")
                except Exception as e:
                    self.logger.error(f"测试执行异常: {test.__class__.__name__} - {str(e)}")
                    results.append({
                        "test_class": test.__class__.__name__,
                        "success": False,
                        "error_message": f"执行异常: {str(e)}",
                        "summary": {"total": 0, "success": 0, "failed": 0, "success_rate": 0}
                    })
                    
        return results
        
    def execute_sequential(self) -> List[Dict[str, Any]]:
        """
        顺序执行测试
        
        Returns:
            List[Dict[str, Any]]: 执行结果列表
        """
        self.logger.info(f"开始顺序执行 {len(self.test_instances)} 个测试")
        
        results = []
        for test in self.test_instances:
            result = self.execute_single_test(test)
            results.append(result)
            
        return results
        
    def execute(self) -> Dict[str, Any]:
        """
        执行所有测试
        
        Returns:
            Dict[str, Any]: 总体执行结果
        """
        if not self.test_instances:
            self.logger.warning("没有可执行的测试")
            return {
                "total_tests": 0,
                "results": [],
                "summary": {"total": 0, "success": 0, "failed": 0, "success_rate": 0}
            }
            
        start_time = datetime.now()
        
        # 根据并发配置选择执行方式
        if self.config.parallel > 1:
            results = self.execute_parallel()
        else:
            results = self.execute_sequential()
            
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        # 计算总体统计
        total_tests = sum(result["summary"]["total"] for result in results)
        total_success = sum(result["summary"]["success"] for result in results)
        total_failed = total_tests - total_success
        success_rate = total_success / total_tests if total_tests > 0 else 0
        
        execution_summary = {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "total_execution_time": total_time,
            "total_test_classes": len(self.test_instances),
            "total_tests": total_tests,
            "results": results,
            "summary": {
                "total": total_tests,
                "success": total_success,
                "failed": total_failed,
                "success_rate": success_rate
            }
        }
        
        self.execution_results = results
        self.logger.info(f"测试执行完成，总用时: {total_time:.2f}s，成功率: {success_rate:.2%}")
        
        return execution_summary
        
    def get_failed_tests(self) -> List[Dict[str, Any]]:
        """获取失败的测试"""
        return [result for result in self.execution_results if not result["success"]]
        
    def retry_failed_tests(self) -> Dict[str, Any]:
        """重试失败的测试"""
        failed_tests = self.get_failed_tests()
        if not failed_tests:
            self.logger.info("没有失败的测试需要重试")
            return {"message": "没有失败的测试"}
            
        self.logger.info(f"重试 {len(failed_tests)} 个失败的测试")
        
        # 重新执行失败的测试
        failed_test_names = [result["test_class"] for result in failed_tests]
        retry_instances = [
            test for test in self.test_instances 
            if test.__class__.__name__ in failed_test_names
        ]
        
        # 创建新的执行器来重试
        retry_executor = TestExecutor(self.config)
        for test in retry_instances:
            retry_executor.add_test(test)
            
        return retry_executor.execute()