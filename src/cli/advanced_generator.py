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
    password: "your-password-here"
    
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
# export AUTH_KEY_AUTH_API_KEY=your-api-key-here

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
    api_title = analysis['api_info'].get('title', 'Unknown')
    api_version = analysis['api_info'].get('version', 'Unknown')
    total_endpoints = str(analysis['total_endpoints'])
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    report = "# API依赖分析报告\n\n"
    report += "## 📊 基本信息\n"
    report += "- **API名称**: " + api_title + "\n"
    report += "- **版本**: " + api_version + "\n"
    report += "- **接口总数**: " + total_endpoints + "\n"
    report += "- **分析时间**: " + current_time + "\n\n"
    report += "## 🔐 认证需求分析\n"
    
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
    
    # 使用简单字符串拼接来生成测试类
    api_title = api_info.get('title', 'API')
    generate_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    class_name = _to_class_name(api_title)
    
    # 构建文件头部
    test_content = "#!/usr/bin/env python3\n"
    test_content += '"""\n'
    test_content += api_title + " 自动化测试\n"
    test_content += "生成时间: " + generate_time + "\n"
    test_content += "支持功能: 认证管理, 依赖处理, 数据提取\n"
    test_content += '"""\n\n'
    
    # 添加导入语句
    test_content += "import sys\n"
    test_content += "import json\n"
    test_content += "import time\n"
    test_content += "import logging\n"
    test_content += "from pathlib import Path\n"
    test_content += "from typing import Dict, Any, Optional, List\n\n"
    
    test_content += "# 添加项目路径\n"
    test_content += "project_root = Path(__file__).parent.parent\n"
    test_content += "sys.path.insert(0, str(project_root))\n\n"
    
    test_content += "from src.core.base_test import BaseTest\n"
    test_content += "from src.auth.auth_manager import AuthManager\n"
    test_content += "from src.workflow.dependency_manager import DependencyManager, WorkflowResult\n\n\n"
    
    # 构建类定义
    test_content += "class " + class_name + "Test(BaseTest):\n"
    test_content += '    """\n'
    test_content += "    " + api_title + " 自动化测试类\n"
    test_content += '    """\n\n'
    
    # __init__ 方法
    test_content += "    def __init__(self, config_path: Optional[str] = None, auth_config: Optional[str] = None):\n"
    test_content += "        super().__init__(config_path)\n\n"
    
    # 初始化认证管理器
    if auth_manager:
        test_content += "        # 初始化认证管理器\n"
        test_content += "        self.auth_manager = AuthManager(auth_config)\n\n"
    else:
        test_content += "        # 初始化认证管理器\n"
        test_content += "        self.auth_manager = None\n\n"
    
    # 初始化依赖管理器
    if dependency_manager:
        test_content += "        # 初始化依赖管理器\n"
        test_content += "        self.dependency_manager = DependencyManager()\n\n"
    else:
        test_content += "        # 初始化依赖管理器\n"
        test_content += "        self.dependency_manager = None\n\n"
    
    test_content += "        # 测试数据存储\n"
    test_content += "        self.test_data = {}\n"
    test_content += "        self.execution_order = []\n\n"
    
