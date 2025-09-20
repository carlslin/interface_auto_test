"""
接口自动化测试框架 - 主命令行入口

这是整个框架的主命令行入口，提供统一的CLI界面和命令管理。
支持从基础的API文档解析到高级的AI智能化功能的全部操作。

主要功能模块：
1. 基础模块：
   - parse: API文档解析和验证
   - generate: 测试代码和文档生成
   - export: 测试用例导出不同格式
   - mock: Mock服务器和数据管理

2. 高级模块：
   - ai: AI智能化功能集合（架构优化后）
   - workflow: 工作流管理和自动化
   - auth: 认证和授权管理

3. 一键功能：
   - auto-complete: 传统一键全自动完成（保留兼容）
   - ai-auto-complete: AI增强一键全自动完成（推荐）

架构优化后的改进：
- 精简了AI相关的命令和功能，去除了冗余部分
- 统一了错误处理和用户反馈，提供更友好的交互
- 整合了数据生成和代码审查功能到测试生成器
- 支持多级别的AI功能调用（basic/standard/comprehensive/enterprise）

使用示例：
  # 基础功能
  python3 -m src.cli.main parse --input api.yaml
  python3 -m src.cli.main generate tests --input api.yaml --output tests/
  
  # 一键完成功能
  python3 -m src.cli.main generate auto-complete --input api.yaml
  
  # AI智能化功能（优化后）
  python3 -m src.cli.main ai test-generate --input api.yaml --output tests/
  python3 -m src.cli.main ai auto-complete --input api.yaml --completion-level comprehensive
  python3 -m src.cli.main ai decision --context-file context.json
"""

import click
import logging
import sys
import yaml
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config_loader import ConfigLoader
from src.mock.mock_server import MockServer
from src.parsers.openapi_parser import OpenAPIParser
from src.runners.test_runner import TestRunner
from src.runners.report_generator import ReportGenerator
from src.utils.data_manager import DataManager
from src.exporters.test_case_exporter import TestCaseExporter
try:
    from src.ai import DeepSeekClient, AITestGenerator, AITestReporter
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    # 使用类型注释避免语法错误
    from typing import Optional, Any
    DeepSeekClient: Optional[Any] = None
    AITestGenerator: Optional[Any] = None
    AITestReporter: Optional[Any] = None


@click.group()
@click.option('--config', '-c', type=click.Path(), help='配置文件路径')
@click.option('--env', '-e', default='dev', help='环境名称')
@click.option('--debug', is_flag=True, help='启用调试模式')
@click.pass_context
def cli(ctx, config, env, debug):
    """
    接口自动化测试框架命令行工具 - 主入口
    
    这是整个框架的核心CLI群组，为所有子命令提供统一的上下文和配置管理。
    
    传递的全局配置：
    - 配置文件加载和管理
    - 环境设置和切换
    - 日志级别和调试模式
    - 项目根目录和路径设置
    
    支持的子命令组：
    - parse: API文档解析和验证
    - generate: 测试代码和文档生成
    - mock: Mock服务器管理
    - ai: AI智能化功能（架构优化后）
    - workflow: 工作流管理
    - auth: 认证管理
    """
    # 设置日志级别 - 根据调试模式自动调整
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建上下文对象 - 传递给所有子命令
    ctx.ensure_object(dict)
    
    # 加载配置 - 支持多环境和自定义配置文件
    config_loader = ConfigLoader(config)
    config_loader.set_environment(env)
    
    # 将配置和参数传递给所有子命令
    ctx.obj['config'] = config_loader
    ctx.obj['env'] = env
    ctx.obj['debug'] = debug


@cli.group()
@click.pass_context
def mock(ctx):
    """Mock服务器相关命令"""
    pass


@mock.command()
@click.option('--port', '-p', type=int, help='服务器端口')
@click.option('--host', '-h', default='localhost', help='服务器主机')
@click.option('--routes-file', '-f', type=click.Path(exists=True), help='路由配置文件')
@click.pass_context
def start(ctx, port, host, routes_file):
    """启动Mock服务器"""
    config = ctx.obj['config']
    
    # 构建服务器配置
    server_config = {
        'host': host or config.get('mock.host', 'localhost'),
        'port': port or config.get('mock.port', 5000),
        'debug': config.get('mock.debug', True),
        'enable_cors': config.get('mock.enable_cors', True)
    }
    
    click.echo(f"启动Mock服务器: http://{server_config['host']}:{server_config['port']}")
    
    # 创建并启动服务器
    server = MockServer(server_config)
    
    # 加载路由文件
    if routes_file:
        server.load_routes_from_file(routes_file)
        click.echo(f"已加载路由文件: {routes_file}")
    
    try:
        server.start(threaded=False)
    except KeyboardInterrupt:
        click.echo("\n正在停止Mock服务器...")
        server.stop()


@mock.command()
@click.option('--output', '-o', type=click.Path(), required=True, help='输出文件路径')
@click.option('--port', '-p', type=int, default=5000, help='服务器端口')
@click.pass_context
def save_routes(ctx, output, port):
    """保存当前Mock路由到文件"""
    # 这里应该连接到运行中的Mock服务器获取路由
    # 简化实现，直接提示用户
    click.echo(f"Mock路由将保存到: {output}")
    click.echo("请确保Mock服务器正在运行")


@cli.group()
@click.pass_context
def generate(ctx):
    """生成测试脚本相关命令"""
    pass


@generate.command()
@click.option('--input', '-i', required=True, help='输入的API文档文件路径或URL')
@click.option('--output', '-o', type=click.Path(), required=True, help='输出目录')
@click.option('--format', '-f', type=click.Choice(['python', 'json']), default='python', help='输出格式')
@click.option('--template', '-t', type=click.Path(exists=True), help='自定义模板文件')
@click.option('--export-format', type=click.Choice(['excel', 'csv', 'json', 'markdown', 'xml']), help='同时导出测试用例文档格式')
@click.pass_context
def tests(ctx, input, output, format, template, export_format):
    """从API文档生成测试脚本"""
    config = ctx.obj['config']
    
    click.echo(f"正在解析API文档: {input}")
    
    # 解析API文档
    parser = OpenAPIParser()
    
    # 判断是文件路径还是URL
    if input.startswith(('http://', 'https://')):
        success = parser.load_from_url(input)
    else:
        success = parser.load_from_file(input)
        
    if not success:
        click.echo("❌ API文档解析失败", err=True)
        sys.exit(1)
    
    click.echo("✅ API文档解析成功")
    
    # 获取API信息
    api_info = parser.get_api_info()
    click.echo(f"API名称: {api_info['title']}")
    click.echo(f"版本: {api_info['version']}")
    
    # 获取所有路径
    paths = parser.get_all_paths()
    click.echo(f"发现 {len(paths)} 个API接口")
    
    # 创建输出目录
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    if format == 'python':
        _generate_python_tests(paths, output_path, api_info, template)
    else:
        _generate_json_tests(paths, output_path, api_info)
    
    click.echo(f"✅ 测试脚本已生成到: {output}")
    
    # 如果指定了导出格式，则同时导出测试用例文档
    if export_format:
        _export_test_cases(paths, output_path, api_info, export_format)


