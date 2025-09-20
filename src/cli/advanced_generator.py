#!/usr/bin/env python3
"""
高级代码生成器 - 支持认证、依赖和多种格式
"""

import click
import sys
import json
import yaml
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.parsers.openapi_parser import OpenAPIParser
from src.exporters.test_case_exporter import TestCaseExporter
from src.auth.auth_manager import AuthManager
from src.workflow.dependency_manager import DependencyManager


@click.command()
@click.option('--input', '-i', required=True, help='API文档文件路径或URL')
@click.option('--output', '-o', type=click.Path(), default='./advanced_tests', help='输出目录')
@click.option('--auth-config', type=click.Path(), help='认证配置文件路径')
@click.option('--workflow-config', type=click.Path(), help='工作流配置文件路径')
@click.option('--generate-auth-template', is_flag=True, help='生成认证配置模板')
@click.option('--generate-workflow-template', is_flag=True, help='生成工作流配置模板')
@click.option('--auth-guide', is_flag=True, help='显示认证配置指南')
@click.option('--dependency-analysis', is_flag=True, help='执行依赖分析')
@click.option('--format', '-f', multiple=True, default=['python'], 
              help='生成格式: python, postman, insomnia, curl, newman')
@click.option('--include-auth', is_flag=True, help='包含认证处理代码')
@click.option('--include-workflow', is_flag=True, help='包含工作流管理代码')
@click.option('--mock-sensitive-data', is_flag=True, help='Mock敏感数据')
@click.pass_context
def advanced_generate(ctx, input, output, auth_config, workflow_config, 
                     generate_auth_template, generate_workflow_template,
                     auth_guide, dependency_analysis, format, 
                     include_auth, include_workflow, mock_sensitive_data):
    """🚀 高级自动化测试生成器 - 支持认证、依赖、多格式"""
    
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    click.echo("🚀 高级自动化测试生成器")
    click.echo("=" * 60)
    
    # 生成配置模板
    if generate_auth_template:
        _generate_auth_template(output_path)
        return
    
    if generate_workflow_template:
        _generate_workflow_template(output_path)
        return
    
    # 显示认证指南
    if auth_guide:
        _show_auth_guide()
        return
    
    try:
        # 解析API文档
        click.echo("🔍 第一步：解析API文档")
        parser = OpenAPIParser()
        
        if input.startswith(('http://', 'https://')):
            click.echo(f"🌐 从URL加载: {input}")
            success = parser.load_from_url(input)
        else:
            click.echo(f"📁 从文件加载: {input}")
            success = parser.load_from_file(input)
        
        if not success:
            click.echo("❌ API文档解析失败", err=True)
            sys.exit(1)
        
        api_info = parser.get_api_info()
        paths = parser.get_all_paths()
        
        click.echo(f"✅ 成功解析API: {api_info.get('title', 'Unknown')} v{api_info.get('version', '1.0.0')}")
        click.echo(f"📊 发现 {len(paths)} 个API接口")
        
        # 初始化认证管理器
        auth_manager = None
        if auth_config or include_auth:
            click.echo("\n🔐 第二步：初始化认证管理")
            auth_manager = AuthManager(auth_config)
            click.echo("✅ 认证管理器初始化完成")
        
        # 初始化依赖管理器
        dependency_manager = None
        if workflow_config or include_workflow:
            click.echo("\n🔗 第三步：初始化依赖管理")
            dependency_manager = DependencyManager()
            if workflow_config and Path(workflow_config).exists():
                dependency_manager.load_workflow_config(workflow_config)
                click.echo("✅ 工作流配置加载完成")
            else:
                click.echo("⚠️ 未提供工作流配置，将生成基础依赖分析")
        
        # 执行依赖分析
        if dependency_analysis:
            click.echo("\n📈 第四步：执行依赖分析")
            analysis_result = _analyze_dependencies(paths, api_info)
            _save_dependency_analysis(output_path, analysis_result)
            click.echo("✅ 依赖分析完成")
        
        # 生成多格式测试代码
        click.echo("\n🤖 第五步：生成测试代码")
        for fmt in format:
            click.echo(f"📝 生成 {fmt.upper()} 格式...")
            
            if fmt == 'python':
                _generate_python_tests(output_path, parser, auth_manager, dependency_manager, mock_sensitive_data)
            elif fmt == 'postman':
                _generate_postman_collection(output_path, parser, auth_manager)
            elif fmt == 'insomnia':
                _generate_insomnia_collection(output_path, parser, auth_manager)
            elif fmt == 'curl':
                _generate_curl_scripts(output_path, parser, auth_manager)
            elif fmt == 'newman':
                _generate_newman_scripts(output_path, parser)
            else:
                click.echo(f"⚠️ 暂不支持的格式: {fmt}")
        
        # 生成配置文件
        click.echo("\n⚙️ 第六步：生成配置文件")
        _generate_configs(output_path, api_info, auth_manager, dependency_manager)
        
        # 生成文档
        click.echo("\n📚 第七步：生成文档")
        _generate_documentation(output_path, api_info, paths, auth_manager, dependency_manager)
        
        # 显示结果
        click.echo("\n" + "=" * 60)
        click.echo("🎉 高级自动化测试生成完成！")
        click.echo("=" * 60)
        click.echo(f"📁 输出目录: {output_path.absolute()}")
        click.echo(f"📊 生成格式: {', '.join(format)}")
        click.echo(f"🔐 认证支持: {'是' if auth_manager else '否'}")
        click.echo(f"🔗 依赖管理: {'是' if dependency_manager else '否'}")
        
        click.echo("\n📋 生成内容:")
        for item in output_path.rglob("*"):
            if item.is_file():
                relative_path = item.relative_to(output_path)
                click.echo(f"   📄 {relative_path}")
        
        click.echo("\n🛠️ 下一步操作:")
        click.echo("1. 查看生成的测试代码和配置文件")
        click.echo("2. 根据需要修改认证配置")
        click.echo("3. 配置工作流依赖关系")
        click.echo("4. 执行自动化测试")
        
    except Exception as e:
        click.echo(f"\n❌ 生成失败: {str(e)}", err=True)
        sys.exit(1)


