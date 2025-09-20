"""
命令行接口模块

提供完整的命令行界面，支持框架的所有核心功能：
- 测试脚本生成和执行
- Mock服务器管理
- 测试报告生成
- 配置管理
- AI功能集成

主要命令组：
- generate: 生成测试脚本和用例文档
- run: 执行测试和测试管理
- mock: Mock服务器相关操作
- export: 测试用例和报告导出
- config: 配置管理
- ai: AI功能集成（需要DeepSeek API密钥）

核心特性：
- 基于Click框架的现代CLI设计
- 多环境配置支持
- 交互式和批处理模式
- 详细的帮助文档和错误提示
- 彩色输出和进度条
- 调试模式支持

使用示例:
    # 从OpenAPI文档生成测试
    python -m src.cli.main generate tests -i api-spec.yaml -o ./tests
    
    # 启动Mock服务器
    python -m src.cli.main mock start --port 5000
    
    # 执行测试
    python -m src.cli.main run tests --parallel 4
    
    # 导出测试用例
    python -m src.cli.main export test-cases -o cases.xlsx --format excel
    
    # AI生成测试
    python -m src.cli.main ai generate-tests -i api-spec.yaml
"""

from .main import cli

__all__ = ['cli']