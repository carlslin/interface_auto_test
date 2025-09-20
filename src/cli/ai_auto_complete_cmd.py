"""
AI增强的一键自动完成命令

集成全面的AI功能，为所有接口提供智能补全
"""

import click
import sys
import json
import yaml
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.parsers.openapi_parser import OpenAPIParser
from src.exporters.test_case_exporter import TestCaseExporter

try:
    from src.ai import (
        DeepSeekClient, 
        AICompletionManager, 
        AIDecisionCenter
    )
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    # 类型提示，避免语法错误
    from typing import Any
    DeepSeekClient = Any
    AICompletionManager = Any
    AIDecisionCenter = Any


@click.command()
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
    
    # 获取API Key
    if not api_key:
        config = ctx.obj.get('config') if ctx.obj else None
        if config:
            api_key = config.get('ai.deepseek_api_key')
        
        if not api_key:
            click.echo("❌ 请提供DeepSeek API Key", err=True)
            click.echo("💡 使用 --api-key 参数或运行 'python3 -m src.cli.main ai setup --api-key YOUR_KEY'")
            sys.exit(1)
    
    click.echo("🎆 欢迎使用AI增强一键自动完成功能！")
    click.echo("=" * 70)
    click.echo(f"📁 API文档: {input}")
    click.echo(f"💼 工作区: {workspace}")
    click.echo(f"🤖 补全级别: {completion_level}")
    click.echo(f"🔧 并发数量: {parallel_workers}")
    if business_context:
        click.echo(f"🏢 业务上下文: {business_context}")
    click.echo("=" * 70)
    
    start_time = datetime.now()
    
    try:
        # 第一步：初始化AI客户端
        click.echo("\n🚀 第一步：初始化AI服务")
        client = DeepSeekClient(api_key)  # type: ignore
        
        if not client.validate_api_key():
            click.echo("❌ API Key验证失败", err=True)
            sys.exit(1)
        
        click.echo("✅ AI服务初始化成功")
        
        # 第二步：解析API文档
        click.echo("\n🔍 第二步：解析API文档")
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
        api_spec = parser.get_full_spec()
        
        if not project_name:
            project_name = api_info.get('title', 'AI_Complete_Project').replace(' ', '_')
        
        click.echo(f"✅ 解析成功: {api_info['title']} v{api_info['version']}")
        click.echo(f"📊 发现 {len(parser.get_all_paths())} 个API接口")
        
        # 第三步：创建项目结构
        click.echo("\n📁 第三步：创建增强项目结构")
        workspace_path = Path(workspace)
        _create_enhanced_project_structure(workspace_path)
        
        # 第四步：AI智能分析
        if enable_analysis:
            click.echo("\n🧠 第四步：AI智能分析API")
            decision_center = AIDecisionCenter()  # type: ignore
            
            with click.progressbar(length=100, label='分析进度') as bar:
                # 使用简化的API分析功能
                from src.ai import AITestGenerator
                analyzer = AITestGenerator(client)
                analysis_result = analyzer.simple_api_analysis(api_spec, business_context)
                bar.update(100)
            
            if analysis_result.get('status') == 'completed':
                click.echo("✅ API智能分析完成")
                
                # 保存分析结果
                analysis_file = workspace_path / 'ai_generated' / 'reports' / 'api_analysis.json'
                with open(analysis_file, 'w', encoding='utf-8') as f:
                    json.dump(analysis_result, f, ensure_ascii=False, indent=2)
                
                # 显示分析摘要
                _display_analysis_summary(analysis_result)
            else:
                click.echo(f"⚠️ API分析部分失败: {analysis_result.get('error', '未知错误')}")
                analysis_result = None
        else:
            analysis_result = None
        
        # 第五步：生成补全策略
        click.echo("\n📋 第五步：制定AI补全策略")
        
        # 解析自定义需求
        requirements = []
        if custom_requirements:
            requirements = [req.strip() for req in custom_requirements.split(',')]
        
        # 根据补全级别调整配置
        completion_config = _get_completion_config(completion_level)
        
        if analysis_result:
            strategy_manager = CompletionStrategy(analyzer)  # type: ignore
            completion_strategy = strategy_manager.generate_completion_strategy(
                analysis_result, requirements
            )
            click.echo("✅ 智能补全策略制定完成")
        else:
            completion_strategy = _get_default_strategy()
            click.echo("✅ 默认补全策略制定完成")
        
        # 第六步：执行AI全面补全
        click.echo("\n🤖 第六步：执行AI全面补全")
        completion_manager = AICompletionManager(client)  # type: ignore
        
        # 配置补全管理器
        completion_manager.completion_config.update(completion_config)
        completion_manager.completion_config['max_workers'] = parallel_workers
        
        with click.progressbar(length=100, label='补全进度') as bar:
            completion_result = completion_manager.complete_all_interfaces(
                api_spec, workspace_path, business_context, requirements
            )
            bar.update(100)
        
        if completion_result.get('status') == 'completed':
            click.echo("✅ AI全面补全完成")
            _display_completion_summary(completion_result)
        else:
            click.echo(f"❌ AI补全失败: {completion_result.get('error', '未知错误')}")
            sys.exit(1)
        
        # 第七步：生成项目配置
        click.echo("\n⚙️ 第七步：生成项目配置")
        _generate_ai_project_config(workspace_path, project_name, api_info, completion_result)
        click.echo("✅ 项目配置生成完成")
        
        # 第八步：生成执行脚本
        click.echo("\n🔧 第八步：生成执行脚本")
        _generate_ai_scripts(workspace_path, project_name, completion_strategy)
        click.echo("✅ 执行脚本生成完成")
        
        # 第九步：生成综合报告
        click.echo("\n📊 第九步：生成综合报告")
        report_path = _generate_comprehensive_report(
            workspace_path, project_name, api_info, analysis_result, 
            completion_result, completion_strategy
        )
        click.echo(f"✅ 综合报告生成完成: {report_path}")
        
        # 完成总结
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        click.echo("\n" + "=" * 70)
        click.echo("🎉 AI增强一键自动完成成功！")
        click.echo("=" * 70)
        click.echo(f"⏱️ 总耗时: {duration:.2f}秒")
        click.echo(f"💼 项目位置: {workspace_path.absolute()}")
        click.echo(f"📊 完成接口: {completion_result.get('summary', {}).get('completed', 0)}/{completion_result.get('summary', {}).get('total_interfaces', 0)}")
        click.echo(f"🧪 生成测试: {completion_result.get('summary', {}).get('generated_tests', 0)}个")
        click.echo(f"📄 生成文件: {len(completion_result.get('generated_files', []))}个")
        
        click.echo("\n🛠️ 快速操作指南:")
        click.echo(f"  进入项目:    cd {workspace_path}")
        click.echo("  查看报告:    open ai_generated/reports/")
        click.echo("  运行AI测试:  ./scripts/run_ai_tests.sh")
        click.echo("  查看分析:    ./scripts/view_analysis.sh")
        
        click.echo("\n📚 AI增强功能:")
        click.echo(f"  智能分析:    {workspace_path}/ai_generated/reports/api_analysis.json")
        click.echo(f"  补全报告:    {workspace_path}/ai_generated/reports/completion_report.md")
        click.echo(f"  测试用例:    {workspace_path}/ai_generated/tests/")
        click.echo(f"  测试数据:    {workspace_path}/ai_generated/data/")
        
    except KeyboardInterrupt:
        click.echo("\n⚠️ 用户中断操作")
        sys.exit(1)
    except Exception as e:
        click.echo(f"\n❌ AI自动完成失败: {str(e)}", err=True)
        sys.exit(1)


