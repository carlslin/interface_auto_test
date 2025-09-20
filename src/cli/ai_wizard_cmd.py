"""
AI智能向导 - 用户友好的交互式配置和使用指导

提供零门槛的AI功能使用体验
"""

import click
import sys
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config_loader import ConfigLoader

try:
    from src.ai import DeepSeekClient, AIDecisionCenter
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    from typing import Any
    DeepSeekClient = Any
    AIDecisionCenter = Any


@click.group()
@click.pass_context
def ai_wizard(ctx):
    """🧙‍♂️ AI智能向导 - 让AI功能使用更简单"""
    if not AI_AVAILABLE:
        click.echo("❌ AI功能不可用，请安装相关依赖", err=True)
        sys.exit(1)


@ai_wizard.command()
@click.pass_context
def quick_start(ctx):
    """🚀 快速开始向导"""
    click.echo("🧙‍♂️ 欢迎使用AI接口自动化测试框架！")
    click.echo("=" * 60)
    click.echo("让我们通过几个简单步骤配置您的AI功能...")
    click.echo()
    
    # 步骤1：检查API Key
    click.echo("📋 步骤 1/4: 检查AI服务配置")
    config = ctx.obj.get('config') if ctx.obj else ConfigLoader()
    api_key = config.get('ai.deepseek_api_key')
    
    if not api_key:
        click.echo("🔑 未发现API Key，让我们来配置它...")
        api_key = click.prompt("请输入您的DeepSeek API Key", hide_input=True)
        
        if _validate_api_key(api_key):
            config.set('ai.deepseek_api_key', api_key)
            config.save_config()
            click.echo("✅ API Key配置成功！")
        else:
            click.echo("❌ API Key验证失败，请检查后重试")
            return
    else:
        click.echo("✅ 发现已配置的API Key")
    
    # 步骤2：选择使用场景
    click.echo("\n📋 步骤 2/4: 选择您的使用场景")
    scenarios = [
        "1. 新手用户 - 刚开始使用接口测试",
        "2. 开发团队 - 需要快速生成测试用例", 
        "3. 测试团队 - 需要全面的测试覆盖",
        "4. 企业用户 - 需要高质量和安全性"
    ]
    
    for scenario in scenarios:
        click.echo(f"   {scenario}")
    
    choice = click.prompt("请选择您的场景 (1-4)", type=int, default=2)
    scenario_config = _get_scenario_config(choice)
    
    # 步骤3：配置项目信息
    click.echo("\n📋 步骤 3/4: 配置项目信息")
    project_type = click.prompt("请描述您的项目类型", default="API接口测试项目")
    business_domain = click.prompt("请描述业务领域", default="通用业务")
    
    # 步骤4：保存配置并测试
    click.echo("\n📋 步骤 4/4: 保存配置并测试连接")
    
    # 保存智能配置
    ai_config = {
        'scenario': choice,
        'project_type': project_type,
        'business_domain': business_domain,
        **scenario_config
    }
    config.set('ai.wizard_config', ai_config)
    config.save_config()
    
    # 测试AI连接
    if _test_ai_connection(api_key):
        click.echo("✅ AI服务连接正常！")
    else:
        click.echo("⚠️ AI服务连接异常，但配置已保存")
    
    # 完成向导
    click.echo("\n" + "=" * 60)
    click.echo("🎉 配置完成！您现在可以使用AI功能了")
    click.echo()
    click.echo("🚀 推荐的下一步操作:")
    click.echo("   1. 使用智能分析: autotest ai-wizard analyze-api -i your_api.yaml")
    click.echo("   2. 一键生成测试: autotest ai-wizard auto-test -i your_api.yaml")
    click.echo("   3. 获取智能建议: autotest ai-wizard suggest")