def _generate_auth_template(output_path: Path):
    """生成认证配置模板"""
    click.echo("🔐 生成认证配置模板")
    
    auth_template = """# 认证配置文件
# 支持多种认证方式: Bearer Token, Basic Auth, API Key, OAuth2

authentication:
  # Bearer Token认证 - 适用于JWT等场景
  api_auth:
    type: bearer
    login_url: "https://your-api.com/auth/login"
    username: "your_username"  # 或使用环境变量 ${AUTH_USERNAME}
    password: "your_password"  # 或使用环境变量 ${AUTH_PASSWORD}
    token_ttl: 24  # Token有效期（小时）
    
  # Basic认证 - 适用于简单的用户名密码认证
  basic_auth:
    type: basic
    username: "admin"
    password: "password123"
    
  # API Key认证 - 适用于服务间调用
  key_auth:
    type: api_key
    api_key: "your-api-key-here"
    header_name: "X-API-Key"  # 可选，默认为X-API-Key
    
  # OAuth2认证 - 适用于第三方授权
  oauth_auth:
    type: oauth2
    client_id: "your_client_id"
    client_secret: "your_client_secret"
    token_url: "https://your-api.com/oauth/token"
    grant_type: "client_credentials"  # 或 password
    # 如果使用password模式，需要添加:
    # username: "user"
    # password: "pass"

# 环境变量配置（推荐用于敏感信息）
# export AUTH_API_AUTH_USERNAME=your_username
# export AUTH_API_AUTH_PASSWORD=your_password
# export AUTH_KEY_AUTH_API_KEY=your-api-key

# 安全提示:
# 1. 生产环境中请使用环境变量存储敏感信息
# 2. 不要将包含密码的配置文件提交到版本控制
# 3. 定期轮换API密钥和令牌
# 4. 使用最小权限原则配置认证
"""
    
    auth_file = output_path / 'config' / 'auth.yaml'
    auth_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(auth_file, 'w', encoding='utf-8') as f:
        f.write(auth_template)
    
    click.echo(f"✅ 认证配置模板已生成: {auth_file}")
    
    # 生成环境变量示例
    env_template = """# 环境变量配置示例
# 复制此文件为 .env 并填入实际值

# Bearer Token认证
AUTH_API_AUTH_USERNAME=your_username
AUTH_API_AUTH_PASSWORD=your_password

# API Key认证
AUTH_KEY_AUTH_API_KEY=your-api-key-here

# OAuth2认证
AUTH_OAUTH_AUTH_CLIENT_ID=your_client_id
AUTH_OAUTH_AUTH_CLIENT_SECRET=your_client_secret

# 基础配置
API_BASE_URL=https://your-api.com
API_TIMEOUT=30
API_RETRY_COUNT=3
"""
    
    env_file = output_path / '.env.template'
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(env_template)
    
    click.echo(f"✅ 环境变量模板已生成: {env_file}")