def _create_enhanced_project_structure(workspace_path: Path):
    """创建增强的项目结构"""
    directories = [
        'ai_generated',
        'ai_generated/tests',
        'ai_generated/data', 
        'ai_generated/reports',
        'ai_generated/reviews',
        'ai_generated/assertions',
        'ai_generated/optimizations',
        'config',
        'specs',
        'scripts',
        'docs',
        'exports'
    ]
    
    for dir_name in directories:
        (workspace_path / dir_name).mkdir(parents=True, exist_ok=True)


def _get_completion_config(completion_level: str) -> Dict[str, Any]:
    """获取补全配置"""
    configs = {
        'basic': {
            'enable_parallel': False,
            'enable_test_generation': True,
            'enable_data_generation': False,
            'enable_code_review': False,
            'enable_assertion_optimization': False
        },
        'standard': {
            'enable_parallel': True,
            'enable_test_generation': True,
            'enable_data_generation': True,
            'enable_code_review': False,
            'enable_assertion_optimization': True
        },
        'comprehensive': {
            'enable_parallel': True,
            'enable_test_generation': True,
            'enable_data_generation': True,
            'enable_code_review': True,
            'enable_assertion_optimization': True,
            'auto_optimize': True
        },
        'enterprise': {
            'enable_parallel': True,
            'enable_test_generation': True,
            'enable_data_generation': True,
            'enable_code_review': True,
            'enable_assertion_optimization': True,
            'auto_optimize': True,
            'enable_smart_analysis': True
        }
    }
    
    return configs.get(completion_level, configs['standard'])


