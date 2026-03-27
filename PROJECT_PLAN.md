# 数字货币价格监控和预警系统 - 架构设计与开发计划

## 项目概述
我们将开发一个完整的全栈数字货币监控系统，包含实时价格监控、新闻聚合、预警通知和资产管理功能。系统采用前后端分离架构，支持Docker容器化部署。

## 技术栈

### 后端技术栈
- **Python 3.11+** - 主要编程语言
- **FastAPI** - 现代异步Web框架，自动生成API文档
- **SQLAlchemy 2.0** - ORM框架
- **SQLite** - 初期数据库（可迁移至PostgreSQL）
- **APScheduler** - 定时任务调度（价格获取、新闻抓取）
- **HTTPX** - 异步HTTP客户端（调用外部API）
- **JWT (PyJWT)** - 用户认证
- **Alembic** - 数据库迁移工具
- **Pydantic v2** - 数据验证

### 前端技术栈
- **Vue 3** - 前端框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **Pinia** - 状态管理
- **Vue Router** - 路由管理
- **Element Plus** - UI组件库
- **Axios** - HTTP客户端
- **ECharts** - 图表可视化（仪表盘）
- **SCSS** - CSS预处理器

### 部署与运维
- **Docker** + **Docker Compose** - 容器化
- **Nginx** - 反向代理和静态文件服务
- **Redis** (可选) - 缓存和消息队列（第二阶段）

## 系统架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                      前端 (Vue 3)                            │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │ 登录认证 │  │ 仪表盘  │  │ 币种管理 │  │ 预警管理 │       │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘       │
│  ┌─────────┐  ┌─────────┐                                  │
│  │ 资产管理 │  │ 新闻中心 │                                  │
│  └─────────┘  └─────────┘                                  │
└───────────────────────────┬─────────────────────────────────┘
                           │ HTTP/REST API (JSON)
┌───────────────────────────▼─────────────────────────────────┐
│                   后端 (FastAPI)                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   API 层                            │   │
│  │  • 用户认证 (JWT)                                   │   │
│  │  • 币种 CRUD                                        │   │
│  │  • 预警规则 CRUD                                    │   │
│  │  • 资产管理 CRUD                                    │   │
│  │  • 新闻查询                                         │   │
│  │  • 仪表盘数据                                       │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   服务层                            │   │
│  │  • 价格获取服务 (Binance/OKX)                       │   │
│  │  • 新闻抓取服务 (RSS/API)                           │   │
│  │  • 预警引擎服务                                     │   │
│  │  • 通知服务 (HTTP Webhook)                          │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   数据层                            │   │
│  │  • SQLAlchemy ORM                                   │   │
│  │  • SQLite/PostgreSQL                                │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
┌───────────────────────────▼─────────────────────────────────┐
│                    外部服务                                  │
│  ┌─────────┐  ┌─────────┐  ┌─────────────┐  ┌──────────┐  │
│  │ Binance │  │   OKX   │  │ 新闻 RSS    │  │ 用户定义  │  │
│  │   API   │  │   API   │  │ CoinDesk等  │  │ Webhook  │  │
│  └─────────┘  └─────────┘  └─────────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 数据库设计

### 主要数据表

1. **users** - 用户表
   - id, username, email, hashed_password, is_active, created_at

2. **cryptocurrencies** - 支持的币种表
   - id, symbol, name, logo_url, is_active, created_at

3. **price_alerts** - 价格预警规则表
   - id, user_id, crypto_id, alert_type (above/below), threshold_price, webhook_url, is_active, triggered_at, created_at

4. **assets** - 用户资产记录表
   - id, user_id, crypto_id, buy_price, quantity, notes, created_at

5. **news_sources** - 新闻源配置表
   - id, name, rss_url, is_active, language, created_at

6. **news_articles** - 新闻数据表
   - id, title, source, url, summary, published_at, crypto_id, source_id, created_at
   - 外键关联: source_id → news_sources.id

7. **price_history** - 价格历史记录表（可选）
   - id, crypto_id, price, volume, timestamp

## 文件目录结构

```
crypto-info/
├── backend/                      # 后端服务
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py               # FastAPI 应用入口
│   │   ├── config.py             # 配置文件
│   │   ├── database.py           # 数据库连接
│   │   ├── models/               # SQLAlchemy 模型
│   │   │   ├── user.py
│   │   │   ├── cryptocurrency.py
│   │   │   ├── alert.py
│   │   │   ├── asset.py
│   │   │   ├── news_source.py
│   │   │   └── news.py
│   │   ├── schemas/              # Pydantic 模式
│   │   │   ├── user.py
│   │   │   ├── cryptocurrency.py
│   │   │   ├── alert.py
│   │   │   ├── asset.py
│   │   │   └── news.py
│   │   ├── api/                  # API 路由
│   │   │   ├── __init__.py
│   │   │   ├── deps.py          # 依赖项
│   │   │   ├── auth.py          # 认证路由
│   │   │   ├── users.py
│   │   │   ├── cryptocurrencies.py
│   │   │   ├── alerts.py
│   │   │   ├── assets.py
│   │   │   └── news.py
│   │   ├── services/             # 业务逻辑
│   │   │   ├── __init__.py
│   │   │   ├── price_service.py  # 价格获取服务
│   │   │   ├── news_service.py   # 新闻抓取服务
│   │   │   ├── alert_service.py  # 预警引擎
│   │   │   └── notification_service.py
│   │   ├── tasks/                # 定时任务
│   │   │   ├── __init__.py
│   │   │   └── scheduler.py
│   │   └── utils/                # 工具函数
│   │       ├── __init__.py
│   │       ├── security.py
│   │       └── http_client.py
│   ├── alembic/                  # 数据库迁移
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/                     # 前端应用
│   ├── public/
│   ├── src/
│   │   ├── assets/               # 静态资源
│   │   ├── components/           # 可复用组件
│   │   ├── views/                # 页面组件
│   │   │   ├── Login.vue
│   │   │   ├── Dashboard.vue
│   │   │   ├── Cryptocurrencies.vue
│   │   │   ├── Alerts.vue
│   │   │   ├── Assets.vue
│   │   │   └── News.vue
│   │   ├── router/               # Vue Router
│   │   ├── stores/               # Pinia 状态
│   │   ├── api/                  # API 调用
│   │   ├── utils/                # 工具函数
│   │   ├── App.vue
│   │   └── main.ts
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── Dockerfile
├── docker-compose.yml
├── nginx/                        # Nginx 配置
│   └── default.conf
└── README.md
```

