#!/usr/bin/env python3
"""
依赖管理器 - 处理接口测试的复杂依赖场景
"""

import json
import yaml
import logging
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import networkx as nx


class DependencyType(Enum):
    """依赖类型枚举"""
    DATA = "data"           # 数据依赖（需要前置接口返回的数据）
    AUTH = "auth"           # 认证依赖（需要登录后的Token）
    SEQUENCE = "sequence"   # 序列依赖（必须按顺序执行）
    CONDITION = "condition" # 条件依赖（满足特定条件才执行）
    RESOURCE = "resource"   # 资源依赖（需要先创建资源）


@dataclass
class TestStep:
    """测试步骤定义"""
    id: str
    name: str
    method: str
    url: str
    description: str = ""
    auth_required: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    dependency_type: DependencyType = DependencyType.SEQUENCE
    data_mappings: Dict[str, str] = field(default_factory=dict)
    preconditions: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    request_body: Optional[Dict[str, Any]] = None
    expected_status: int = 200
    validations: List[Dict[str, Any]] = field(default_factory=list)
    timeout: int = 30
    retry_count: int = 3
    tags: List[str] = field(default_factory=list)


@dataclass
class WorkflowResult:
    """工作流执行结果"""
    step_id: str
    success: bool
    status_code: int = 0
    response_data: Optional[Dict[str, Any]] = None
    response_time: float = 0.0
    error_message: Optional[str] = None
    extracted_data: Dict[str, Any] = field(default_factory=dict)