def _get_default_strategy() -> Dict[str, Any]:
    """获取默认策略"""
    return {
        'test_priorities': [
            {'category': 'functional', 'priority': 'high'},
            {'category': 'boundary', 'priority': 'medium'},
            {'category': 'security', 'priority': 'high'}
        ],
        'data_generation_strategy': {
            'realistic_data_needed': True,
            'boundary_testing': True,
            'security_testing': True
        }
    }


def _display_analysis_summary(analysis_result: Dict[str, Any]):
    """显示分析摘要"""
    analysis = analysis_result.get('analysis', {})
    
    # 显示结构信息
    structure = analysis.get('structure', {})
    if structure:
        endpoints = structure.get('endpoints', {})
        click.echo(f"  📊 接口统计: 总数 {endpoints.get('total', 0)}")
        click.echo(f"  🔒 安全接口: {endpoints.get('with_security', 0)}个")
        click.echo(f"  📝 复杂度分数: {structure.get('complexity_score', 0):.1f}")
    
    # 显示风险评估
    risks = analysis.get('risk_assessment', {})
    if risks:
        risk_score = risks.get('overall_risk_score', 0)
        click.echo(f"  ⚠️ 风险评分: {risk_score:.1f}")
        if risks.get('security_risks'):
            click.echo(f"  🔐 安全风险: {len(risks['security_risks'])}项")


def _display_completion_summary(completion_result: Dict[str, Any]):
    """显示补全摘要"""
    summary = completion_result.get('summary', {})
    
    click.echo(f"  📊 完成接口: {summary.get('completed', 0)}/{summary.get('total_interfaces', 0)}")
    click.echo(f"  🧪 生成测试: {summary.get('generated_tests', 0)}个")
    click.echo(f"  📦 生成数据集: {summary.get('generated_data_sets', 0)}个")
    
    if summary.get('failed', 0) > 0:
        click.echo(f"  ❌ 失败接口: {summary.get('failed', 0)}个")


def _generate_ai_project_config(workspace_path: Path, project_name: str, 
                               api_info: Dict[str, Any], completion_result: Dict[str, Any]):
    """生成AI项目配置"""
    config_content = {
        'project': {
            'name': project_name,
            'version': '1.0.0',
            'description': f"AI增强的{api_info.get('title', 'API')}测试项目",
            'created_at': datetime.now().isoformat()
        },
        'api': {
            'title': api_info.get('title', 'API'),
            'version': api_info.get('version', '1.0.0'),
            'description': api_info.get('description', '')
        },
        'ai': {
            'completion_status': completion_result.get('status'),
            'completed_interfaces': completion_result.get('summary', {}).get('completed', 0),
            'total_interfaces': completion_result.get('summary', {}).get('total_interfaces', 0),
            'generated_tests': completion_result.get('summary', {}).get('generated_tests', 0)
        },
        'testing': {
            'test_framework': 'pytest',
            'parallel_execution': True,
            'generate_reports': True,
            'report_formats': ['html', 'json']
        }
    }
    
    config_file = workspace_path / 'config' / 'ai_project.yaml'
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(config_content, f, default_flow_style=False, allow_unicode=True)