def _generate_helper_methods():
    """生成帮助方法"""
    helper_content = ""
    helper_content += "    def setup_authentication(self, auth_name: str = \"default\") -> Dict[str, str]:\n"
    helper_content += '        """设置认证"""\n'
    helper_content += "        if not self.auth_manager:\n"
    helper_content += "            return {}\n\n"
    helper_content += "        try:\n"
    helper_content += "            headers = self.auth_manager.get_auth_headers(auth_name)\n"
    helper_content += "            self.logger.info(\"\u8ba4\u8bc1\u8bbe\u7f6e\u6210\u529f: \" + auth_name)\n"
    helper_content += "            return headers\n"
    helper_content += "        except Exception as e:\n"
    helper_content += "            self.logger.error(\"\u8ba4\u8bc1\u8bbe\u7f6e\u5931\u8d25: \" + str(e))\n"
    helper_content += "            return {}\n\n"
    
    helper_content += "    def extract_data(self, response_data: Dict[str, Any], extractions: Dict[str, str]) -> Dict[str, Any]:\n"
    helper_content += '        """从响应中提取数据"""\n'
    helper_content += "        extracted = {}\n\n"
    helper_content += "        for alias, path in extractions.items():\n"
    helper_content += "            try:\n"
    helper_content += "                value = self._get_nested_value(response_data, path)\n"
    helper_content += "                if value is not None:\n"
    helper_content += "                    extracted[alias] = value\n"
    helper_content += "                    self.test_data[alias] = value\n"
    helper_content += "                    self.logger.info(\"\u6570\u636e\u63d0\u53d6\u6210\u529f: \" + alias + \" = \" + str(value))\n"
    helper_content += "            except Exception as e:\n"
    helper_content += "                self.logger.warning(\"\u6570\u636e\u63d0\u53d6\u5931\u8d25: \" + alias + \" - \" + str(e))\n\n"
    helper_content += "        return extracted\n\n"
    
    helper_content += "    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:\n"
    helper_content += '        """按路径获取嵌套值"""\n'
    helper_content += "        keys = path.split('.')\n"
    helper_content += "        current = data\n\n"
    helper_content += "        for key in keys:\n"
    helper_content += "            if isinstance(current, dict) and key in current:\n"
    helper_content += "                current = current[key]\n"
    helper_content += "            elif isinstance(current, list) and key.isdigit():\n"
    helper_content += "                index = int(key)\n"
    helper_content += "                if 0 <= index < len(current):\n"
    helper_content += "                    current = current[index]\n"
    helper_content += "                else:\n"
    helper_content += "                    return None\n"
    helper_content += "            else:\n"
    helper_content += "                return None\n\n"
    helper_content += "        return current\n\n"
    
    helper_content += "    def substitute_variables(self, text: str) -> str:\n"
    helper_content += '        """替换文本中的变量"""\n'
    helper_content += "        if not isinstance(text, str):\n"
    helper_content += "            return text\n\n"
    helper_content += "        for key, value in self.test_data.items():\n"
    helper_content += "            placeholder = \"${\" + key + \"}\"\n"
    helper_content += "            if placeholder in text:\n"
    helper_content += "                text = text.replace(placeholder, str(value))\n\n"
    helper_content += "        return text\n\n"
    
    return helper_content