class DependencyManager:
    """依赖管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.steps: Dict[str, TestStep] = {}
        self.graph = nx.DiGraph()
        self.execution_results: Dict[str, WorkflowResult] = {}
        self.global_data: Dict[str, Any] = {}
    
    def load_workflow_config(self, config_path: str) -> None:
        """加载工作流配置"""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"工作流配置文件不存在: {config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            if config_path.endswith(('.yaml', '.yml')):
                config = yaml.safe_load(f)
            else:
                config = json.load(f)
        
        self._parse_workflow_config(config)
        self._build_dependency_graph()
    
    def _parse_workflow_config(self, config: Dict[str, Any]) -> None:
        """解析工作流配置"""
        workflow = config.get('workflow', {})
        
        # 解析全局设置
        global_settings = workflow.get('global', {})
        self.global_data.update(global_settings.get('variables', {}))
        
        # 解析测试步骤
        steps_config = workflow.get('steps', [])
        for step_config in steps_config:
            step = self._create_test_step(step_config)
            self.steps[step.id] = step
            self.graph.add_node(step.id)
    
    def _create_test_step(self, config: Dict[str, Any]) -> TestStep:
        """创建测试步骤"""
        return TestStep(
            id=config['id'],
            name=config.get('name', ''),
            method=config.get('method', 'GET'),
            url=config.get('url', ''),
            description=config.get('description', ''),
            auth_required=config.get('auth_required'),
            dependencies=config.get('dependencies', []),
            dependency_type=DependencyType(config.get('dependency_type', 'sequence')),
            data_mappings=config.get('data_mappings', {}),
            preconditions=config.get('preconditions', []),
            postconditions=config.get('postconditions', []),
            parameters=config.get('parameters', {}),
            headers=config.get('headers', {}),
            request_body=config.get('request_body'),
            expected_status=config.get('expected_status', 200),
            validations=config.get('validations', []),
            timeout=config.get('timeout', 30),
            retry_count=config.get('retry_count', 3),
            tags=config.get('tags', [])
        )
    
    def _build_dependency_graph(self) -> None:
        """构建依赖图"""
        for step_id, step in self.steps.items():
            for dep_id in step.dependencies:
                if dep_id in self.steps:
                    self.graph.add_edge(dep_id, step_id)
                else:
                    self.logger.warning(f"依赖步骤不存在: {dep_id} (被 {step_id} 依赖)")
    
    def get_execution_order(self, start_steps: Optional[List[str]] = None) -> List[str]:
        """获取执行顺序"""
        if start_steps:
            # 从指定步骤开始的子图
            subgraph_nodes = set()
            for start_step in start_steps:
                if start_step in self.graph:
                    subgraph_nodes.update(nx.descendants(self.graph, start_step))
                    subgraph_nodes.add(start_step)
            subgraph = self.graph.subgraph(subgraph_nodes)
        else:
            subgraph = self.graph
        
        try:
            # 拓扑排序获取执行顺序
            return list(nx.topological_sort(subgraph))
        except nx.NetworkXError as e:
            # 检测到循环依赖
            cycles = list(nx.simple_cycles(self.graph))
            if cycles:
                raise ValueError(f"检测到循环依赖: {cycles}")
            raise ValueError(f"依赖图排序失败: {str(e)}")
    
    def check_preconditions(self, step: TestStep) -> Tuple[bool, List[str]]:
        """检查前置条件"""
        failed_conditions = []
        
        # 检查依赖步骤是否成功执行
        for dep_id in step.dependencies:
            if dep_id not in self.execution_results:
                failed_conditions.append(f"依赖步骤未执行: {dep_id}")
            elif not self.execution_results[dep_id].success:
                failed_conditions.append(f"依赖步骤执行失败: {dep_id}")
        
        # 检查认证依赖
        if step.auth_required:
            # 这里应该检查认证状态
            pass
        
        # 检查自定义前置条件
        for condition in step.preconditions:
            if not self._evaluate_condition(condition):
                failed_conditions.append(f"前置条件不满足: {condition}")
        
        return len(failed_conditions) == 0, failed_conditions
    
    def _evaluate_condition(self, condition: str) -> bool:
        """评估条件表达式"""
        # 简化的条件评估，实际应该更复杂
        try:
            # 支持简单的变量检查，如 "${user_id} != null"
            if "${" in condition and "}" in condition:
                # 提取变量名
                import re
                variables = re.findall(r'\$\{([^}]+)\}', condition)
                for var in variables:
                    if var in self.global_data:
                        condition = condition.replace(f"${{{var}}}", str(self.global_data[var]))
                    else:
                        return False
            
            # 安全的条件评估（这里简化处理）
            if "!= null" in condition:
                var_name = condition.split(" != null")[0].strip()
                return var_name != "null" and var_name != ""
            
            return True
        except Exception:
            return False
    
    def resolve_data_mappings(self, step: TestStep) -> Dict[str, Any]:
        """解析数据映射"""
        resolved_data = {}
        
        for target_key, source_expr in step.data_mappings.items():
            resolved_value = self._resolve_data_expression(source_expr)
            if resolved_value is not None:
                resolved_data[target_key] = resolved_value
        
        return resolved_data
    
    def _resolve_data_expression(self, expression: str) -> Any:
        """解析数据表达式"""
        # 支持多种数据来源
        if expression.startswith("${") and expression.endswith("}"):
            # 变量引用：${variable_name}
            var_name = expression[2:-1]
            return self.global_data.get(var_name)
        
        elif expression.startswith("@{") and expression.endswith("}"):
            # 结果引用：@{step_id.response.field}
            path = expression[2:-1]
            parts = path.split('.')
            
            if len(parts) >= 2:
                step_id = parts[0]
                if step_id in self.execution_results:
                    result = self.execution_results[step_id]
                    
                    if parts[1] == 'response' and result.response_data:
                        # 访问响应数据
                        data = result.response_data
                        for field in parts[2:]:
                            if isinstance(data, dict) and field in data:
                                data = data[field]
                            else:
                                return None
                        return data
                    
                    elif parts[1] == 'extracted':
                        # 访问提取的数据
                        data = result.extracted_data
                        for field in parts[2:]:
                            if isinstance(data, dict) and field in data:
                                data = data[field]
                            else:
                                return None
                        return data
        
        # 直接返回字面值
        return expression
    
    def extract_response_data(self, step: TestStep, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """从响应中提取数据"""
        extracted = {}
        
        # 自动提取常见字段
        auto_extract_fields = ['id', 'token', 'access_token', 'user_id', 'order_id']
        for field in auto_extract_fields:
            if field in response_data:
                extracted[field] = response_data[field]
                self.global_data[f"{step.id}_{field}"] = response_data[field]
        
        # 根据步骤配置提取特定字段
        extraction_rules = step.parameters.get('extract', {})
        for alias, path in extraction_rules.items():
            value = self._extract_by_path(response_data, path)
            if value is not None:
                extracted[alias] = value
                self.global_data[alias] = value
        
        return extracted
    
    def _extract_by_path(self, data: Dict[str, Any], path: str) -> Any:
        """按路径提取数据"""
        parts = path.split('.')
        current = data
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            elif isinstance(current, list) and part.isdigit():
                index = int(part)
                if 0 <= index < len(current):
                    current = current[index]
                else:
                    return None
            else:
                return None
        
        return current
    
    def update_execution_result(self, result: WorkflowResult) -> None:
        """更新执行结果"""
        self.execution_results[result.step_id] = result
        
        # 提取响应数据
        if result.success and result.response_data:
            step = self.steps.get(result.step_id)
            if step:
                extracted = self.extract_response_data(step, result.response_data)
                result.extracted_data = extracted
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """获取工作流状态"""
        total_steps = len(self.steps)
        executed_steps = len(self.execution_results)
        successful_steps = sum(1 for result in self.execution_results.values() if result.success)
        
        return {
            'total_steps': total_steps,
            'executed_steps': executed_steps,
            'successful_steps': successful_steps,
            'failed_steps': executed_steps - successful_steps,
            'pending_steps': total_steps - executed_steps,
            'success_rate': successful_steps / executed_steps if executed_steps > 0 else 0,
            'overall_success': successful_steps == total_steps
        }
    
    def generate_workflow_report(self) -> str:
        """生成工作流报告"""
        status = self.get_workflow_status()
        
        report = f"""
# 工作流执行报告