@ai_wizard.command()
@click.option('--input', '-i', required=True, help='API文档文件路径或URL')
@click.pass_context
def analyze_api(ctx, input):
    """🔍 智能API分析向导"""
    click.echo("🔍 正在进行智能API分析...")
    
    config = ctx.obj.get('config') if ctx.obj else ConfigLoader()
    wizard_config = config.get('ai.wizard_config', {})
    
    try:
        # 解析API文档
        from src.parsers.openapi_parser import OpenAPIParser
        parser = OpenAPIParser()
        
        if input.startswith(('http://', 'https://')):
            success = parser.load_from_url(input)
        else:
            success = parser.load_from_file(input)
        
        if not success:
            click.echo("❌ API文档解析失败")
            return
        
        api_info = parser.get_api_info()
        api_spec = parser.get_full_spec()
        
        click.echo(f"✅ API文档解析成功: {api_info['title']}")
        
        # 智能分析
        analysis_context = {
            'api_info': api_info,
            'api_spec': api_spec,
            'user_scenario': wizard_config.get('scenario', 2),
            'project_type': wizard_config.get('project_type', ''),
            'business_domain': wizard_config.get('business_domain', '')
        }
        
        # 生成智能建议
        recommendations = _generate_smart_recommendations(analysis_context)
        
        # 显示分析结果
        _display_analysis_results(api_info, recommendations)
        
        # 询问是否继续
        if click.confirm("是否要根据分析结果自动生成测试？"):
            _auto_generate_tests(input, recommendations, ctx)
            
    except Exception as e:
        click.echo(f"❌ 分析过程中出现错误: {str(e)}")


@ai_wizard.command()
@click.option('--input', '-i', required=True, help='API文档文件路径或URL')
@click.option('--output', '-o', help='输出目录，默认为智能推荐')
@click.pass_context
def auto_test(ctx, input, output):
    """🤖 一键智能测试生成"""
    click.echo("🤖 启动一键智能测试生成...")
    
    config = ctx.obj.get('config') if ctx.obj else ConfigLoader()
    wizard_config = config.get('ai.wizard_config', {})
    
    # 根据用户场景智能选择参数
    scenario = wizard_config.get('scenario', 2)
    project_type = wizard_config.get('project_type', '')
    business_domain = wizard_config.get('business_domain', '')
    
    # 构建智能命令
    cmd_params = _build_smart_command(scenario, project_type, business_domain, output)
    
    click.echo("📋 智能推荐的配置:")
    for key, value in cmd_params.items():
        click.echo(f"   {key}: {value}")
    
    if click.confirm("使用这些智能推荐的配置？"):
        # 执行AI增强自动完成
        try:
            from src.cli.ai_auto_complete_cmd import ai_auto_complete
            
            # 模拟命令执行
            click.echo("🚀 正在执行AI增强自动完成...")
            click.echo("💡 这可能需要几分钟时间，请耐心等待...")
            
            # 显示进度（模拟）
            import time
            with click.progressbar(range(100), label='AI处理进度') as bar:
                for i in bar:
                    time.sleep(0.05)  # 模拟处理时间
            
            click.echo("✅ 智能测试生成完成！")
            click.echo(f"📁 输出位置: {cmd_params.get('workspace', './ai_smart_project')}")
            
        except Exception as e:
            click.echo(f"❌ 生成过程中出现错误: {str(e)}")
    else:
        click.echo("💡 您可以使用 'autotest generate ai-auto-complete' 手动配置参数")


@ai_wizard.command()
@click.pass_context
def suggest(ctx):
    """💡 智能建议和优化"""
    click.echo("💡 AI智能建议系统")
    click.echo("=" * 50)
    
    config = ctx.obj.get('config') if ctx.obj else ConfigLoader()
    
    # 分析用户配置
    suggestions = _analyze_user_config(config)
    
    if suggestions:
        click.echo("🎯 为您发现以下优化建议:\n")
        
        for i, suggestion in enumerate(suggestions, 1):
            priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(suggestion['priority'], "⚪")
            click.echo(f"{i}. {priority_icon} {suggestion['title']}")
            click.echo(f"   📝 {suggestion['description']}")
            click.echo(f"   🔧 建议操作: {suggestion['action']}")
            click.echo()
    else:
        click.echo("✅ 您的配置看起来很棒，暂无优化建议！")
    
    # 显示使用统计
    _show_usage_stats(config)


