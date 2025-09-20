"""
AI补全配置和管理界面

提供用户友好的AI功能配置和管理工具
"""

import click
import sys
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config_loader import ConfigLoader

try:
    from src.ai import DeepSeekClient
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    from typing import Any
    DeepSeekClient = Any


@click.group()
@click.pass_context
def ai_config(ctx):
    """🤖 AI补全配置管理"""
    if not AI_AVAILABLE:
        click.echo("❌ AI功能不可用，请安装相关依赖", err=True)
        sys.exit(1)


@ai_config.command()
@click.option('--api-key', prompt='请输入DeepSeek API Key', hide_input=True, help='DeepSeek API Key')
@click.option('--base-url', default='https://api.deepseek.com/v1', help='API基础URL')
@click.option('--test-connection', is_flag=True, default=True, help='测试连接')
@click.pass_context
def setup(ctx, api_key, base_url, test_connection):
    """设置AI配置"""
    click.echo("🤖 设置AI配置")
    
    config = ctx.obj.get('config') if ctx.obj else ConfigLoader()
    
    # 验证API Key
    if test_connection:
        click.echo("🔍 验证API Key...")
        try:
            client = DeepSeekClient(api_key, base_url)  # type: ignore
            if client.validate_api_key():
                click.echo("✅ API Key验证成功")
            else:
                click.echo("❌ API Key验证失败", err=True)
                return
        except Exception as e:
            click.echo(f"❌ 连接测试失败: {e}", err=True)
            return
    
    # 保存配置
    config.set('ai.deepseek_api_key', api_key)
    config.set('ai.base_url', base_url)
    config.set('ai.setup_time', datetime.now().isoformat())
    
    click.echo("💾 配置已保存")
    click.echo(f"🔗 API URL: {base_url}")
    click.echo("✅ AI功能已启用")


@ai_config.command()
@click.pass_context
def status(ctx):
    """查看AI配置状态"""
    click.echo("📊 AI配置状态")
    click.echo("=" * 50)
    
    config = ctx.obj.get('config') if ctx.obj else ConfigLoader()
    
    # 检查API Key
    api_key = config.get('ai.deepseek_api_key')
    if api_key:
        masked_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "****"
        click.echo(f"🔑 API Key: {masked_key}")
        
        # 测试连接
        try:
            client = DeepSeekClient(api_key)  # type: ignore
            if client.validate_api_key():
                click.echo("🟢 连接状态: 正常")
                
                # 获取模型信息
                model_info = client.get_model_info()
                click.echo(f"🤖 默认模型: {model_info.get('default_model', 'Unknown')}")
                click.echo(f"🔗 API URL: {model_info.get('base_url', 'Unknown')}")
            else:
                click.echo("🔴 连接状态: 失败")
        except Exception as e:
            click.echo(f"🔴 连接状态: 异常 - {e}")
    else:
        click.echo("❌ 未配置API Key")
        click.echo("💡 使用 'autotest ai-config setup' 进行配置")
    
    # 显示功能状态
    click.echo("\n🛠️ 功能状态:")
    features = {
        'ai_test_generator': '测试用例生成（整合数据生成）',
        'ai_test_reporter': '测试报告生成器',
        'ai_completion_manager': '接口补全管理',
        'ai_decision_center': 'AI决策中心（整合分析）'
    }
    
    for feature, description in features.items():
        status_icon = "✅" if AI_AVAILABLE else "❌"
        click.echo(f"  {status_icon} {description}")


@ai_config.command()
@click.option('--completion-level', 
              type=click.Choice(['basic', 'standard', 'comprehensive', 'enterprise']), 
              default='standard', 
              help='默认补全级别')
