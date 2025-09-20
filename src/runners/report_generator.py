"""
报告生成器模块
负责生成各种格式的测试报告
"""

import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import asdict

from .test_runner import ExecutionResult


class ReportGenerator:
    """测试报告生成器"""
    
    def __init__(self, output_dir: str = "./reports"):
        """
        初始化报告生成器
        
        Args:
            output_dir: 报告输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def generate_html_report(self, summary: Dict[str, Any], 
                           results: List[ExecutionResult],
                           output_file: Optional[str] = None) -> str:
        """
        生成HTML格式报告
        
        Args:
            summary: 测试执行汇总
            results: 执行结果列表
            output_file: 输出文件名
            
        Returns:
            str: 生成的报告文件路径
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"test_report_{timestamp}.html"
            
        output_path = self.output_dir / output_file
        
        html_content = self._generate_html_content(summary, results)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        self.logger.info(f"HTML报告已生成: {output_path}")
        return str(output_path)
        
    def _generate_html_content(self, summary: Dict[str, Any], 
                             results: List[ExecutionResult]) -> str:
        """生成HTML内容"""
        # 计算统计信息
        total_duration = summary.get('total_duration', 0)
        success_rate = summary.get('success_rate', 0)
        
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>接口自动化测试报告</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #eee;
        }}
        .title {{
            color: #2c3e50;
            margin: 0;
            font-size: 2.5em;
        }}
        .subtitle {{
            color: #7f8c8d;
            margin: 10px 0;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .metric.success {{
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        }}
        .metric.failed {{
            background: linear-gradient(135deg, #f44336 0%, #da190b 100%);
        }}
        .metric.time {{
            background: linear-gradient(135deg, #2196F3 0%, #0d47a1 100%);
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .metric-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        .results-section {{
            margin-top: 30px;
        }}
        .section-title {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .test-result {{
            border: 1px solid #ddd;
            border-radius: 8px;
            margin-bottom: 15px;
            overflow: hidden;
        }}
        .test-header {{
            background: #f8f9fa;
            padding: 15px;
            border-bottom: 1px solid #ddd;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .test-name {{
            font-weight: bold;
            color: #2c3e50;
        }}
        .test-status {{
            padding: 5px 15px;
            border-radius: 20px;
            color: white;
            font-size: 0.9em;
        }}
        .status-success {{
            background-color: #28a745;
        }}
        .status-failed {{
            background-color: #dc3545;
        }}
        .test-details {{
            padding: 15px;
            background: white;
        }}
        .detail-row {{
            display: flex;
            margin-bottom: 8px;
        }}
        .detail-label {{
            font-weight: bold;
            width: 120px;
            color: #555;
        }}
        .detail-value {{
            color: #333;
        }}
        .progress-bar {{
            width: 100%;
            height: 20px;
            background-color: #f0f0f0;
            border-radius: 10px;
            overflow: hidden;
            margin: 20px 0;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #4CAF50 0%, #45a049 100%);
            transition: width 0.3s ease;
        }}
        .timestamp {{
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9em;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="title">🚀 接口自动化测试报告</h1>
            <p class="subtitle">Interface Automation Test Report</p>
        </div>
        
        <div class="summary">
            <div class="metric">
                <div class="metric-value">{summary.get('total_tests', 0)}</div>
                <div class="metric-label">总测试数</div>
            </div>
            <div class="metric success">
                <div class="metric-value">{summary.get('passed_tests', 0)}</div>
                <div class="metric-label">通过测试</div>
            </div>
            <div class="metric failed">
                <div class="metric-value">{summary.get('failed_tests', 0)}</div>
                <div class="metric-label">失败测试</div>
            </div>
            <div class="metric time">
                <div class="metric-value">{total_duration:.2f}s</div>
                <div class="metric-label">执行时间</div>
            </div>
        </div>
        
        <div class="progress-bar">
            <div class="progress-fill" style="width: {success_rate * 100:.1f}%"></div>
        </div>
        <p style="text-align: center; margin: 10px 0;">
            <strong>成功率: {success_rate * 100:.1f}%</strong>
        </p>
        
        <div class="results-section">
            <h2 class="section-title">📊 详细测试结果</h2>
"""
        
        # 添加每个测试结果
        for result in results:
            status_class = "status-success" if result.success else "status-failed"
            status_text = "✅ 通过" if result.success else "❌ 失败"
            
            html += f"""
            <div class="test-result">
                <div class="test-header">
                    <div class="test-name">{result.class_name}</div>
                    <div class="test-status {status_class}">{status_text}</div>
                </div>
                <div class="test-details">
                    <div class="detail-row">
                        <div class="detail-label">测试套件:</div>
                        <div class="detail-value">{result.suite_name}</div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label">执行时间:</div>
                        <div class="detail-value">{result.duration:.3f}s</div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label">测试数量:</div>
                        <div class="detail-value">{result.total_tests}</div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label">通过数量:</div>
                        <div class="detail-value">{result.passed_tests}</div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label">失败数量:</div>
                        <div class="detail-value">{result.failed_tests}</div>
                    </div>
"""
            
            if result.error_message:
                html += f"""
                    <div class="detail-row">
                        <div class="detail-label">错误信息:</div>
                        <div class="detail-value" style="color: #dc3545;">{result.error_message}</div>
                    </div>
"""
            
            html += """
                </div>
            </div>
"""
        
        html += f"""
        </div>
        
        <div class="timestamp">
            报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>
"""
        
        return html
        
    def generate_json_report(self, summary: Dict[str, Any], 
                           results: List[ExecutionResult],
                           output_file: Optional[str] = None) -> str:
        """
        生成JSON格式报告
        
        Args:
            summary: 测试执行汇总
            results: 执行结果列表
            output_file: 输出文件名
            
        Returns:
            str: 生成的报告文件路径
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"test_report_{timestamp}.json"
            
        output_path = self.output_dir / output_file
        
        # 转换结果为可序列化的格式
        serializable_results = []
        for result in results:
            result_dict = asdict(result)
            # 转换datetime对象为字符串
            result_dict['start_time'] = result.start_time.isoformat()
            result_dict['end_time'] = result.end_time.isoformat()
            
            # 转换测试结果
            test_results = []
            for test_result in result.test_results:
                test_result_dict = asdict(test_result)
                test_results.append(test_result_dict)
            result_dict['test_results'] = test_results
            
            serializable_results.append(result_dict)
        
        report_data = {
            "report_info": {
                "generated_at": datetime.now().isoformat(),
                "generator": "Interface AutoTest Framework",
                "version": "1.0.0"
            },
            "summary": summary,
            "results": serializable_results
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
            
        self.logger.info(f"JSON报告已生成: {output_path}")
        return str(output_path)
        
    def generate_xml_report(self, summary: Dict[str, Any], 
                          results: List[ExecutionResult],
                          output_file: Optional[str] = None) -> str:
        """
        生成XML格式报告（JUnit格式）
        
        Args:
            summary: 测试执行汇总
            results: 执行结果列表
            output_file: 输出文件名
            
        Returns:
            str: 生成的报告文件路径
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"test_report_{timestamp}.xml"
            
        output_path = self.output_dir / output_file
        
        # 创建XML结构
        testsuites = ET.Element("testsuites")
        testsuites.set("tests", str(summary.get('total_tests', 0)))
        testsuites.set("failures", str(summary.get('failed_tests', 0)))
        testsuites.set("time", str(summary.get('total_duration', 0)))
        testsuites.set("timestamp", datetime.now().isoformat())
        
        for result in results:
            testsuite = ET.SubElement(testsuites, "testsuite")
            testsuite.set("name", result.class_name)
            testsuite.set("tests", str(result.total_tests))
            testsuite.set("failures", str(result.failed_tests))
            testsuite.set("time", str(result.duration))
            testsuite.set("timestamp", result.start_time.isoformat())
            
            # 添加测试用例
            for test_result in result.test_results:
                testcase = ET.SubElement(testsuite, "testcase")
                testcase.set("classname", result.class_name)
                testcase.set("name", test_result.test_name)
                testcase.set("time", str(test_result.response_time))
                
                if not test_result.success:
                    failure = ET.SubElement(testcase, "failure")
                    failure.set("message", test_result.error_message or "Test failed")
                    failure.text = test_result.error_message or "Unknown error"
        
        # 格式化XML
        xml_str = ET.tostring(testsuites, encoding='unicode')
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent="  ")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)
            
        self.logger.info(f"XML报告已生成: {output_path}")
        return str(output_path)
        
    def generate_all_reports(self, summary: Dict[str, Any], 
                           results: List[ExecutionResult],
                           formats: Optional[List[str]] = None) -> Dict[str, str]:
        """
        生成所有格式的报告
        
        Args:
            summary: 测试执行汇总
            results: 执行结果列表
            formats: 要生成的格式列表
            
        Returns:
            Dict[str, str]: 格式到文件路径的映射
        """
        if formats is None:
            formats = ['html', 'json', 'xml']
            
        generated_reports = {}
        
        if 'html' in formats:
            html_path = self.generate_html_report(summary, results)
            generated_reports['html'] = html_path
            
        if 'json' in formats:
            json_path = self.generate_json_report(summary, results)
            generated_reports['json'] = json_path
            
        if 'xml' in formats:
            xml_path = self.generate_xml_report(summary, results)
            generated_reports['xml'] = xml_path
            
        self.logger.info(f"已生成 {len(generated_reports)} 个报告文件")
        return generated_reports