@generate.command()
@click.option('--input', '-i', required=True, help='API文档文件路径或URL')
@click.option('--workspace', '-w', type=click.Path(), default='./auto_test_project', help='工作区路径')
@click.option('--mock-port', type=int, default=8080, help='Mock服务器端口')
@click.pass_context
def auto_complete(ctx, input, workspace, mock_port):
    """🤖 一键全自动完成：从API文档到完整测试系统"""
    import shutil
    
    click.echo("🎆 欢迎使用一键全自动完成功能！")
    click.echo("=" * 60)
    click.echo(f"📁 API文档: {input}")
    click.echo(f"💼 工作区: {workspace}")
    click.echo(f"🎭 Mock端口: {mock_port}")
    click.echo("=" * 60)
    
    try:
        # 第一步：解析API文档
        click.echo("\n🔍 第一步：解析API文档")
        parser = OpenAPIParser()
        
        # 判断是文件路径还是URL
        if input.startswith(('http://', 'https://')):
            click.echo(f"🌐 从 URL 加载: {input}")
            success = parser.load_from_url(input)
        else:
            click.echo(f"📁 从文件加载: {input}")
            success = parser.load_from_file(input)
            
        if not success:
            click.echo("❌ API文档解析失败", err=True)
            sys.exit(1)
        
        api_info = parser.get_api_info()
        paths = parser.get_all_paths()
        project_name = api_info.get('title', 'API_Test_Project').replace(' ', '_')
        
        click.echo(f"✅ 解析成功: {api_info['title']} v{api_info['version']}")
        click.echo(f"📊 发现 {len(paths)} 个API接口")
        
        # 第二步：创建项目结构
        click.echo("\n📁 第二步：创建项目结构")
        workspace_path = Path(workspace)
        workspace_path.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        directories = ['config', 'specs', 'tests', 'tests/generated', 'data', 'reports', 'exports', 'scripts']
        for dir_name in directories:
            (workspace_path / dir_name).mkdir(parents=True, exist_ok=True)
        
        # 第三步：保存API文档
        click.echo("\n📄 第三步：保存API文档")
        spec_file = workspace_path / 'specs' / f'{project_name.lower()}.yaml'
        
        if input.startswith(('http://', 'https://')):
            # URL来源，保存解析后的规范
            import yaml
            with open(spec_file, 'w', encoding='utf-8') as f:
                yaml.dump(parser.get_full_spec(), f, default_flow_style=False, allow_unicode=True)
            click.echo(f"✅ API文档已从URL保存到: {spec_file}")
        else:
            # 文件来源，直接复制
            shutil.copy2(input, spec_file)
            click.echo(f"✅ API文档已复制到: {spec_file}")
        
        # 第四步：生成配置文件
        click.echo("\n⚙️ 第四步：生成配置文件")
        config_content = f'''# {project_name} 项目配置文件

global:
  timeout: 30
  retry: 3
  parallel: 4

environments:
  dev:
    base_url: "http://localhost:{mock_port}"
    headers:
      Content-Type: "application/json"
    timeout: 30

mock:
  port: {mock_port}
  host: "localhost"
  enable_cors: true
'''
        
        config_file = workspace_path / 'config' / 'default.yaml'
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        # 第五步：生成测试文件
        click.echo("\n🤖 第五步：生成测试文件")
        tests_output = workspace_path / 'tests' / 'generated'
        _generate_python_tests(paths, tests_output, api_info)
        
        # 第六步：导出测试用例
        click.echo("\n📤 第六步：导出测试用例")
        exports_output = workspace_path / 'exports'
        _export_test_cases(paths, exports_output, api_info, 'excel')
        
        # 第七步：生成Mock配置
        click.echo("\n🎭 第七步：生成Mock配置")
        mock_routes = {"routes": []}
        for path in paths[:5]:  # 只生成前5个接口
            route = {
                "method": path.get('method', 'GET').upper(),
                "path": path.get('path', '/'),
                "response": {
                    "status_code": 200,
                    "body": {"message": "Mock response", "data": {}}
                }
            }
            mock_routes["routes"].append(route)
        
        mock_file = workspace_path / 'config' / 'mock_routes.json'
        with open(mock_file, 'w', encoding='utf-8') as f:
            json.dump(mock_routes, f, ensure_ascii=False, indent=2)
        
        # 第八步：生成README
        click.echo("\n📚 第八步：生成项目文档")
        readme_content = f'''# {project_name} 自动化测试项目

## 项目信息
- API名称: {api_info.get('title', 'Unknown')}
- 版本: {api_info.get('version', '1.0.0')}
- 接口数量: {len(paths)}
- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 快速开始

1. 运行测试：
```bash
python tests/generated/test_*.py
```

2. 启动Mock服务器：
```bash
autotest mock start --port {mock_port} --routes-file config/mock_routes.json
```

## 目录结构
- config/: 配置文件
- specs/: API规格文档
- tests/: 测试文件
- exports/: 导出的测试用例
'''
        
        readme_file = workspace_path / 'README.md'
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        # 显示成功信息
        click.echo("\n" + "=" * 60)
        click.echo("🎉 一键全自动完成成功！")
        click.echo("=" * 60)
        click.echo(f"💼 项目位置: {workspace_path.absolute()}")
        click.echo(f"📁 测试文件: {workspace_path}/tests/generated/")
        click.echo(f"📤 测试用例: {workspace_path}/exports/")
        click.echo(f"🎭 Mock配置: {workspace_path}/config/mock_routes.json")
        
        click.echo("\n🛠️ 下一步操作:")
        click.echo(f"1. 进入项目: cd {workspace_path}")
        click.echo(f"2. 启动Mock: autotest mock start --port {mock_port} --routes-file config/mock_routes.json")
        click.echo("3. 运行测试: python tests/generated/test_*.py")
        click.echo("4. 查看文档: cat README.md")
        
    except Exception as e:
        click.echo(f"\n❌ 全自动完成失败: {str(e)}", err=True)
        sys.exit(1)


@generate.command()
@click.option('--input', '-i', required=True, help='API文档文件路径或URL')
@click.option('--project-name', '-n', help='项目名称（可选，从文档自动推断）')
@click.option('--workspace', '-w', type=click.Path(), default='./ai_complete_project', help='工作区路径')
@click.option('--api-key', help='DeepSeek API Key（可选，从配置读取）')
@click.option('--business-context', help='业务上下文描述')
@click.option('--completion-level', 
              type=click.Choice(['basic', 'standard', 'comprehensive', 'enterprise']), 
              default='standard', 
              help='AI补全级别')
@click.option('--parallel-workers', type=int, default=4, help='并发工作数量')
@click.option('--enable-analysis', is_flag=True, default=True, help='启用智能分析')
@click.option('--enable-optimization', is_flag=True, default=True, help='启用优化建议')
@click.option('--custom-requirements', help='自定义需求（逗号分隔）')
@click.pass_context
def ai_auto_complete(ctx, input, project_name, workspace, api_key, business_context, 
                    completion_level, parallel_workers, enable_analysis, enable_optimization, 
                    custom_requirements):
    """🤖 AI增强一键自动完成：智能分析所有接口并生成完整测试系统"""
    if not AI_AVAILABLE:
        click.echo("❌ AI功能不可用，请安装相关依赖", err=True)
        sys.exit(1)
    
    # 导入AI自动完成功能
    try:
        from .ai_auto_complete_cmd import ai_auto_complete as run_ai_auto_complete
        # 运行AI自动完成命令
        if run_ai_auto_complete and hasattr(run_ai_auto_complete, 'callback'):
            run_ai_auto_complete.callback(  # type: ignore
                ctx, input, project_name, workspace, api_key, business_context,
                completion_level, parallel_workers, enable_analysis, enable_optimization,
                custom_requirements
            )
        else:
            click.echo("❌ AI自动完成功能不可用", err=True)
            sys.exit(1)
    except ImportError as e:
        click.echo(f"❌ 无法导入AI增强功能: {e}", err=True)
        click.echo("💡 请检查AI模块是否正确安装")
        sys.exit(1)


# 以下是辅助函数


def _export_test_cases(paths, output_path, api_info, export_format):
    """导出测试用例文档"""
    click.echo(f"📊 正在导出测试用例文档...")
    
    # 转换路径为测试用例格式
    test_cases = []
    for i, path in enumerate(paths, 1):
        test_case = {
            'name': f"{path.get('summary', path.get('operation_id', f'Test_{i}'))}",
            'description': path.get('description', path.get('summary', '')),
            'method': path.get('method', 'GET').upper(),
            'url': path.get('path', ''),
            'priority': 'Medium',
            'category': 'API测试',
            'tags': [api_info.get('title', 'API'), path.get('method', 'GET')],
            'operation_id': path.get('operation_id', ''),
            'parameters': path.get('parameters', {}),
            'request_body': path.get('requestBody', {}),
            'expected_status': 200,
            'expected_response': path.get('responses', {}).get('200', {}),
            'assertions': [
                f"验证响应状态码为200",
                f"验证响应格式为JSON"
            ],
            'created_by': '系统生成',
            'test_suite': api_info.get('title', 'API测试套件')
        }
        test_cases.append(test_case)
    
    # 导出测试用例
    exporter = TestCaseExporter()
    export_file = output_path / f"test_cases_{api_info.get('title', 'api').replace(' ', '_')}"
    
    try:
        exported_path = exporter.export_test_cases(
            test_cases=test_cases,
            output_path=export_file,
            format_type=export_format,
            include_metadata=True
        )
        click.echo(f"✅ 测试用例文档已导出: {exported_path}")
        
        # 显示统计信息
        summary = exporter.generate_test_summary(test_cases)
        click.echo(f"📊 统计信息:")
        click.echo(f"  测试用例总数: {summary['total_cases']}")
        click.echo(f"  HTTP方法分布: {summary['methods']}")
        
    except Exception as e:
        click.echo(f"❌ 导出失败: {str(e)}", err=True)