@click.option('--parallel-workers', type=int, default=4, help='默认并发数量')
@click.option('--enable-analysis', is_flag=True, default=True, help='默认启用分析')
@click.option('--enable-optimization', is_flag=True, default=True, help='默认启用优化')
@click.option('--timeout', type=int, default=300, help='请求超时时间（秒）')
@click.pass_context
def preferences(ctx, completion_level, parallel_workers, enable_analysis, enable_optimization, timeout):
    """设置AI补全偏好"""
    click.echo("⚙️ 设置AI补全偏好")
    
    config = ctx.obj.get('config') if ctx.obj else ConfigLoader()
    
    preferences_config = {
        'completion_level': completion_level,
        'parallel_workers': parallel_workers,
        'enable_analysis': enable_analysis,
        'enable_optimization': enable_optimization,
        'timeout': timeout
    }
    
    config.set('ai.preferences', preferences_config)
    
    click.echo("✅ 偏好设置已保存")
    click.echo(f"🎚️ 补全级别: {completion_level}")
    click.echo(f"🔄 并发数量: {parallel_workers}")
    click.echo(f"🧠 智能分析: {'启用' if enable_analysis else '禁用'}")
    click.echo(f"🚀 自动优化: {'启用' if enable_optimization else '禁用'}")
    click.echo(f"⏱️ 超时时间: {timeout}秒")


@ai_config.command()
@click.option('--output', '-o', type=click.Path(), help='导出配置文件路径')
@click.option('--format', type=click.Choice(['yaml', 'json']), default='yaml', help='导出格式')
@click.pass_context
def export(ctx, output, format):
    """导出AI配置"""
    click.echo("📤 导出AI配置")
    
    config = ctx.obj.get('config') if ctx.obj else ConfigLoader()
    
    ai_config = {
        'ai': {
            'deepseek_api_key': config.get('ai.deepseek_api_key', ''),
            'base_url': config.get('ai.base_url', 'https://api.deepseek.com/v1'),
            'preferences': config.get('ai.preferences', {}),
            'setup_time': config.get('ai.setup_time', ''),
            'export_time': datetime.now().isoformat()
        }
    }
    
    # 隐藏敏感信息
    if ai_config['ai']['deepseek_api_key']:
        ai_config['ai']['deepseek_api_key'] = '[HIDDEN]'
    
    if not output:
        output = f"ai_config.{format}"
    
    output_path = Path(output)
    
    if format == 'json':
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(ai_config, f, ensure_ascii=False, indent=2)
    else:
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(ai_config, f, default_flow_style=False, allow_unicode=True)
    
    click.echo(f"✅ 配置已导出到: {output_path}")


