# 函数调用示例 (Function Calling Example)

这个示例展示了如何实现类似大模型 Function Calling 的功能，让程序能够根据用户的自然语言输入智能选择合适的处理方法。

## 🆕 DeepSeek 集成版本

现在提供了两个版本：
- **基础版本** (`function_calling_example.py`): 使用关键词匹配的简单实现
- **DeepSeek版本** (`deepseek_function_calling.py`): 集成DeepSeek大模型的智能版本

### DeepSeek 版本优势
- 🧠 **智能理解**: 使用大模型理解复杂的自然语言输入
- 🎯 **精准识别**: 更准确的函数选择和参数提取
- 🔄 **自动降级**: API不可用时自动切换到关键词匹配模式
- 📊 **详细反馈**: 提供置信度和分析来源信息

## 功能特性

- 🤖 **智能函数选择**: 根据用户输入的关键词自动选择最合适的处理函数
- 📝 **参数提取**: 使用正则表达式从自然语言中提取函数所需的参数
- 🔧 **多种功能**: 支持天气查询、数学计算、信息搜索、文本翻译、提醒设置、邮件发送等
- 💬 **交互式模式**: 提供命令行交互界面，支持实时对话
- 📊 **详细反馈**: 显示函数选择过程、参数提取结果和执行状态

## 支持的功能

| 功能 | 描述 | 示例输入 |
|------|------|----------|
| 天气查询 | 获取指定城市的天气信息 | "北京的天气怎么样？" |
| 数学计算 | 执行基本的数学运算 | "计算 25 + 37 * 2" |
| 信息搜索 | 搜索相关信息 | "搜索人工智能的最新发展" |
| 文本翻译 | 翻译文本到指定语言 | "把'Hello World'翻译成中文" |
| 设置提醒 | 创建定时提醒 | "提醒我明天下午3点开会" |
| 发送邮件 | 发送邮件到指定地址 | "发送邮件给 test@example.com 主题 会议通知 内容 明天开会" |

## 使用方法

### DeepSeek 版本（推荐）

#### 1. 获取 DeepSeek API Key
访问 [DeepSeek 平台](https://platform.deepseek.com/api_keys) 获取你的 API Key

#### 2. 设置环境变量
```bash
# macOS/Linux
export DEEPSEEK_API_KEY="your_api_key_here"

# Windows
set DEEPSEEK_API_KEY=your_api_key_here
```

#### 3. 运行 DeepSeek 版本
```bash
cd /Users/cuixueyong/code/github/yili-ai-python/app/scripts
python deepseek_function_calling.py
```

#### 4. 运行测试
```bash
# 基本功能测试
python test_deepseek.py

# 交互模式测试
python test_deepseek.py --interactive
```

### 基础版本

#### 1. 运行示例

```bash
cd /Users/cuixueyong/code/github/yili-ai-python/app/scripts
python function_calling_example.py
```

### 2. 测试模式

程序首先会运行预设的测试用例，展示各种功能的使用效果。

### 3. 交互模式

测试完成后，程序会进入交互模式，您可以输入自然语言请求：

```
请输入您的需求: 上海今天天气如何？
✅ 上海的天气：晴天，温度22°C，湿度65%，风速5 km/h

请输入您的需求: 计算 100 / 5 + 3
✅ 100 / 5 + 3 = 23.0

请输入您的需求: quit
再见！
```

## 核心实现原理

### 1. 函数选择算法

- 为每个函数定义关键词列表
- 计算用户输入与各函数关键词的匹配分数
- 选择得分最高的函数作为处理方法

### 2. 参数提取

- 使用正则表达式模式匹配
- 针对不同函数类型设计专门的提取规则
- 支持中英文混合输入

### 3. 函数执行

- 模拟实际的API调用
- 提供统一的返回格式
- 包含错误处理和异常捕获

## 扩展指南

### 添加新功能

1. 在 `available_functions` 中定义新函数的描述和关键词
2. 在 `extract_parameters` 方法中添加参数提取逻辑
3. 在 `execute_function` 方法中实现具体的执行逻辑
4. 添加对应的私有方法实现具体功能

### 示例：添加文件操作功能

```python
# 1. 在 available_functions 中添加
"file_operation": {
    "description": "文件操作",
    "parameters": {
        "action": {"type": "string", "description": "操作类型"},
        "file_path": {"type": "string", "description": "文件路径"}
    },
    "keywords": ["文件", "创建", "删除", "读取", "写入", "file"]
}

# 2. 添加参数提取逻辑
# 3. 添加执行逻辑
# 4. 实现具体功能方法
```

## 注意事项

- 这是一个演示示例，实际的函数执行都是模拟的
- 数学计算功能使用了 `eval()`，在生产环境中应该使用更安全的计算方法
- 正则表达式模式可能需要根据实际使用场景进行调整
- 建议在实际应用中集成真实的API服务

## 文件结构

```
app/scripts/
├── function_calling_example.py    # 基础版本（关键词匹配）
├── deepseek_function_calling.py   # DeepSeek版本（大模型智能识别）
├── test_deepseek.py              # DeepSeek版本测试脚本
├── config_example.py             # 配置示例文件
└── README.md                     # 使用说明
```

## DeepSeek API 说明

- **模型**: 使用 `deepseek-chat` 模型
- **Function Calling**: 支持原生的函数调用功能
- **费用**: 按token计费，具体价格请查看官网
- **限制**: 请遵守API使用条款和频率限制

## 技术栈

- Python 3.7+
- DeepSeek API
- 正则表达式 (re)
- JSON 数据处理
- 面向对象编程
- HTTP 请求处理

## 许可证

本示例代码仅供学习和参考使用。