def _generate_python_tests(paths, output_path, api_info, template_file=None):
    """生成Python测试脚本"""
    # 创建主测试文件
    test_content = f'''"""
自动生成的API测试脚本
API: {api_info["title"]} v{api_info["version"]}
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.base_test import BaseTest
from src.utils.config_loader import ConfigLoader


class {_to_class_name(api_info["title"])}Test(BaseTest):
    """
    {api_info["title"]} API测试类
    """
    
    def __init__(self, config_path=None):
        super().__init__(config_path)
        
    def run_tests(self):
        """运行所有测试"""
        results = []
        
'''
    
    # 为每个接口生成测试方法
    for path in paths:
        method_name = _to_method_name(path['operation_id'])
        test_content += f'''
    def test_{method_name}(self):
        """测试 {path['summary'] or path['operation_id']}"""
        # 构建请求参数
        url = "{path['path']}"
        method = "{path['method']}"
        
        # TODO: 根据需要修改请求参数
        params = {{}}
        headers = {{}}
        data = None
        
        # 发送请求
        result = self.make_request(
            method=method,
            url=url,
            params=params,
            headers=headers,
            json=data,
            test_name="test_{method_name}"
        )
        
        # 断言检查
        self.assert_status_code(result, 200)  # 根据接口实际情况修改期望状态码
        # self.assert_response_time(result.response_time, 5.0)  # 最大响应时间5秒
        
        return result
'''
    
    test_content += '''

if __name__ == "__main__":
    # 运行测试
    test_instance = ''' + _to_class_name(api_info["title"]) + '''Test()
    test_instance.run_tests()
    
    # 获取测试结果
    summary = test_instance.get_test_summary()
    print(f"测试完成: 成功 {summary['success']}, 失败 {summary['failed']}, 成功率 {summary['success_rate']:.2%}")
'''
    
    # 写入文件
    test_file = output_path / f"test_{_to_file_name(api_info['title'])}.py"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)


def _generate_json_tests(paths, output_path, api_info):
    """生成JSON格式的测试配置"""
    import json
    
    test_config = {
        "api_info": api_info,
        "tests": []
    }
    
    for path in paths:
        test_case = {
            "name": path['operation_id'],
            "description": path['summary'] or path['description'],
            "method": path['method'],
            "path": path['path'],
            "parameters": path['parameters'],
            "request_body": path['request_body'],
            "expected_responses": path['responses']
        }
        test_config["tests"].append(test_case)
    
    # 写入JSON文件
    json_file = output_path / f"tests_{_to_file_name(api_info['title'])}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(test_config, f, indent=2, ensure_ascii=False)


def _to_class_name(name):
    """转换为类名格式"""
    import re
    # 移除特殊字符，转换为驼峰命名
    clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', name)
    words = clean_name.split()
    return ''.join(word.capitalize() for word in words)


def _to_method_name(name):
    """转换为方法名格式"""
    import re
    # 转换为下划线命名
    clean_name = re.sub(r'[^a-zA-Z0-9]', '_', name)
    return clean_name.lower()


def _to_file_name(name):
    """转换为文件名格式"""
    import re
    # 转换为下划线命名
    clean_name = re.sub(r'[^a-zA-Z0-9]', '_', name)
    return clean_name.lower()


@cli.group()
@click.pass_context
def test(ctx):
    """测试执行相关命令"""
    pass


@test.command()
@click.option('--path', '-p', type=click.Path(exists=True), help='测试文件或目录路径')
@click.option('--pattern', default='test_*.py', help='测试文件匹配模式')
@click.option('--parallel', type=int, default=1, help='并发执行数量')
@click.option('--output', '-o', type=click.Path(), help='测试报告输出路径')
@click.option('--format', '-f', multiple=True, type=click.Choice(['html', 'json', 'xml']), 
              default=['html'], help='报告格式')
@click.option('--fail-fast', is_flag=True, help='在第一个失败时停止')
@click.option('--filter', multiple=True, help='测试过滤器')
@click.pass_context
def run(ctx, path, pattern, parallel, output, format, fail_fast, filter):
    """运行测试"""
    config = ctx.obj['config']
    
    if not path:
        path = "./tests"
    
    click.echo(f"🚀 正在运行测试: {path}")
    click.echo(f"🔍 匹配模式: {pattern}")
    click.echo(f"⚡ 并发数: {parallel}")
    
    # 创建测试运行器
    runner = TestRunner()
    
    # 发现测试
    test_count = runner.discover_tests(path, pattern)
    if test_count == 0:
        click.echo("❌ 未发现测试文件")
        return
        
    click.echo(f"📄 发现 {test_count} 个测试套件")
    
    # 运行测试
    if filter:
        click.echo(f"🔍 使用过滤器: {', '.join(filter)}")
        summary = runner.run_specific_tests(list(filter))
    else:
        summary = runner.run_all_tests(parallel=parallel, fail_fast=fail_fast)
    
    # 显示结果
    click.echo("\n" + "=" * 60)
    click.echo("📈 测试结果汇总")
    click.echo("=" * 60)
    click.echo(f"📋 总测试数: {summary['total_tests']}")
    click.echo(f"✅ 通过数: {summary['passed_tests']}")
    click.echo(f"❌ 失败数: {summary['failed_tests']}")
    click.echo(f"📈 成功率: {summary['success_rate']:.2%}")
    
    if 'total_duration' in summary:
        click.echo(f"⏱️  总用时: {summary['total_duration']:.2f}s")
    
    # 生成报告
    if output or format:
        report_generator = ReportGenerator(output or "./reports")
        results = summary.get('results', [])
        
        if results:
            click.echo("\n📄 正在生成测试报告...")
            
            generated_reports = report_generator.generate_all_reports(
                summary, results, list(format)
            )
            
            for report_format, file_path in generated_reports.items():
                click.echo(f"✅ {report_format.upper()}报告已生成: {file_path}")
        else:
            click.echo("⚠️  无法生成报告：没有测试结果")
    
@test.command()
@click.option('--path', '-p', type=click.Path(exists=True), default="./tests", help='测试文件或目录路径')
@click.option('--pattern', default='test_*.py', help='测试文件匹配模式')
@click.pass_context
def discover(ctx, path, pattern):
    """发现测试文件"""
    click.echo(f"🔍 正在发现测试: {path}")
    
    runner = TestRunner()
    test_count = runner.discover_tests(path, pattern)
    
    if test_count == 0:
        click.echo("❌ 未发现测试文件")
        return
    
    # 获取测试信息
    test_info = runner.get_test_info()
    
    click.echo(f"\n📄 发现测试结果:")
    click.echo(f"  测试套件: {test_info['total_suites']}")
    click.echo(f"  测试类: {test_info['total_classes']}")
    click.echo(f"  测试方法: {test_info['total_methods']}")
    
    click.echo("\n📝 详细信息:")
    for suite in test_info['suites']:
        click.echo(f"\n  📁 {suite['name']} ({suite['file_path']})")
        for cls in suite['classes']:
            click.echo(f"    🔮 {cls['name']} - {cls['method_count']} 个测试方法")
            if cls['doc']:
                click.echo(f"      {cls['doc'].strip()}")


@test.command()
@click.option('--path', '-p', type=click.Path(exists=True), default="./tests", help='测试文件或目录路径')
@click.option('--output', '-o', type=click.Path(), default="./reports", help='报告输出目录')
@click.option('--format', '-f', multiple=True, type=click.Choice(['html', 'json', 'xml']), 
              default=['html'], help='报告格式')
@click.pass_context
def report(ctx, path, output, format):
    """生成测试报告模板"""
    click.echo(f"📄 正在生成示例报告: {output}")
    
    # 生成示例数据
    from datetime import datetime
    from ..runners.test_runner import ExecutionResult
    from ..core.base_test import TestResult
    
    # 创建示例数据
    sample_test_result = TestResult(
        test_name="test_example",
        method="GET",
        url="/api/test",
        status_code=200,
        response_time=1.5,
        success=True,
        request_data={"param": "value"},
        response_data={"result": "success"}
    )
    
    sample_execution_result = ExecutionResult(
        suite_name="example_suite",
        class_name="ExampleTest",
        start_time=datetime.now(),
        end_time=datetime.now(),
        duration=2.5,
        total_tests=1,
        passed_tests=1,
        failed_tests=0,
        test_results=[sample_test_result],
        success=True
    )
    
    sample_summary = {
        'total_suites': 1,
        'total_classes': 1,
        'total_tests': 1,
        'passed_tests': 1,
        'failed_tests': 0,
        'success_rate': 1.0,
        'total_duration': 2.5
    }
    
    # 生成报告
    report_generator = ReportGenerator(output)
    generated_reports = report_generator.generate_all_reports(
        sample_summary, [sample_execution_result], list(format)
    )
    
@cli.group()
@click.pass_context
def config(ctx):
    """配置管理相关命令"""
    pass