@ai_config.command()
@click.option('--input', '-i', type=click.Path(exists=True), required=True, help='配置文件路径')
@click.option('--merge', is_flag=True, help='合并到现有配置')
@click.pass_context
def import_config(ctx, input, merge):
    """导入AI配置"""
    click.echo(f"📥 导入AI配置: {input}")
    
    config = ctx.obj.get('config') if ctx.obj else ConfigLoader()
    
    input_path = Path(input)
    
    try:
        if input_path.suffix.lower() == '.json':
            with open(input_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
        else:
            with open(input_path, 'r', encoding='utf-8') as f:
                imported_config = yaml.safe_load(f)
        
        ai_config = imported_config.get('ai', {})
        
        if not merge:
            # 完全替换
            for key, value in ai_config.items():
                if key != 'deepseek_api_key' or value != '[HIDDEN]':
                    config.set(f'ai.{key}', value)
        else:
            # 合并配置
            for key, value in ai_config.items():
                if key != 'deepseek_api_key' or value != '[HIDDEN]':
                    existing_value = config.get(f'ai.{key}')
                    if existing_value is None:
                        config.set(f'ai.{key}', value)
        
        click.echo("✅ 配置导入成功")
        
    except Exception as e:
        click.echo(f"❌ 配置导入失败: {e}", err=True)


@ai_config.command()
@click.confirmation_option(prompt='确定要重置所有AI配置吗？')
@click.pass_context
def reset(ctx):
    """重置AI配置"""
    click.echo("🔄 重置AI配置")
    
    config = ctx.obj.get('config') if ctx.obj else ConfigLoader()
    
    # 删除所有AI相关配置
    ai_keys = [
        'ai.deepseek_api_key',
        'ai.base_url',
        'ai.preferences',
        'ai.setup_time'
    ]
    
    for key in ai_keys:
        try:
            # 使用set方法设置为None来删除
            keys = key.split('.')
            if len(keys) == 2:
                ai_config = config.get('ai', {})
                if isinstance(ai_config, dict) and keys[1] in ai_config:
                    del ai_config[keys[1]]
                    config.set('ai', ai_config)
        except Exception:
            pass
    
    click.echo("✅ AI配置已重置")
    click.echo("💡 使用 'autotest ai-config setup' 重新配置")


@ai_config.command()
@click.pass_context
def validate(ctx):
    """验证AI配置"""
    click.echo("🔍 验证AI配置")
    
    config = ctx.obj.get('config') if ctx.obj else ConfigLoader()
    
    # 检查必要配置
    api_key = config.get('ai.deepseek_api_key')
    if not api_key:
        click.echo("❌ 缺少API Key")
        return
    
    base_url = config.get('ai.base_url', 'https://api.deepseek.com/v1')
    
    try:
        client = DeepSeekClient(api_key, base_url)  # type: ignore
        
        # 测试基本连接
        if client.validate_api_key():
            click.echo("✅ API Key有效")
        else:
            click.echo("❌ API Key无效")
            return
        
        # 测试模型信息获取
        model_info = client.get_model_info()
        click.echo(f"✅ 模型信息获取成功: {model_info.get('default_model')}")
        
        # 测试简单请求
        test_response = client.chat_completion([
            {"role": "user", "content": "Hello"}
        ], max_tokens=10)
        
        if test_response.success:
            click.echo("✅ AI服务响应正常")
            click.echo(f"📊 使用统计: {test_response.usage}")
        else:
            click.echo(f"❌ AI服务响应异常: {test_response.error}")
        
    except Exception as e:
        click.echo(f"❌ 验证失败: {e}")


@ai_config.command()
@click.pass_context
def usage(ctx):
    """显示AI功能使用指南"""
    click.echo("📚 AI功能使用指南")
    click.echo("=" * 60)
    
    click.echo("\n🎯 主要功能:")
    
    features = [
        {
            "name": "AI增强自动完成",
            "command": "autotest generate ai-auto-complete -i api.yaml",
            "description": "智能分析所有接口并生成完整测试系统"
        },
        {
            "name": "AI测试生成",
            "command": "autotest ai generate-tests -i api.yaml -o tests/",
            "description": "生成智能测试用例"
        },
        {
            "name": "AI代码审查",
            "command": "autotest ai review-code -f test.py -o review.md",
            "description": "AI代码质量分析"
        },
        {
            "name": "AI数据生成",
            "command": "autotest ai generate-data -s schema.json -o data.json",
            "description": "生成智能测试数据"
        }
    ]
    
    for feature in features:
        click.echo(f"\n🔹 {feature['name']}")
        click.echo(f"   命令: {feature['command']}")
        click.echo(f"   描述: {feature['description']}")
    
    click.echo("\n⚙️ 配置管理:")
    config_commands = [
        "autotest ai-config setup      # 设置API Key",
        "autotest ai-config status     # 查看配置状态",
        "autotest ai-config preferences # 设置偏好",
        "autotest ai-config validate   # 验证配置"
    ]
    
    for cmd in config_commands:
        click.echo(f"   {cmd}")
    
    click.echo("\n💡 最佳实践:")
    practices = [
        "首次使用前先运行 'setup' 配置API Key",
        "定期使用 'validate' 检查配置状态",
        "根据项目需要调整 'preferences' 设置",
        "使用业务上下文描述提高AI生成质量"
    ]
    
    for practice in practices:
        click.echo(f"   • {practice}")
    
    click.echo("\n🔗 相关链接:")
    click.echo("   • DeepSeek API文档: https://api-docs.deepseek.com/zh-cn/")
    click.echo("   • 获取API Key: https://platform.deepseek.com/")


if __name__ == '__main__':
    ai_config()