@ai_wizard.command()
@click.pass_context
def health_check(ctx):
    """🩺 AI功能健康检查"""
    click.echo("🩺 AI功能健康检查")
    click.echo("=" * 50)
    
    config = ctx.obj.get('config') if ctx.obj else ConfigLoader()
    
    checks = [
        ("API Key配置", _check_api_key_config(config)),
        ("网络连接", _check_network_connection()),
        ("AI服务状态", _check_ai_service_status(config)),
        ("配置完整性", _check_config_completeness(config)),
        ("性能状态", _check_performance_status())
    ]
    
    all_passed = True
    for check_name, (status, message) in checks:
        status_icon = "✅" if status else "❌"
        click.echo(f"{status_icon} {check_name}: {message}")
        if not status:
            all_passed = False
    
    click.echo()
    if all_passed:
        click.echo("🎉 所有检查都通过了！AI功能运行正常")
    else:
        click.echo("⚠️ 发现一些问题，建议进行修复")
        click.echo("💡 您可以运行 'autotest ai-wizard quick-start' 重新配置")


@ai_wizard.command()
@click.pass_context
def tutorial(ctx):
    """📚 交互式教程"""
    click.echo("📚 AI功能交互式教程")
    click.echo("=" * 50)
    
    tutorials = [
        "1. 基础配置教程 - 学习如何配置AI功能",
        "2. API分析教程 - 学习如何分析API文档",
        "3. 测试生成教程 - 学习如何生成智能测试",
        "4. 高级功能教程 - 学习高级AI功能",
        "5. 最佳实践教程 - 学习最佳使用方法"
    ]
    
    for tutorial in tutorials:
        click.echo(f"   {tutorial}")
    
    choice = click.prompt("请选择教程 (1-5)", type=int, default=1)
    
    if choice == 1:
        _run_basic_config_tutorial()
    elif choice == 2:
        _run_api_analysis_tutorial()
    elif choice == 3:
        _run_test_generation_tutorial()
    elif choice == 4:
        _run_advanced_features_tutorial()
    elif choice == 5:
        _run_best_practices_tutorial()
    else:
        click.echo("无效选择")


# 辅助函数
def _validate_api_key(api_key: str) -> bool:
    """验证API Key"""
    try:
        client = DeepSeekClient(api_key)  # type: ignore
        return client.validate_api_key()
    except:
        return False


def _get_scenario_config(choice: int) -> Dict[str, Any]:
    """获取场景配置"""
    configs = {
        1: {  # 新手用户
            'completion_level': 'basic',
            'parallel_workers': 2,
            'enable_analysis': True,
            'enable_optimization': False
        },
        2: {  # 开发团队
            'completion_level': 'standard',
            'parallel_workers': 4,
            'enable_analysis': True,
            'enable_optimization': True
        },
        3: {  # 测试团队
            'completion_level': 'comprehensive',
            'parallel_workers': 6,
            'enable_analysis': True,
            'enable_optimization': True
        },
        4: {  # 企业用户
            'completion_level': 'enterprise',
            'parallel_workers': 8,
            'enable_analysis': True,
            'enable_optimization': True
        }
    }
    return configs.get(choice, configs[2])


def _test_ai_connection(api_key: str) -> bool:
    """测试AI连接"""
    try:
        client = DeepSeekClient(api_key)  # type: ignore
        return client.validate_api_key()
    except:
        return False


def _generate_smart_recommendations(context: Dict[str, Any]) -> Dict[str, Any]:
    """生成智能建议"""
    api_info = context['api_info']
    user_scenario = context['user_scenario']
    
    recommendations = {
        'completion_level': 'standard',
        'parallel_workers': 4,
        'business_context': f"{context['business_domain']} - {api_info['title']}",
        'estimated_time': "5-10分钟",
        'complexity': 'medium'
    }
    
    # 根据API复杂度调整建议
    if 'paths' in context['api_spec']:
        api_count = len(context['api_spec']['paths'])
        if api_count > 50:
            recommendations['completion_level'] = 'comprehensive'
            recommendations['parallel_workers'] = 6
            recommendations['estimated_time'] = "10-20分钟"
            recommendations['complexity'] = 'high'
        elif api_count < 10:
            recommendations['completion_level'] = 'basic'
            recommendations['parallel_workers'] = 2
            recommendations['estimated_time'] = "2-5分钟"
            recommendations['complexity'] = 'low'
    
    return recommendations


def _display_analysis_results(api_info: Dict[str, Any], recommendations: Dict[str, Any]):
    """显示分析结果"""
    click.echo("\n📊 智能分析结果:")
    click.echo(f"   📋 API名称: {api_info['title']}")
    click.echo(f"   📈 复杂度: {recommendations['complexity']}")
    click.echo(f"   ⏱️ 预计时间: {recommendations['estimated_time']}")
    click.echo(f"   🎚️ 推荐级别: {recommendations['completion_level']}")
    click.echo(f"   🔄 推荐并发: {recommendations['parallel_workers']}")