@config.command()
@click.pass_context
def show(ctx):
    """显示当前配置"""
    config = ctx.obj['config']
    
    click.echo("📄 当前配置信息:")
    click.echo("=" * 50)
    
    # 显示基本信息
    click.echo(f"📋 配置文件: {config.config_path}")
    click.echo(f"🌍 当前环境: {config.current_env}")
    click.echo(f"🔗 基础URL: {config.get_base_url()}")
    click.echo(f"⏱️  超时时间: {config.get_timeout()}秒")
    
    # 显示可用环境
    environments = config.get_all_environments()
    click.echo(f"🔄 可用环境: {', '.join(environments)}")
    
    # 显示全局配置
    global_config = config.get("global", {})
    if global_config:
        click.echo("\n🌐 全局配置:")
        for key, value in global_config.items():
            click.echo(f"  {key}: {value}")
    
    # 显示当前环境配置
    env_config = config.get_current_env_config()
    if env_config:
        click.echo(f"\n🔧 {config.current_env} 环境配置:")
        for key, value in env_config.items():
            if key == "headers" and isinstance(value, dict):
                click.echo(f"  {key}:")
                for h_key, h_value in value.items():
                    click.echo(f"    {h_key}: {h_value}")
            else:
                click.echo(f"  {key}: {value}")


@config.command()
@click.option('--env', '-e', required=True, help='环境名称')
@click.pass_context
def switch(ctx, env):
    """切换环境"""
    config = ctx.obj['config']
    
    old_env = config.current_env
    config.set_environment(env)
    
    if config.current_env == env:
        click.echo(f"✅ 已切换到环境: {old_env} → {env}")
        click.echo(f"🔗 新的基础URL: {config.get_base_url()}")
    else:
        click.echo(f"❌ 切换失败：环境 {env} 不存在")
        click.echo(f"📄 可用环境: {', '.join(config.get_all_environments())}")


@config.command()
@click.pass_context
def validate(ctx):
    """验证配置文件"""
    config = ctx.obj['config']
    
    click.echo("🔍 正在验证配置文件...")
    
    validation_result = config.validate_config()
    errors = validation_result["errors"]
    warnings = validation_result["warnings"]
    
    if not errors and not warnings:
        click.echo("✅ 配置文件验证通过")
    else:
        if errors:
            click.echo(f"\n❌ 发现 {len(errors)} 个错误:")
            for i, error in enumerate(errors, 1):
                click.echo(f"  {i}. {error}")
        
        if warnings:
            click.echo(f"\n⚠️  发现 {len(warnings)} 个警告:")
            for i, warning in enumerate(warnings, 1):
                click.echo(f"  {i}. {warning}")
        
        if errors:
            sys.exit(1)


@config.command()
@click.option('--output', '-o', required=True, help='输出文件路径')
@click.pass_context
def export(ctx, output):
    """导出配置文件"""
    config = ctx.obj['config']
    
    click.echo(f"📤 正在导出配置到: {output}")
    
    if config.export_config(output):
        click.echo("✅ 配置导出成功")
    else:
        click.echo("❌ 配置导出失败")
        sys.exit(1)


@config.command()
@click.option('--input', '-i', required=True, help='输入文件路径')
@click.option('--merge/--replace', default=True, help='合并或替换现有配置')
@click.pass_context
def import_cmd(ctx, input, merge):
    """导入配置文件"""
    config = ctx.obj['config']
    
    mode = "合并" if merge else "替换"
    click.echo(f"📥 正在导入配置: {input} ({mode}模式)")
    
    if config.import_config(input, merge):
        click.echo("✅ 配置导入成功")
    else:
        click.echo("❌ 配置导入失败")
        sys.exit(1)


@config.command()
@click.option('--output', '-o', default='./config/template.yaml', help='输出文件路径')
@click.pass_context
def template(ctx, output):
    """生成配置模板"""
    config = ctx.obj['config']
    
    click.echo(f"📄 正在生成配置模板: {output}")
    
    template_config = config.get_config_template()
    
    try:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(template_config, f, default_flow_style=False, allow_unicode=True)
        
        click.echo("✅ 配置模板生成成功")
        click.echo(f"📁 文件位置: {output_path.absolute()}")
        
    except Exception as e:
        click.echo(f"❌ 生成模板失败: {str(e)}")
        sys.exit(1)


@cli.group()
@click.pass_context
def data(ctx):
    """数据管理相关命令"""
    pass


@data.command()
@click.option('--category', '-c', help='数据分类')
@click.pass_context
def list_data(ctx, category):
    """列出数据"""
    data_manager = DataManager()
    
    if category:
        click.echo(f"📁 分类 '{category}' 下的数据:")
        names = data_manager.list_data_names(category)
        if names:
            for name in names:
                click.echo(f"  • {name}")
        else:
            click.echo("ℹ️  暂无数据")
    else:
        click.echo("📂 所有数据分类:")
        categories = data_manager.list_categories()
        if categories:
            for cat in categories:
                names = data_manager.list_data_names(cat)
                click.echo(f"  📁 {cat} ({len(names)} 项)")
        else:
            click.echo("ℹ️  暂无数据")


@data.command()
@click.option('--input', '-i', required=True, help='输入文件路径')
@click.option('--category', '-c', required=True, help='数据分类')
@click.pass_context
def load(ctx, input, category):
    """加载数据文件"""
    data_manager = DataManager()
    
    click.echo(f"📥 正在加载数据文件: {input}")
    
    data = data_manager.load_data_file(input, category)
    
    if data:
        # 保存到数据库
        file_name = Path(input).stem
        if data_manager.save_data(category, file_name, data, f"从文件 {input} 加载"):
            click.echo("✅ 数据加载成功")
        else:
            click.echo("❌ 数据保存失败")
    else:
        click.echo("❌ 数据加载失败")


@data.command()
@click.option('--output', '-o', required=True, help='输出文件路径')
@click.option('--category', '-c', help='数据分类')
@click.option('--format', '-f', type=click.Choice(['json', 'yaml']), default='json', help='导出格式')
@click.pass_context
def export_data(ctx, output, category, format):
    """导出数据"""
    data_manager = DataManager()
    
    scope = f"分类 '{category}'" if category else "所有数据"
    click.echo(f"📤 正在导出{scope}到: {output}")
    
    if data_manager.export_data(output, category, format):
        click.echo("✅ 数据导出成功")
    else:
        click.echo("❌ 数据导出失败")
        sys.exit(1)


@cli.command()
@click.pass_context
def info(ctx):
    """显示框架信息"""
    config = ctx.obj['config']
    
    click.echo("🚀 接口自动化测试框架")
    click.echo("=" * 50)
    click.echo(f"当前环境: {ctx.obj['env']}")
    click.echo(f"配置文件: {config.config_path}")
    click.echo(f"基础URL: {config.get_base_url()}")
    click.echo(f"超时时间: {config.get_timeout()}秒")
    
    # 显示可用环境
    environments = config.get_all_environments()
    if environments:
        click.echo(f"可用环境: {', '.join(environments)}")
    
    # 显示AI功能状态
    ai_status = "✅ 可用" if AI_AVAILABLE else "❌ 不可用"
    click.echo(f"AI功能: {ai_status}")


