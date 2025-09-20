"""
接口自动化测试框架

一个功能完整的接口自动化测试框架，支持：
- OpenAPI/Swagger文档解析
- 自动化测试脚本生成
- Mock服务器功能
- AI智能测试生成和报告生成
- 多格式测试报告和用例导出
- 多环境配置管理

主要模块：
- ai: AI智能功能模块
- cli: 命令行接口
- core: 核心测试功能
- exporters: 测试用例导出
- mock: Mock服务器
- parsers: 文档解析器
- runners: 测试运行器
- utils: 工具模块

版本: 1.0.0
作者: 接口自动化测试框架团队
"""

__version__ = "1.0.0"
__author__ = "接口自动化测试框架团队"

# 导入主要组件
from .core.base_test import BaseTest
from .utils.config_loader import ConfigLoader

# AI功能（可选）
try:
    from .ai import DeepSeekClient, AITestGenerator, AITestReporter
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

__all__ = [
    'BaseTest',
    'ConfigLoader',
    'AI_AVAILABLE'
]

# 如果AI功能可用，添加到导出列表
if AI_AVAILABLE:
    __all__.extend([
        'DeepSeekClient',
        'AITestGenerator',
        'AITestReporter'
    ])