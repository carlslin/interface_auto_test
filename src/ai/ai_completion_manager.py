"""
AI接口补全管理器

统一管理和调度所有AI功能，为接口自动化测试提供全面的AI补全支持
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from .deepseek_client import DeepSeekClient, AIResponse
from .ai_test_generator import AITestGenerator


class AICompletionManager:
    """
    AI接口补全管理器 - 统一协调所有AI补全任务
    
    这是架构中的L2层（智能分析）核心组件，负责统一管理和协调
    所有AI功能模块，为所有API接口提供智能分析和补全服务。
    
    核心功能：
    1. 统一管理所有AI功能模块 - 作为中央协调器
    2. 为所有接口提供智能分析和补全 - 批量处理能力
    3. 自动优化测试用例覆盖率 - 持续改进测试质量
    4. 智能生成测试数据和断言 - 提高测试有效性
    5. 提供一键 AI补全功能 - 简化用户操作
    6. 支持批量和并发处理 - 提高处理效率
    
    架构优化亮点：
    - 整合原有的多个AI模块功能，减少复杂性
    - 统一的任务调度和结果聚合
    - 支持多级别补全策略（basic/standard/comprehensive/enterprise）
    """
    
    def __init__(self, deepseek_client: DeepSeekClient):
        """
        初始化AI补全管理器
        
        Args:
            deepseek_client: DeepSeek AI客户端实例，用于与AI服务交互
        """
        self.client = deepseek_client
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 初始化AI模块 - 架构优化后仅使用核心模块
        self.test_generator = AITestGenerator(deepseek_client)
        
        # 整合后的AI模块功能说明：
        # - 测试生成器已整合数据生成功能（generate_realistic_test_data等）
        # - API分析功能已简化并整合到测试生成器（simple_api_analysis）
        # - 代码审查功能已移除，可通过AI决策中心实现
        
        # 补全配置 - 支持灵活的配置和优化
        self.completion_config = {
            'enable_parallel': True,           # 是否启用并发处理
            'max_workers': 4,                  # 最大并发工作线程数
            'timeout': 300,                    # 请求超时时间（秒）
            'auto_optimize': True,             # 是否自动优化结果
            'enable_smart_analysis': True,     # 是否启用智能分析
            'enable_test_generation': True,    # 是否启用测试生成
            'enable_data_generation': True,    # 是否启用数据生成
            'enable_assertion_optimization': True  # 是否启用断言优化
        }
    
    def complete_all_interfaces(
        self,
        api_spec: Dict[str, Any],
        workspace_path: Path,
        business_context: Optional[str] = None,
        custom_requirements: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        为所有接口进行AI补全 - 核心补全方法
        
        这是管理器的核心方法，负责协调所有AI功能模块，
        为整个API规范中的所有接口提供全面的AI补全服务。
        
        处理流程：
        1. 分析API规范，提取所有接口信息
        2. 创建输出目录结构
        3. 执行并发/串行AI补全
        4. 汇总和分析结果
        5. 全局优化分析
        6. 生成综合报告
        
        Args:
            api_spec: API规范字典，包含所有接口定义
            workspace_path: 工作区路径，用于保存生成的文件
            business_context: 业务上下文描述，帮助AI理解业务逻辑
            custom_requirements: 自定义需求列表，用于定制化补全
            
        Returns:
            Dict: 完整的补全结果，包含统计信息、生成文件、优化建议等
        """
        self.logger.info("开始为所有接口进行AI补全")
        
        start_time = datetime.now()
        # 初始化补全结果结构
        completion_result = {
            'status': 'in_progress',
            'start_time': start_time.isoformat(),
            'api_info': api_spec.get('info', {}),
            'interfaces': {},              # 各个接口的补全结果
            'summary': {                   # 统计摘要信息
                'total_interfaces': 0,
                'completed': 0,
                'failed': 0,
                'generated_tests': 0,
                'generated_data_sets': 0,
                'reviewed_files': 0
            },
            'generated_files': [],         # 生成的文件列表
            'optimization_suggestions': [] # 全局优化建议
        }
        
        try:
            # 1. 分析API规范，提取所有接口
            interfaces = self._extract_all_interfaces(api_spec)
            completion_result['summary']['total_interfaces'] = len(interfaces)
            
            # 2. 创建输出目录结构
            self._create_output_structure(workspace_path)
            
            # 3. 执行并发AI补全
            if self.completion_config['enable_parallel']:
                completion_results = self._parallel_complete_interfaces(
                    interfaces, api_spec, workspace_path, business_context, custom_requirements
                )
            else:
                completion_results = self._sequential_complete_interfaces(
                    interfaces, api_spec, workspace_path, business_context, custom_requirements
                )
            
            # 4. 汇总结果
            for interface_id, result in completion_results.items():
                completion_result['interfaces'][interface_id] = result
                if result.get('success', False):
                    completion_result['summary']['completed'] += 1
                else:
                    completion_result['summary']['failed'] += 1
                
                # 统计生成的文件
                if 'generated_files' in result:
                    completion_result['generated_files'].extend(result['generated_files'])
                    completion_result['summary']['generated_tests'] += result.get('test_count', 0)
                    completion_result['summary']['generated_data_sets'] += result.get('data_sets', 0)
            
            # 5. 全局优化分析
            if self.completion_config['auto_optimize']:
                optimization = self._analyze_global_optimization(
                    api_spec, completion_results, workspace_path
                )
                completion_result['optimization_suggestions'] = optimization
            
            # 6. 生成补全报告
            report_path = self._generate_completion_report(completion_result, workspace_path)
            completion_result['report_path'] = str(report_path)
            
            completion_result['status'] = 'completed'
            completion_result['end_time'] = datetime.now().isoformat()
            completion_result['duration'] = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(f"AI补全完成: {completion_result['summary']['completed']}/{completion_result['summary']['total_interfaces']}")
            
            return completion_result
            
        except Exception as e:
            self.logger.error(f"AI补全失败: {str(e)}")
            completion_result['status'] = 'failed'
            completion_result['error'] = str(e)
            completion_result['end_time'] = datetime.now().isoformat()
            return completion_result
    
    def _extract_all_interfaces(self, api_spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取所有接口信息"""
        interfaces = []
        paths = api_spec.get('paths', {})
        
        for path, path_item in paths.items():
            for method, operation in path_item.items():
                if method.lower() in ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']:
                    interface = {
                        'id': f"{method.upper()}_{path}".replace('/', '_').replace('{', '').replace('}', ''),
                        'path': path,
                        'method': method.upper(),
                        'operation_id': operation.get('operationId', f"{method}_{path}"),
                        'summary': operation.get('summary', ''),
                        'description': operation.get('description', ''),
                        'tags': operation.get('tags', []),
                        'parameters': operation.get('parameters', []),
                        'request_body': operation.get('requestBody', {}),
                        'responses': operation.get('responses', {}),
                        'security': operation.get('security', []),
                        'deprecated': operation.get('deprecated', False)
                    }
                    interfaces.append(interface)
        
        return interfaces
    
    def _create_output_structure(self, workspace_path: Path):
        """创建输出目录结构"""
        directories = [
            'ai_generated',
            'ai_generated/tests',
            'ai_generated/data',
            'ai_generated/reviews',
            'ai_generated/assertions',
            'ai_generated/reports',
            'ai_generated/optimizations'
        ]
        
        for dir_name in directories:
            (workspace_path / dir_name).mkdir(parents=True, exist_ok=True)
    
    def _parallel_complete_interfaces(
        self,
        interfaces: List[Dict[str, Any]],
        api_spec: Dict[str, Any],
        workspace_path: Path,
        business_context: Optional[str],
        custom_requirements: Optional[List[str]]
    ) -> Dict[str, Dict[str, Any]]:
        """并发处理接口补全"""
        completion_results = {}
        
        with ThreadPoolExecutor(max_workers=self.completion_config['max_workers']) as executor:
            # 提交所有任务
            future_to_interface = {
                executor.submit(
                    self._complete_single_interface,
                    interface, api_spec, workspace_path, business_context, custom_requirements
                ): interface for interface in interfaces
            }
            
            # 收集结果
            for future in as_completed(future_to_interface, timeout=self.completion_config['timeout']):
                interface = future_to_interface[future]
                try:
                    result = future.result()
                    completion_results[interface['id']] = result
                except Exception as e:
                    self.logger.error(f"接口 {interface['id']} 补全失败: {str(e)}")
                    completion_results[interface['id']] = {
                        'success': False,
                        'error': str(e),
                        'interface': interface
                    }
        
        return completion_results
    
    def _sequential_complete_interfaces(
        self,
        interfaces: List[Dict[str, Any]],
        api_spec: Dict[str, Any],
        workspace_path: Path,
        business_context: Optional[str],
        custom_requirements: Optional[List[str]]
    ) -> Dict[str, Dict[str, Any]]:
        """顺序处理接口补全"""
        completion_results = {}
        
        for interface in interfaces:
            try:
                result = self._complete_single_interface(
                    interface, api_spec, workspace_path, business_context, custom_requirements
                )
                completion_results[interface['id']] = result
            except Exception as e:
                self.logger.error(f"接口 {interface['id']} 补全失败: {str(e)}")
                completion_results[interface['id']] = {
                    'success': False,
                    'error': str(e),
                    'interface': interface
                }
        
        return completion_results
    
    def _complete_single_interface(
        self,
        interface: Dict[str, Any],
        api_spec: Dict[str, Any],
        workspace_path: Path,
        business_context: Optional[str],
        custom_requirements: Optional[List[str]]
    ) -> Dict[str, Any]:
        """完成单个接口的AI补全"""
        interface_id = interface['id']
        self.logger.info(f"开始补全接口: {interface_id}")
        
        result = {
            'interface': interface,
            'success': False,
            'generated_files': [],
            'test_count': 0,
            'data_sets': 0,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # 1. 生成测试用例
            if self.completion_config['enable_test_generation']:
                test_result = self._generate_interface_tests(
                    interface, api_spec, workspace_path, business_context, custom_requirements
                )
                result.update(test_result)
            
            # 2. 生成测试数据
            if self.completion_config['enable_data_generation']:
                data_result = self._generate_interface_data(
                    interface, workspace_path, business_context
                )
                result['data_sets'] = data_result.get('data_sets', 0)
                if data_result.get('files'):
                    result['generated_files'].extend(data_result['files'])
            
            # 3. 生成智能断言
            if self.completion_config['enable_assertion_optimization']:
                assertion_result = self._generate_interface_assertions(
                    interface, workspace_path
                )
                if assertion_result.get('files'):
                    result['generated_files'].extend(assertion_result['files'])
            
            # 4. 接口特定分析
            if self.completion_config['enable_smart_analysis']:
                analysis_result = self._analyze_interface_specifics(
                    interface, api_spec, workspace_path
                )
                result['analysis'] = analysis_result
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"接口 {interface_id} 补全失败: {str(e)}")
        
        return result
    
    def _generate_interface_tests(
        self,
        interface: Dict[str, Any],
        api_spec: Dict[str, Any],
        workspace_path: Path,
        business_context: Optional[str],
        custom_requirements: Optional[List[str]]
    ) -> Dict[str, Any]:
        """为接口生成测试用例"""
        
        # 构建接口专用的API规范
        interface_spec = {
            'info': api_spec.get('info', {}),
            'paths': {
                interface['path']: {
                    interface['method'].lower(): interface
                }
            },
            'components': api_spec.get('components', {}),
            'security': api_spec.get('security', [])
        }
        
        # 生成测试用例
        test_result = self.test_generator.generate_comprehensive_tests(
            interface_spec, business_context, custom_requirements
        )
        
        if test_result.get('error'):
            return {'test_count': 0, 'generated_files': []}
        
        # 保存测试文件
        test_files = []
        interface_dir = workspace_path / 'ai_generated' / 'tests' / interface['id']
        interface_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存测试套件
        for test_type, suite in test_result.get('test_suites', {}).items():
            test_file = interface_dir / f"test_{interface['id']}_{test_type}.json"
            with open(test_file, 'w', encoding='utf-8') as f:
                json.dump(suite, f, ensure_ascii=False, indent=2)
            test_files.append(str(test_file))
        
        # 生成可执行的Python测试代码
        if test_result.get('test_suites'):
            python_code = self.test_generator.generate_executable_test_code(
                test_result['test_suites'], 'pytest', 'python'
            )
            
            if python_code.get('success'):
                python_file = interface_dir / f"test_{interface['id']}.py"
                with open(python_file, 'w', encoding='utf-8') as f:
                    f.write(python_code['code'])
                test_files.append(str(python_file))
        
        return {
            'test_count': test_result.get('summary', {}).get('total_tests', 0),
            'generated_files': test_files
        }
    
    def _generate_interface_data(
        self,
        interface: Dict[str, Any],
        workspace_path: Path,
        business_context: Optional[str]
    ) -> Dict[str, Any]:
        """为接口生成测试数据"""
        
        data_files = []
        data_sets = 0
        
        # 分析接口参数，生成对应的测试数据
        scenarios = [
            f"{interface['method']} {interface['path']}",
            interface.get('summary', ''),
            business_context or ''
        ]
        
        # 生成不同类型的测试数据
        data_types = ['realistic', 'boundary', 'invalid']
        
        for data_type in data_types:
            try:
                # 构建数据模式
                data_schema = self._extract_data_schema(interface)
                
                if data_schema:
                    if data_type == 'realistic':
                        data_result = self.test_generator.generate_realistic_test_data(
                            data_schema, count=10, business_context=' '.join(scenarios)
                        )
                    elif data_type == 'boundary':
                        data_result = self.test_generator.generate_boundary_test_data(
                            data_schema, include_edge_cases=True
                        )
                    elif data_type == 'invalid':
                        data_result = self.test_generator.generate_invalid_test_data(
                            data_schema, attack_vectors=True
                        )
                    else:
                        data_result = self.test_generator.generate_realistic_test_data(
                            data_schema, count=10
                        )
                    
                    if data_result.get('success'):
                        data_dir = workspace_path / 'ai_generated' / 'data' / interface['id']
                        data_dir.mkdir(parents=True, exist_ok=True)
                        
                        data_file = data_dir / f"{data_type}_data.json"
                        with open(data_file, 'w', encoding='utf-8') as f:
                            json.dump(data_result['data'], f, ensure_ascii=False, indent=2)
                        
                        data_files.append(str(data_file))
                        data_sets += 1
                        
            except Exception as e:
                self.logger.warning(f"生成 {data_type} 数据失败: {str(e)}")
        
        return {
            'data_sets': data_sets,
            'files': data_files
        }
    
    def _generate_interface_assertions(
        self,
        interface: Dict[str, Any],
        workspace_path: Path
    ) -> Dict[str, Any]:
        """为接口生成智能断言"""
        
        # 构建响应示例
        response_examples = []
        for status_code, response in interface.get('responses', {}).items():
            example = {
                'status_code': status_code,
                'description': response.get('description', ''),
                'content': response.get('content', {}),
                'headers': response.get('headers', {})
            }
            response_examples.append(example)
        
        if not response_examples:
            return {'files': []}
        
        # 生成断言建议
        assertion_result = self.test_generator.enhance_test_assertions(
            interface, response_examples
        )
        
        if not assertion_result.get('success'):
            return {'files': []}
        
        # 保存断言文件
        assertion_dir = workspace_path / 'ai_generated' / 'assertions' / interface['id']
        assertion_dir.mkdir(parents=True, exist_ok=True)
        
        assertion_file = assertion_dir / f"assertions_{interface['id']}.json"
        with open(assertion_file, 'w', encoding='utf-8') as f:
            json.dump(assertion_result['assertions'], f, ensure_ascii=False, indent=2)
        
        return {'files': [str(assertion_file)]}
    
    def _analyze_interface_specifics(
        self,
        interface: Dict[str, Any],
        api_spec: Dict[str, Any],
        workspace_path: Path
    ) -> Dict[str, Any]:
        """分析接口特定信息"""
        
        analysis = {
            'complexity': self._calculate_interface_complexity(interface),
            'security_level': self._analyze_security_requirements(interface),
            'data_sensitivity': self._analyze_data_sensitivity(interface),
            'performance_requirements': self._analyze_performance_needs(interface),
            'testing_priority': self._calculate_testing_priority(interface),
            'dependencies': self._analyze_interface_dependencies(interface, api_spec)
        }
        
        # 保存分析结果
        analysis_dir = workspace_path / 'ai_generated' / 'reports' / interface['id']
        analysis_dir.mkdir(parents=True, exist_ok=True)
        
        analysis_file = analysis_dir / f"analysis_{interface['id']}.json"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        
        return analysis
    
    def _extract_data_schema(self, interface: Dict[str, Any]) -> Dict[str, Any]:
        """提取接口数据模式"""
        schema = {
            'type': 'object',
            'properties': {}
        }
        
        # 从参数中提取模式
        for param in interface.get('parameters', []):
            if 'schema' in param:
                schema['properties'][param['name']] = param['schema']
        
        # 从请求体中提取模式
        request_body = interface.get('request_body', {})
        if 'content' in request_body:
            for content_type, content in request_body['content'].items():
                if 'schema' in content:
                    schema['properties'].update(content['schema'].get('properties', {}))
        
        return schema if schema['properties'] else {}
    
    def _calculate_interface_complexity(self, interface: Dict[str, Any]) -> str:
        """计算接口复杂度"""
        complexity_score = 0
        
        # 参数数量
        complexity_score += len(interface.get('parameters', []))
        
        # 响应类型数量
        complexity_score += len(interface.get('responses', {}))
        
        # 安全要求
        if interface.get('security'):
            complexity_score += 2
        
        # 请求体复杂度
        if interface.get('request_body'):
            complexity_score += 3
        
        if complexity_score <= 3:
            return 'low'
        elif complexity_score <= 7:
            return 'medium'
        else:
            return 'high'
    
    def _analyze_security_requirements(self, interface: Dict[str, Any]) -> str:
        """分析安全需求"""
        if interface.get('security'):
            return 'high'
        
        # 检查路径中的安全指示
        path = interface.get('path', '').lower()
        security_keywords = ['admin', 'auth', 'login', 'user', 'secure', 'private']
        
        if any(keyword in path for keyword in security_keywords):
            return 'medium'
        
        return 'low'
    
    def _analyze_data_sensitivity(self, interface: Dict[str, Any]) -> str:
        """分析数据敏感性"""
        sensitive_keywords = ['password', 'token', 'key', 'secret', 'email', 'phone', 'personal']
        
        # 检查参数
        for param in interface.get('parameters', []):
            if any(keyword in param.get('name', '').lower() for keyword in sensitive_keywords):
                return 'high'
        
        # 检查路径
        path = interface.get('path', '').lower()
        if any(keyword in path for keyword in sensitive_keywords):
            return 'high'
        
        return 'low'
    
    def _analyze_performance_needs(self, interface: Dict[str, Any]) -> Dict[str, Any]:
        """分析性能需求"""
        method = interface.get('method', '').upper()
        path = interface.get('path', '')
        
        # 基于HTTP方法的性能期望
        performance_expectations = {
            'GET': {'response_time': 1000, 'throughput': 'high'},
            'POST': {'response_time': 2000, 'throughput': 'medium'},
            'PUT': {'response_time': 3000, 'throughput': 'medium'},
            'DELETE': {'response_time': 2000, 'throughput': 'low'},
            'PATCH': {'response_time': 2000, 'throughput': 'medium'}
        }
        
        base_expectations = performance_expectations.get(method, {'response_time': 2000, 'throughput': 'medium'})
        
        # 根据路径调整期望
        if 'search' in path.lower() or 'query' in path.lower():
            base_expectations['response_time'] *= 2
        
        return base_expectations
    
    def _calculate_testing_priority(self, interface: Dict[str, Any]) -> str:
        """计算测试优先级"""
        priority_score = 0
        
        # HTTP方法权重
        method_weights = {'POST': 3, 'PUT': 3, 'DELETE': 3, 'GET': 2, 'PATCH': 2}
        priority_score += method_weights.get(interface.get('method', ''), 1)
        
        # 安全性权重
        if interface.get('security'):
            priority_score += 3
        
        # 标签权重（核心功能）
        core_tags = ['user', 'auth', 'payment', 'order', 'admin']
        tags = [tag.lower() for tag in interface.get('tags', [])]
        if any(tag in core_tags for tag in tags):
            priority_score += 2
        
        # 弃用接口降低优先级
        if interface.get('deprecated'):
            priority_score -= 2
        
        if priority_score >= 6:
            return 'high'
        elif priority_score >= 3:
            return 'medium'
        else:
            return 'low'
    
    def _analyze_interface_dependencies(self, interface: Dict[str, Any], api_spec: Dict[str, Any]) -> List[str]:
        """分析接口依赖关系"""
        dependencies = []
        
        # 简单的依赖分析：检查路径参数是否在其他接口中作为响应ID
        path = interface.get('path', '')
        if '{' in path and '}' in path:
            # 这个接口需要路径参数，可能依赖其他接口创建的资源
            resource_type = path.split('/')[1] if '/' in path else ''
            if resource_type:
                dependencies.append(f"可能依赖创建{resource_type}的接口")
        
        return dependencies
    
    def _analyze_global_optimization(
        self,
        api_spec: Dict[str, Any],
        completion_results: Dict[str, Dict[str, Any]],
        workspace_path: Path
    ) -> List[Dict[str, Any]]:
        """分析全局优化建议"""
        
        # 收集所有生成的测试用例
        all_tests = []
        for result in completion_results.values():
            if result.get('success') and 'interface' in result:
                all_tests.append(result['interface'])
        
        # 使用AI分析覆盖率
        coverage_analysis = self.test_generator.optimize_test_coverage(all_tests, api_spec)
        
        optimization_suggestions = []
        
        if coverage_analysis.get('success'):
            optimization_suggestions.append({
                'type': 'coverage_optimization',
                'content': coverage_analysis['analysis'],
                'priority': 'high'
            })
        
        # 添加其他优化建议
        optimization_suggestions.extend([
            {
                'type': 'test_execution_order',
                'content': '建议按照依赖关系组织测试执行顺序',
                'priority': 'medium'
            },
            {
                'type': 'data_sharing',
                'content': '考虑在测试间共享通用测试数据以提高效率',
                'priority': 'medium'
            },
            {
                'type': 'parallel_execution',
                'content': '独立的GET接口可以并行执行以提高测试效率',
                'priority': 'low'
            }
        ])
        
        return optimization_suggestions
    
    def _generate_completion_report(
        self,
        completion_result: Dict[str, Any],
        workspace_path: Path
    ) -> Optional[Path]:
        """生成补全报告"""
        
        report_content = f"""# AI接口补全报告

## 📊 补全概览

- **总接口数**: {completion_result['summary']['total_interfaces']}
- **补全成功**: {completion_result['summary']['completed']}
- **补全失败**: {completion_result['summary']['failed']}
- **生成测试用例**: {completion_result['summary']['generated_tests']}
- **生成数据集**: {completion_result['summary']['generated_data_sets']}
- **补全时间**: {completion_result.get('duration', 0):.2f}秒

## 🎯 API信息

- **名称**: {completion_result['api_info'].get('title', 'Unknown')}
- **版本**: {completion_result['api_info'].get('version', '1.0.0')}
- **描述**: {completion_result['api_info'].get('description', '无描述')}

## 📋 补全详情

"""
        
        for interface_id, result in completion_result['interfaces'].items():
            status = "✅" if result.get('success') else "❌"
            interface = result.get('interface', {})
            
            report_content += f"""### {status} {interface.get('method', 'UNKNOWN')} {interface.get('path', '/')}

- **操作ID**: {interface.get('operation_id', 'N/A')}
- **摘要**: {interface.get('summary', '无摘要')}
- **生成测试**: {result.get('test_count', 0)}个
- **生成数据集**: {result.get('data_sets', 0)}个
- **文件数量**: {len(result.get('generated_files', []))}个

"""
        
        # 添加优化建议
        if completion_result.get('optimization_suggestions'):
            report_content += "\n## 🚀 优化建议\n\n"
            for suggestion in completion_result['optimization_suggestions']:
                priority_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(suggestion['priority'], '⚪')
                report_content += f"### {priority_emoji} {suggestion['type']}\n\n{suggestion['content']}\n\n"
        
        # 保存报告
        report_path = workspace_path / 'ai_generated' / 'reports' / 'completion_report.md'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return report_path