## 📊 执行统计
- **总步骤数**: {status['total_steps']}
- **已执行**: {status['executed_steps']}
- **成功**: {status['successful_steps']}
- **失败**: {status['failed_steps']}
- **待执行**: {status['pending_steps']}
- **成功率**: {status['success_rate']:.1%}

## 📋 步骤详情
"""
        
        execution_order = self.get_execution_order()
        for step_id in execution_order:
            step = self.steps[step_id]
            result = self.execution_results.get(step_id)
            
            status_emoji = "✅" if result and result.success else "❌" if result else "⏳"
            
            report += f"""
### {status_emoji} {step.name} ({step.id})
- **方法**: {step.method}
- **URL**: {step.url}
- **依赖**: {', '.join(step.dependencies) if step.dependencies else '无'}
"""
            
            if result:
                report += f"""- **状态码**: {result.status_code}
- **响应时间**: {result.response_time:.3f}s
"""
                if result.error_message:
                    report += f"- **错误信息**: {result.error_message}\n"
                
                if result.extracted_data:
                    report += f"- **提取数据**: {json.dumps(result.extracted_data, ensure_ascii=False, indent=2)}\n"
        
        return report
    
    def create_workflow_config_template(self) -> str:
        """创建工作流配置模板"""
        template = """
# 工作流配置示例
workflow:
  # 全局设置
  global:
    variables:
      base_url: "https://api.example.com"
      api_version: "v1"
    
  # 测试步骤
  steps:
    # 1. 用户登录
    - id: "login"
      name: "用户登录"
      method: "POST"
      url: "${base_url}/auth/login"
      description: "获取访问令牌"
      request_body:
        username: "test_user"
        password: "test_password"
      expected_status: 200
      validations:
        - type: "json_path"
          path: "$.token"
          condition: "not_null"
      parameters:
        extract:
          token: "token"
          user_id: "user.id"
    
    # 2. 获取用户信息
    - id: "get_user_info"
      name: "获取用户信息"
      method: "GET"
      url: "${base_url}/users/@{login.extracted.user_id}"
      description: "获取当前用户的详细信息"
      dependencies: ["login"]
      dependency_type: "data"
      headers:
        Authorization: "Bearer @{login.extracted.token}"
      expected_status: 200
      
    # 3. 创建订单
    - id: "create_order"
      name: "创建订单"
      method: "POST"
      url: "${base_url}/orders"
      description: "创建新订单"
      dependencies: ["login"]
      dependency_type: "auth"
      headers:
        Authorization: "Bearer @{login.extracted.token}"
      request_body:
        user_id: "@{login.extracted.user_id}"
        items:
          - product_id: 1
            quantity: 2
          - product_id: 2
            quantity: 1
      expected_status: 201
      parameters:
        extract:
          order_id: "id"
          order_status: "status"
      
    # 4. 查询订单详情
    - id: "get_order_details"
      name: "查询订单详情"
      method: "GET"
      url: "${base_url}/orders/@{create_order.extracted.order_id}"
      description: "查询刚创建的订单详情"
      dependencies: ["create_order"]
      dependency_type: "data"
      headers:
        Authorization: "Bearer @{login.extracted.token}"
      expected_status: 200
      validations:
        - type: "json_path"
          path: "$.status"
          condition: "equals"
          expected: "pending"
      
    # 5. 更新订单状态
    - id: "update_order_status"
      name: "更新订单状态"
      method: "PUT"
      url: "${base_url}/orders/@{create_order.extracted.order_id}/status"
      description: "将订单状态更新为已确认"
      dependencies: ["get_order_details"]
      dependency_type: "sequence"
      headers:
        Authorization: "Bearer @{login.extracted.token}"
      request_body:
        status: "confirmed"
      expected_status: 200
      
    # 6. 用户登出
    - id: "logout"
      name: "用户登出"
      method: "POST"
      url: "${base_url}/auth/logout"
      description: "用户安全登出"
      dependencies: ["update_order_status"]
      dependency_type: "sequence"
      headers:
        Authorization: "Bearer @{login.extracted.token}"
      expected_status: 200
"""
        return template.strip()


# 使用示例
def create_sample_dependency_manager():
    """创建示例依赖管理器"""
    manager = DependencyManager()
    
    # 创建示例步骤
    login_step = TestStep(
        id="login",
        name="用户登录",
        method="POST",
        url="/auth/login",
        auth_required=None,
        request_body={"username": "test", "password": "test123"},
        parameters={"extract": {"token": "token", "user_id": "user.id"}}
    )
    
    get_profile_step = TestStep(
        id="get_profile",
        name="获取用户资料",
        method="GET",
        url="/users/@{login.extracted.user_id}",
        dependencies=["login"],
        dependency_type=DependencyType.DATA,
        headers={"Authorization": "Bearer @{login.extracted.token}"}
    )
    
    manager.steps["login"] = login_step
    manager.steps["get_profile"] = get_profile_step
    manager._build_dependency_graph()
    
    return manager