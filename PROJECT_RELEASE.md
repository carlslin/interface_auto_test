# 接口自动化测试框架

一个功能完整的接口自动化测试框架，集成了AI智能功能，支持多种格式的测试用例导出。

## 🚀 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 基础使用
```bash
# 查看帮助
python3 -m src.cli.main --help

# 从API文档生成测试脚本
python3 -m src.cli.main generate tests -i api.yaml -o tests/

# 运行测试
python3 -m src.cli.main test run -p tests/
```

### AI功能配置
```bash
# 设置DeepSeek API Key（需要自己申请）
python3 -m src.cli.main ai setup --api-key sk-your-deepseek-api-key

# 使用AI生成测试用例
python3 -m src.cli.main ai generate-tests -i api.yaml -o ai_tests/
```

## 📦 主要功能

- 🤖 **AI智能测试生成** - 集成DeepSeek AI，智能分析API文档生成高质量测试用例
- 📊 **多格式导出** - 支持Excel、Markdown、JSON、CSV、XML等格式的测试用例导出
- 🎯 **自动化测试脚本生成** - 基于OpenAPI/Swagger文档自动生成可执行的测试代码
- 🔧 **Mock服务器** - 内置Flask Mock服务器，支持动态数据生成
- 📈 **多格式测试报告** - HTML、JSON、XML等多种格式的测试报告
- 🌐 **多环境配置** - 支持开发、测试、生产等多环境配置管理

## 📚 详细文档

- [用户使用指南](docs/user_guide.md) - 完整的功能介绍和使用说明
- [AI集成指南](docs/ai_integration_guide.md) - AI功能的详细配置和使用
- [测试用例导出指南](docs/test_case_export_guide.md) - 各种格式的导出功能说明
- [API参考文档](docs/api_reference.md) - 详细的API接口说明
- [配置说明](docs/configuration.md) - 配置文件的详细说明

## 🛠️ 技术栈

- **Python 3.8+** - 主要编程语言
- **Click** - 命令行界面框架
- **Flask** - Mock服务器
- **SQLite** - 数据存储
- **DeepSeek AI** - AI智能功能
- **OpenAPI/Swagger** - API文档解析

## 📂 项目结构

```
interface_autotest/
├── src/                    # 源代码目录
│   ├── ai/                 # AI功能模块
│   ├── cli/                # 命令行接口
│   ├── core/               # 核心功能
│   ├── exporters/          # 导出功能
│   ├── mock/               # Mock服务器
│   ├── parsers/            # 文档解析器
│   ├── runners/            # 测试运行器
│   └── utils/              # 工具模块
├── docs/                   # 文档目录
├── examples/               # 示例代码
├── config/                 # 配置文件
├── tests/                  # 测试文件
└── README.md               # 项目说明
```

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request 来改进这个项目。

## 📄 许可证

MIT License

## 📧 联系方式

如有问题或建议，请通过 GitHub Issues 联系我们。

---

**注意事项：**
- 使用AI功能需要自己申请DeepSeek API Key
- 部分导出功能需要安装额外依赖（如pandas用于Excel导出）
- 建议在虚拟环境中运行此项目