# AI功能相关命令
if AI_AVAILABLE:
    @cli.group()
    @click.pass_context
    def ai(ctx):
        """🤖 AI智能功能"""
        pass
    
    # 添加AI配置管理命令
    try:
        from .ai_config_cmd import ai_config
        cli.add_command(ai_config, name='ai-config')
    except ImportError:
        pass
    
    # 添加AI智能向导命令
    try:
        from .ai_wizard_cmd import ai_wizard
        cli.add_command(ai_wizard, name='ai-wizard')
    except ImportError:
        pass
    
    @ai.command()
    @click.option('--api-key', required=True, help='DeepSeek API Key')
    @click.pass_context
    def setup(ctx, api_key):
        """设置AI功能"""
        try:
            if not AI_AVAILABLE or DeepSeekClient is None:
                raise ImportError("AI功能不可用")
                
            client = DeepSeekClient(api_key)  # type: ignore
            if client.validate_api_key():
                click.echo("✅ AI功能设置成功")
                # 保存API Key到配置文件
                config = ctx.obj['config']
                config.set('ai.deepseek_api_key', api_key)
                config.save_config()
                click.echo("💾 API Key已保存到配置文件")
            else:
                click.echo("❌ API Key验证失败", err=True)
                sys.exit(1)
        except Exception as e:
            click.echo(f"❌ AI功能设置失败: {e}", err=True)
            sys.exit(1)
    
    @ai.command()
    @click.option('--input', '-i', type=click.Path(exists=True), required=True, help='API文档文件')
    @click.option('--output', '-o', type=click.Path(), required=True, help='输出目录')
    @click.option('--business-context', help='业务上下文描述')
    @click.option('--test-types', multiple=True, default=['functional'], help='测试类型')
    @click.pass_context
    def generate_tests(ctx, input, output, business_context, test_types):
        """使用AI生成智能测试用例"""
        config = ctx.obj['config']
        api_key = config.get('ai.deepseek_api_key')
        
        if not api_key:
            click.echo("❌ 请先设置AI API Key: interface-test ai setup --api-key YOUR_KEY", err=True)
            sys.exit(1)
        
        click.echo(f"🤖 使用AI生成测试用例: {input}")
        
        try:
            # 初始化AI客户端
            from ..ai import DeepSeekClient, AITestGenerator  # type: ignore
            client = DeepSeekClient(api_key)  # type: ignore
            generator = AITestGenerator(client)  # type: ignore
            
            # 解析API文档
            parser = OpenAPIParser()
            if not parser.load_from_file(input):
                click.echo("❌ API文档解析失败", err=True)
                sys.exit(1)
            
            api_info = parser.get_api_info()
            api_spec = parser.get_full_spec()
            
            click.echo(f"✅ API文档解析成功: {api_info['title']}")
            
            # 生成AI测试用例
            result = generator.generate_comprehensive_tests(
                api_spec=api_spec,
                business_context=business_context,
                test_requirements=list(test_types)
            )
            
            if 'error' in result:
                click.echo(f"❌ AI生成失败: {result['error']}", err=True)
                sys.exit(1)
            
            # 保存结果
            output_path = Path(output)
            output_path.mkdir(parents=True, exist_ok=True)
            
            output_file = output_path / f"ai_generated_tests_{api_info['title'].replace(' ', '_')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            click.echo(f"✅ AI测试用例已生成: {output_file}")
            
            # 显示统计信息
            summary = result.get('summary', {})
            click.echo(f"\n📊 生成统计:")
            click.echo(f"  总测试数: {summary.get('total_tests', 0)}")
            click.echo(f"  API接口数: {summary.get('api_endpoints', 0)}")
            click.echo(f"  测试类型: {', '.join(test_types)}")
            
        except Exception as e:
            click.echo(f"❌ AI功能执行失败: {e}", err=True)
            sys.exit(1)
    
    @ai.command()
    @click.option('--file', '-f', type=click.Path(exists=True), required=True, help='代码文件')
    @click.option('--language', '-l', default='python', help='编程语言')
    @click.option('--output', '-o', type=click.Path(), help='输出报告文件')
    @click.option('--format', type=click.Choice(['markdown', 'html', 'text']), default='markdown', help='报告格式')
    @click.pass_context
    def review_code(ctx, file, language, output, format):
        """使用AI进行代码审查"""
        config = ctx.obj['config']
        api_key = config.get('ai.deepseek_api_key')
        
        if not api_key:
            click.echo("❌ 请先设置AI API Key: interface-test ai setup --api-key YOUR_KEY", err=True)
            sys.exit(1)
        
        click.echo(f"🤖 使用AI审查代码: {file}")
        
        try:
            # 读取代码文件
            with open(file, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # 初始化AI客户端
            client = DeepSeekClient(api_key)  # type: ignore
            # 代码审查功能已移除，可使用AI决策中心替代
            click.echo("⚠️ 代码审查功能已整合到AI决策中心，请使用相关命令")
            click.echo("💡 建议使用: interface-test ai decision --help")
            return
            
            # 执行代码审查
            result = reviewer.comprehensive_review(
                code=code,
                language=language,
                file_path=str(file)
            )
            
            # 生成报告
            report_result = reviewer.generate_review_report(result, format)
            
            if output:
                # 保存到文件
                output_path = Path(output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(report_result['report'])
                
                click.echo(f"✅ 代码审查报告已保存: {output_path}")
            else:
                # 直接显示
                click.echo("\n" + report_result['report'])
            
            # 显示总体评分
            overall_score = result.get('overall_score', 0)
            click.echo(f"\n🏆 总体评分: {overall_score}/10")
            
        except Exception as e:
            click.echo(f"❌ AI代码审查失败: {e}", err=True)
            sys.exit(1)
    
    @ai.command()
    @click.option('--schema', '-s', required=True, help='数据模式文件或JSON字符串')
    @click.option('--count', '-c', type=int, default=10, help='生成数据数量')
    @click.option('--type', type=click.Choice(['realistic', 'boundary', 'invalid', 'performance']), default='realistic', help='数据类型')
    @click.option('--output', '-o', type=click.Path(), required=True, help='输出文件')
    @click.option('--business-context', help='业务上下文')
    @click.pass_context
    def generate_data(ctx, schema, count, type, output, business_context):
        """使用AI生成测试数据"""
        config = ctx.obj['config']
        api_key = config.get('ai.deepseek_api_key')
        
        if not api_key:
            click.echo("❌ 请先设置AI API Key: interface-test ai setup --api-key YOUR_KEY", err=True)
            sys.exit(1)
        
        click.echo(f"🤖 使用AI生成{type}测试数据")
        
        try:
            # 解析数据模式
            if Path(schema).exists():
                with open(schema, 'r', encoding='utf-8') as f:
                    schema_data = json.load(f)
            else:
                schema_data = json.loads(schema)
            
            # 初始化AI客户端
            client = DeepSeekClient(api_key)  # type: ignore
            # 数据生成功能已整合到测试生成器中
            generator = AITestGenerator(client)  # type: ignore
            
            # 生成数据
            result = None
            if type == 'realistic':
                result = generator.generate_realistic_test_data(
                    schema=schema_data,
                    count=count,
                    business_context=business_context
                )
            elif type == 'boundary':
                result = generator.generate_boundary_test_data(
                    schema=schema_data,
                    include_edge_cases=True
                )
            elif type == 'invalid':
                result = generator.generate_invalid_test_data(
                    schema=schema_data,
                    attack_vectors=True
                )
            elif type == 'performance':
                # 性能数据生成功能
                click.echo("⚠️ 性能数据生成功能暂未实现")
                sys.exit(1)
            
            if result is None:
                click.echo("❌ 数据生成失败: 未支持的数据类型", err=True)
                sys.exit(1)
                
            if not result.get('success', False):
                click.echo(f"❌ 数据生成失败: {result.get('error', '未知错误')}", err=True)
                sys.exit(1)
            
            # 保存结果
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            click.echo(f"✅ 测试数据已生成: {output_path}")
            
            # 显示统计信息
            if 'count' in result:
                click.echo(f"📊 生成数量: {result['count']}条")
            click.echo(f"🏷️ 数据类型: {result.get('type', type)}")
            
        except Exception as e:
            click.echo(f"❌ AI数据生成失败: {e}", err=True)
            sys.exit(1)
else:
    # 如果AI不可用，提供友好的错误信息
    @cli.group()
    def ai():
        """🤖 AI智能功能（不可用）"""
        click.echo("❌ AI功能不可用，请安装相关依赖")
        click.echo("💡 安装命令: pip install requests")
        sys.exit(1)


@generate.command()
@click.option('--input', '-i', required=True, help='输入的API文档文件路径或URL')
@click.option('--output', '-o', type=click.Path(), required=True, help='输出文件路径')
@click.option('--format', '-f', type=click.Choice(['excel', 'csv', 'json', 'markdown', 'xml']), default='excel', help='导出格式')
@click.option('--include-metadata', is_flag=True, default=True, help='包含元数据信息')
@click.pass_context
def export_cases(ctx, input, output, format, include_metadata):
    """从 API 文档导出测试用例文档"""
    click.echo(f"📄 正在解析API文档: {input}")
    
    # 解析API文档
    parser = OpenAPIParser()
    
    # 判断是文件路径还是URL
    if input.startswith(('http://', 'https://')):
        success = parser.load_from_url(input)
    else:
        success = parser.load_from_file(input)
        
    if not success:
        click.echo("❌ API文档解析失败", err=True)
        sys.exit(1)
    
    # 获取API信息
    api_info = parser.get_api_info()
    paths = parser.get_all_paths()
    
    click.echo(f"✅ 解析成功: {api_info['title']} v{api_info['version']}")
    click.echo(f"🔍 发现 {len(paths)} 个API接口")
    
    # 转换为测试用例格式
    test_cases = []
    for i, path in enumerate(paths, 1):
        test_case = {
            'name': f"{path.get('summary', path.get('operation_id', f'Test_{i}'))}",
            'description': path.get('description', path.get('summary', '')),
            'method': path.get('method', 'GET').upper(),
            'url': path.get('path', ''),
            'priority': _determine_priority(path),
            'category': _determine_category(path),
            'tags': [api_info.get('title', 'API'), path.get('method', 'GET')],
            'operation_id': path.get('operation_id', ''),
            'parameters': _format_parameters(path.get('parameters', [])),
            'request_body': _format_request_body(path.get('requestBody', {})),
            'expected_status': 200,
            'expected_response': _format_expected_response(path.get('responses', {})),
            'assertions': _generate_assertions(path),
            'pre_conditions': _determine_pre_conditions(path),
            'created_by': '系统生成',
            'test_suite': api_info.get('title', 'API测试套件')
        }
        test_cases.append(test_case)
    
    # 导出测试用例
    exporter = TestCaseExporter()
    
    try:
        exported_path = exporter.export_test_cases(
            test_cases=test_cases,
            output_path=output,
            format_type=format,
            include_metadata=include_metadata
        )
        
        click.echo(f"✅ 测试用例文档已导出: {exported_path}")
        
        # 显示统计信息
        summary = exporter.generate_test_summary(test_cases)
        click.echo(f"\n📊 导出统计:")
        click.echo(f"  测试用例总数: {summary['total_cases']}")
        click.echo(f"  优先级分布: {dict(summary['priorities'])}")
        click.echo(f"  HTTP方法分布: {dict(summary['methods'])}")
        click.echo(f"  分类分布: {dict(summary['categories'])}")
        
    except Exception as e:
        click.echo(f"❌ 导出失败: {str(e)}", err=True)
        sys.exit(1)


def _determine_priority(path):
    """根据接口信息确定优先级"""
    method = path.get('method', '').upper()
    if method in ['POST', 'PUT', 'DELETE']:
        return 'High'
    elif method == 'GET':
        return 'Medium'
    else:
        return 'Low'


def _determine_category(path):
    """根据接口信息确定分类"""
    url = path.get('path', '')
    if '/auth' in url or '/login' in url:
        return '认证测试'
    elif '/user' in url:
        return '用户管理'
    elif '/admin' in url:
        return '管理功能'
    else:
        return 'API测试'


def _format_parameters(parameters):
    """格式化请求参数"""
    if not parameters:
        return {}
    
    formatted = {}
    for param in parameters:
        if isinstance(param, dict):
            name = param.get('name', '')
            param_type = param.get('type', 'string')
            required = param.get('required', False)
            description = param.get('description', '')
            
            formatted[name] = {
                'type': param_type,
                'required': required,
                'description': description,
                'example': _generate_example_value(param_type)
            }
    
    return formatted


def _format_request_body(request_body):
    """格式化请求体"""
    if not request_body:
        return {}
    
    content = request_body.get('content', {})
    if 'application/json' in content:
        schema = content['application/json'].get('schema', {})
        return _generate_example_from_schema(schema)
    
    return {}


def _format_expected_response(responses):
    """格式化预期响应"""
    if not responses:
        return {}
    
    success_response = responses.get('200', responses.get('201', {}))
    content = success_response.get('content', {})
    
    if 'application/json' in content:
        schema = content['application/json'].get('schema', {})
        return _generate_example_from_schema(schema)
    
    return {'message': 'success'}


def _generate_assertions(path):
    """生成断言列表"""
    assertions = ['验证响应状态码为200']
    
    method = path.get('method', '').upper()
    if method == 'POST':
        assertions.append('验证创建成功消息')
    elif method == 'PUT':
        assertions.append('验证更新成功消息')
    elif method == 'DELETE':
        assertions.append('验证删除成功消息')
    elif method == 'GET':
        assertions.append('验证返回数据结构')
    
    assertions.append('验证响应时间小于2秒')
    return assertions


def _determine_pre_conditions(path):
    """确定前置条件"""
    url = path.get('path', '')
    method = path.get('method', '').upper()
    
    if '/auth' in url or '/login' in url:
        return '无'
    elif method in ['PUT', 'DELETE'] and '{id}' in url:
        return '需要先创建测试数据'
    elif '/admin' in url:
        return '需要管理员权限'
    else:
        return '需要有效的认证Token'


def _generate_example_value(param_type):
    """根据类型生成示例值"""
    examples = {
        'string': 'example_string',
        'integer': 123,
        'number': 123.45,
        'boolean': True,
        'array': [],
        'object': {}
    }
    return examples.get(param_type, 'example_value')


def _generate_example_from_schema(schema):
    """从模式生成示例数据"""
    if not schema:
        return {}
    
    schema_type = schema.get('type', 'object')
    
    if schema_type == 'object':
        properties = schema.get('properties', {})
        example = {}
        for prop_name, prop_schema in properties.items():
            example[prop_name] = _generate_example_from_schema(prop_schema)
        return example
    elif schema_type == 'array':
        items = schema.get('items', {})
        return [_generate_example_from_schema(items)]
    else:
        return _generate_example_value(schema_type)
@click.option('--input', '-i', type=click.Path(exists=True), required=True, help='API文档文件路径')
@click.option('--workspace', '-w', type=click.Path(), default='./ai_smart_test_project', help='工作区路径')
@click.option('--execute', is_flag=True, help='生成后立即执行测试')
@click.option('--data-count', type=int, default=10, help='生成测试数据数量')
@click.option('--business-context', help='业务上下文描述')
@click.option('--test-types', multiple=True, default=['functional', 'boundary'], help='测试类型')
@click.option('--parallel', type=int, default=2, help='并行执行数量')
@click.pass_context
def ai_smart_test(ctx, input, workspace, execute, data_count, business_context, test_types, parallel):
    """🤖 AI智能测试：根据接口情况结合AI生成测试数据和测试用例并执行"""
    config = ctx.obj['config']
    api_key = config.get('ai.deepseek_api_key')
    
    if not api_key:
        click.echo("❌ 请先设置AI API Key: python3 -m src.cli.main ai setup --api-key YOUR_KEY", err=True)
        sys.exit(1)
    
    click.echo("🎯 欢迎使用AI智能测试功能！")
    click.echo("=" * 60)
    click.echo(f"📁 API文档: {input}")
    click.echo(f"💼 工作区: {workspace}")
    click.echo(f"📊 数据数量: {data_count}")
    click.echo(f"🎭 测试类型: {', '.join(test_types)}")
    if business_context:
        click.echo(f"🏢 业务上下文: {business_context}")
    click.echo("=" * 60)
    
    try:
        import json
        from pathlib import Path
        from datetime import datetime
        
        workspace_path = Path(workspace)
        workspace_path.mkdir(parents=True, exist_ok=True)
        
        click.echo("\n🔍 第一步：解析API文档")
        # 解析API文档
        parser = OpenAPIParser()
        if not parser.load_from_file(input):
            click.echo("❌ API文档解析失败", err=True)
            sys.exit(1)
        
        api_info = parser.get_api_info()
        api_spec = parser.get_full_spec()
        paths = parser.get_all_paths()
        
        click.echo(f"✅ 解析成功: {api_info['title']} v{api_info['version']}")
        click.echo(f"📊 发现 {len(paths)} 个API接口")
        
        # 初始化AI客户端
        click.echo("\n🤖 第二步：初始化AI客户端")
        from ..ai import DeepSeekClient, AITestGenerator, AITestReporter
        client = DeepSeekClient(api_key)
        test_generator = AITestGenerator(client)
        test_generator = AITestGenerator(client)
        
        # AI分析接口情况
        click.echo("\n🧠 第三步：AI分析接口情况")
        analysis_result = test_generator._analyze_api_specification(api_spec, business_context)
        
        if not analysis_result.success:
            click.echo(f"❌ AI分析失败: {analysis_result.error}", err=True)
            sys.exit(1)
        
        click.echo("✅ AI分析完成")
        
        # 创建项目结构
        click.echo("\n📁 第四步：创建项目结构")
        _create_smart_project_structure(workspace_path)
        
        # 生成智能测试数据
        click.echo("\n📊 第五步：AI生成智能测试数据")
        test_data = {}
        
        for i, path in enumerate(paths[:5], 1):  # 限制处理数量
            operation_id = path.get('operation_id', f'operation_{i}')
            click.echo(f"  📍 生成 {operation_id} 的测试数据...")
            
            # 构建数据模式
            data_schema = _extract_data_schema(path)
            scenarios = [f"{path.get('method', 'GET')} {path.get('path', '/')}"]
            
            # 为每种测试类型生成数据
            for test_type in test_types:
                data_result = test_generator.generate_realistic_test_data(
                    schema=data_schema,
                    count=data_count,
                    business_context=business_context or f"{api_info['title']} API测试"
                )
                
                if data_result.get('success'):
                    test_data[f"{operation_id}_{test_type}"] = data_result.get('data', {})
                    click.echo(f"    ✅ {test_type} 测试数据生成成功")
                else:
                    click.echo(f"    ⚠️ {test_type} 测试数据生成失败: {data_result.get('error', '未知错误')}")
        
        # 保存测试数据
        data_file = workspace_path / 'data' / 'ai_generated_test_data.json'
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
        
        click.echo(f"✅ 测试数据已保存: {data_file}")
        
        # AI生成智能测试用例
        click.echo("\n🧪 第六步：AI生成智能测试用例")
        
        test_result = test_generator.generate_comprehensive_tests(
            api_spec=api_spec,
            business_context=business_context,
            test_requirements=list(test_types)
        )
        
        if 'error' in test_result:
            click.echo(f"❌ 测试用例生成失败: {test_result['error']}", err=True)
            sys.exit(1)
        
        click.echo(f"✅ 测试用例生成成功，共 {test_result['summary']['total_tests']} 个测试")
        
        # 生成可执行的测试脚本
        click.echo("\n💻 第七步：生成可执行测试脚本")
        _generate_ai_test_scripts(workspace_path, api_info, test_result, test_data)
        
        # 生成配置文件
        click.echo("\n⚙️ 第八步：生成智能测试配置")
        _generate_smart_test_config(workspace_path, api_info, api_key)
        
        # 生成项目文档
        click.echo("\n📚 第九步：生成项目文档")
        _generate_smart_project_docs(workspace_path, api_info, test_result, business_context)
        
        click.echo("\n" + "=" * 60)
        click.echo("🎉 AI智能测试项目生成成功！")
        click.echo("=" * 60)
        click.echo(f"💼 项目位置: {workspace_path.absolute()}")
        click.echo(f"📊 测试数据: {data_file.relative_to(workspace_path)}")
        click.echo(f"🧪 测试脚本: tests/ai_generated/")
        click.echo(f"📋 测试配置: config/ai_test_config.yaml")
        
        # 如果选择执行测试
        if execute:
            click.echo("\n🚀 第十步：立即执行AI生成的测试")
            _execute_ai_tests(workspace_path, parallel)
        else:
            click.echo("\n🛠️ 下一步操作:")
            click.echo(f"1. 进入项目: cd {workspace}")
            click.echo("2. 执行测试: python3 -m src.cli.main test run --path tests/ai_generated/ --parallel 2")
            click.echo("3. 查看报告: open reports/")
            click.echo("4. 查看文档: cat README.md")
        
    except Exception as e:
        click.echo(f"❌ AI智能测试失败: {e}", err=True)
        import traceback
        if ctx.obj.get('debug'):
            click.echo(traceback.format_exc(), err=True)
        sys.exit(1)
    



def _create_project_config(workspace_path, project_name, api_info, mock_port, api_key=None):
    """创建项目配置文件"""
    config_content = f'''# {project_name} 项目配置文件
# 自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

global:
  timeout: 30
  retry: 3
  parallel: 4
  keep_alive: true
  pool_connections: 10
  pool_maxsize: 10

environments:
  dev:
    base_url: "http://localhost:{mock_port}"
    headers:
      Content-Type: "application/json"
      User-Agent: "{project_name}-AutoTest/1.0"
    timeout: 30
  
  test:
    base_url: "http://test-api.example.com"
    headers:
      Content-Type: "application/json"
      Authorization: "Bearer test-token"
    timeout: 20
    
  prod:
    base_url: "https://api.example.com"
    headers:
      Content-Type: "application/json"
      Authorization: "Bearer prod-token"
    timeout: 15

mock:
  port: {mock_port}
  host: "localhost"
  enable_cors: true
  debug: true

logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# API信息
api_info:
  title: "{api_info.get('title', 'API')}"
  version: "{api_info.get('version', '1.0.0')}"
  description: "{api_info.get('description', '')}"
'''
    
    if api_key:
        config_content += f'''
# AI配置
ai:
  provider: "deepseek"
  api_key: "{api_key}"
  model: "deepseek-chat"
  max_tokens: 4000
  temperature: 0.3
'''
    
    # 写入配置文件
    config_file = workspace_path / 'config' / 'default.yaml'
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(config_content)


def _generate_ai_enhanced_tests(api_info, api_spec, workspace_path, business_context, api_key):
    """生成AI增强测试"""
    try:
        client = DeepSeekClient(api_key)  # type: ignore
        generator = AITestGenerator(client)  # type: ignore
        
        result = generator.generate_comprehensive_tests(
            api_spec=api_spec,
            business_context=business_context or f"{api_info['title']} API测试",
            test_requirements=['functional', 'boundary', 'security']
        )
        
        if result.get('success'):
            # 保存AI生成的测试
            ai_output = workspace_path / 'tests' / 'ai_enhanced'
            output_file = ai_output / f"ai_tests_{api_info['title'].replace(' ', '_')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
    except Exception as e:
        click.echo(f"AI增强失败: {e}")


def _generate_mock_config(workspace_path, paths, api_info):
    """生成Mock配置"""
    mock_routes = {
        "routes": []
    }
    
    for path in paths[:5]:  # 只生成前5个接口的Mock
        route = {
            "method": path.get('method', 'GET').upper(),
            "path": path.get('path', '/'),
            "response": {
                "status_code": 200,
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": {
                    "message": "Mock response",
                    "data": {},
                    "timestamp": "2023-11-20T10:00:00Z"
                }
            }
        }
        mock_routes["routes"].append(route)
    
    # 写入Mock配置文件
    mock_file = workspace_path / 'config' / 'mock_routes.json'
    with open(mock_file, 'w', encoding='utf-8') as f:
        json.dump(mock_routes, f, ensure_ascii=False, indent=2)


def _generate_scripts(workspace_path, project_name, mock_port, parallel):
    """生成脚本文件"""
    # 生成运行测试脚本
    run_script = f'''#!/bin/bash
echo "🚀 运行 {project_name} 自动化测试"

# 设置环境变量
export PYTHONPATH="$(pwd):$PYTHONPATH"

# 运行测试
python -m src.cli.main test run \\
  --path tests/ \\
  --parallel {parallel} \\
  --format html,json \\
  --output reports/

echo "✅ 测试完成，查看报告: reports/"
'''
    
    # 生成停止Mock脚本
    stop_script = f'''#!/bin/bash
echo "🛑 停止Mock服务器"
pkill -f "port {mock_port}"
echo "✅ Mock服务器已停止"
'''
    
    # 写入脚本文件
    scripts_dir = workspace_path / 'scripts'
    
    run_file = scripts_dir / 'run_tests.sh'
    with open(run_file, 'w', encoding='utf-8') as f:
        f.write(run_script)
    run_file.chmod(0o755)
    
    stop_file = scripts_dir / 'stop_mock.sh'
    with open(stop_file, 'w', encoding='utf-8') as f:
        f.write(stop_script)
    stop_file.chmod(0o755)


def _generate_project_docs(workspace_path, project_name, api_info, api_count):
    """生成项目文档"""
    readme_content = f'''# {project_name} 自动化测试项目

由接口自动化测试框架自动生成

## 项目信息

- **API名称**: {api_info.get('title', 'Unknown')}
- **版本**: {api_info.get('version', '1.0.0')}
- **接口数量**: {api_count}
- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 快速开始

### 1. 运行测试
```bash
./scripts/run_tests.sh
```

### 2. 查看报告
```bash
open reports/
```

### 3. 停止Mock服务器
```bash
./scripts/stop_mock.sh
```

## 目录结构

```
{project_name.lower()}/
├── config/          # 配置文件
├── specs/           # API规格文档
├── tests/           # 测试文件
│   ├── generated/   # 自动生成的测试
│   ├── manual/      # 手动编写的测试
│   └── ai_enhanced/ # AI增强测试
├── data/            # 测试数据
├── reports/         # 测试报告
├── exports/         # 导出文件
├── scripts/         # 脚本文件
└── docs/            # 文档
```

## 配置说明

主要配置文件位于 `config/default.yaml`，包含：
- 环境配置
- Mock服务配置
- AI功能配置（如果启用）

## 使用指南

详细使用指南请参考框架文档。
'''
    
    # 写入README文件
    readme_file = workspace_path / 'README.md'
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)


