# LangChain Agent 示例

这个目录包含了使用LangChain Agent架构的简单示例。

## 文件结构

```
examples/
├── agent_demo.py    # Agent使用示例脚本
└── README.md        # 本文件
```

## Agent类型

### 1. SimpleAgent
- **功能**: 简单的工具调用Agent
- **特点**: 单轮对话，直接调用工具并返回结果
- **适用场景**: 简单的计算、查询等任务

### 2. ReactAgent  
- **功能**: 推理和行动Agent
- **特点**: 多轮推理，能够进行复杂的思考和决策
- **适用场景**: 需要多步骤推理的复杂任务

## 可用工具

- **safe_calculator**: 安全的数学计算器
- **get_current_date**: 获取当前日期
- **get_current_time**: 获取当前时间
- **get_current_timestamp**: 获取当前时间戳
- **get_current_utc_time**: 获取当前UTC时间

## 使用方式

### 1. 命令行演示

```bash
# 运行完整演示
python examples/agent_demo.py
```

这将依次运行：
1. SimpleAgent演示 - 展示简单工具调用
2. ReactAgent演示 - 展示复杂推理过程
3. 交互式演示 - 可以与Agent进行实时对话

### 2. API接口

启动服务器后，可以通过HTTP API使用Agent：

```bash
# 启动服务器
python main.py
```

#### 获取可用Agent和工具列表
```bash
curl -X GET "http://localhost:8000/api/v1/agents"
```

#### 使用SimpleAgent
```bash
curl -X POST "http://localhost:8000/api/v1/agents/simple" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "计算 15 + 27 * 3",
    "agent_name": "数学助手"
  }'
```

#### 使用ReactAgent
```bash
curl -X POST "http://localhost:8000/api/v1/agents/react" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "先计算 20 + 15，然后告诉我现在的时间",
    "max_iterations": 5,
    "verbose": true
  }'
```

#### 通用Agent接口
```bash
curl -X POST "http://localhost:8000/api/v1/agents/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "今天是什么日期？",
    "agent_type": "simple"
  }'
```

## API文档

启动服务器后，访问以下地址查看完整的API文档：

- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc

## 示例查询

### SimpleAgent示例
- "计算 15 + 27 * 3"
- "现在是几点？"
- "今天是什么日期？"
- "计算 (10 + 5) / 3 的结果"

### ReactAgent示例
- "先计算 20 + 15，然后告诉我现在的时间"
- "计算 (8 * 7) - 10，然后告诉我今天是星期几"
- "如果现在是下午，计算 100 / 4，否则计算 50 * 2"

## 架构说明

### SimpleAgent架构
```
用户查询 → SimpleAgent → LLMService → 工具调用 → 结果返回
```

### ReactAgent架构
```
用户查询 → ReactAgent → AgentExecutor → 
  ↓
推理循环：思考 → 行动 → 观察 → 思考 → ...
  ↓
最终答案
```

## 扩展说明

### 添加新工具
1. 在 `app/tools/` 目录下创建新的工具文件
2. 使用 `@tool` 装饰器定义工具函数
3. 在 `app/tools/__init__.py` 中导入并添加到 `AVAILABLE_TOOLS`

### 创建新Agent类型
1. 继承 `BaseAgent` 类
2. 实现 `run` 方法
3. 在 `app/agents/__init__.py` 中导入

## 注意事项

1. **安全性**: 所有工具都经过安全检查，数学计算使用AST解析避免代码注入
2. **错误处理**: Agent具有完善的错误处理机制
3. **日志记录**: 所有操作都有详细的日志记录
4. **性能**: ReactAgent的推理步骤有限制，避免无限循环

## 故障排除

### 常见问题

1. **API Key未设置**
   - 确保在 `.env` 文件中设置了 `DEEPSEEK_API_KEY`

2. **工具调用失败**
   - 检查工具函数的参数格式
   - 查看日志文件获取详细错误信息

3. **Agent响应慢**
   - ReactAgent需要多轮推理，响应时间较长是正常的
   - 可以通过设置 `max_iterations` 限制推理步骤

4. **导入错误**
   - 确保所有依赖包都已安装
   - 检查Python路径设置