def _generate_workflow_template(output_path: Path):
    """生成工作流配置模板"""
    click.echo("🔗 生成工作流配置模板")
    
    manager = DependencyManager()
    workflow_template = manager.create_workflow_config_template()
    
    workflow_file = output_path / 'config' / 'workflow.yaml'
    workflow_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(workflow_file, 'w', encoding='utf-8') as f:
        f.write(workflow_template)
    
    click.echo(f"✅ 工作流配置模板已生成: {workflow_file}")


def _show_auth_guide():
    """显示认证配置指南"""
    auth_manager = AuthManager()
    guide = auth_manager.get_authentication_guide()
    click.echo(guide)


def _analyze_dependencies(paths: List[Dict[str, Any]], api_info: Dict[str, Any]) -> Dict[str, Any]:
    """分析API依赖关系"""
    
    analysis = {
        'api_info': api_info,
        'total_endpoints': len(paths),
        'auth_required_endpoints': [],
        'potential_dependencies': [],
        'suggested_workflow': [],
        'security_considerations': [],
        'recommendations': []
    }
    
    # 分析认证需求
    for path in paths:
        url = path.get('path', '')
        method = path.get('method', '').upper()
        
        # 检测需要认证的接口
        if any(keyword in url.lower() for keyword in ['/admin', '/user', '/private', '/secure']):
            analysis['auth_required_endpoints'].append({
                'method': method,
                'url': url,
                'reason': 'URL模式表明需要认证'
            })
        
        # 检测CRUD操作的依赖关系
        if method in ['PUT', 'DELETE'] and '{id}' in url:
            analysis['potential_dependencies'].append({
                'dependent': f"{method} {url}",
                'requires': f"POST {url.replace('/{id}', '')}",
                'reason': '修改/删除操作需要先创建资源'
            })
    
    # 生成建议的工作流
    workflow_steps = []
    
    # 1. 登录步骤
    login_endpoints = [p for p in paths if '/login' in p.get('path', '').lower() or '/auth' in p.get('path', '').lower()]
    if login_endpoints:
        workflow_steps.append({
            'step': 1,
            'name': '用户认证',
            'endpoints': login_endpoints,
            'description': '获取访问令牌或建立会话'
        })
    
    # 2. 基础数据查询
    get_endpoints = [p for p in paths if p.get('method', '').upper() == 'GET' and '{id}' not in p.get('path', '')]
    if get_endpoints:
        workflow_steps.append({
            'step': 2,
            'name': '基础数据查询',
            'endpoints': get_endpoints[:3],  # 取前3个
            'description': '验证基础查询功能'
        })
    
    # 3. 创建资源
    post_endpoints = [p for p in paths if p.get('method', '').upper() == 'POST' and '/login' not in p.get('path', '').lower()]
    if post_endpoints:
        workflow_steps.append({
            'step': 3,
            'name': '创建资源',
            'endpoints': post_endpoints,
            'description': '创建测试数据'
        })
    
    # 4. 更新和删除
    put_delete_endpoints = [p for p in paths if p.get('method', '').upper() in ['PUT', 'DELETE']]
    if put_delete_endpoints:
        workflow_steps.append({
            'step': 4,
            'name': '更新和删除',
            'endpoints': put_delete_endpoints,
            'description': '验证数据修改功能'
        })
    
    analysis['suggested_workflow'] = workflow_steps
    
    # 安全考虑
    analysis['security_considerations'] = [
        '使用环境变量存储敏感信息（密码、API密钥等）',
        '实现Token自动刷新机制',
        '为不同环境配置不同的认证方式',
        '实施测试数据隔离，避免影响生产数据',
        '定期轮换测试用的API密钥和密码'
    ]
    
    # 推荐事项
    analysis['recommendations'] = [
        '为CRUD操作建立依赖关系，确保正确的执行顺序',
        '实现智能重试机制，处理网络波动和临时失败',
        '添加数据清理步骤，在测试结束后清理创建的数据',
        '使用Mock服务器模拟外部依赖',
        '建立监控机制，及时发现API变更'
    ]
    
    return analysis


