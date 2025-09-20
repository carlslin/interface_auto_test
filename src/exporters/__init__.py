"""导出器模块

提供测试用例导出功能，支持多种格式：
- Excel (.xlsx): 结构化电子表格格式
- Markdown (.md): 文档友好的标记语言格式
- JSON (.json): 机器可读的数据交换格式
- CSV (.csv): 逗号分隔值格式
- XML (.xml): 可扩展标记语言格式

主要功能：
- 测试用例数据导出
- 自定义字段映射
- 模板化导出支持
- 批量处理能力

使用示例:
    from src.exporters import TestCaseExporter
    
    exporter = TestCaseExporter()
    test_cases = [
        {
            'name': '登录接口测试',
            'method': 'POST',
            'url': '/api/login',
            'description': '用户登录功能测试'
        }
    ]
    
    # 导出Excel格式
    exporter.export_test_cases(test_cases, 'test_cases.xlsx', 'excel')
"""

from .test_case_exporter import TestCaseExporter

__all__ = ['TestCaseExporter']