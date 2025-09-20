"""测试运行器模块

提供测试执行和报告生成功能：
- 测试用例发现和执行
- 并行测试支持
- 多格式测试报告生成
- 测试结果统计和分析

主要组件：
- TestRunner: 测试运行器，负责发现和执行测试
- ReportGenerator: 报告生成器，生成HTML/JSON/XML报告

使用示例:
    from src.runners import TestRunner, ReportGenerator
    
    # 执行测试
    runner = TestRunner()
    runner.discover_tests('./tests')
    summary = runner.run_all_tests(parallel=4)
    
    # 生成报告
    generator = ReportGenerator()
    generator.generate_html_report(summary, runner.execution_results)
"""

from .test_runner import TestRunner
from .report_generator import ReportGenerator

__all__ = ["TestRunner", "ReportGenerator"]