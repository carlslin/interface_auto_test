"""
测试运行器模块
负责发现、执行和管理测试用例
"""

import os
import sys
import glob
import importlib.util
import inspect
import logging
import concurrent.futures
from typing import Dict, Any, List, Optional, Tuple, Union
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

from ..core.base_test import BaseTest, TestResult
from ..utils.config_loader import ConfigLoader


@dataclass
class TestSuite:
    """测试套件数据类"""
    name: str
    file_path: str
    test_classes: List[type]
    description: Optional[str] = None


@dataclass
class ExecutionResult:
    """执行结果数据类"""
    suite_name: str
    class_name: str
    start_time: datetime
    end_time: datetime
    duration: float
    total_tests: int
    passed_tests: int
    failed_tests: int
    test_results: List[TestResult]
    success: bool
    error_message: Optional[str] = None


class TestRunner:
    """测试运行器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化测试运行器
        
        Args:
            config_path: 配置文件路径
        """
        self.config = ConfigLoader(config_path)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.test_suites: List[TestSuite] = []
        self.execution_results: List[ExecutionResult] = []
        self._setup_logging()
        
    def _setup_logging(self):
        """设置日志"""
        log_level = self.config.get('logging.level', 'INFO')
        log_format = self.config.get('logging.format', 
                                   '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format=log_format
        )
        
    def discover_tests(self, test_path: str, pattern: str = "test_*.py") -> int:
        """
        发现测试文件和测试类
        
        Args:
            test_path: 测试文件或目录路径
            pattern: 测试文件匹配模式
            
        Returns:
            int: 发现的测试套件数量
        """
        self.test_suites.clear()
        test_path_obj = Path(test_path)
        
        if test_path_obj.is_file():
            # 单个测试文件
            if test_path_obj.name.endswith('.py'):
                suite = self._load_test_suite(test_path_obj)
                if suite:
                    self.test_suites.append(suite)
        elif test_path_obj.is_dir():
            # 测试目录
            pattern_path = test_path_obj / pattern
            test_files = glob.glob(str(pattern_path), recursive=True)
            
            for test_file in test_files:
                suite = self._load_test_suite(Path(test_file))
                if suite:
                    self.test_suites.append(suite)
                    
        self.logger.info(f"发现 {len(self.test_suites)} 个测试套件")
        return len(self.test_suites)
        
    def _load_test_suite(self, file_path: Path) -> Optional[TestSuite]:
        """
        加载测试套件
        
        Args:
            file_path: 测试文件路径
            
        Returns:
            Optional[TestSuite]: 测试套件对象
        """
        try:
            # 动态导入模块
            spec = importlib.util.spec_from_file_location(
                file_path.stem, file_path
            )
            if not spec or not spec.loader:
                return None
                
            module = importlib.util.module_from_spec(spec)
            
            # 添加项目根目录到Python路径
            project_root = file_path.parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))
                
            spec.loader.exec_module(module)
            
            # 查找测试类
            test_classes = []
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, BaseTest) and 
                    obj != BaseTest):
                    test_classes.append(obj)
                    
            if test_classes:
                suite = TestSuite(
                    name=file_path.stem,
                    file_path=str(file_path),
                    test_classes=test_classes,
                    description=module.__doc__
                )
                self.logger.debug(f"加载测试套件: {suite.name}, 包含 {len(test_classes)} 个测试类")
                return suite
                
        except Exception as e:
            self.logger.error(f"加载测试套件失败: {file_path} - {str(e)}")
            
        return None
        
    def run_all_tests(self, parallel: int = 1, fail_fast: bool = False) -> Dict[str, Any]:
        """
        运行所有测试
        
        Args:
            parallel: 并行执行数量
            fail_fast: 是否在第一个失败时停止
            
        Returns:
            Dict[str, Any]: 执行结果汇总
        """
        if not self.test_suites:
            self.logger.warning("没有发现测试套件")
            return self._create_summary([])
            
        self.logger.info(f"开始执行 {len(self.test_suites)} 个测试套件")
        start_time = datetime.now()
        
        self.execution_results.clear()
        
        if parallel > 1:
            results = self._run_parallel(parallel, fail_fast)
        else:
            results = self._run_sequential(fail_fast)
            
        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        
        summary = self._create_summary(results)
        summary.update({
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'total_duration': total_duration,
            'parallel': parallel
        })
        
        self.logger.info(f"测试执行完成，总用时: {total_duration:.2f}s")
        return summary
        
    def _run_sequential(self, fail_fast: bool = False) -> List[ExecutionResult]:
        """顺序执行测试"""
        results = []
        
        for suite in self.test_suites:
            for test_class in suite.test_classes:
                result = self._execute_test_class(suite, test_class)
                results.append(result)
                
                if fail_fast and not result.success:
                    self.logger.info(f"快速失败模式：在 {result.class_name} 失败后停止执行")
                    break
                    
            if fail_fast and results and not results[-1].success:
                break
                
        return results
        
    def _run_parallel(self, parallel: int, fail_fast: bool = False) -> List[ExecutionResult]:
        """并行执行测试"""
        results = []
        
        # 准备执行任务
        tasks = []
        for suite in self.test_suites:
            for test_class in suite.test_classes:
                tasks.append((suite, test_class))
                
        with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as executor:
            # 提交任务
            future_to_task = {
                executor.submit(self._execute_test_class, suite, test_class): (suite, test_class)
                for suite, test_class in tasks
            }
            
            # 收集结果
            for future in concurrent.futures.as_completed(future_to_task):
                suite, test_class = future_to_task[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    if fail_fast and not result.success:
                        self.logger.info(f"快速失败模式：在 {result.class_name} 失败后停止执行")
                        # 取消剩余任务
                        for remaining_future in future_to_task:
                            if not remaining_future.done():
                                remaining_future.cancel()
                        break
                        
                except Exception as e:
                    self.logger.error(f"执行测试异常: {test_class.__name__} - {str(e)}")
                    
        return results
        
    def _execute_test_class(self, suite: TestSuite, test_class: type) -> ExecutionResult:
        """
        执行测试类
        
        Args:
            suite: 测试套件
            test_class: 测试类
            
        Returns:
            ExecutionResult: 执行结果
        """
        start_time = datetime.now()
        
        try:
            # 创建测试实例
            test_instance = test_class()
            
            # 执行测试
            test_instance.run_tests()
            
            # 获取测试结果
            summary = test_instance.get_test_summary()
            test_results = summary.get('results', [])
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            result = ExecutionResult(
                suite_name=suite.name,
                class_name=test_class.__name__,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                total_tests=summary.get('total', 0),
                passed_tests=summary.get('success', 0),
                failed_tests=summary.get('failed', 0),
                test_results=test_results,
                success=summary.get('failed', 0) == 0
            )
            
            self.logger.info(f"测试类执行完成: {test_class.__name__} "
                           f"({result.passed_tests}/{result.total_tests} 通过)")
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            result = ExecutionResult(
                suite_name=suite.name,
                class_name=test_class.__name__,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                total_tests=0,
                passed_tests=0,
                failed_tests=1,
                test_results=[],
                success=False,
                error_message=str(e)
            )
            
            self.logger.error(f"测试类执行失败: {test_class.__name__} - {str(e)}")
            
        return result
        
    def _create_summary(self, results: List[ExecutionResult]) -> Dict[str, Any]:
        """创建执行结果汇总"""
        total_suites = len(set(result.suite_name for result in results))
        total_classes = len(results)
        total_tests = sum(result.total_tests for result in results)
        total_passed = sum(result.passed_tests for result in results)
        total_failed = sum(result.failed_tests for result in results)
        
        success_rate = total_passed / total_tests if total_tests > 0 else 0
        
        return {
            'total_suites': total_suites,
            'total_classes': total_classes, 
            'total_tests': total_tests,
            'passed_tests': total_passed,
            'failed_tests': total_failed,
            'success_rate': success_rate,
            'results': results
        }
        
    def run_specific_tests(self, test_filters: List[str]) -> Dict[str, Any]:
        """
        运行指定的测试
        
        Args:
            test_filters: 测试过滤器列表（支持套件名、类名、方法名）
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        filtered_tasks = []
        
        for suite in self.test_suites:
            for test_class in suite.test_classes:
                # 检查是否匹配过滤器
                class_name = test_class.__name__
                suite_name = suite.name
                
                should_run = False
                for filter_pattern in test_filters:
                    if (filter_pattern in suite_name or 
                        filter_pattern in class_name or
                        filter_pattern == "*"):
                        should_run = True
                        break
                        
                if should_run:
                    filtered_tasks.append((suite, test_class))
                    
        if not filtered_tasks:
            self.logger.warning(f"没有找到匹配的测试: {test_filters}")
            return self._create_summary([])
            
        self.logger.info(f"找到 {len(filtered_tasks)} 个匹配的测试类")
        
        # 执行过滤后的测试
        results = []
        for suite, test_class in filtered_tasks:
            result = self._execute_test_class(suite, test_class)
            results.append(result)
            
        return self._create_summary(results)
        
    def get_test_info(self) -> Dict[str, Any]:
        """获取测试信息"""
        suites_info = []
        
        for suite in self.test_suites:
            classes_info = []
            for test_class in suite.test_classes:
                # 获取测试方法
                test_methods = [
                    method_name for method_name in dir(test_class)
                    if method_name.startswith('test_') and callable(getattr(test_class, method_name))
                ]
                
                classes_info.append({
                    'name': test_class.__name__,
                    'doc': test_class.__doc__,
                    'test_methods': test_methods,
                    'method_count': len(test_methods)
                })
                
            suites_info.append({
                'name': suite.name,
                'file_path': suite.file_path,
                'description': suite.description,
                'classes': classes_info,
                'class_count': len(classes_info)
            })
            
        return {
            'total_suites': len(suites_info),
            'total_classes': sum(suite['class_count'] for suite in suites_info),
            'total_methods': sum(
                sum(cls['method_count'] for cls in suite['classes'])
                for suite in suites_info
            ),
            'suites': suites_info
        }
        
    def get_execution_results(self) -> List[ExecutionResult]:
        """获取执行结果"""
        return self.execution_results.copy()
        
    def clear_results(self):
        """清除执行结果"""
        self.execution_results.clear()
        self.logger.info("清除执行结果")