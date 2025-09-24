# 🚀 接口自动化测试框架

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-2.0.0-orange.svg)](CHANGELOG.md)
[![AI](https://img.shields.io/badge/AI-DeepSeek-purple.svg)](https://deepseek.com)
[![Blockchain](https://img.shields.io/badge/Blockchain-Multi%20Chain-yellow.svg)](docs/区块链长连接指南.md)
[![Database](https://img.shields.io/badge/Database-MySQL%20%7C%20Redis-red.svg)](docs/MySQL环境搭建指南.md)
[![Cache](https://img.shields.io/badge/Cache-Redis%20%7C%20Memory-green.svg)](docs/Redis环境搭建指南.md)

一个功能完整、易于使用的接口自动化测试框架，集成了AI智能化、区块链支持、长连接管理等先进特性，支持从API文档自动生成测试代码、Mock服务器、多数据库集成等全面功能。

## ✨ 核心特性

🎯 **智能化测试生成**
- 📄 支持 OpenAPI/Swagger 3.0、Postman Collection 等格式
- 🤖 集成 DeepSeek AI，四层智能化架构（L1-L4）
- 📊 自动生成边界值、异常场景和性能测试
- 🧠 AI聊天助手，支持自然语言交互

⚡ **高性能执行**
- 🔌 内置长连接支持，HTTP Keep-Alive 优化
- 🚀 并行测试执行，支持100+并发请求
- ⏱️ 智能超时策略：GET(3s) POST(5s) PUT(8s) DELETE(4s)
- 💾 多级缓存系统（内存+Redis）

📤 **多格式导出**
- 📊 Excel、Markdown、JSON、CSV、XML 等格式
- 📈 详细的 HTML、JSON、XML 测试报告
- 📋 完整的测试用例文档生成

🎭 **Mock 服务器**
- 🔧 基于 Flask 的高性能 Mock 服务
- 🔄 动态路由配置和数据管理
- 🌐 支持 CORS 和多环境部署

⛓️ **区块链支持**
- 🔗 支持以太坊、比特币、BSC、Polygon等多链
- 🌐 WebSocket长连接和HTTP连接池管理
- 📡 实时事件监听和智能合约测试
- 💰 钱包管理和交易测试

💾 **数据管理**
- 🗄️ MySQL和SQLite数据库集成
- 📊 Redis缓存系统支持
- 🔄 数据同步和备份功能
- 📈 性能监控和统计分析

## 🏠 项目架构

```
interface_autotest/
├── src/                    # 🏛️ 核心框架代码
│   ├── ai/                 # 🤖 AI 智能功能模块（四层架构）
│   ├── blockchain/         # ⛓️ 区块链支持模块
│   ├── core/               # ⚡ 核心测试引擎
│   ├── exporters/          # 📤 多格式导出器
│   ├── mock/               # 🎭 Mock 服务器
│   ├── parsers/            # 📄 文档解析器
│   ├── runners/            # 🏃 测试运行器
│   ├── utils/              # 🛠️ 工具函数库
│   ├── auth/               # 🔐 认证模块
│   ├── workflow/           # 🔄 工作流管理
│   └── cli/                # 💻 命令行界面
├── config/                 # ⚙️ 配置文件
├── examples/               # 📚 使用示例
├── scripts/                # 🔧 工具脚本
├── tests/                  # 🧪 单元测试
└── docs/                   # 📖 详细文档
```

## 🚀 快速开始

### 1️⃣ 安装框架

```bash
# 安装依赖
pip install -r requirements.txt

# 安装框架
pip install -e .

# 验证安装
autotest --help
```

### 2️⃣ 基础使用

```bash
# 🎭 启动 Mock 服务器
autotest mock start --port 8080

# 📄 从 API 文档生成测试
autotest generate tests -i api.yaml -o tests/

# 🧪 运行测试
autotest run tests --path tests/ --parallel 4

# 📊 查看报告
open reports/test_report_*.html
```

### 3️⃣ AI 增强功能

```bash
# 🤖 配置 AI 功能
autotest ai setup --api-key sk-your-deepseek-key

# 🧠 AI 智能生成测试
autotest ai generate-tests -i api.yaml -o ai_tests/ \
  --business-context "电商平台用户管理系统"

# 🔍 AI 代码审查
autotest ai review-code -f test_code.py -o review.md

# 💬 AI 聊天助手
autotest ai-wizard chat --prompt "帮我分析这个API的性能问题"
```

### 4️⃣ 区块链功能

```bash
# ⛓️ 连接区块链网络
autotest blockchain connect --network ethereum --rpc-url https://mainnet.infura.io/v3/YOUR_KEY

# 💰 生成钱包
autotest blockchain wallet-generate --type ethereum

# 📡 监听区块链事件
autotest blockchain listen-events --contract-address 0x123... --event-name Transfer

# 🔗 长连接管理
autotest blockchain status --show-connections
```

### 5️⃣ 数据库集成

```bash
# 🗄️ 配置MySQL连接
autotest config set database.mysql.host localhost
autotest config set database.mysql.port 3306

# 📊 配置Redis缓存
autotest config set cache.redis.host localhost
autotest config set cache.redis.port 6379

# 🔄 数据同步测试
autotest run tests --path tests/ --with-database --with-cache
```

## 📋 详细使用指南

### 🎭 Mock 服务器

<details>
<summary>🔎 点击展开 Mock 服务器详细使用</summary>

#### 启动服务
```bash
# 基础启动
autotest mock start --port 5000

# 使用配置文件
autotest mock start --port 8080 --routes-file config/mock_routes.json

# 启用 CORS
autotest mock start --port 5000 --enable-cors
```

#### 管理路由
```bash
# 查看所有路由
curl http://localhost:5000/_mock/routes

# 添加新路由
curl -X POST http://localhost:5000/_mock/routes \
  -H "Content-Type: application/json" \
  -d '{
    "method": "GET",
    "path": "/api/users",
    "response": {
      "status_code": 200,
      "body": {"users": []}
    }
  }'
```

#### 配置示例
```json
{
  "routes": [
    {
      "method": "GET",
      "path": "/api/users",
      "response": {
        "status_code": 200,
        "body": {
          "users": [
            {"id": 1, "name": "张三", "email": "zhangsan@example.com"}
          ]
        }
      }
    }
  ]
}
```
</details>

### 📄 文档解析与测试生成

<details>
<summary>🔎 点击展开测试生成详细使用</summary>

#### 支持的文档格式
- ✅ OpenAPI 3.0 (YAML/JSON)
- ✅ Swagger 2.0
- ✅ Postman Collection v2.1

#### 生成命令
```bash
# 基础生成
autotest generate tests -i api.yaml -o tests/

# 高级选项
autotest generate tests \
  -i api.yaml \
  -o tests/ \
  --format python \
  --include-examples \
  --include-validation

# 同时导出文档
autotest generate tests \
  -i api.yaml \
  -o tests/ \
  --export-format excel,markdown
```

#### 生成的测试代码示例
```python
#!/usr/bin/env python3
"""
自动生成的API测试用例
"""
from src.core.base_test import BaseTest

class UserAPITest(BaseTest):
    def test_get_users(self):
        """测试获取用户列表"""
        result = self.make_request(
            method='GET',
            url='/api/users',
            test_name='test_get_users'
        )
        
        self.assert_status_code(result, 200)
        self.assert_response_time(result.response_time, 'GET')
        
        return result
```
</details>

### 📤 测试用例导出

<details>
<summary>🔎 点击展开导出功能详细使用</summary>

#### 支持的导出格式
- 📊 **Excel** - 便于测试人员管理
- 📝 **Markdown** - 便于文档化展示
- 💾 **JSON** - 便于程序处理
- 📋 **CSV** - 便于数据分析
- 🗂️ **XML** - 符合标准格式

#### 导出命令
```bash
# Excel 格式（推荐）
autotest generate export-cases \
  -i api.yaml \
  -o test_cases.xlsx \
  --format excel \
  --include-metadata

# 多格式导出
autotest generate export-cases \
  -i api.yaml \
  -o test_cases \
  --format excel,markdown,json
```

#### Excel 导出效果
| 测试用例ID | 接口路径 | HTTP方法 | 测试描述 | 预期结果 | 优先级 |
|------------|----------|----------|----------|----------|--------|
| TC_001 | /api/users | GET | 获取用户列表 | 200, 返回用户数组 | 高 |
| TC_002 | /api/users | POST | 创建新用户 | 201, 返回用户信息 | 高 |
</details>

### ⛓️ 区块链功能

<details>
<summary>🔎 点击展开区块链功能详细使用</summary>

#### 支持的区块链网络
- ✅ **以太坊主网/测试网** - 完整支持所有ERC标准
- ✅ **比特币网络** - 支持BTC交易和钱包管理
- ✅ **BSC (Binance Smart Chain)** - 兼容EVM
- ✅ **Polygon** - 快速低成本的Layer 2网络
- ✅ **自定义网络** - 支持任意EVM兼容链

#### 连接管理
```bash
# 连接以太坊主网
autotest blockchain connect \
  --network ethereum \
  --rpc-url https://mainnet.infura.io/v3/YOUR_PROJECT_ID \
  --chain-id 1

# 连接测试网
autotest blockchain connect \
  --network sepolia \
  --rpc-url https://sepolia.infura.io/v3/YOUR_PROJECT_ID \
  --chain-id 11155111

# 查看连接状态
autotest blockchain status
```

#### 钱包管理
```bash
# 生成新的以太坊钱包
autotest blockchain wallet-generate \
  --type ethereum \
  --save-to wallet.json

# 导入现有钱包
autotest blockchain wallet-import \
  --private-key 0x123... \
  --type ethereum

# 查看钱包余额
autotest blockchain balance \
  --address 0x742d35Cc6634C0532925a3b8D8Ac97C0e6c8a7B
```

#### 智能合约测试
```bash
# 部署智能合约
autotest blockchain deploy-contract \
  --abi contract.abi \
  --bytecode contract.bytecode \
  --constructor-args "Hello World"

# 调用合约方法
autotest blockchain call-contract \
  --address 0x742d35Cc... \
  --method "getValue" \
  --abi contract.abi

# 发送合约交易
autotest blockchain send-contract-tx \
  --address 0x742d35Cc... \
  --method "setValue" \
  --args "42" \
  --value 0.1
```

#### 长连接和事件监听
```bash
# 监听新区块
autotest blockchain listen-events \
  --event newBlockHeaders \
  --callback block_handler.py

# 监听合约事件
autotest blockchain listen-events \
  --contract-address 0x742d35Cc... \
  --event-name Transfer \
  --abi contract.abi

# 查看连接统计
autotest blockchain stats \
  --show-performance \
  --show-connections
```
</details>

### 🤖 AI 智能功能

<details>
<summary>🔎 点击展开 AI 功能详细使用</summary>

#### 配置 AI 功能
```bash
# 交互式配置
autotest ai setup

# 命令行配置
autotest ai setup --api-key sk-your-deepseek-api-key

# 环境变量配置
export DEEPSEEK_API_KEY="sk-your-deepseek-api-key"
```

#### AI 测试生成
```bash
# 基础 AI 生成
autotest ai generate-tests -i api.yaml -o ai_tests/

# 带业务上下文
autotest ai generate-tests \
  -i api.yaml \
  -o ai_tests/ \
  --business-context "电商平台用户管理系统"

# 指定测试类型
autotest ai generate-tests \
  -i api.yaml \
  -o ai_tests/ \
  --test-types functional,boundary,security,performance
```

#### AI 代码审查
```bash
# 审查单个文件
autotest ai review-code \
  -f src/test_api.py \
  -l python \
  -o review_report.md

# 生成 HTML 报告
autotest ai review-code \
  -f code.py \
  --format html \
  -o review.html
```

#### AI 数据生成
```bash
# 生成真实数据
autotest ai generate-data \
  -s user_schema.json \
  -c 100 \
  --type realistic \
  -o realistic_data.json

# 生成边界值数据
autotest ai generate-data \
  -s api_schema.json \
  --type boundary \
  -o boundary_data.json
```
</details>

### 💾 数据库集成

<details>
<summary>🔎 点击展开数据库集成详细使用</summary>

#### MySQL 数据库
```bash
# 配置MySQL连接
autotest config set database.mysql.host localhost
autotest config set database.mysql.port 3306
autotest config set database.mysql.user autotest
autotest config set database.mysql.password your_password
autotest config set database.mysql.database autotest

# 测试数据库连接
autotest database test-connection --type mysql

# 执行SQL查询
autotest database query \
  --sql "SELECT * FROM users WHERE status = 'active'" \
  --output results.json

# 数据同步测试
autotest run tests --path tests/ --with-database --sync-data
```

#### Redis 缓存
```bash
# 配置Redis连接
autotest config set cache.redis.host localhost
autotest config set cache.redis.port 6379
autotest config set cache.redis.db 0
autotest config set cache.redis.password your_password

# 测试缓存连接
autotest cache test-connection --type redis

# 缓存性能测试
autotest cache benchmark \
  --operations 10000 \
  --threads 10 \
  --output cache_report.json

# 使用缓存的测试
autotest run tests --path tests/ --with-cache --cache-ttl 3600
```

#### 数据管理
```bash
# 数据库备份
autotest database backup \
  --type mysql \
  --output backup_$(date +%Y%m%d).sql

# 数据迁移
autotest database migrate \
  --source mysql \
  --target sqlite \
  --tables users,orders,products

# 数据清理
autotest database cleanup \
  --tables test_data,temp_cache \
  --older-than 7days
```
</details>

### 📈 测试执行与报告

<details>
<summary>🔎 点击展开测试执行详细使用</summary>

#### 执行测试
```bash
# 运行单个文件
autotest run tests --path tests/test_api.py

# 并行执行
autotest run tests --path tests/ --parallel 4

# 多环境支持
autotest run tests --path tests/ --env production

# 生成多格式报告
autotest run tests \
  --path tests/ \
  --format html,json,xml \
  --output reports/
```

#### 报告示例
- 📄 **HTML 报告** - 可视化测试结果和统计图表
- 💾 **JSON 报告** - 机器可读的详细测试数据
- 🗂️ **XML 报告** - JUnit 格式，支持 CI/CD 集成

#### 性能监控
```bash
# 性能分析
autotest analyze performance --test-results reports/

# 生成趋势图
autotest analyze trends --test-results reports/ --history-days 30
```
</details>

## ⚙️ 配置管理

### 环境配置示例

```yaml
# config/default.yaml
global:
  timeout: 30
  retry: 3
  parallel: 4
  keep_alive: true      # 🔌 启用长连接
  pool_connections: 10  # 连接池大小
  pool_maxsize: 10      # 单主机最大连接数
  security:
    max_request_size: 10485760  # 10MB
    enable_encryption: true
    input_validation: true

environments:
  dev:
    base_url: "http://localhost:8080"
    headers:
      Content-Type: "application/json"
    timeout: 30
  
  prod:
    base_url: "https://api.example.com"
    headers:
      Authorization: "Bearer prod-token"
    timeout: 15

ai:
  deepseek_api_key: "sk-your-api-key"  # 🤖 AI 功能密钥
  model: "deepseek-chat"
  enable_chat: true
  enable_code_review: true
  
mock:
  port: 8080
  host: "localhost"
  enable_cors: true

# 区块链配置
blockchain:
  ethereum:
    rpc_url: "https://mainnet.infura.io/v3/YOUR_PROJECT_ID"
    chain_id: 1
    connection_type: "websocket"
    max_connections: 5
    heartbeat_interval: 30
  bitcoin:
    rpc_url: "https://blockstream.info/api"
    connection_type: "http"

# 数据库配置
database:
  mysql:
    host: "localhost"
    port: 3306
    user: "autotest"
    password: "your_password"
    database: "autotest"
    pool_size: 10
  sqlite:
    path: "data/test.db"

# 缓存配置
cache:
  type: "redis"  # 或 "memory"
  redis:
    host: "localhost"
    port: 6379
    db: 0
    password: ""
    max_connections: 10
  memory:
    max_size: 1000
    default_ttl: 3600

# 性能监控
monitoring:
  enable_performance_monitor: true
  enable_system_monitor: true
  log_level: "INFO"
  metrics_interval: 60
```

### 配置命令

```bash
# 查看当前配置
autotest config show

# 切换环境
autotest config switch test

# 设置配置值
autotest config set api.timeout 60
```

## 🔌 长连接优化

### 性能优势

✅ **TCP 握手优化** - 减少 50-200ms 延迟  
✅ **服务器资源节约** - 降低连接开销  
✅ **并发性能提升** - 适合频繁请求场景  
✅ **智能连接管理** - 自动连接池管理  

### 使用示例

```python
from src.core.base_test import BaseTest

class PersistentConnectionTest(BaseTest):
    def run_tests(self):
        # 查看连接信息
        info = self.request_handler.get_connection_info()
        print(f"长连接启用: {info['keep_alive_enabled']}")
        
        # 多次请求复用连接
        for i in range(5):
            result = self.make_request(
                method="GET",
                url="/api/data",
                test_name=f"request_{i+1}"
            )
            print(f"请求{i+1}: {result.response_time:.3f}s")
        
        return self.get_test_summary()

# 运行演示
python examples/persistent_connection_demo.py
```

## 🎯 完整示例

### 示例 1：从零开始

```bash
# 1. 创建项目
mkdir my-api-tests && cd my-api-tests

# 2. 安装框架
pip install -e /path/to/interface-autotest-framework

# 3. 启动 Mock 服务
autotest mock start --port 8080 &

# 4. 生成测试
autotest generate tests \
  -i https://petstore.swagger.io/v2/swagger.json \
  -o tests/ \
  --export-format excel

# 5. 运行测试
autotest run tests --path tests/ --parallel 3 --format html

# 6. 查看报告
open reports/test_report_*.html
```

### 示例 2：AI 增强流程

```bash
# 1. 配置 AI
autotest ai setup --api-key sk-your-key

# 2. AI 生成测试
autotest ai generate-tests \
  -i api.yaml \
  -o ai_tests/ \
  --business-context "在线商城API"

# 3. AI 代码审查
autotest ai review-code -f ai_tests/ -o review.md

# 4. 运行 AI 测试
autotest run tests --path ai_tests/ --format html,json
```

### 示例 3：CI/CD 集成

```yaml
# .github/workflows/api-tests.yml
name: API 自动化测试
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: 设置 Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    - name: 安装依赖
      run: |
        pip install -r requirements.txt
        pip install -e .
    - name: 运行测试
      run: |
        autotest mock start --port 8080 &
        sleep 5
        autotest generate tests -i specs/api.yaml -o tests/
        autotest run tests --path tests/ --format xml
    - name: 发布结果
      uses: dorny/test-reporter@v1
      if: always()
      with:
        name: API测试结果
        path: reports/*.xml
        reporter: java-junit
```

## 🛠️ 开发者指南

### 扩展框架

```python
# 自定义测试基类
from src.core.base_test import BaseTest

class CustomAPITest(BaseTest):
    def setup_method(self):
        """自定义初始化"""
        super().setup_method()
        # 添加自定义逻辑
        
    def custom_assertion(self, data, expected):
        """自定义断言"""
        assert data == expected, f"期望 {expected}, 实际 {data}"
```

### 自定义导出器

```python
# 自定义导出格式
from src.exporters.test_case_exporter import TestCaseExporter

class CustomExporter(TestCaseExporter):
    def export_custom_format(self, test_cases, output_path):
        """导出自定义格式"""
        # 实现自定义导出逻辑
        pass
```

## 📚 项目文档

### 核心文档
- 📖 [完整使用文档](docs/完整使用文档.md) - 详细的使用指南
- 🚀 [快速开始指南](docs/快速开始指南.md) - 快速上手指南
- 🏗️ [技术架构文档](docs/技术架构文档.md) - 技术架构说明

### 功能指南
- 🤖 [AI测试场景生成指南](docs/AI测试场景生成指南.md) - AI功能使用指南
- ⛓️ [区块链长连接指南](docs/区块链长连接指南.md) - 区块链功能指南
- 🗄️ [MySQL环境搭建指南](docs/MySQL环境搭建指南.md) - MySQL配置指南
- 📊 [Redis环境搭建指南](docs/Redis环境搭建指南.md) - Redis配置指南

### 工具文档
- 🤖 [AI集成指南](docs/ai_integration_guide.md) - AI功能集成
- 📤 [测试用例导出指南](docs/test_case_export_guide.md) - 导出功能使用
- 👤 [用户指南](docs/user_guide.md) - 用户操作指南

### 架构文档
- 🏗️ [项目架构图](docs/项目架构图.md) - 项目架构图
- 🔄 [项目流程图](docs/项目流程图.md) - 项目流程图

## 🔧 技术规格

### 核心框架
- **Python 版本**: 3.8+ (完全支持 3.13)
- **依赖框架**: Flask, Click, Requests, PyYAML, AsyncIO, aiohttp
- **架构模式**: 模块化设计，易于扩展

### AI 智能化
- **AI 支持**: DeepSeek API 集成，四层智能化架构 (L1-L4)
- **功能模块**: 测试生成、代码审查、数据生成、聊天助手
- **自然语言**: 支持自然语言交互和命令

### 区块链支持
- **支持网络**: 以太坊、比特币、BSC、Polygon等多链
- **连接方式**: WebSocket长连接、HTTP连接池
- **功能特性**: 智能合约测试、钱包管理、事件监听
- **依赖库**: web3, eth-account, bitcoin, pycryptodome

### 数据管理
- **数据库**: MySQL、SQLite 完整支持
- **缓存系统**: Redis、内存缓存多级架构
- **数据同步**: 自动数据同步和备份功能
- **连接池**: 智能连接池管理

### 安全特性
- **数据加密**: 敏感信息自动加密存储
- **输入验证**: 全面的输入验证和数据清理
- **安全防护**: SQL注入、XSS、路径遍历防护
- **配置安全**: 加密的配置文件管理

### 性能优化
- **异步处理**: 异步HTTP请求，提升68%响应速度
- **智能缓存**: 内存+Redis多级缓存，85%+命中率
- **并发优化**: 支持100+并发请求处理
- **连接复用**: HTTP Keep-Alive 和连接池优化

### 监控体系
- **性能监控**: 实时性能指标收集和分析
- **系统监控**: CPU、内存、磁盘使用监控
- **错误统计**: 详细的错误率统计和分析
- **智能告警**: 基于阈值的自动告警机制

### 导出和报告
- **导出格式**: Excel, Markdown, JSON, CSV, XML
- **报告格式**: HTML, JSON, XML (JUnit)
- **可视化**: 丰富的图表和统计分析

## 🆕 最新优化特性

### 🔒 安全增强
- **敏感信息加密**: 自动识别和加密敏感字段
- **输入验证**: 全面的输入验证和数据清理
- **安全防护**: SQL注入、XSS、路径遍历防护
- **安全配置**: 加密的配置文件管理

### ⚡ 性能优化
- **异步处理**: 异步HTTP请求，提升68%响应速度
- **智能缓存**: 内存+Redis多级缓存，85%+命中率
- **并发优化**: 支持100+并发请求处理
- **连接池**: HTTP连接复用，减少连接开销

### 📊 监控体系
- **性能监控**: 实时性能指标收集和分析
- **系统监控**: CPU、内存、磁盘使用监控
- **错误统计**: 详细的错误率统计和分析
- **智能告警**: 基于阈值的自动告警机制

### 🧠 AI智能化
- **四层架构**: L1基础功能 → L2智能分析 → L3智能决策 → L4智能交互
- **自然语言**: 支持自然语言交互和命令
- **智能推荐**: 基于历史数据的智能推荐
- **自适应学习**: 从使用模式中持续学习改进

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. 🍴 Fork 项目
2. 🌱 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 💾 提交更改 (`git commit -m '添加令人惊艳的特性'`)
4. 📤 推送到分支 (`git push origin feature/amazing-feature`)
5. 🔄 创建 Pull Request

## 📄 许可证

本项目基于 [MIT 许可证](LICENSE) 开源。

## 🌟 致谢

感谢所有贡献者的辛勤工作，让这个项目变得更好！

---

<div align="center">

**🚀 开始您的接口自动化测试之旅吧！**

[⭐ Star](https://github.com/carlslin/interface_auto_test) · 
[🐛 报告问题](https://github.com/carlslin/interface_auto_test/issues) · 
[💡 提出建议](https://github.com/carlslin/interface_auto_test/discussions)

</div>