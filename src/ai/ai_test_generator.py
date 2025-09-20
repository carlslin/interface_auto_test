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
    
    def generate_comprehensive_tests(
        self,
        api_spec: Dict[str, Any],
        business_context: Optional[str] = None,
        test_requirements: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        生成全面的测试用例
        
        这是核心的测试生成方法，能够根据API规范生成多种类型的测试用例。
        包括功能测试、边界值测试、异常测试、安全测试和性能测试。
        
        Args:
            api_spec: API规范字典，通常为OpenAPI 3.0格式
            business_context: 业务上下文描述，帮助AI理解业务逻辑
            test_requirements: 特定的测试需求列表，用于定制化测试生成
            
        Returns:
            Dict: 包含各类型测试用例的综合结果
                - analysis: API分析结果
                - test_suites: 各类型测试用例集合
                - summary: 生成统计信息
        """
        self.logger.info("开始生成全面的API测试用例")
        
        # 第一步：分析API规范，了解接口结构和业务逻辑
        analysis_result = self._analyze_api_specification(api_spec, business_context)
        
        if not analysis_result.success:
            self.logger.error(f"API规范分析失败: {analysis_result.error}")
            return {"error": "API规范分析失败", "details": analysis_result.error}
        
        # 第二步：定义不同类型的测试用例
        # 每种类型都有其特定的测试目标和关注点
        test_types = [
            ("functional", "功能测试"),      # 验证基本功能是否正常
            ("boundary", "边界值测试"),     # 测试参数的边界情况
            ("negative", "异常测试"),       # 测试异常输入和错误处理
            ("security", "安全测试"),       # 验证安全机制和漏洞
            ("performance", "性能测试")     # 测试响应时间和并发处理
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