def _generate_test_method(path, method_name, mock_sensitive_data):
    """生成单个测试方法"""
    path_url = path.get('path', '')
    method_upper = path.get('method', 'GET').upper()
    test_summary = path.get('summary', path_url)
    auth_default = 'True' if '/login' not in path_url else 'False'
    expected_status = path.get('expected_status', 200)
    
    test_method = "    def test_" + method_name + "(self, auth_required: bool = " + auth_default + "):\n"
    test_method += '        """测试 ' + test_summary + '"""\n\n'
    test_method += "        # 设置认证\n"
    test_method += "        headers = {}\n"
    test_method += "        if auth_required and self.auth_manager:\n"
    test_method += "            headers.update(self.setup_authentication())\n\n"
    test_method += "        # 替换URL中的变量\n"
    test_method += "        url = self.substitute_variables(\"" + path_url + "\")\n\n"
    test_method += "        # 准备请求参数\n"
    test_method += "        params = {}\n"
    test_method += "        request_body = None\n\n"
    test_method += "        # TODO: 根据API规范设置实际参数\n"
    
    if mock_sensitive_data:
        test_method += "        # 示例数据 (请根据实际需求修改)\n"
    
    test_method += "\n        # 发送请求\n"
    test_method += "        result = self.make_request(\n"
    test_method += "            method=\"" + method_upper + "\",\n"
    test_method += "            url=url,\n"
    test_method += "            params=params,\n"
    test_method += "            headers=headers,\n"
    test_method += "            json=request_body,\n"
    test_method += "            test_name=\"test_" + method_name + "\"\n"
    test_method += "        )\n\n"
    test_method += "        # 基础断言\n"
    test_method += "        self.assert_status_code(result, " + str(expected_status) + ")\n\n"
    test_method += "        # 提取响应数据 (如果需要)\n"
    test_method += "        extractions = {}\n"
    test_method += "            # 示例: 'user_id': 'id', 'token': 'access_token'\n\n"
    test_method += "        if result.success and result.response_data and extractions:\n"
    test_method += "            extracted = self.extract_data(result.response_data, extractions)\n"
    test_method += "            self.logger.info(\"提取的数据: \" + str(extracted))\n\n"
    test_method += "        return result\n\n"
    
    return test_method
    
    # 添加 run_tests 方法
    test_content += "    def run_tests(self):\n"
    test_content += '        """运行所有测试"""\n'
    test_content += "        results = []\n"
    test_content += "        # 这里可以添加具体的测试调用\n"
    test_content += "        return results\n\n\n"
    
    # 写入文件
    test_file = output_path / 'test_api.py'
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)


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
        # 使用变量来避免f-string嵌套问题
        base_url_var = "{{base_url}}"
        path_url = path.get('path', '')
        
        item = {
            "name": path.get('summary', path.get('path', '')),
            "request": {
                "method": path.get('method', 'GET').upper(),
                "header": [],
                "url": {
                    "raw": base_url_var + path_url,
                    "host": [base_url_var],
                    "path": path_url.split('/')[1:]
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
    api_title = api_info.get('title', 'API')
    
    config_content = "# " + api_title + " 测试配置\n\n"
    config_content += "global:\n"
    config_content += "  timeout: 30\n"
    config_content += "  retry: 3\n"
    config_content += "  parallel: 4\n\n"
    config_content += "environments:\n"
    config_content += "  dev:\n"
    config_content += '    base_url: "http://localhost:8080"\n'
    config_content += "    headers:\n"
    config_content += '      Content-Type: "application/json"\n\n'
    config_content += "  test:\n"
    config_content += '    base_url: "https://test-api.example.com"\n'
    config_content += "    headers:\n"
    config_content += '      Content-Type: "application/json"\n'
    config_content += '      Authorization: "Bearer test-token"\n\n'
    config_content += "  prod:\n"
    config_content += '    base_url: "https://api.example.com"\n'
    config_content += "    headers:\n"
    config_content += '      Content-Type: "application/json"\n'
    config_content += '      Authorization: "Bearer prod-token"\n'
    
    config_file = output_path / 'config' / 'test_config.yaml'
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(config_content)


def _generate_documentation(output_path: Path, api_info: Dict[str, Any], 
                           paths: List[Dict[str, Any]], 
                           auth_manager: Optional[AuthManager], 
                           dependency_manager: Optional[DependencyManager]):
    """生成文档"""
    api_title = api_info.get('title', 'API')
    api_name = api_info.get('title', 'Unknown')
    api_version = api_info.get('version', '1.0.0')
    api_desc = api_info.get('description', '无描述')
    paths_count = str(len(paths))
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    doc_content = "# " + api_title + " 自动化测试文档\n\n"
    doc_content += "## 项目信息\n"
    doc_content += "- **API名称**: " + api_name + "\n"
    doc_content += "- **版本**: " + api_version + "\n"
    doc_content += "- **描述**: " + api_desc + "\n"
    doc_content += "- **接口数量**: " + paths_count + "\n"
    doc_content += "- **生成时间**: " + current_time + "\n\n"
    
    doc_content += "## 功能特性\n"
    doc_content += "- ✅ 多种认证方式支持\n"
    doc_content += "- ✅ 依赖管理和工作流\n"
    doc_content += "- ✅ 多格式测试生成\n"
    doc_content += "- ✅ 自动化数据提取\n"
    doc_content += "- ✅ 敏感数据Mock\n\n"
    
    doc_content += "## 使用指南\n\n"
    doc_content += "### 1. 配置认证\n"
    doc_content += "```bash\n"
    doc_content += "# 编辑认证配置\n"
    doc_content += "vim config/auth.yaml\n\n"
    doc_content += "# 设置环境变量\n"
    doc_content += "export AUTH_API_AUTH_USERNAME=your_username\n"
    doc_content += "export AUTH_API_AUTH_PASSWORD=your_password\n"
    doc_content += "```\n\n"
    
    doc_content += "### 2. 运行测试\n"
    doc_content += "```bash\n"
    doc_content += "# 运行Python测试\n"
    doc_content += "python tests/test_api.py\n\n"
    doc_content += "# 运行Postman集合\n"
    doc_content += "newman run postman/collection.json\n\n"
    doc_content += "# 运行cURL脚本\n"
    doc_content += "bash curl/api_tests.sh\n"
    doc_content += "```\n\n"
    
    doc_content += "## 接口列表\n"
    
    for i, path in enumerate(paths, 1):
        method = path.get('method', 'GET').upper()
        path_str = path.get('path', '')
        summary = path.get('summary', '无描述')
        doc_content += f"\n{i}. **{method} {path_str}** - {summary}"
    
    doc_file = output_path / 'README.md'
    with open(doc_file, 'w', encoding='utf-8') as f:
        f.write(doc_content)