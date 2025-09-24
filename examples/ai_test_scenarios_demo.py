#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI驱动的测试场景生成示例

演示如何使用AI生成全面的测试场景，包括各种错误、空值、服务失效等
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ai import DeepSeekClient, AITestGenerator
from src.parsers.openapi_parser import OpenAPIParser


class AITestScenarioDemo:
    """AI测试场景生成演示"""
    
    def __init__(self, api_key: str):
        """初始化演示"""
        self.client = DeepSeekClient(api_key)
        self.generator = AITestGenerator(self.client)
        
    def demo_comprehensive_scenarios(self, api_spec_file: str, endpoint: str, method: str):
        """演示全面测试场景生成"""
        print("🤖 AI驱动的全面测试场景生成演示")
        print("=" * 60)
        
        # 解析API文档
        parser = OpenAPIParser()
        if not parser.load_from_file(api_spec_file):
            print("❌ API文档解析失败")
            return
            
        api_spec = parser.get_full_spec()
        api_info = parser.get_api_info()
        
        print(f"📋 API信息: {api_info['title']} v{api_info['version']}")
        print(f"🎯 目标接口: {method} {endpoint}")
        
        # 生成全面测试场景
        print("\n🔄 正在生成全面测试场景...")
        result = self.generator.generate_comprehensive_test_scenarios(
            api_spec=api_spec,
            endpoint_path=endpoint,
            method=method,
            business_context="用户管理系统API"
        )
        
        if 'error' in result:
            print(f"❌ 生成失败: {result['error']}")
            return
            
        print("✅ 测试场景生成成功！")
        
        # 显示结果统计
        summary = result.get('summary', {})
        print(f"\n📊 生成统计:")
        print(f"  总场景数: {summary.get('total_scenarios', 0)}")
        print(f"  生成用例数: {summary.get('generated_cases', 0)}")
        
        # 显示各类场景
        print("\n📋 场景详情:")
        scenarios = result.get('test_scenarios', {})
        
        for scenario_type, scenario_data in scenarios.items():
            count = scenario_data.get('count', 0)
            priority = scenario_data.get('priority', 'Medium')
            category = scenario_data.get('category', 'Other')
            description = scenario_data.get('description', scenario_type)
            
            status = "✅" if count > 0 else "❌"
            print(f"  {status} {description}")
            print(f"      用例数: {count}, 优先级: {priority}, 分类: {category}")
            
            # 显示部分测试用例示例
            if count > 0 and 'test_cases' in scenario_data:
                test_cases = scenario_data['test_cases']
                if isinstance(test_cases, list) and len(test_cases) > 0:
                    case = test_cases[0]  # 显示第一个用例
                    if isinstance(case, dict) and 'name' in case:
                        print(f"      示例: {case.get('name', 'N/A')}")
        
        return result
    
    def demo_traditional_test_enhancement(self, test_file_path: str, api_spec_file: str):
        """演示传统测试增强"""
        print("\n🚀 传统测试AI增强演示")
        print("=" * 60)
        
        # 检查文件是否存在
        if not Path(test_file_path).exists():
            print(f"❌ 测试文件不存在: {test_file_path}")
            return
            
        if not Path(api_spec_file).exists():
            print(f"❌ API规范文件不存在: {api_spec_file}")
            return
        
        # 解析API规范
        parser = OpenAPIParser()
        if not parser.load_from_file(api_spec_file):
            print("❌ API规范解析失败")
            return
            
        api_spec = parser.get_full_spec()
        
        print(f"📁 原始测试文件: {test_file_path}")
        print("⚡ 正在分析和增强测试...")
        
        # 使用AI增强传统测试
        result = self.generator.enhance_traditional_tests(
            existing_test_file_path=test_file_path,
            api_spec=api_spec,
            enhancement_options={
                "add_edge_cases": True,
                "add_error_handling": True,
                "add_security_tests": True,
                "improve_assertions": True,
                "optimize_test_data": True
            }
        )
        
        if not result.get('success'):
            print(f"❌ 增强失败: {result.get('error', '未知错误')}")
            return
            
        print("✅ 测试增强成功！")
        
        # 显示增强统计
        print(f"\n📊 增强统计:")
        print(f"  改进项数量: {result.get('improvements_count', 0)}")
        print(f"  原始文件: {result.get('file_path', 'N/A')}")
        
        # 显示启用的增强选项
        print(f"\n⚙️ 启用的增强选项:")
        options = result.get('enhancement_options', {})
        for option, enabled in options.items():
            status = "✅" if enabled else "❌"
            print(f"  {status} {option}")
        
        return result


def main():
    """主演示函数"""
    print("🎯 AI驱动的接口测试场景生成演示")
    print("=" * 60)
    
    # 注意：这里需要实际的API密钥
    api_key = "your_deepseek_api_key_here"
    
    if api_key == "your_deepseek_api_key_here":
        print("⚠️ 请设置真实的DeepSeek API密钥")
        print("💡 使用方法:")
        print("   export DEEPSEEK_API_KEY=your_actual_key")
        print("   或者修改代码中的api_key变量")
        return
    
    try:
        # 创建演示实例
        demo = AITestScenarioDemo(api_key)
        
        # 演示1：全面测试场景生成
        print("\n🎬 演示1：全面测试场景生成")
        print("-" * 40)
        
        # 这里需要实际的API文档文件
        api_spec_file = "examples/petstore.json"  # 示例API文档
        endpoint = "/api/users/{id}"
        method = "GET"
        
        if Path(api_spec_file).exists():
            scenario_result = demo.demo_comprehensive_scenarios(
                api_spec_file=api_spec_file,
                endpoint=endpoint,
                method=method
            )
            
            if scenario_result:
                print(f"🎉 全面测试场景生成完成！")
        else:
            print(f"⚠️ 示例API文档不存在: {api_spec_file}")
            print("💡 请提供实际的OpenAPI 3.0规范文件")
        
        # 演示2：传统测试增强
        print("\n🎬 演示2：传统测试增强")
        print("-" * 40)
        
        test_file = "tests/test_example.py"  # 示例测试文件
        
        if Path(test_file).exists() and Path(api_spec_file).exists():
            enhancement_result = demo.demo_traditional_test_enhancement(
                test_file_path=test_file,
                api_spec_file=api_spec_file
            )
            
            if enhancement_result:
                print(f"🎉 传统测试增强完成！")
        else:
            print(f"⚠️ 示例文件不存在")
            print("💡 请提供实际的测试文件和API规范文件")
        
        print("\n🎯 功能特色:")
        print("✨ 智能场景生成 - 自动生成20+种测试场景")
        print("🛡️ 安全测试覆盖 - 包含SQL注入、XSS等安全测试")
        print("🔍 边界值测试 - 自动识别参数边界情况")
        print("❌ 错误处理测试 - 全面覆盖异常场景")
        print("📊 数据验证测试 - 智能生成验证用例")
        print("⚡ 性能压力测试 - 并发和负载测试场景")
        print("🔄 服务可靠性测试 - 服务失效、超时等场景")
        
        print("\n💡 使用建议:")
        print("1. 开发阶段使用AI生成全面测试场景")
        print("2. 对现有测试使用AI增强功能")
        print("3. 结合业务上下文提供更准确的测试")
        print("4. 根据优先级和分类执行测试")
        
    except Exception as e:
        print(f"❌ 演示执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()