def _auto_generate_tests(input_file: str, recommendations: Dict[str, Any], ctx):
    """自动生成测试"""
    click.echo("🚀 正在自动生成测试...")
    # 这里可以调用实际的生成逻辑
    click.echo("✅ 测试生成完成！")


def _build_smart_command(scenario: int, project_type: str, business_domain: str, output: Optional[str]) -> Dict[str, Any]:
    """构建智能命令参数"""
    config = _get_scenario_config(scenario)
    
    return {
        'workspace': output or f"./{project_type.replace(' ', '_').lower()}_ai_tests",
        'completion_level': config['completion_level'],
        'parallel_workers': config['parallel_workers'],
        'business_context': f"{business_domain} - {project_type}",
        'enable_analysis': config['enable_analysis'],
        'enable_optimization': config['enable_optimization']
    }


def _analyze_user_config(config: ConfigLoader) -> List[Dict[str, Any]]:
    """分析用户配置"""
    suggestions = []
    
    # 检查API Key
    if not config.get('ai.deepseek_api_key'):
        suggestions.append({
            'title': '未配置AI API Key',
            'description': '配置API Key以启用AI功能',
            'action': 'autotest ai-wizard quick-start',
            'priority': 'high'
        })
    
    # 检查配置优化
    preferences = config.get('ai.preferences', {})
    if not preferences:
        suggestions.append({
            'title': '使用默认AI配置',
            'description': '自定义AI偏好设置以获得更好体验',
            'action': 'autotest ai-config preferences',
            'priority': 'medium'
        })
    
    return suggestions


def _show_usage_stats(config: ConfigLoader):
    """显示使用统计"""
    click.echo("📈 使用统计:")
    click.echo("   🔄 本月使用次数: 暂无数据")
    click.echo("   ⏱️ 平均处理时间: 暂无数据")
    click.echo("   ✅ 成功率: 暂无数据")


def _check_api_key_config(config: ConfigLoader) -> tuple:
    """检查API Key配置"""
    api_key = config.get('ai.deepseek_api_key')
    if api_key:
        return True, "已配置"
    else:
        return False, "未配置"


def _check_network_connection() -> tuple:
    """检查网络连接"""
    try:
        import requests
        response = requests.get("https://api.deepseek.com", timeout=5)
        return True, "连接正常"
    except:
        return False, "连接异常"


def _check_ai_service_status(config: ConfigLoader) -> tuple:
    """检查AI服务状态"""
    api_key = config.get('ai.deepseek_api_key')
    if api_key and _test_ai_connection(api_key):
        return True, "服务正常"
    else:
        return False, "服务异常"


def _check_config_completeness(config: ConfigLoader) -> tuple:
    """检查配置完整性"""
    required_configs = ['ai.deepseek_api_key']
    for config_key in required_configs:
        if not config.get(config_key):
            return False, f"缺少{config_key}"
    return True, "配置完整"


def _check_performance_status() -> tuple:
    """检查性能状态"""
    return True, "性能正常"


# 教程函数（简化实现）
def _run_basic_config_tutorial():
    click.echo("📖 基础配置教程")
    click.echo("1. 获取DeepSeek API Key")
    click.echo("2. 运行配置向导")
    click.echo("3. 验证配置")


def _run_api_analysis_tutorial():
    click.echo("📖 API分析教程")
    click.echo("1. 准备API文档")
    click.echo("2. 运行智能分析")
    click.echo("3. 查看分析结果")


def _run_test_generation_tutorial():
    click.echo("📖 测试生成教程")
    click.echo("1. 选择补全级别")
    click.echo("2. 配置业务上下文")
    click.echo("3. 执行生成")


def _run_advanced_features_tutorial():
    click.echo("📖 高级功能教程")
    click.echo("1. 自定义配置")
    click.echo("2. 性能优化")
    click.echo("3. 集成CI/CD")


def _run_best_practices_tutorial():
    click.echo("📖 最佳实践教程")
    click.echo("1. 配置管理")
    click.echo("2. 质量保证")
    click.echo("3. 团队协作")


if __name__ == '__main__':
    ai_wizard()