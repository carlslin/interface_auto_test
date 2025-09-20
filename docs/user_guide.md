# 接口自动化测试框架使用指南

## 快速开始

### 1. 安装依赖

```bash
cd /Users/lin/interface_autotest
python3 -m pip install -r requirements.txt
```

### 2. 启动Mock服务器

```bash
python3 src/cli/main.py mock start --port 5000
```

### 3. 从API文档生成测试脚本

```bash
python3 src/cli/main.py generate tests --input examples/petstore.yaml --output tests/
```

### 4. 运行测试

```bash
python3 src/cli/main.py test run --path tests/
```

## 功能特性

### Mock服务器

框架内置了一个功能强大的Mock服务器，支持：

- 动态路由配置
- 条件匹配响应
- 模板化响应数据
- CORS支持
- 请求延迟模拟

#### 启动Mock服务器

```bash
# 基本启动
python3 src/cli/main.py mock start

# 指定端口和主机
python3 src/cli/main.py mock start --port 8080 --host 0.0.0.0

# 加载路由配置文件
python3 src/cli/main.py mock start --routes-file examples/mock_routes.json
```

#### Mock服务器API

Mock服务器提供了管理API：

- `GET /_mock/routes` - 获取所有路由
- `POST /_mock/routes` - 添加路由
- `PUT /_mock/routes/{id}` - 更新路由
- `DELETE /_mock/routes/{id}` - 删除路由
- `POST /_mock/reset` - 重置所有数据

### 测试脚本生成

支持从多种API文档格式生成测试脚本：

- OpenAPI 3.0
- Swagger 2.0
- Postman Collection (计划支持)

#### 生成Python测试脚本

```bash
python3 src/cli/main.py generate tests \
  --input swagger.json \
  --output tests/ \
  --format python
```

#### 生成JSON测试配置

```bash
python3 src/cli/main.py generate tests \
  --input openapi.yaml \
  --output configs/ \
  --format json
```

### 测试执行

框架提供了强大的测试执行功能：

- 并发执行
- 失败重试
- 多环境支持
- 详细报告

#### 运行测试

```bash
# 运行所有测试
python3 src/cli/main.py test run

# 指定测试路径
python3 src/cli/main.py test run --path tests/api_tests.py

# 并发执行
python3 src/cli/main.py test run --parallel 5

# 生成报告
python3 src/cli/main.py test run --output reports/test_report.html
```

## 配置管理

### 配置文件结构

配置文件使用YAML格式，支持多环境配置：

```yaml
# 全局配置
global:
  timeout: 30
  retry: 3
  parallel: 5

# 环境配置
environments:
  dev:
    base_url: "http://dev-api.example.com"
    headers:
      Authorization: "Bearer dev-token"
  test:
    base_url: "http://test-api.example.com"
    headers:
      Authorization: "Bearer test-token"
  prod:
    base_url: "https://api.example.com"
    headers:
      Authorization: "Bearer prod-token"

# Mock服务器配置
mock:
  port: 5000
  host: "localhost"
  debug: true
  enable_cors: true

# 报告配置
report:
  format: ["html", "json"]
  output_dir: "./reports"
```

### 环境切换

```bash
# 使用开发环境
python3 src/cli/main.py --env dev test run

# 使用测试环境
python3 src/cli/main.py --env test test run

# 使用生产环境
python3 src/cli/main.py --env prod test run
```

## 编写测试用例

### 基础测试类

```python
from src.core.base_test import BaseTest

class UserAPITest(BaseTest):
    def __init__(self, config_path=None):
        super().__init__(config_path)
        
    def run_tests(self):
        """运行所有测试"""
        self.test_get_user()
        self.test_create_user()
        self.test_update_user()
        self.test_delete_user()
        
    def test_get_user(self):
        """测试获取用户"""
        result = self.make_request(
            method="GET",
            url="/users/123",
            test_name="get_user"
        )
        
        # 状态码断言
        self.assert_status_code(result, 200)
        
        # 响应时间断言
        self.assert_response_time(result.response_time, 2.0)
        
        # 响应内容断言
        response_data = result.response_data
        self.assert_contains(response_data, "id", 123)
        self.assert_contains(response_data, "name", "张三")
        
        return result
```

### 使用Mock数据

```python
def test_with_mock_data(self):
    """使用Mock数据测试"""
    # 设置Mock响应
    mock_response = {
        "status_code": 200,
        "body": {
            "id": 123,
            "name": "测试用户",
            "email": "test@example.com"
        }
    }
    
    # 发送请求到Mock服务器
    result = self.make_request(
        method="GET",
        url="http://localhost:5000/users/123"
    )
    
    self.assert_status_code(result, 200)
```

## 高级功能

### 数据生成

框架内置了数据生成器，支持：

```python
from src.utils.data_faker import DataFaker

faker = DataFaker()

# 使用模板生成用户数据
user_data = faker.generate_from_template("user")

# 使用JSON Schema生成数据
schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer", "minimum": 18, "maximum": 80}
    }
}
data = faker.generate_from_schema(schema)
```

### 响应验证

```python
from src.utils.validator import ResponseValidator

validator = ResponseValidator()

# 验证状态码
validator.validate_status_code(200, [200, 201])

# 验证响应时间
validator.validate_response_time(1.5, 3.0)

# 验证JSON结构
schema = {"type": "object", "properties": {"id": {"type": "integer"}}}
validator.validate_json_schema(response_data, schema)

# 验证字段值
validator.validate_field_value(response_data, "status", "success")
```

## 命令行参考

### 全局选项

- `--config, -c` - 指定配置文件路径
- `--env, -e` - 指定环境名称
- `--debug` - 启用调试模式

### Mock服务器命令

- `mock start` - 启动Mock服务器
  - `--port, -p` - 端口号
  - `--host, -h` - 主机地址
  - `--routes-file, -f` - 路由配置文件

### 生成命令

- `generate tests` - 生成测试脚本
  - `--input, -i` - 输入文档文件
  - `--output, -o` - 输出目录
  - `--format, -f` - 输出格式（python/json）
  - `--template, -t` - 自定义模板

### 测试命令

- `test run` - 运行测试
  - `--path, -p` - 测试文件路径
  - `--pattern` - 文件匹配模式
  - `--parallel` - 并发数量
  - `--output, -o` - 报告输出路径

### 信息命令

- `info` - 显示框架信息

## 最佳实践

1. **环境隔离**: 为不同环境配置独立的配置文件
2. **测试分层**: 将API测试按模块分组
3. **数据驱动**: 使用外部数据文件驱动测试
4. **断言充分**: 除了状态码，还要验证响应内容和性能
5. **Mock使用**: 在不稳定的外部依赖中使用Mock
6. **持续集成**: 集成到CI/CD流水线中

## 故障排除

### 常见问题

1. **Mock服务器启动失败**
   - 检查端口是否被占用
   - 确认配置文件格式正确

2. **测试脚本生成失败**
   - 验证API文档格式是否正确
   - 检查文件路径是否存在

3. **测试执行失败**
   - 确认目标服务器可访问
   - 检查认证信息是否正确

4. **配置加载失败**
   - 验证YAML语法
   - 检查文件编码（建议UTF-8）