## 分步开发计划

### ✅ 第一阶段：基础架构搭建（已完成）

1. **项目初始化** ✅
   - 创建项目目录结构
   - 配置Docker开发环境
   - 创建 `.clinerules` 执行规则

2. **后端基础框架** ✅
   - 搭建FastAPI应用框架
   - 配置数据库连接（SQLAlchemy + SQLite）
   - 创建基础数据模型（User, Cryptocurrency, Asset, PriceAlert, NewsSource, NewsArticle）
   - 设置数据库迁移工具（Alembic）
   - 初始化数据库：默认管理员账户（admin@crypto.local / admin123）
   - 初始化数据库：默认币种（BTCUSDT, ETHUSDT）
   - 初始化数据库：默认新闻源（CoinDesk, PANews）

3. **前端基础框架** ✅
   - 使用Vite创建Vue 3 + TypeScript项目
   - 配置Element Plus UI库
   - 设置Vue Router路由
   - 配置Pinia状态管理
   - 创建基础布局组件

### ✅ 第二阶段：用户认证与基础API（已完成）

4. **用户认证系统** ✅
   - 实现用户注册/登录API
   - JWT token生成与验证
   - 密码加密（bcrypt）
   - 前端登录页面
   - 路由守卫和权限控制
   - 前后端连通测试

5. **基础CRUD API** ✅
   - 币种管理API（CRUD）
   - 预警规则管理API（CRUD）
   - 前端预警管理页面（Alerts.vue）
   - 前端仪表盘页面（Dashboard.vue）
   - 基本的表格展示和表单操作

### 第三阶段：价格监控核心（1-2周）

6. **价格获取服务**
   - 集成Binance API（python-binance或直接HTTP调用）
   - 实现OKX备用API
   - 定时任务调度（APScheduler）
   - 价格数据存储

7. **预警系统基础**
   - 预警规则数据模型
   - 预警规则CRUD API
   - 前端预警管理页面

8. **预警引擎**
   - 价格阈值检查逻辑
   - HTTP Webhook通知发送
   - 预警触发记录

### 第四阶段：资产管理与新闻（1周）

9. **资产管理模块**
   - 资产记录数据模型
   - 资产CRUD API
   - 前端资产管理页面
   - 资产总值计算

10. **新闻聚合模块**
    - 选择新闻源（CoinDesk RSS、ChainDD API等）
    - 新闻抓取服务
    - 新闻数据存储
    - 前端新闻展示页面

### 第五阶段：仪表盘与优化（1周）

11. **仪表盘开发**
    - 资产总值图表（ECharts）
    - 价格走势展示
    - 预警状态概览
    - 最新新闻摘要

12. **系统优化**
    - 添加缓存机制（Redis可选）
    - API响应优化
    - 前端性能优化
    - 错误处理和日志记录

### 第六阶段：部署与测试（1周）

13. **Docker容器化**
    - 编写Dockerfile（前后端）
    - 创建docker-compose.yml
    - 配置Nginx反向代理

14. **测试与文档**
    - 编写单元测试
    - API文档自动生成（FastAPI Swagger）
    - 用户使用文档

## 新闻源建议

1. **CoinDesk RSS** - 可靠的加密货币新闻源
2. **ChainDD API** - 中文加密货币新闻
3. **CoinTelegraph RSS** - 主流加密货币新闻
4. **CryptoPotato RSS** - 多样化的加密货币内容

建议初期使用RSS源，因为：
- 无需API密钥
- 数据格式标准化
- 更新频率合理

## 部署架构

```
用户浏览器 → Nginx (端口80/443) → 
  ├── /api/* → 后端FastAPI (端口8000)
  └── /* → 前端静态文件
```

Docker Compose将包含：
- frontend服务（Nginx提供静态文件）
- backend服务（FastAPI应用）
- nginx服务（反向代理）
- redis服务（可选，用于缓存）

## 关键设计决策

1. **异步处理**：FastAPI支持异步，适合IO密集型操作（API调用、数据库查询）
2. **定时任务**：使用APScheduler而不是Celery，减少依赖复杂度
3. **数据库**：初期SQLite便于开发，生产环境可轻松切换PostgreSQL
4. **前端状态管理**：Pinia替代Vuex，更符合Vue 3组合式API风格
5. **通知机制**：Webhook方式提供最大灵活性，用户可自定义通知渠道

这个架构具有良好的可扩展性，未来可添加：
- 实时WebSocket价格推送
- 更多交易所支持
- 移动端应用
- 社交功能（分享预警策略）exit