def _save_dependency_analysis(output_path: Path, analysis: Dict[str, Any]):
    """保存依赖分析结果"""
    analysis_file = output_path / 'reports' / 'dependency_analysis.json'
    analysis_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    
    # 生成Markdown报告
    md_report = _generate_dependency_report(analysis)
    md_file = output_path / 'reports' / 'dependency_analysis.md'
    
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(md_report)


def _generate_dependency_report(analysis: Dict[str, Any]) -> str:
    """生成依赖分析报告"""
    report = f"""# API依赖分析报告

## 📊 基本信息
- **API名称**: {analysis['api_info'].get('title', 'Unknown')}
- **版本**: {analysis['api_info'].get('version', 'Unknown')}
- **接口总数**: {analysis['total_endpoints']}
- **分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🔐 认证需求分析
"""
    
    if analysis['auth_required_endpoints']:
        report += "\n### 需要认证的接口\n"
        for endpoint in analysis['auth_required_endpoints']:
            report += f"- **{endpoint['method']} {endpoint['url']}** - {endpoint['reason']}\n"
    else:
        report += "\n✅ 未检测到明确需要认证的接口\n"
    
    report += "\n## 🔗 依赖关系分析\n"
    
    if analysis['potential_dependencies']:
        report += "\n### 潜在的依赖关系\n"
        for dep in analysis['potential_dependencies']:
            report += f"- **{dep['dependent']}** 依赖于 **{dep['requires']}** - {dep['reason']}\n"
    else:
        report += "\n✅ 未检测到明显的依赖关系\n"
    
    report += "\n## 🚀 建议的测试工作流\n"
    
    for step in analysis['suggested_workflow']:
        report += f"\n### 步骤 {step['step']}: {step['name']}\n"
        report += f"**描述**: {step['description']}\n\n"
        report += "**相关接口**:\n"
        for endpoint in step['endpoints']:
            report += f"- {endpoint.get('method', 'GET')} {endpoint.get('path', '')}\n"
    
    report += "\n## 🛡️ 安全考虑\n"
    for consideration in analysis['security_considerations']:
        report += f"- {consideration}\n"
    
    report += "\n## 💡 推荐事项\n"
    for recommendation in analysis['recommendations']:
        report += f"- {recommendation}\n"
    
    return report


