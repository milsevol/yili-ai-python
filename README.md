# Yili AI Python 项目

基于 FastAPI 框架的 Python 项目，提供 RESTful API 服务。

## 项目结构

```
.
├── app                  # 应用主目录
│   ├── api             # API 相关代码
│   │   └── endpoints   # API 端点
│   ├── core            # 核心配置
│   ├── db              # 数据库相关
│   ├── models          # 数据库模型
│   └── schemas         # Pydantic 模型
├── tests               # 测试目录
├── main.py             # 应用入口
└── requirements.txt    # 依赖包
```

## 功能特性

- 基于 FastAPI 的高性能 API
- Pydantic 数据验证
- SQLAlchemy ORM 支持
- 自动生成 API 文档
- 用户、商品、产品、订单和客户的增删改查API
- 单元测试支持

## 安装与运行

### 环境要求

- Python 3.11.11 或更高版本

### 创建虚拟环境

推荐使用虚拟环境来隔离项目依赖：

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境（在macOS/Linux上）
source venv/bin/activate

# 激活虚拟环境（在Windows上）
venv\Scripts\activate
```

### 安装依赖

在激活的虚拟环境中安装依赖：

```bash
pip install -r requirements.txt
```

### 运行应用

```bash
python main.py
```

或者使用 uvicorn 直接运行：

```bash
uvicorn main:app --reload
```

应用将在 http://localhost:8000 上运行。

### 退出虚拟环境

当完成工作后，可以通过以下命令退出虚拟环境：

```bash
deactivate
```

### API 文档

- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc

**注意**：API文档路径包含版本前缀 `/api/v1`，这是项目配置决定的。请确保使用正确的URL访问文档。

## API 端点说明

本项目实现了以下API端点：

### 用户管理 (/api/v1/users)
- GET /api/v1/users - 获取所有用户
- GET /api/v1/users/{user_id} - 获取特定用户
- POST /api/v1/users - 创建新用户
- PUT /api/v1/users/{user_id} - 更新用户信息
- DELETE /api/v1/users/{user_id} - 删除用户

### 商品管理 (/api/v1/items)
- GET /api/v1/items - 获取所有商品
- GET /api/v1/items/{item_id} - 获取特定商品
- POST /api/v1/items - 创建新商品
- PUT /api/v1/items/{item_id} - 更新商品信息
- DELETE /api/v1/items/{item_id} - 删除商品

### 产品管理 (/api/v1/products)
- GET /api/v1/products - 获取所有产品（支持分页和按类别筛选）
- GET /api/v1/products/{product_id} - 获取特定产品
- POST /api/v1/products - 创建新产品
- PUT /api/v1/products/{product_id} - 更新产品信息
- DELETE /api/v1/products/{product_id} - 删除产品

### 订单管理 (/api/v1/orders)
- GET /api/v1/orders - 获取所有订单（支持分页和按状态、用户筛选）
- GET /api/v1/orders/{order_id} - 获取特定订单
- POST /api/v1/orders - 创建新订单
- PUT /api/v1/orders/{order_id} - 更新订单信息
- DELETE /api/v1/orders/{order_id} - 删除订单

### 客户管理 (/api/v1/customers)
- GET /api/v1/customers - 获取所有客户（支持分页、按VIP等级筛选和搜索）
- GET /api/v1/customers/{customer_id} - 获取特定客户
- POST /api/v1/customers - 创建新客户
- PUT /api/v1/customers/{customer_id} - 更新客户信息
- DELETE /api/v1/customers/{customer_id} - 删除客户

### 健康检查
- GET /api/v1/health - 检查API服务健康状态

**注意**：当前所有API都使用模拟数据实现，未连接实际数据库。

## 开发指南

### 添加新的 API 端点

1. 在 `app/api/endpoints/` 目录下创建新的路由文件
2. 在 `app/api/endpoints/__init__.py` 中注册新的路由

### 添加新的数据模型

1. 在 `app/schemas/` 目录下创建新的 Pydantic 模型
2. 在 `app/models/` 目录下创建新的 SQLAlchemy 模型

## 已实现的数据模型

本项目已实现以下Pydantic数据模型：

### 用户模型 (User)
- UserBase: 用户基础信息
- UserCreate: 创建用户时的数据结构
- UserUpdate: 更新用户时的数据结构
- UserResponse: 返回给客户端的用户数据结构

### 商品模型 (Item)
- ItemBase: 商品基础信息
- ItemCreate: 创建商品时的数据结构
- ItemUpdate: 更新商品时的数据结构
- ItemResponse: 返回给客户端的商品数据结构

### 产品模型 (Product)
- ProductBase: 产品基础信息
- ProductCreate: 创建产品时的数据结构
- ProductUpdate: 更新产品时的数据结构
- ProductResponse: 返回给客户端的产品数据结构

### 订单模型 (Order)
- OrderItemBase: 订单项基础信息
- OrderItemCreate: 创建订单项时的数据结构
- OrderItemResponse: 返回给客户端的订单项数据结构
- OrderBase: 订单基础信息
- OrderCreate: 创建订单时的数据结构
- OrderUpdate: 更新订单时的数据结构
- OrderResponse: 返回给客户端的订单数据结构

### 客户模型 (Customer)
- CustomerBase: 客户基础信息
- CustomerCreate: 创建客户时的数据结构
- CustomerUpdate: 更新客户时的数据结构
- CustomerResponse: 返回给客户端的客户数据结构

## 测试

运行测试：

```bash
pytest
```

## 未来开发计划

- 实现数据库连接，替换当前的模拟数据
- 添加用户认证与授权功能
- 实现更复杂的业务逻辑，如订单处理流程
- 添加更多的数据验证和错误处理
- 实现文件上传功能
- 添加更多的单元测试和集成测试

## 许可证

[MIT](LICENSE)