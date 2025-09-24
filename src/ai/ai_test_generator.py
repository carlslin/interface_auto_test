"""
AI测试生成器

使用DeepSeek AI智能生成高质量的测试用例、测试代码和测试数据
整合测试生成的所有相关功能，包括数据生成、用例生成、代码生成等
"""

import json
import logging
import random
from typing import Dict, Any, List, Optional, Tuple, Union
from pathlib import Path
from datetime import datetime, timedelta

from .deepseek_client import DeepSeekClient, AIResponse


class AITestGenerator:
    """
    AI驱动的综合测试生成器
    
    功能特性：
    1. 智能分析API文档，生成全面的测试用例
    2. 根据业务场景生成有意义的测试数据
    3. 自动生成边界值和异常测试场景
    4. 智能优化测试用例覆盖率
    5. 生成可执行的测试代码
    6. 综合数据生成：真实数据、边界数据、异常数据
    7. 简化的API分析功能
    """
    
    def __init__(self, deepseek_client: DeepSeekClient):
        """
        初始化AI测试生成器
        
        Args:
            deepseek_client: DeepSeek AI客户端实例，用于与AI服务交互
        """
        self.client = deepseek_client
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 预定义的数据类型映射，用于数据生成功能
        # 这些类型对应常见的API参数和响应数据类型
        self.data_types = {
            "string": "字符串",          # 文本类型，如名称、描述等
            "integer": "整数",          # 整数类型，如ID、数量等
            "number": "数字",           # 数值类型，包括小数
            "boolean": "布尔值",        # 布尔类型，真/假值
            "array": "数组",            # 数组类型，包含多个元素
            "object": "对象",           # 对象类型，嵌套结构
            "date": "日期",             # 日期类型
            "email": "邮箱",            # 邮箱格式
            "phone": "电话",            # 电话号码格式
            "url": "网址",              # URL地址格式
            "uuid": "UUID"              # 唯一标识符格式
        }
    
    def generate_comprehensive_test_scenarios(
        self,
        api_spec: Dict[str, Any],
        endpoint_path: str,
        method: str,
        business_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成全面的测试场景，包括各种错误、空值、服务失效等各种测试场景
        
        Args:
            api_spec: API规范
            endpoint_path: 接口路径
            method: HTTP方法
            business_context: 业务上下文
            
        Returns:
            Dict: 包含所有测试场景的综合结果
        """
        self.logger.info(f"为接口 {method} {endpoint_path} 生成全面测试场景")
        
        # 获取接口信息
        endpoint_info = self._extract_endpoint_info(api_spec, endpoint_path, method)
        if not endpoint_info:
            return {
                "error": f"未找到接口 {method} {endpoint_path}",
                "success": False
            }
        
        # 定义全面的测试场景类型
        test_scenarios = {
            "normal": "正常流程测试",
            "boundary": "边界值测试", 
            "null_empty": "空值和空字符串测试",
            "invalid_data": "非法数据测试",
            "type_mismatch": "数据类型不匹配测试",
            "missing_required": "缺少必需参数测试",
            "extra_fields": "额外字段测试",
            "length_limits": "长度限制测试",
            "format_validation": "格式验证测试",
            "sql_injection": "SQL注入攻击测试",
            "xss_attack": "XSS攻击测试",
            "auth_bypass": "权限绕过测试",
            "rate_limiting": "频率限制测试",
            "concurrent_access": "并发访问测试",
            "service_unavailable": "服务不可用测试",
            "timeout": "超时测试",
            "network_error": "网络错误测试",
            "load_testing": "负载测试",
            "stress_testing": "压力测试",
            "data_consistency": "数据一致性测试",
            "idempotency": "幂等性测试"
        }
        
        results = {
            "endpoint": f"{method} {endpoint_path}",
            "business_context": business_context,
            "endpoint_info": endpoint_info,
            "test_scenarios": {},
            "summary": {
                "total_scenarios": len(test_scenarios),
                "generated_cases": 0,
                "generation_time": datetime.now().isoformat()
            }
        }
        
        # 为每个场景生成测试用例
        for scenario_type, description in test_scenarios.items():
            self.logger.info(f"生成{description}用例")
            
            scenario_cases = self._generate_scenario_test_cases(
                endpoint_info, scenario_type, business_context
            )
            
            if scenario_cases.success:
                try:
                    parsed_cases = json.loads(scenario_cases.content)
                    case_count = len(parsed_cases) if isinstance(parsed_cases, list) else 1
                    
                    results["test_scenarios"][scenario_type] = {
                        "description": description,
                        "test_cases": parsed_cases,
                        "count": case_count,
                        "priority": self._get_scenario_priority(scenario_type),
                        "category": self._get_scenario_category(scenario_type)
                    }
                    
                    results["summary"]["generated_cases"] += case_count
                    
                except json.JSONDecodeError:
                    # 如果不是JSON格式，保存原始内容
                    results["test_scenarios"][scenario_type] = {
                        "description": description,
                        "content": scenario_cases.content,
                        "count": 1,
                        "priority": self._get_scenario_priority(scenario_type),
                        "category": self._get_scenario_category(scenario_type)
                    }
                    results["summary"]["generated_cases"] += 1
            else:
                self.logger.warning(f"{description}生成失败: {scenario_cases.error}")
                results["test_scenarios"][scenario_type] = {
                    "description": description,
                    "error": scenario_cases.error,
                    "count": 0
                }
        
        return results
    
    def _extract_endpoint_info(self, api_spec: Dict[str, Any], endpoint_path: str, method: str) -> Optional[Dict[str, Any]]:
        """提取接口信息"""
        paths = api_spec.get("paths", {})
        if endpoint_path not in paths:
            return None
            
        endpoint = paths[endpoint_path]
        if method.lower() not in endpoint:
            return None
            
        method_info = endpoint[method.lower()]
        
        return {
            "path": endpoint_path,
            "method": method.upper(),
            "summary": method_info.get("summary", ""),
            "description": method_info.get("description", ""),
            "parameters": method_info.get("parameters", []),
            "requestBody": method_info.get("requestBody", {}),
            "responses": method_info.get("responses", {}),
            "security": method_info.get("security", []),
            "tags": method_info.get("tags", [])
        }
    
    def _generate_scenario_test_cases(self, endpoint_info: Dict[str, Any], scenario_type: str, business_context: Optional[str] = None) -> AIResponse:
        """为特定场景生成测试用例"""
        
        context_prompt = ""
        if business_context:
            context_prompt = f"\n\n业务上下文：\n{business_context}"
        
        endpoint_str = json.dumps(endpoint_info, ensure_ascii=False, indent=2)
        
        # 为不同场景类型定义特定的提示词
        scenario_prompts = {
            "normal": "生成正常流程的测试用例，验证基本功能是否正常工作。包括有效的输入参数和正常的业务场景。",
            "boundary": "生成边界值测试用例，测试参数的最大值、最小值、临界值等。包括数值范围、字符串长度、数组大小等边界情况。",
            "null_empty": "生成空值和空字符串测试用例，测试null、空字符串、空数组、空对象等情况下的系统表现。",
            "invalid_data": "生成非法数据测试用例，包括不符合格式的数据、超出范围的值、特殊字符等。",
            "type_mismatch": "生成数据类型不匹配测试用例，测试传入错误类型的参数（如期望整数但传入字符串）。",
            "missing_required": "生成缺少必需参数的测试用例，测试不提供必填字段时的错误处理。",
            "extra_fields": "生成包含额外字段的测试用例，测试系统对未定义字段的处理能力。",
            "length_limits": "生成超出长度限制的测试用例，测试超长字符串、大数组等情况。",
            "format_validation": "生成格式验证测试用例，测试邮箱、日期、URL等特定格式的验证。",
            "sql_injection": "生成SQL注入攻击测试用例，测试系统对SQL注入攻击的防护能力。",
            "xss_attack": "生成XSS攻击测试用例，测试系统对跨站脚本攻击的防护。",
            "auth_bypass": "生成权限绕过测试用例，测试未授权访问、token伪造等安全问题。",
            "rate_limiting": "生成频率限制测试用例，测试高频访问时的限流机制。",
            "concurrent_access": "生成并发访问测试用例，测试同时多个请求的处理情况。",
            "service_unavailable": "生成服务不可用测试用例，模拟依赖服务失效的情况。",
            "timeout": "生成超时测试用例，测试请求超时的处理情况。",
            "network_error": "生成网络错误测试用例，模拟网络中断、连接失败等情况。",
            "load_testing": "生成负载测试用例，测试系统在正常负载下的性能表现。",
            "stress_testing": "生成压力测试用例，测试系统在极限条件下的稳定性。",
            "data_consistency": "生成数据一致性测试用例，验证数据的一致性和完整性。",
            "idempotency": "生成幂等性测试用例，测试重复操作的结果一致性。"
        }
        
        scenario_description = scenario_prompts.get(scenario_type, f"生成{scenario_type}测试用例")
        
        prompt = f"""请为以下接口{scenario_description}

接口信息：
{endpoint_str}{context_prompt}

请生成详细的测试用例，包含：
1. 测试用例名称和描述
2. 测试目标
3. 请求参数（路径参数、查询参数、请求体）
4. 预期响应状态码
5. 预期响应内容
6. 断言验证点
7. 测试数据说明
8. 注意事项

请以JSON数组格式返回测试用例列表。"""
        
        return self.client.generate_test_cases(
            {"endpoint": endpoint_info, "scenario": scenario_type, "prompt": prompt},
            scenario_type
        )
    
    def _get_scenario_priority(self, scenario_type: str) -> str:
        """获取场景优先级"""
        high_priority = ["normal", "missing_required", "auth_bypass", "sql_injection"]
        medium_priority = ["boundary", "invalid_data", "type_mismatch", "xss_attack"]
        low_priority = ["extra_fields", "length_limits", "format_validation"]
        
        if scenario_type in high_priority:
            return "High"
        elif scenario_type in medium_priority:
            return "Medium"
        else:
            return "Low"
    
    def _get_scenario_category(self, scenario_type: str) -> str:
        """获取场景分类"""
        functional_tests = ["normal", "boundary"]
        security_tests = ["sql_injection", "xss_attack", "auth_bypass"]
        error_tests = ["null_empty", "invalid_data", "type_mismatch", "missing_required"]
        performance_tests = ["rate_limiting", "concurrent_access", "load_testing", "stress_testing"]
        reliability_tests = ["service_unavailable", "timeout", "network_error"]
        data_tests = ["data_consistency", "idempotency"]
        
        if scenario_type in functional_tests:
            return "Functional"
        elif scenario_type in security_tests:
            return "Security"
        elif scenario_type in error_tests:
            return "Error Handling"
        elif scenario_type in performance_tests:
            return "Performance"
        elif scenario_type in reliability_tests:
            return "Reliability"
        elif scenario_type in data_tests:
            return "Data Integrity"
        else:
            return "Other"
    
    def enhance_traditional_tests(
        self,
        existing_test_file_path: str,
        api_spec: Dict[str, Any],
        enhancement_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        使用AI对传统测试进行智能化补全和增强
        
        Args:
            existing_test_file_path: 现有测试文件路径
            api_spec: API规范
            enhancement_options: 增强选项
            
        Returns:
            Dict: 增强后的测试结果
        """
        self.logger.info(f"使用AI增强传统测试: {existing_test_file_path}")
        
        try:
            # 读取现有测试文件
            with open(existing_test_file_path, 'r', encoding='utf-8') as f:
                existing_test_code = f.read()
        except FileNotFoundError:
            return {
                "success": False,
                "error": f"测试文件不存在: {existing_test_file_path}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"读取测试文件失败: {str(e)}"
            }
        
        # 分析现有测试代码
        analysis_result = self._analyze_existing_test_code(existing_test_code)
        
        if not analysis_result.success:
            return {
                "success": False,
                "error": f"测试代码分析失败: {analysis_result.error}"
            }
        
        # 默认增强选项
        default_options = {
            "add_edge_cases": True,           # 添加边界情况测试
            "add_error_handling": True,      # 添加错误处理测试
            "add_security_tests": True,      # 添加安全测试
            "improve_assertions": True,      # 改进断言
            "add_data_validation": True,     # 添加数据验证
            "add_performance_checks": True,  # 添加性能检查
            "optimize_test_data": True,      # 优化测试数据
            "add_documentation": True,       # 添加文档注释
            "refactor_structure": False      # 重构测试结构
        }
        
        if enhancement_options:
            default_options.update(enhancement_options)
        
        # 生成增强建议
        enhancement_suggestions = self._generate_enhancement_suggestions(
            existing_test_code, api_spec, analysis_result.content, default_options
        )
        
        if not enhancement_suggestions.success:
            return {
                "success": False,
                "error": f"增强建议生成失败: {enhancement_suggestions.error}"
            }
        
        # 生成增强后的测试代码
        enhanced_code_result = self._generate_enhanced_test_code(
            existing_test_code, enhancement_suggestions.content, default_options
        )
        
        if not enhanced_code_result.success:
            return {
                "success": False,
                "error": f"增强代码生成失败: {enhanced_code_result.error}"
            }
        
        return {
            "success": True,
            "original_analysis": analysis_result.content,
            "enhancement_suggestions": enhancement_suggestions.content,
            "enhanced_code": enhanced_code_result.content,
            "enhancement_options": default_options,
            "improvements_count": self._count_improvements(enhancement_suggestions.content),
            "file_path": existing_test_file_path
        }
    
    def _analyze_existing_test_code(self, test_code: str) -> AIResponse:
        """分析现有测试代码"""
        
        prompt = f"""请对以下测试代码进行深度分析：

测试代码：
```python
{test_code}
```

请从以下角度进行分析：
1. 测试覆盖范围分析
   - 测试的API接口
   - 测试场景识别
   - 数据覆盖情况

2. 测试质量评估
   - 断言的完整性
   - 错误处理覆盖
   - 边界情况考虑

3. 潜在问题识别
   - 缺少的测试场景
   - 不充分的验证
   - 可能的安全风险

4. 代码质量分析
   - 可读性和可维护性
   - 代码结构合理性
   - 最佳实践遵循情况

请提供结构化的分析结果。"""
        
        return self.client.analyze_api_doc(prompt, "test_analysis")
    
    def _generate_enhancement_suggestions(
        self, 
        test_code: str, 
        api_spec: Dict[str, Any], 
        analysis: str, 
        options: Dict[str, Any]
    ) -> AIResponse:
        """生成增强建议"""
        
        api_spec_str = json.dumps(api_spec, ensure_ascii=False, indent=2)
        options_str = json.dumps(options, ensure_ascii=False, indent=2)
        
        prompt = f"""基于以下分析结果和API规范，请提供测试代码的增强建议：

分析结果：
{analysis}

API规范：
{api_spec_str}

增强选项：
{options_str}

请提供具体的增强建议，包括：

1. 新增测试场景
   - 缺少的边界情况测试
   - 错误处理测试
   - 安全性测试
   - 性能测试

2. 改进现有测试
   - 增强断言验证
   - 优化测试数据
   - 改进代码结构

3. 添加辅助功能
   - 测试数据准备
   - 环境清理
   - 日志和报告

请以结构化的方式提供建议，包含优先级和具体实施步骤。"""
        
        return self.client.optimize_test_data({"code": test_code, "spec": api_spec}, ["enhancement"])
    
    def _generate_enhanced_test_code(self, original_code: str, suggestions: str, options: Dict[str, Any]) -> AIResponse:
        """生成增强后的测试代码"""
        
        options_str = json.dumps(options, ensure_ascii=False, indent=2)
        
        prompt = f"""请根据以下增强建议，对原始测试代码进行改进和增强：

原始测试代码：
```python
{original_code}
```

增强建议：
{suggestions}

增强选项：
{options_str}

请生成改进后的完整测试代码，确保：

1. 保持原有功能的同时添加新的测试场景
2. 改进断言和验证逻辑
3. 添加适当的注释和文档
4. 遵循代码质量最佳实践
5. 确保代码的可读性和可维护性

请返回完整的Python测试代码。"""
        
        return self.client.generate_code(prompt, "python")
    
    def _count_improvements(self, suggestions: str) -> int:
        """统计改进项数量"""
        try:
            # 简单统计建议中的改进点
            improvement_keywords = [
                "新增", "添加", "改进", "增强", "优化",
                "add", "improve", "enhance", "optimize", "fix"
            ]
            
            count = 0
            suggestions_lower = suggestions.lower()
            
            for keyword in improvement_keywords:
                count += suggestions_lower.count(keyword.lower())
            
            return count
        except:
            return 0
    
    def generate_comprehensive_tests(
        self,
        api_spec: Dict[str, Any],
        business_context: Optional[str] = None,
        test_requirements: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        生成全面的测试用例（兼容旧API）
        
        这是兼容旧版本的方法，建议使用 generate_comprehensive_test_scenarios 方法
        
        Args:
            api_spec: API规范字典
            business_context: 业务上下文描述
            test_requirements: 特定的测试需求列表
            
        Returns:
            Dict: 包含各类型测试用例的综合结果
        """
        self.logger.info("开始生成全面的API测试用例（兼容模式）")
        
        # 第一步：分析API规范
        analysis_result = self._analyze_api_specification(api_spec, business_context)
        
        if not analysis_result.success:
            self.logger.error(f"API规范分析失败: {analysis_result.error}")
            return {"error": "API规范分析失败", "details": analysis_result.error}
        
        # 第二步：定义不同类型的测试用例
        test_types = [
            ("functional", "功能测试"),
            ("boundary", "边界值测试"),
            ("negative", "异常测试"),
            ("security", "安全测试"),
            ("performance", "性能测试")
        ]
        
        # 初始化结果结构
        generated_tests = {
            "analysis": analysis_result.content,
            "test_suites": {},
            "summary": {
                "total_tests": 0,
                "generation_time": datetime.now().isoformat(),
                "api_endpoints": len(api_spec.get("paths", {}))
            }
        }
        
        for test_type, description in test_types:
            self.logger.info(f"生成{description}用例")
            
            test_cases = self._generate_test_suite(
                api_spec, test_type, analysis_result.content, test_requirements
            )
            
            if test_cases.success:
                try:
                    parsed_tests = json.loads(test_cases.content)
                    generated_tests["test_suites"][test_type] = {
                        "description": description,
                        "test_cases": parsed_tests,
                        "count": len(parsed_tests) if isinstance(parsed_tests, list) else 1
                    }
                    generated_tests["summary"]["total_tests"] += len(parsed_tests) if isinstance(parsed_tests, list) else 1
                except json.JSONDecodeError:
                    # 如果不是JSON格式，保存原始内容
                    generated_tests["test_suites"][test_type] = {
                        "description": description,
                        "content": test_cases.content,
                        "count": 1
                    }
                    generated_tests["summary"]["total_tests"] += 1
            else:
                self.logger.warning(f"{description}生成失败: {test_cases.error}")
        
        return generated_tests
    
    def _analyze_api_specification(
        self,
        api_spec: Dict[str, Any],
        business_context: Optional[str] = None
    ) -> AIResponse:
        """分析API规范"""
        
        # 构建分析提示
        context_prompt = ""
        if business_context:
            context_prompt = f"\n\n业务上下文：\n{business_context}"
        
        spec_str = json.dumps(api_spec, ensure_ascii=False, indent=2)
        
        prompt = f"""请对以下API规范进行深度分析，为测试用例生成提供指导：

API规范：
{spec_str}{context_prompt}

请从以下角度进行分析：
1. API整体架构和设计模式
2. 核心业务流程和关键接口
3. 数据模型和关系
4. 认证和授权机制
5. 错误处理和状态码
6. 潜在的安全风险点
7. 性能考虑因素
8. 测试重点和难点

请以结构化的方式提供分析结果。"""

        return self.client.analyze_api_doc(prompt, "analysis")
    
    def _generate_test_suite(
        self,
        api_spec: Dict[str, Any],
        test_type: str,
        analysis: str,
        requirements: Optional[List[str]] = None
    ) -> AIResponse:
        """生成特定类型的测试套件"""
        
        requirements_prompt = ""
        if requirements:
            requirements_prompt = f"\n\n特殊要求：\n" + "\n".join([f"- {req}" for req in requirements])
        
        test_type_prompts = {
            "functional": "功能测试用例，验证API的基本功能是否正确实现",
            "boundary": "边界值测试用例，测试参数的边界条件和极值情况",
            "negative": "异常测试用例，测试错误输入和异常场景的处理",
            "security": "安全测试用例，验证认证、授权、输入验证等安全机制",
            "performance": "性能测试用例，测试API的响应时间和并发处理能力"
        }
        
        prompt = f"""基于之前的API分析结果，请生成{test_type_prompts.get(test_type, test_type)}。

API分析：
{analysis}

请生成详细的测试用例，包含：
1. 测试用例名称和描述
2. 前置条件
3. 测试步骤
4. 测试数据
5. 预期结果
6. 断言验证点
7. 优先级和分类{requirements_prompt}

请以JSON格式返回测试用例列表，每个测试用例包含以上所有信息。"""

        return self.client.generate_test_cases(
            {"type": test_type, "prompt": prompt}, 
            test_type
        )
    
    def generate_test_data(
        self,
        data_schema: Dict[str, Any],
        scenarios: List[str],
        data_type: str = "realistic"
    ) -> Dict[str, Any]:
        """
        生成智能测试数据
        
        Args:
            data_schema: 数据模式
            scenarios: 测试场景
            data_type: 数据类型 (realistic, boundary, invalid)
            
        Returns:
            Dict: 生成的测试数据
        """
        self.logger.info(f"生成{data_type}类型的测试数据")
        
        response = self.client.optimize_test_data(data_schema, scenarios)
        
        if response.success:
            try:
                return {
                    "success": True,
                    "data": json.loads(response.content),
                    "usage": response.usage,
                    "type": data_type
                }
            except json.JSONDecodeError:
                return {
                    "success": True,
                    "data": response.content,
                    "usage": response.usage,
                    "type": data_type,
                    "format": "text"
                }
        else:
            return {
                "success": False,
                "error": response.error,
                "type": data_type
            }
    
    def enhance_test_assertions(
        self,
        endpoint_info: Dict[str, Any],
        response_examples: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        增强测试断言
        
        Args:
            endpoint_info: 端点信息
            response_examples: 响应示例
            
        Returns:
            Dict: 增强的断言建议
        """
        self.logger.info("生成智能断言建议")
        
        response = self.client.suggest_assertions(endpoint_info, response_examples)
        
        if response.success:
            return {
                "success": True,
                "assertions": response.content,
                "usage": response.usage
            }
        else:
            return {
                "success": False,
                "error": response.error
            }
    
    def generate_executable_test_code(
        self,
        test_cases: List[Dict[str, Any]],
        framework: str = "pytest",
        language: str = "python"
    ) -> Dict[str, Any]:
        """
        生成可执行的测试代码
        
        Args:
            test_cases: 测试用例列表
            framework: 测试框架
            language: 编程语言
            
        Returns:
            Dict: 生成的测试代码
        """
        self.logger.info(f"生成{language}/{framework}测试代码")
        
        test_cases_str = json.dumps(test_cases, ensure_ascii=False, indent=2)
        
        prompt = f"""请将以下测试用例转换为可执行的{language}测试代码，使用{framework}框架：

测试用例：
{test_cases_str}

要求：
1. 生成结构清晰的测试类和方法
2. 包含完整的测试逻辑和断言
3. 添加必要的注释和文档
4. 考虑测试数据的参数化
5. 包含适当的错误处理
6. 遵循{framework}最佳实践

请生成完整的测试文件代码。"""

        response = self.client.generate_code(prompt, language)
        
        if response.success:
            return {
                "success": True,
                "code": response.content,
                "framework": framework,
                "language": language,
                "usage": response.usage
            }
        else:
            return {
                "success": False,
                "error": response.error,
                "framework": framework,
                "language": language
            }
    
    def optimize_test_coverage(
        self,
        existing_tests: List[Dict[str, Any]],
        api_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        优化测试覆盖率
        
        Args:
            existing_tests: 现有测试用例
            api_spec: API规范
            
        Returns:
            Dict: 覆盖率分析和优化建议
        """
        self.logger.info("分析测试覆盖率并提供优化建议")
        
        existing_str = json.dumps(existing_tests, ensure_ascii=False, indent=2)
        spec_str = json.dumps(api_spec, ensure_ascii=False, indent=2)
        
        prompt = f"""请分析现有测试用例的覆盖率，并提供优化建议：

现有测试用例：
{existing_str}

API规范：
{spec_str}

请分析：
1. 当前测试覆盖的API端点
2. 缺失的测试场景
3. 测试深度分析
4. 覆盖率统计
5. 优化建议和补充测试用例

请提供详细的分析报告和具体的改进建议。"""

        response = self.client.chat_completion([
            {"role": "system", "content": "你是一个测试覆盖率分析专家，专门评估和优化API测试覆盖率。"},
            {"role": "user", "content": prompt}
        ])
        
        if response.success:
            return {
                "success": True,
                "analysis": response.content,
                "usage": response.usage
            }
        else:
            return {
                "success": False,
                "error": response.error
            }
    
    def generate_performance_tests(
        self,
        api_spec: Dict[str, Any],
        performance_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成性能测试用例
        
        Args:
            api_spec: API规范
            performance_requirements: 性能要求
            
        Returns:
            Dict: 性能测试用例
        """
        self.logger.info("生成性能测试用例")
        
        spec_str = json.dumps(api_spec, ensure_ascii=False, indent=2)
        req_str = json.dumps(performance_requirements, ensure_ascii=False, indent=2)
        
        prompt = f"""请为以下API生成性能测试用例：

API规范：
{spec_str}

性能要求：
{req_str}

请生成：
1. 负载测试场景
2. 压力测试场景
3. 并发测试场景
4. 容量测试场景
5. 稳定性测试场景

每个测试场景包含：
- 测试目标
- 测试配置（并发数、持续时间等）
- 测试数据准备
- 性能指标监控
- 成功标准定义
- 预期结果

请以结构化的JSON格式返回。"""

        response = self.client.generate_test_cases(
            {"spec": api_spec, "requirements": performance_requirements},
            "performance"
        )
        
        if response.success:
            try:
                return {
                    "success": True,
                    "tests": json.loads(response.content),
                    "usage": response.usage
                }
            except json.JSONDecodeError:
                return {
                    "success": True,
                    "tests": response.content,
                    "usage": response.usage,
                    "format": "text"
                }
        else:
            return {
                "success": False,
                "error": response.error
            }
    
    def validate_test_quality(
        self,
        test_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        验证测试用例质量
        
        Args:
            test_cases: 测试用例列表
            
        Returns:
            Dict: 质量评估结果
        """
        self.logger.info("评估测试用例质量")
        
        test_cases_str = json.dumps(test_cases, ensure_ascii=False, indent=2)
        
        prompt = f"""请评估以下测试用例的质量：

测试用例：
{test_cases_str}

请从以下维度进行评估：
1. 完整性 - 测试覆盖是否全面
2. 正确性 - 测试逻辑是否正确
3. 可维护性 - 测试是否易于维护
4. 可读性 - 测试描述是否清晰
5. 有效性 - 能否发现潜在问题
6. 独立性 - 测试之间是否独立
7. 可重复性 - 测试结果是否稳定

请提供：
- 每个维度的评分（1-10分）
- 具体的问题点
- 改进建议
- 整体质量评级

请以结构化的格式返回评估结果。"""

        response = self.client.chat_completion([
            {"role": "system", "content": "你是一个测试质量评估专家，专门评估测试用例的质量和有效性。"},
            {"role": "user", "content": prompt}
        ])
        
        if response.success:
            return {
                "success": True,
                "assessment": response.content,
                "usage": response.usage
            }
        else:
            return {
                "success": False,
                "error": response.error
            }
    
    # ======================== 数据生成功能 ========================
    
    def generate_realistic_test_data(
        self,
        schema: Dict[str, Any],
        count: int = 10,
        business_context: Optional[str] = None,
        locale: str = "zh_CN"
    ) -> Dict[str, Any]:
        """
        生成真实有意义的测试数据
        
        Args:
            schema: 数据模式定义
            count: 生成数据数量
            business_context: 业务上下文
            locale: 地区设置
            
        Returns:
            Dict: 生成的测试数据
        """
        self.logger.info(f"生成{count}条真实测试数据")
        
        schema_str = json.dumps(schema, ensure_ascii=False, indent=2)
        context_prompt = ""
        if business_context:
            context_prompt = f"\n\n业务上下文：\n{business_context}"
        
        prompt = f"""请根据以下数据模式生成{count}条真实有意义的测试数据：

数据模式：
{schema_str}{context_prompt}

要求：
1. 数据应该真实可信，符合业务逻辑
2. 考虑数据之间的关联性和一致性
3. 使用{locale}地区的数据格式和习惯
4. 包含多样化的数据组合
5. 确保数据格式正确
6. 避免敏感信息（如真实身份证号等）

请以JSON数组格式返回生成的数据。"""

        response = self.client.optimize_test_data(schema, [f"生成{count}条真实数据"])
        
        if response.success:
            try:
                return {
                    "success": True,
                    "data": json.loads(response.content),
                    "count": count,
                    "type": "realistic",
                    "usage": response.usage
                }
            except json.JSONDecodeError:
                return {
                    "success": True,
                    "data": response.content,
                    "count": count,
                    "type": "realistic",
                    "format": "text",
                    "usage": response.usage
                }
        else:
            return {
                "success": False,
                "error": response.error,
                "count": count,
                "type": "realistic"
            }
    
    def generate_boundary_test_data(
        self,
        schema: Dict[str, Any],
        include_edge_cases: bool = True
    ) -> Dict[str, Any]:
        """
        生成边界值测试数据
        
        Args:
            schema: 数据模式定义
            include_edge_cases: 是否包含极端情况
            
        Returns:
            Dict: 边界值测试数据
        """
        self.logger.info("生成边界值测试数据")
        
        schema_str = json.dumps(schema, ensure_ascii=False, indent=2)
        edge_prompt = "包含极端边界情况" if include_edge_cases else "适度的边界值"
        
        prompt = f"""请根据以下数据模式生成边界值测试数据：

数据模式：
{schema_str}

请生成{edge_prompt}，包括：
1. 最小值和最大值
2. 空值和null情况
3. 长度边界（最短、最长）
4. 数值边界（正负极值）
5. 特殊字符和Unicode字符
6. 数组和对象的空/满状态
7. 日期时间的边界值
8. 格式验证的临界情况

每种边界情况请提供说明和预期行为。
请以JSON格式返回，包含测试数据和描述。"""

        response = self.client.optimize_test_data(schema, ["边界值测试"])
        
        if response.success:
            try:
                return {
                    "success": True,
                    "data": json.loads(response.content),
                    "type": "boundary",
                    "include_edge_cases": include_edge_cases,
                    "usage": response.usage
                }
            except json.JSONDecodeError:
                return {
                    "success": True,
                    "data": response.content,
                    "type": "boundary",
                    "include_edge_cases": include_edge_cases,
                    "format": "text",
                    "usage": response.usage
                }
        else:
            return {
                "success": False,
                "error": response.error,
                "type": "boundary"
            }
    
    def generate_invalid_test_data(
        self,
        schema: Dict[str, Any],
        attack_vectors: bool = False
    ) -> Dict[str, Any]:
        """
        生成无效/恶意测试数据
        
        Args:
            schema: 数据模式定义
            attack_vectors: 是否包含攻击向量
            
        Returns:
            Dict: 无效测试数据
        """
        self.logger.info("生成无效/恶意测试数据")
        
        schema_str = json.dumps(schema, ensure_ascii=False, indent=2)
        attack_prompt = "包含安全攻击向量" if attack_vectors else "基本无效数据"
        
        prompt = f"""请根据以下数据模式生成无效/恶意测试数据：

数据模式：
{schema_str}

请生成{attack_prompt}，包括：
1. 格式错误的数据
2. 类型不匹配的数据
3. 超出范围的数值
4. 特殊字符和控制字符
5. SQL注入测试字符串（如果适用）
6. XSS测试字符串（如果适用）
7. 路径遍历测试字符串
8. 长度溢出测试数据

每种无效数据请提供说明和预期的错误响应。
请以JSON格式返回，包含测试数据和描述。"""

        response = self.client.optimize_test_data(schema, ["无效数据测试"])
        
        if response.success:
            try:
                return {
                    "success": True,
                    "data": json.loads(response.content),
                    "type": "invalid",
                    "attack_vectors": attack_vectors,
                    "usage": response.usage
                }
            except json.JSONDecodeError:
                return {
                    "success": True,
                    "data": response.content,
                    "type": "invalid",
                    "attack_vectors": attack_vectors,
                    "format": "text",
                    "usage": response.usage
                }
        else:
            return {
                "success": False,
                "error": response.error,
                "type": "invalid"
            }
    
    # ======================== 简化API分析功能 ========================
    
    def simple_api_analysis(
        self,
        api_spec: Dict[str, Any],
        business_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        简化的API分析功能，整合到测试生成器中
        
        Args:
            api_spec: API规范
            business_context: 业务上下文
            
        Returns:
            Dict: 分析结果
        """
        self.logger.info("执行简化API分析")
        
        try:
            paths = api_spec.get('paths', {})
            analysis_result = {
                'timestamp': datetime.now().isoformat(),
                'api_info': api_spec.get('info', {}),
                'business_context': business_context,
                'basic_stats': {
                    'total_endpoints': len(paths),
                    'methods': {},
                    'has_security': False,
                    'has_parameters': False,
                    'has_request_body': False
                },
                'recommendations': []
            }
            
            # 基本统计分析
            for path, path_item in paths.items():
                for method, operation in path_item.items():
                    if method.lower() not in ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']:
                        continue
                    
                    method_upper = method.upper()
                    analysis_result['basic_stats']['methods'][method_upper] = analysis_result['basic_stats']['methods'].get(method_upper, 0) + 1
                    
                    if operation.get('security'):
                        analysis_result['basic_stats']['has_security'] = True
                    if operation.get('parameters'):
                        analysis_result['basic_stats']['has_parameters'] = True
                    if operation.get('requestBody'):
                        analysis_result['basic_stats']['has_request_body'] = True
            
            # 生成简单建议
            analysis_result['recommendations'] = self._generate_simple_recommendations(analysis_result['basic_stats'])
            
            return {
                'success': True,
                'analysis': analysis_result
            }
            
        except Exception as e:
            self.logger.error(f"API分析失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_simple_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """生成简单的测试建议"""
        recommendations = []
        
        if stats['total_endpoints'] > 20:
            recommendations.append("推荐使用分组策略来组织测试用例")
        
        if stats['has_security']:
            recommendations.append("检测到安全配置，建议添加认证和授权测试")
        
        if 'POST' in stats['methods'] or 'PUT' in stats['methods']:
            recommendations.append("建议添加数据验证和边界值测试")
        
        if stats['has_parameters']:
            recommendations.append("参数化测试可以提高测试覆盖率")
        
        return recommendations