def _generate_python_tests(output_path: Path, parser: OpenAPIParser, 
                          auth_manager: Optional[AuthManager] = None, 
                          dependency_manager: Optional[DependencyManager] = None,
                          mock_sensitive_data: bool = False):
    """生成Python测试代码"""
    
    api_info = parser.get_api_info()
    paths = parser.get_all_paths()
    
    # 生成增强的测试类
    test_content = f'''#!/usr/bin/env python3
"""
{api_info.get('title', 'API')} 自动化测试
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
支持功能: 认证管理, 依赖处理, 数据提取
"""

import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.base_test import BaseTest
from src.auth.auth_manager import AuthManager
from src.workflow.dependency_manager import DependencyManager, WorkflowResult


class {_to_class_name(api_info.get('title', 'API'))}Test(BaseTest):
    """
    {api_info.get('title', 'API')} 自动化测试类
    """
    
    def __init__(self, config_path: Optional[str] = None, auth_config: Optional[str] = None):
        super().__init__(config_path)
        
        # 初始化认证管理器
        {"self.auth_manager = AuthManager(auth_config)" if auth_manager else "self.auth_manager = None"}
        
        # 初始化依赖管理器
        {"self.dependency_manager = DependencyManager()" if dependency_manager else "self.dependency_manager = None"}
        
        # 测试数据存储
        self.test_data = {{}}
        self.execution_order = []
        
    def setup_authentication(self, auth_name: str = "default") -> Dict[str, str]:
        """设置认证"""
        if not self.auth_manager:
            return {{}}
        
        try:
            headers = self.auth_manager.get_auth_headers(auth_name)
            self.logger.info(f"认证设置成功: {{auth_name}}")
            return headers
        except Exception as e:
            self.logger.error(f"认证设置失败: {{str(e)}}")
            return {{}}
    
    def extract_data(self, response_data: Dict[str, Any], extractions: Dict[str, str]) -> Dict[str, Any]:
        """从响应中提取数据"""
        extracted = {{}}
        
        for alias, path in extractions.items():
            try:
                value = self._get_nested_value(response_data, path)
                if value is not None:
                    extracted[alias] = value
                    self.test_data[alias] = value
                    self.logger.info(f"数据提取成功: {{alias}} = {{value}}")
            except Exception as e:
                self.logger.warning(f"数据提取失败: {{alias}} - {{str(e)}}")
        
        return extracted
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """按路径获取嵌套值"""
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            elif isinstance(current, list) and key.isdigit():
                index = int(key)
                if 0 <= index < len(current):
                    current = current[index]
                else:
                    return None
            else:
                return None
        
        return current
    
    def substitute_variables(self, text: str) -> str:
        """替换文本中的变量"""
        if not isinstance(text, str):
            return text
            
        for key, value in self.test_data.items():
            placeholder = f"${{{{key}}}}"
            if placeholder in text:
                text = text.replace(placeholder, str(value))
        
        return text
'''
    
    # 为每个接口生成测试方法
    for i, path in enumerate(paths):
        method_name = _to_method_name(path.get('operationId') or f"{path.get('method', 'get')}_{i}")
        
        test_content += f'''
    def test_{method_name}(self, auth_required: bool = {'True' if '/login' not in path.get('path', '') else 'False'}):
        """测试 {path.get('summary', path.get('path', ''))}"""
        
        # 设置认证
        headers = {{}}
        if auth_required and self.auth_manager:
            headers.update(self.setup_authentication())
        
        # 替换URL中的变量
        url = self.substitute_variables("{path.get('path', '')}")
        
        # 准备请求参数
        params = {{}}
        request_body = None
        
        # TODO: 根据API规范设置实际参数
        {"# 示例数据 (请根据实际需求修改)" if mock_sensitive_data else ""}
        
        # 发送请求
        result = self.make_request(
            method="{path.get('method', 'GET').upper()}",
            url=url,
            params=params,
            headers=headers,
            json=request_body,
            test_name="test_{method_name}"
        )
        
        # 基础断言
        self.assert_status_code(result, {path.get('expected_status', 200)})
        
        # 提取响应数据 (如果需要)
        extractions = {{
            # 示例: 'user_id': 'id', 'token': 'access_token'
        }}
        
        if result.success and result.response_data and extractions:
            extracted = self.extract_data(result.response_data, extractions)
            self.logger.info(f"提取的数据: {{extracted}}")
        
        return result
    
    def run_tests(self):
        """运行所有测试"""
        results = []
        # 这里可以添加具体的测试调用
        return results


def _to_class_name(text: str) -> str:
    """转换为类名"""
    import re
    # 移除特殊字符，转换为驼峰命名
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    words = text.split()
    return ''.join(word.capitalize() for word in words) or 'API'


def _to_method_name(text: str) -> str:
    """转换为方法名"""
    import re
    # 移除特殊字符，转换为下划线命名
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    words = text.lower().split()
    return '_'.join(words) or 'api_method'


def _generate_postman_collection(output_path: Path, parser: OpenAPIParser, auth_manager: Optional[AuthManager]):
    """生成Postman集合"""
    collection = {
        "info": {
            "name": parser.get_api_info().get('title', 'API Collection'),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": []
    }
    
    for path in parser.get_all_paths():
        item = {
            "name": path.get('summary', path.get('path', '')),
            "request": {
                "method": path.get('method', 'GET').upper(),
                "header": [],
                "url": {
                    "raw": "{{base_url}}" + path.get('path', ''),
                    "host": ["{{base_url}}"],
                    "path": path.get('path', '').split('/')[1:]
                }
            }
        }
        collection["item"].append(item)
    
    postman_file = output_path / 'postman' / 'collection.json'
    postman_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(postman_file, 'w', encoding='utf-8') as f:
        json.dump(collection, f, ensure_ascii=False, indent=2)


def _generate_insomnia_collection(output_path: Path, parser: OpenAPIParser, auth_manager: Optional[AuthManager]):
    """生成Insomnia集合"""
    collection = {
        "_type": "export",
        "__export_format": 4,
        "resources": []
    }
    
    insomnia_file = output_path / 'insomnia' / 'collection.json'
    insomnia_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(insomnia_file, 'w', encoding='utf-8') as f:
        json.dump(collection, f, ensure_ascii=False, indent=2)


def _generate_curl_scripts(output_path: Path, parser: OpenAPIParser, auth_manager: Optional[AuthManager]):
    """生成cURL脚本"""
    script_content = "#!/bin/bash\n\n# API测试脚本\n\n"
    
    for path in parser.get_all_paths():
        method = path.get('method', 'GET').upper()
        url = path.get('path', '')
        
        script_content += f"\n# {path.get('summary', url)}\n"
        script_content += f"curl -X {method} \\\n"
        script_content += f"  \"$BASE_URL{url}\" \\\n"
        script_content += f"  -H \"Content-Type: application/json\"\n\n"
    
    curl_file = output_path / 'curl' / 'api_tests.sh'
    curl_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(curl_file, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    curl_file.chmod(0o755)  # 使脚本可执行


def _generate_newman_scripts(output_path: Path, parser: OpenAPIParser):
    """生成Newman脚本"""
    script_content = """#!/bin/bash
# Newman测试脚本

# 运行Postman集合
newman run collection.json \\
  --environment environment.json \\
  --reporters cli,html \\
  --reporter-html-export report.html
"""
    
    newman_file = output_path / 'newman' / 'run_tests.sh'
    newman_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(newman_file, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    newman_file.chmod(0o755)


def _generate_configs(output_path: Path, api_info: Dict[str, Any], 
                     auth_manager: Optional[AuthManager], 
                     dependency_manager: Optional[DependencyManager]):
    """生成配置文件"""
    config_content = f"""# {api_info.get('title', 'API')} 测试配置

global:
  timeout: 30
  retry: 3
  parallel: 4

environments:
  dev:
    base_url: "http://localhost:8080"
    headers:
      Content-Type: "application/json"
  
  test:
    base_url: "https://test-api.example.com"
    headers:
      Content-Type: "application/json"
      Authorization: "Bearer test-token"
  
  prod:
    base_url: "https://api.example.com"
    headers:
      Content-Type: "application/json"
      Authorization: "Bearer prod-token"
"""
    
    config_file = output_path / 'config' / 'test_config.yaml'
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(config_content)


def _generate_documentation(output_path: Path, api_info: Dict[str, Any], 
                           paths: List[Dict[str, Any]], 
                           auth_manager: Optional[AuthManager], 
                           dependency_manager: Optional[DependencyManager]):
    """生成文档"""
    doc_content = f"""# {api_info.get('title', 'API')} 自动化测试文档

## 项目信息
- **API名称**: {api_info.get('title', 'Unknown')}
- **版本**: {api_info.get('version', '1.0.0')}
- **描述**: {api_info.get('description', '无描述')}
- **接口数量**: {len(paths)}
- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 功能特性
- ✅ 多种认证方式支持
- ✅ 依赖管理和工作流
- ✅ 多格式测试生成
- ✅ 自动化数据提取
- ✅ 敏感数据Mock

## 使用指南

### 1. 配置认证
```bash
# 编辑认证配置
vim config/auth.yaml

# 设置环境变量
export AUTH_API_AUTH_USERNAME=your_username
export AUTH_API_AUTH_PASSWORD=your_password
```

### 2. 运行测试
```bash
# 运行Python测试
python tests/test_api.py

# 运行Postman集合
newman run postman/collection.json

# 运行cURL脚本
bash curl/api_tests.sh
```

## 接口列表
"""
    
    for i, path in enumerate(paths, 1):
        doc_content += f"\n{i}. **{path.get('method', 'GET').upper()} {path.get('path', '')}** - {path.get('summary', '无描述')}"
    
    doc_file = output_path / 'README.md'
    with open(doc_file, 'w', encoding='utf-8') as f:
        f.write(doc_content)