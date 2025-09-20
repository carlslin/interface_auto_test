"""AI智能化模块 - 四层智能化体系架构

集成DeepSeek AI，构建完整的四层智能化体系，让AI成为框架的智能大脑。
经过架构优化，精简为6个核心模块，功能更集中，性能更高效。

🏗️ 四层智能化架构（优化版）：
- L1: 基础AI功能 - 核心AI能力（AI客户端、测试生成、报告生成）
- L2: 智能分析 - 统一补全管理和协调
- L3: 智能决策 - 自适应推荐和智能决策中心
- L4: 智能交互 - 零门槛的自然语言交互

🧠 AI智能化组件（优化后）：
- DeepSeekClient: DeepSeek AI API客户端，提供基础AI交互能力
- AITestGenerator: 综合测试生成器，整合测试用例、数据生成、API分析功能
- AITestReporter: AI增强测试报告生成器，智能分析和洞察
- AICompletionManager: AI补全管理器，统一协调所有AI补全任务
- AIDecisionCenter: AI决策中心，框架的智能大脑和决策支持
- AIChatAssistant: AI聊天助手，自然语言交互界面

🤖 智能化使用示例：
    # L4智能交互 - 自然语言使用
    from src.ai import AIChatAssistant
    assistant = AIChatAssistant()
    response = await assistant.chat("帮我分析这个API文档")
    
    # L3智能决策 - AI决策支持
    from src.ai import AIDecisionCenter
    decision_center = AIDecisionCenter()
    decision = await decision_center.make_intelligent_decision(context)
    
    # L2智能分析 - 统一补全管理
    from src.ai import AICompletionManager
    manager = AICompletionManager(client)
    result = manager.complete_all_interfaces(api_spec, workspace_path)
    
    # L1基础功能 - 综合测试生成
    from src.ai import AITestGenerator
    generator = AITestGenerator(client)
    tests = generator.generate_comprehensive_tests(api_spec)
    data = generator.generate_realistic_test_data(schema)
    analysis = generator.simple_api_analysis(api_spec)

✨ AI智能化特性（优化后）：
- 🎯 智能推荐：基于历史案例和上下文智能推荐最佳配置
- 🔄 自适应学习：从使用模式中持续学习和改进
- 💬 自然交互：支持自然语言操作，零门槛使用
- 🧠 智能决策：为框架的所有操作提供AI决策支持
- 📊 深度分析：整合的API分析和模式识别
- 🔧 自动优化：执行过程中实时监控和动态调整
- ⚡ 高效精简：从9个模块优化到6个，功能整合，性能提升

🔄 架构优化亮点：
- 功能整合：测试生成器整合数据生成和API分析功能
- 依赖简化：减少模块间复杂依赖关系
- 性能提升：减少33%模块数量，提高加载速度
- 维护性增强：统一功能入口，减少代码重复

版本: 2.1.0 - 架构优化版
作者: Interface AutoTest Framework Team
"""

try:
    # L1: 基础AI功能
    from .deepseek_client import DeepSeekClient
    from .ai_test_generator import AITestGenerator
    from .ai_test_reporter import AITestReporter
    
    # L2: 智能分析
    from .ai_completion_manager import AICompletionManager
    
    # L3: 智能决策
    from .ai_decision_center import AIDecisionCenter
    
    # L4: 智能交互
    from .ai_chat_assistant import AIChatAssistant
    
    __all__ = [
        # L1: 基础AI功能
        'DeepSeekClient',
        'AITestGenerator', 
        'AITestReporter',
        # L2: 智能分析
        'AICompletionManager',
        # L3: 智能决策
        'AIDecisionCenter',
        # L4: 智能交互
        'AIChatAssistant'
    ]
except ImportError as e:
    # AI智能化模块导入失败时的友好处理
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"AI智能化模块部分功能不可用: {e}")
    logger.info("请确保已安装必要依赖: pip3 install pyyaml jsonschema faker --break-system-packages")
    
    # 提供基础的占位符类，避免导入错误
    # 当AI依赖不可用时，提供友好的错误提示
    class AIPlaceholder:
        """AI功能占位符类
        
        当AI相关依赖不可用时使用此类替代，提供清晰的错误信息
        避免导入错误导致整个框架无法使用
        """
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "AI功能不可用，请安装相关依赖。\n"
                "安装命令: pip3 install pyyaml jsonschema faker requests --break-system-packages"
            )
    
    # 为所有AI组件提供占位符
    DeepSeekClient = AIPlaceholder
    AITestGenerator = AIPlaceholder
    AITestReporter = AIPlaceholder
    AICompletionManager = AIPlaceholder
    AIDecisionCenter = AIPlaceholder
    AIChatAssistant = AIPlaceholder
    
    __all__ = [
        'DeepSeekClient', 'AITestGenerator', 'AITestReporter',
        'AICompletionManager', 'AIDecisionCenter', 'AIChatAssistant'
    ]