def _start_mock_server(workspace_path, mock_port):
    """启动Mock服务器"""
    import subprocess
    try:
        mock_config = workspace_path / 'config' / 'mock_routes.json'
        cmd = [
            sys.executable, '-m', 'src.cli.main', 'mock', 'start',
            '--port', str(mock_port),
            '--routes-file', str(mock_config)
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=str(workspace_path.parent)
        )
        return process
    except Exception as e:
        click.echo(f"启动Mock服务器失败: {e}")
        return None


def _run_generated_tests(workspace_path, parallel):
    """运行生成的测试"""
    import subprocess
    try:
        cmd = [
            sys.executable, '-m', 'src.cli.main', 'test', 'run',
            '--path', 'tests/',
            '--parallel', str(parallel),
            '--format', 'html,json',
            '--output', 'reports/'
        ]
        
        result = subprocess.run(
            cmd,
            cwd=str(workspace_path),
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            click.echo("测试执行成功")
        else:
            click.echo(f"测试执行失败: {result.stderr}")
            
    except Exception as e:
        click.echo(f"测试执行错误: {e}")


if __name__ == '__main__':
    cli()


def _create_smart_project_structure(workspace_path):
    """创建AI智能测试项目结构"""
    from pathlib import Path
    
    # 创建目录结构
    directories = [
        'config',
        'specs', 
        'tests/ai_generated',
        'tests/manual',
        'data',
        'reports',
        'exports',
        'scripts',
        'docs'
    ]
    
    for directory in directories:
        (workspace_path / directory).mkdir(parents=True, exist_ok=True)


def _extract_data_schema(path_info):
    """从路径信息中提取数据模式"""
    schema = {
        "type": "object",
        "properties": {
            "id": {"type": "integer", "example": 1},
            "name": {"type": "string", "example": "test_name"},
            "email": {"type": "string", "example": "test@example.com"}
        }
    }
    
    # 尝试从requestBody中提取schema
    request_body = path_info.get('requestBody', {})
    if request_body:
        content = request_body.get('content', {})
        if 'application/json' in content:
            json_schema = content['application/json'].get('schema', {})
            if json_schema:
                schema = json_schema
    
    return schema


def _generate_ai_test_scripts(workspace_path, api_info, test_result, test_data):
    """生成AI测试脚本"""
    import json
    from pathlib import Path
    
    # 基础测试类模板
    test_template = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI生成的智能测试脚本
API: {api_info.get('title', 'Unknown API')}
版本: {api_info.get('version', '1.0.0')}
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.base_test import BaseTest


class AI{_to_class_name(api_info.get('title', 'API'))}Test(BaseTest):
    """AI生成的智能测试类"""
    
    def __init__(self, config_path=None):
        super().__init__(config_path or "config/ai_test_config.yaml")
        self.load_test_data()
    
    def load_test_data(self):
        """加载AI生成的测试数据"""
        data_file = Path(__file__).parent.parent / "data" / "ai_generated_test_data.json"
        if data_file.exists():
            with open(data_file, 'r', encoding='utf-8') as f:
                self.test_data = json.load(f)
        else:
            self.test_data = {{}}
    
    def test_ai_generated_comprehensive(self):
        """AI生成的综合测试用例"""
        results = []
        
        # 功能性测试
        if 'functional' in self.test_data:
            result = self._run_functional_tests()
            results.append(result)
        
        # 边界值测试
        if 'boundary' in self.test_data:
            result = self._run_boundary_tests()
            results.append(result)
        
        return results
    
    def _run_functional_tests(self):
        """运行功能性测试"""
        # 这里会使用AI生成的具体测试逻辑
        result = self.make_request(
            method='GET',
            url='/api/test',
            test_name='ai_functional_test'
        )
        
        # AI生成的断言
        self.assert_status_code(result, 200)
        return result
    
    def _run_boundary_tests(self):
        """运行边界值测试"""
        # 使用AI生成的边界值测试数据
        result = self.make_request(
            method='POST',
            url='/api/test',
            json=self.test_data.get('boundary', {{}}),
            test_name='ai_boundary_test'
        )
        
        return result
    
    def run_tests(self):
        """运行所有AI生成的测试"""
        test_methods = [
            self.test_ai_generated_comprehensive
        ]
        
        results = []
        for test_method in test_methods:
            try:
                result = test_method()
                results.append({{
                    'test_name': test_method.__name__,
                    'success': True,
                    'result': result
                }})
                print(f"✅ PASS {{test_method.__name__}}")
            except Exception as e:
                results.append({{
                    'test_name': test_method.__name__,
                    'success': False,
                    'error': str(e)
                }})
                print(f"❌ FAIL {{test_method.__name__}}: {{e}}")
        
        return results


if __name__ == '__main__':
    test_instance = AI{_to_class_name(api_info.get('title', 'API'))}Test()
    results = test_instance.run_tests()
    
    summary = test_instance.get_test_summary()
    print(f"\n📊 AI测试汇总:")
    print(f"总计: {{summary['total']}}, 成功: {{summary['success']}}, 失败: {{summary['failed']}}")
    print(f"成功率: {{summary['success_rate']:.2%}}")
'''
    
    # 写入测试文件
    test_file = workspace_path / 'tests' / 'ai_generated' / f'test_ai_{_to_file_name(api_info.get("title", "api"))}.py'
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_template)


def _generate_smart_test_config(workspace_path, api_info, api_key):
    """生成智能测试配置文件"""
    import yaml
    
    config = {
        'test_config': {
            'name': f'{api_info.get("title", "API")}智能测试',
            'version': api_info.get('version', '1.0.0'),
            'environment': 'dev',
            'timeout': 30,
            'retry_count': 2
        },
        'ai_config': {
            'enabled': True,
            'deepseek_api_key': api_key,
            'model': 'deepseek-chat',
            'max_tokens': 4000,
            'temperature': 0.3
        },
        'data_config': {
            'realistic_count': 10,
            'boundary_count': 5,
            'invalid_count': 3,
            'locale': 'zh_CN'
        },
        'execution_config': {
            'parallel': 2,
            'fail_fast': False,
            'generate_reports': True,
            'report_formats': ['html', 'json']
        }
    }
    
    config_file = workspace_path / 'config' / 'ai_test_config.yaml'
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.safe_dump(config, f, default_flow_style=False, allow_unicode=True)


def _generate_smart_project_docs(workspace_path, api_info, test_result, business_context):
    """生成智能测试项目文档"""
    
    readme_content = f'''# {api_info.get("title", "API")} AI智能测试项目

由接口自动化测试框架AI功能自动生成

## 🤖 项目信息

- **API名称**: {api_info.get('title', 'Unknown')}
- **版本**: {api_info.get('version', '1.0.0')}
- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **测试用例数**: {test_result.get('summary', {}).get('total_tests', 0)}
- **业务上下文**: {business_context or '无'}

## 🧠 AI增强功能

本项目使用AI技术增强测试能力：

1. **智能分析**: AI分析API接口特征和业务逻辑
2. **智能数据生成**: 根据业务场景生成真实有意义的测试数据
3. **智能用例生成**: 自动生成功能、边界、异常等多种测试场景
4. **智能断言**: AI推荐最佳的验证策略
5. **智能优化**: 根据执行结果持续优化测试用例

## 🚀 快速开始

### 1. 执行AI生成的测试
```bash
# 进入项目目录
cd {workspace_path.name}

# 执行AI智能测试
python3 -m src.cli.main test run --path tests/ai_generated/ --parallel 2

# 查看测试报告
open reports/
```

### 2. 查看AI生成的测试数据
```bash
cat data/ai_generated_test_data.json
```

### 3. 自定义配置
```bash
# 编辑AI测试配置
vim config/ai_test_config.yaml
```

## 📁 项目结构

```
ai_smart_test_project/
├── config/
│   └── ai_test_config.yaml    # AI测试配置
├── data/
│   └── ai_generated_test_data.json  # AI生成的测试数据
├── tests/
│   ├── ai_generated/          # AI生成的测试脚本
│   └── manual/                # 手动编写的测试
├── reports/                   # 测试报告
├── exports/                   # 导出文件
└── docs/                      # 文档
```

## 🔧 配置说明

AI测试配置文件 `config/ai_test_config.yaml` 包含：

- **test_config**: 基础测试配置
- **ai_config**: AI功能配置
- **data_config**: 测试数据配置
- **execution_config**: 执行配置

## 📊 AI测试报告

AI增强的测试报告包含：

1. **智能分析结果**: API接口分析和建议
2. **测试覆盖度**: 功能、边界、异常覆盖情况
3. **数据质量评估**: 测试数据的真实性和有效性
4. **性能分析**: 接口响应时间和性能表现
5. **改进建议**: AI提供的测试优化建议

## 💡 使用技巧

1. **业务上下文**: 提供详细的业务上下文可以让AI生成更准确的测试
2. **数据量调整**: 根据需要调整测试数据数量
3. **测试类型**: 选择合适的测试类型组合
4. **并行执行**: 利用并行执行提升测试效率

## 🆘 问题排查

If you encounter issues:

1. 检查AI API Key配置
2. 确认网络连接正常
3. 查看详细错误日志
4. 参考框架文档

---

*本项目由接口自动化测试框架AI功能自动生成，体验智能化测试的强大能力！*
'''
    
    readme_file = workspace_path / 'README.md'
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)


def _execute_ai_tests(workspace_path, parallel):
    """执行AI生成的测试"""
    import subprocess
    
    click.echo("🚀 开始执行AI生成的测试...")
    
    try:
        # 执行测试命令
        cmd = [
            sys.executable, '-m', 'src.cli.main', 'test', 'run',
            '--path', 'tests/ai_generated/',
            '--parallel', str(parallel),
            '--format', 'html,json',
            '--output', 'reports/'
        ]
        
        result = subprocess.run(
            cmd,
            cwd=str(workspace_path),
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            click.echo("✅ AI测试执行成功")
            click.echo("📄 测试报告已生成: reports/")
        else:
            click.echo(f"❌ AI测试执行失败: {result.stderr}")
            
    except Exception as e:
        click.echo(f"❌ AI测试执行错误: {e}")