"""
测试用例导出器

支持将生成的测试用例导出为多种格式：
- Excel格式 (.xlsx) - 便于测试人员查看和管理
- CSV格式 (.csv) - 便于数据处理和分析
- JSON格式 (.json) - 便于程序处理和集成
- Markdown格式 (.md) - 便于文档化和展示
- TestCase格式 (.xml) - 符合测试管理工具标准
"""

from __future__ import annotations

import json
import csv
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import logging

# 处理可选的pandas导入
try:
    import pandas as pd  # type: ignore[import-untyped]
    PANDAS_AVAILABLE = True
except ImportError:
    pd = None  # type: ignore[assignment]
    PANDAS_AVAILABLE = False


class TestCaseExporter:
    """
    测试用例导出器
    
    功能：
    1. 支持多种导出格式
    2. 生成详细的测试用例文档
    3. 包含完整的测试步骤和预期结果
    4. 支持批量导出和个性化配置
    """
    
    def __init__(self):
        """初始化导出器"""
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def export_test_cases(
        self, 
        test_cases: List[Dict[str, Any]], 
        output_path: str | Path, 
        format_type: str = 'excel',
        include_metadata: bool = True
    ) -> str:
        """
        导出测试用例
        
        Args:
            test_cases: 测试用例列表
            output_path: 输出文件路径
            format_type: 导出格式 (excel, csv, json, markdown, xml)
            include_metadata: 是否包含元数据信息
            
        Returns:
            str: 导出文件的完整路径
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 预处理测试用例数据
        processed_cases = self._process_test_cases(test_cases, include_metadata)
        
        # 根据格式类型选择导出方法
        export_methods = {
            'excel': self._export_to_excel,
            'csv': self._export_to_csv,
            'json': self._export_to_json,
            'markdown': self._export_to_markdown,
            'xml': self._export_to_xml
        }
        
        if format_type not in export_methods:
            raise ValueError(f"不支持的导出格式: {format_type}")
            
        export_method = export_methods[format_type]
        return export_method(processed_cases, output_file)
    
    def _process_test_cases(
        self, 
        test_cases: List[Dict[str, Any]], 
        include_metadata: bool
    ) -> List[Dict[str, Any]]:
        """
        预处理测试用例数据
        
        Args:
            test_cases: 原始测试用例
            include_metadata: 是否包含元数据
            
        Returns:
            List[Dict]: 处理后的测试用例
        """
        processed = []
        
        for idx, test_case in enumerate(test_cases, 1):
            processed_case = {
                'test_id': f"TC_{idx:03d}",
                'test_name': test_case.get('name', f"测试用例_{idx}"),
                'description': test_case.get('description', ''),
                'priority': test_case.get('priority', 'Medium'),
                'category': test_case.get('category', 'API测试'),
                'method': test_case.get('method', 'GET'),
                'url': test_case.get('url', ''),
                'headers': self._format_dict(test_case.get('headers', {})),
                'parameters': self._format_dict(test_case.get('parameters', {})),
                'request_body': self._format_request_body(test_case.get('request_body')),
                'expected_status': test_case.get('expected_status', 200),
                'expected_response': self._format_dict(test_case.get('expected_response', {})),
                'assertions': self._format_assertions(test_case.get('assertions', [])),
                'pre_conditions': test_case.get('pre_conditions', '无'),
                'test_steps': self._format_test_steps(test_case),
                'expected_result': test_case.get('expected_result', '请求成功，返回预期数据'),
                'tags': ', '.join(test_case.get('tags', [])),
                'created_by': test_case.get('created_by', '系统生成'),
                'created_time': test_case.get('created_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            }
            
            if include_metadata:
                processed_case.update({
                    'test_suite': test_case.get('test_suite', ''),
                    'automation_level': test_case.get('automation_level', '完全自动化'),
                    'execution_type': test_case.get('execution_type', 'API'),
                    'estimated_time': test_case.get('estimated_time', '30秒'),
                    'dependencies': test_case.get('dependencies', '无')
                })
            
            processed.append(processed_case)
        
        return processed
    
    def _format_dict(self, data: Dict[str, Any]) -> str:
        """格式化字典数据为字符串"""
        if not data:
            return ''
        return '\n'.join([f"{k}: {v}" for k, v in data.items()])
    
    def _format_request_body(self, body: Any) -> str:
        """格式化请求体"""
        if not body:
            return ''
        if isinstance(body, dict):
            return json.dumps(body, ensure_ascii=False, indent=2)
        return str(body)
    
    def _format_assertions(self, assertions: List[str]) -> str:
        """格式化断言列表"""
        if not assertions:
            return '验证响应状态码为200'
        return '\n'.join([f"• {assertion}" for assertion in assertions])
    
    def _format_test_steps(self, test_case: Dict[str, Any]) -> str:
        """生成详细的测试步骤"""
        steps = []
        step_num = 1
        
        # 前置条件
        if test_case.get('pre_conditions'):
            steps.append(f"{step_num}. 前置条件：{test_case['pre_conditions']}")
            step_num += 1
        
        # 构建请求
        method = test_case.get('method', 'GET')
        url = test_case.get('url', '')
        steps.append(f"{step_num}. 发送{method}请求到：{url}")
        step_num += 1
        
        # 设置请求头
        headers = test_case.get('headers', {})
        if headers:
            steps.append(f"{step_num}. 设置请求头：{self._format_dict(headers)}")
            step_num += 1
        
        # 设置请求参数
        params = test_case.get('parameters', {})
        if params:
            steps.append(f"{step_num}. 设置请求参数：{self._format_dict(params)}")
            step_num += 1
        
        # 设置请求体
        body = test_case.get('request_body')
        if body:
            steps.append(f"{step_num}. 设置请求体：{self._format_request_body(body)}")
            step_num += 1
        
        # 执行请求
        steps.append(f"{step_num}. 执行请求")
        step_num += 1
        
        # 验证响应
        expected_status = test_case.get('expected_status', 200)
        steps.append(f"{step_num}. 验证响应状态码为：{expected_status}")
        step_num += 1
        
        # 验证响应内容
        assertions = test_case.get('assertions', [])
        if assertions:
            for assertion in assertions:
                steps.append(f"{step_num}. 验证：{assertion}")
                step_num += 1
        
        return '\n'.join(steps)
    
    def _export_to_excel(
        self, 
        test_cases: List[Dict[str, Any]], 
        output_path: Path
    ) -> str:
        """导出为Excel格式"""
        if not PANDAS_AVAILABLE or pd is None:
            raise ImportError("需要安装pandas库才能导出Excel格式: pip install pandas openpyxl")
        
        # 确保文件扩展名
        if output_path.suffix.lower() != '.xlsx':
            output_path = output_path.with_suffix('.xlsx')
        
        # 创建DataFrame
        df = pd.DataFrame(test_cases)
        
        # 使用ExcelWriter进行格式化
        with pd.ExcelWriter(str(output_path), engine='openpyxl') as writer:
            # 写入主要数据
            df.to_excel(writer, sheet_name='测试用例', index=False)
            
            # 获取工作簿和工作表
            workbook = writer.book
            worksheet = writer.sheets['测试用例']
            
            # 调整列宽
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
            
            # 添加汇总信息工作表
            summary_data = {
                '统计项': ['测试用例总数', '导出时间', '导出格式', '包含字段数'],
                '值': [
                    len(test_cases),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'Excel (.xlsx)',
                    len(df.columns)
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='导出信息', index=False)
        
        self.logger.info(f"Excel测试用例已导出: {output_path}")
        return str(output_path)
    
    def _export_to_csv(
        self, 
        test_cases: List[Dict[str, Any]], 
        output_path: Path
    ) -> str:
        """导出为CSV格式"""
        if output_path.suffix.lower() != '.csv':
            output_path = output_path.with_suffix('.csv')
        
        if not test_cases:
            with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
                f.write("暂无测试用例数据\n")
            return str(output_path)
        
        fieldnames = list(test_cases[0].keys())
        
        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(test_cases)
        
        self.logger.info(f"CSV测试用例已导出: {output_path}")
        return str(output_path)
    
    def _export_to_json(
        self, 
        test_cases: List[Dict[str, Any]], 
        output_path: Path
    ) -> str:
        """导出为JSON格式"""
        if output_path.suffix.lower() != '.json':
            output_path = output_path.with_suffix('.json')
        
        export_data = {
            'export_info': {
                'export_time': datetime.now().isoformat(),
                'total_cases': len(test_cases),
                'format': 'JSON',
                'version': '1.0'
            },
            'test_cases': test_cases
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"JSON测试用例已导出: {output_path}")
        return str(output_path)
    
    def _export_to_markdown(
        self, 
        test_cases: List[Dict[str, Any]], 
        output_path: Path
    ) -> str:
        """导出为Markdown格式"""
        if output_path.suffix.lower() != '.md':
            output_path = output_path.with_suffix('.md')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            # 写入标题和概述
            f.write("# 📋 API测试用例文档\n\n")
            f.write(f"**导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**测试用例总数**: {len(test_cases)}\n\n")
            f.write("---\n\n")
            
            # 写入目录
            f.write("## 📚 测试用例目录\n\n")
            for case in test_cases:
                test_id = case.get('test_id', '')
                test_name = case.get('test_name', '')
                f.write(f"- [{test_id}](#{test_id.lower()}) - {test_name}\n")
            f.write("\n---\n\n")
            
            # 写入详细测试用例
            for case in test_cases:
                self._write_test_case_markdown(f, case)
        
        self.logger.info(f"Markdown测试用例已导出: {output_path}")
        return str(output_path)
    
    def _write_test_case_markdown(self, f, case: Dict[str, Any]):
        """写入单个测试用例的Markdown格式"""
        test_id = case.get('test_id', '')
        test_name = case.get('test_name', '')
        
        f.write(f"## {test_id}\n\n")
        f.write(f"### 🎯 {test_name}\n\n")
        
        # 基本信息
        f.write("#### 📝 基本信息\n\n")
        f.write(f"- **测试ID**: {test_id}\n")
        f.write(f"- **测试名称**: {test_name}\n")
        f.write(f"- **描述**: {case.get('description', '')}\n")
        f.write(f"- **优先级**: {case.get('priority', '')}\n")
        f.write(f"- **分类**: {case.get('category', '')}\n")
        f.write(f"- **标签**: {case.get('tags', '')}\n")
        f.write(f"- **创建者**: {case.get('created_by', '')}\n")
        f.write(f"- **创建时间**: {case.get('created_time', '')}\n\n")
        
        # 请求信息
        f.write("#### 🌐 请求信息\n\n")
        f.write(f"- **方法**: `{case.get('method', '')}`\n")
        f.write(f"- **URL**: `{case.get('url', '')}`\n")
        
        if case.get('headers'):
            f.write(f"- **请求头**:\n```\n{case.get('headers')}\n```\n")
        
        if case.get('parameters'):
            f.write(f"- **请求参数**:\n```\n{case.get('parameters')}\n```\n")
        
        if case.get('request_body'):
            f.write(f"- **请求体**:\n```json\n{case.get('request_body')}\n```\n")
        
        f.write("\n")
        
        # 测试步骤
        f.write("#### 🔄 测试步骤\n\n")
        f.write(f"{case.get('test_steps', '')}\n\n")
        
        # 预期结果
        f.write("#### ✅ 预期结果\n\n")
        f.write(f"- **状态码**: {case.get('expected_status', '')}\n")
        f.write(f"- **预期响应**: {case.get('expected_result', '')}\n")
        
        if case.get('assertions'):
            f.write(f"- **断言检查**:\n{case.get('assertions')}\n")
        
        f.write("\n---\n\n")
    
    def _export_to_xml(
        self, 
        test_cases: List[Dict[str, Any]], 
        output_path: Path
    ) -> str:
        """导出为XML格式（TestCase标准）"""
        if output_path.suffix.lower() != '.xml':
            output_path = output_path.with_suffix('.xml')
        
        # 创建根元素
        root = ET.Element('testsuite')
        root.set('name', 'API自动化测试用例')
        root.set('tests', str(len(test_cases)))
        root.set('timestamp', datetime.now().isoformat())
        
        for case in test_cases:
            # 创建测试用例元素
            testcase = ET.SubElement(root, 'testcase')
            testcase.set('name', case.get('test_name', ''))
            testcase.set('classname', case.get('category', 'APITest'))
            testcase.set('time', case.get('estimated_time', '30'))
            
            # 添加描述
            description = ET.SubElement(testcase, 'description')
            description.text = case.get('description', '')
            
            # 添加测试步骤
            steps = ET.SubElement(testcase, 'steps')
            steps.text = case.get('test_steps', '')
            
            # 添加预期结果
            expected = ET.SubElement(testcase, 'expected_result')
            expected.text = case.get('expected_result', '')
            
            # 添加请求信息
            request_info = ET.SubElement(testcase, 'request')
            request_info.set('method', case.get('method', ''))
            request_info.set('url', case.get('url', ''))
            request_info.text = case.get('request_body', '')
            
            # 添加属性
            properties = ET.SubElement(testcase, 'properties')
            for key in ['priority', 'tags', 'created_by', 'test_id']:
                if case.get(key):
                    prop = ET.SubElement(properties, 'property')
                    prop.set('name', key)
                    prop.set('value', str(case.get(key)))
        
        # 写入文件
        tree = ET.ElementTree(root)
        tree.write(str(output_path), encoding='utf-8', xml_declaration=True)
        
        self.logger.info(f"XML测试用例已导出: {output_path}")
        return str(output_path)
    
    def generate_test_summary(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        生成测试用例统计摘要
        
        Args:
            test_cases: 测试用例列表
            
        Returns:
            Dict: 统计摘要信息
        """
        if not test_cases:
            return {
                'total_cases': 0,
                'priorities': {},
                'categories': {},
                'methods': {},
                'creation_stats': {}
            }
        
        # 统计优先级分布
        priorities = {}
        for case in test_cases:
            priority = case.get('priority', 'Medium')
            priorities[priority] = priorities.get(priority, 0) + 1
        
        # 统计分类分布
        categories = {}
        for case in test_cases:
            category = case.get('category', 'API测试')
            categories[category] = categories.get(category, 0) + 1
        
        # 统计HTTP方法分布
        methods = {}
        for case in test_cases:
            method = case.get('method', 'GET')
            methods[method] = methods.get(method, 0) + 1
        
        return {
            'total_cases': len(test_cases),
            'priorities': priorities,
            'categories': categories,
            'methods': methods,
            'creation_stats': {
                'created_by_system': len([c for c in test_cases if c.get('created_by') == '系统生成']),
                'with_custom_assertions': len([c for c in test_cases if c.get('assertions')])
            }
        }