def _generate_ai_scripts(workspace_path: Path, project_name: str, strategy: Dict[str, Any]):
    """生成AI脚本"""
    
    # 生成AI测试运行脚本
    ai_test_script = f'''#!/bin/bash
echo "🤖 运行AI增强测试"

# 设置环境变量
export PYTHONPATH="$(pwd):$PYTHONPATH"

# 运行AI生成的测试
echo "📋 执行功能测试..."
python -m pytest ai_generated/tests/ -v --tb=short

echo "✅ AI测试完成"
'''
    
    # 生成分析查看脚本
    view_analysis_script = f'''#!/bin/bash
echo "📊 查看AI分析报告"

if [ -f "ai_generated/reports/api_analysis.json" ]; then
    echo "=== API分析摘要 ==="
    python -c "
import json
with open('ai_generated/reports/api_analysis.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    print(f'API: {{data.get(\"api_info\", {{}}).get(\"title\", \"Unknown\")}}')
    print(f'状态: {{data.get(\"status\", \"Unknown\")}}')
    analysis = data.get('analysis', {{}})
    if 'structure' in analysis:
        print(f'接口数量: {{analysis[\"structure\"].get(\"endpoints\", {{}}).get(\"total\", 0)}}')
        print(f'复杂度: {{analysis[\"structure\"].get(\"complexity_score\", 0):.1f}}')
"
    echo ""
    echo "详细报告位置: ai_generated/reports/"
else
    echo "❌ 分析报告未找到"
fi
'''
    
    # 写入脚本文件
    scripts_dir = workspace_path / 'scripts'
    
    ai_test_file = scripts_dir / 'run_ai_tests.sh'
    with open(ai_test_file, 'w', encoding='utf-8') as f:
        f.write(ai_test_script)
    ai_test_file.chmod(0o755)
    
    view_file = scripts_dir / 'view_analysis.sh'
    with open(view_file, 'w', encoding='utf-8') as f:
        f.write(view_analysis_script)
    view_file.chmod(0o755)


def _generate_comprehensive_report(workspace_path: Path, project_name: str, 
                                 api_info: Dict[str, Any], analysis_result: Optional[Dict[str, Any]],
                                 completion_result: Dict[str, Any], strategy: Dict[str, Any]) -> Path:
    """生成综合报告"""
    
    report_content = f"""# {project_name} AI增强测试项目报告

## 📋 项目概述

- **项目名称**: {project_name}
- **API名称**: {api_info.get('title', 'Unknown')}
- **API版本**: {api_info.get('version', '1.0.0')}
- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🤖 AI补全结果

### 总体统计
- **总接口数**: {completion_result.get('summary', {}).get('total_interfaces', 0)}
- **完成补全**: {completion_result.get('summary', {}).get('completed', 0)}
- **生成测试**: {completion_result.get('summary', {}).get('generated_tests', 0)}个
- **生成数据集**: {completion_result.get('summary', {}).get('generated_data_sets', 0)}个
- **生成文件**: {len(completion_result.get('generated_files', []))}个

### 补全状态
- **状态**: {completion_result.get('status', 'Unknown')}
- **耗时**: {completion_result.get('duration', 0):.2f}秒

## 📊 智能分析结果
"""
    
    if analysis_result and analysis_result.get('status') == 'completed':
        analysis = analysis_result.get('analysis', {})
        
        # 添加结构分析
        if 'structure' in analysis:
            structure = analysis['structure']
            report_content += f"""
### API结构分析
- **复杂度分数**: {structure.get('complexity_score', 0):.1f}
- **安全接口数**: {structure.get('endpoints', {}).get('with_security', 0)}
- **参数化接口**: {structure.get('endpoints', {}).get('with_parameters', 0)}
"""
        
        # 添加风险评估
        if 'risk_assessment' in analysis:
            risks = analysis['risk_assessment']
            report_content += f"""
### 风险评估
- **总体风险分数**: {risks.get('overall_risk_score', 0):.1f}
- **安全风险**: {len(risks.get('security_risks', []))}项
- **性能风险**: {len(risks.get('performance_risks', []))}项
- **维护风险**: {len(risks.get('maintenance_risks', []))}项
"""
    
    report_content += f"""
## 🚀 使用指南

### 快速开始
```bash
# 进入项目目录
cd {workspace_path.name}

# 运行AI生成的测试
./scripts/run_ai_tests.sh

# 查看分析报告
./scripts/view_analysis.sh
```

### 目录结构
```
{project_name}/
├── ai_generated/          # AI生成内容
│   ├── tests/             # 测试用例
│   ├── data/              # 测试数据
│   ├── reports/           # 分析报告
│   └── assertions/        # 断言规则
├── config/                # 配置文件
├── scripts/               # 执行脚本
└── docs/                  # 文档
```

## 📝 下一步建议

1. **执行测试**: 运行AI生成的测试用例验证API功能
2. **审查数据**: 检查生成的测试数据是否符合业务需求
3. **优化配置**: 根据实际需要调整测试配置
4. **集成CI/CD**: 将测试集成到持续集成流程中

---
*报告由AI增强接口自动化测试框架生成*
"""
    
    # 保存报告
    report_path = workspace_path / 'ai_generated' / 'reports' / 'comprehensive_report.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    return report_path


if __name__ == '__main__':
    ai_auto_complete()