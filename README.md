# Crypto-info 数字货币价格监控和预警系统

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/Vue-3+-green.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-teal.svg)](https://fastapi.tiangolo.com/)

## 📋 项目简介

Crypto-info 是一个全栈数字货币价格监控和预警系统，提供实时价格监控、新闻聚合、预警通知和资产管理功能。系统采用前后端分离架构，支持 Docker 容器化部署。

### ✨ 核心功能

- **实时价格监控** - 支持 BTC、ETH 等主流币种，自动从币安/OKX 获取最新价格
- **智能预警系统** - 设置价格阈值，触发时通过 Webhook 发送通知
- **新闻聚合** - 自动抓取并翻译加密货币相关新闻（支持中英文）
- **资产管理** - 记录持仓信息，实时计算盈亏
- **数据可视化** - ECharts 图表展示资产配置和价格走势
- **系统设置** - 动态配置推送 API 地址和鉴权 Token

## 🛠 技术栈

### 后端
- **Python 3.11+** - 主要编程语言
- **FastAPI 0.104.1** - 现代异步 Web 框架
- **SQLAlchemy 2.0** - ORM 框架
- **SQLite** - 数据库（可迁移至 PostgreSQL）
- **APScheduler** - 定时任务调度
- **HTTPX** - 异步 HTTP 客户端
- **Alembic** - 数据库迁移工具
- **PyJWT** - JWT 认证
- **Feedparser** - RSS 解析
- **Deep Translator** - 翻译服务

### 前端
- **Vue 3** - 前端框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **Element Plus** - UI 组件库
- **Pinia** - 状态管理
- **Vue Router** - 路由管理
- **Axios** - HTTP 客户端
- **ECharts** - 数据可视化

### 部署
- **Docker** + **Docker Compose** - 容器化部署
- **Nginx** - 反向代理和静态文件服务

## 📁 目录结构

```
crypto-info/
├── backend/                      # 后端服务
│   ├── app/
│   │   ├── api/                  # API 路由
│   │   │   ├── auth.py          # 认证接口
│   │   │   ├── cryptocurrencies.py # 币种管理
│   │   │   ├── alerts.py        # 预警管理
│   │   │   ├── assets.py        # 资产管理
│   │   │   ├── news.py          # 新闻接口
│   │   │   ├── dashboard.py     # 仪表盘
│   │   │   └── settings.py      # 系统设置
│   │   ├── models/              # 数据模型
│   │   │   ├── user.py
│   │   │   ├── cryptocurrency.py
│   │   │   ├── alert.py
│   │   │   ├── asset.py
│   │   │   ├── news.py
│   │   │   ├── news_source.py
│   │   │   └── system_setting.py
│   │   ├── services/            # 业务逻辑
│   │   │   ├── price_service.py # 价格获取
│   │   │   ├── alert_service.py # 预警引擎
│   │   │   ├── news_service.py  # 新闻抓取
│   │   │   └── notification_service.py # 通知服务
│   │   ├── tasks/               # 定时任务
│   │   │   └── scheduler.py
│   │   ├── utils/               # 工具函数
│   │   │   ├── security.py     # 安全工具
│   │   │   └── http_client.py  # HTTP 客户端
│   │   ├── database.py         # 数据库配置
│   │   ├── config.py           # 应用配置
│   │   └── main.py             # 应用入口
│   ├── alembic/                # 数据库迁移
│   ├── requirements.txt        # Python 依赖
│   └── Dockerfile              # 后端容器配置
├── frontend/                    # 前端应用
│   ├── src/
│   │   ├── api/                # API 封装
│   │   ├── components/         # 通用组件
│   │   ├── views/              # 页面组件
│   │   │   ├── Login.vue      # 登录页
│   │   │   ├── Dashboard.vue  # 仪表盘
│   │   │   ├── Alerts.vue     # 预警管理
│   │   │   ├── Assets.vue     # 资产管理
│   │   │   ├── News.vue       # 新闻中心
│   │   │   └── Settings.vue   # 系统设置
│   │   ├── router/            # 路由配置
│   │   ├── stores/            # 状态管理
│   │   └── utils/             # 工具函数
│   ├── Dockerfile             # 前端容器配置
│   └── package.json           # 前端依赖
├── nginx/                      # Nginx 配置
│   └── default.conf
├── docker-compose.yml          # Docker Compose 配置
├── .clinerules                 # CLI 执行规则
└── README.md                   # 项目文档
```

## 🚀 本地开发指南

### 环境要求

- Python 3.11+
- Node.js 18+
- npm 或 yarn

### 后端设置

1. **进入后端目录**
```bash
cd backend
```

2. **创建 Python 虚拟环境**
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **初始化数据库**
```bash
# 运行数据库迁移
alembic upgrade head

# 初始化数据（创建管理员账户和默认币种）
python -m app.init_db
```

5. **启动后端服务**
```bash
python run.py
```

后端服务将在 http://localhost:8000 启动

### 前端设置

1. **进入前端目录**
```bash
cd frontend
```

2. **安装依赖**
```bash
npm install
```

3. **启动开发服务器**
```bash
npm run dev
```

前端应用将在 http://localhost:5173 启动

### 默认管理员账户

- **邮箱**: admin@crypto.local
- **密码**: admin123

## 🐳 Docker 一键部署

### 使用 Docker Compose

1. **克隆项目**
```bash
git clone <repository-url>
cd crypto-info
```

2. **启动服务**
```bash
docker-compose up -d
```

3. **访问应用**
- 前端应用: http://localhost:3000
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

4. **查看日志**
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看后端日志
docker-compose logs -f backend

# 查看前端日志
docker-compose logs -f frontend
```

5. **停止服务**
```bash
docker-compose down
```

### 数据持久化

Docker 部署时，以下数据会被持久化：
- **数据库文件**: `./backend/crypto.db`
- **日志文件**: `./logs/backend/`

### 环境变量配置

在 `docker-compose.yml` 中可以配置以下环境变量：

```yaml
environment:
  - DATABASE_URL=sqlite:///./crypto.db  # 数据库连接
  - SECRET_KEY=your-secret-key          # JWT 密钥
  - DEBUG=false                         # 调试模式
```

## 🔧 配置说明

### 后端配置

配置文件: `backend/.env`

```env
# 数据库配置
DATABASE_URL=sqlite:///./crypto.db

# JWT 配置
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# API 配置
API_V1_STR=/api/v1
PROJECT_NAME=Crypto-info API

# CORS 配置
BACKEND_CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]
```

### 前端配置

配置文件: `frontend/src/utils/request.ts`

```typescript
const request = axios.create({
  baseURL: 'http://localhost:8000',  // 后端 API 地址
  timeout: 10000,
})
```

## 📊 API 文档

启动后端服务后，访问以下地址查看 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 主要 API 端点

- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户信息
- `GET /api/cryptocurrencies/` - 获取币种列表
- `GET /api/alerts/` - 获取预警规则
- `POST /api/alerts/` - 创建预警规则
- `GET /api/assets/` - 获取资产列表
- `POST /api/assets/` - 创建资产记录
- `GET /api/news/` - 获取新闻列表
- `GET /api/dashboard/summary` - 获取仪表盘数据
- `GET /api/settings/notification` - 获取通知设置
- `POST /api/settings/notification` - 创建通知设置

## 🔒 安全提示

### 敏感信息管理

- **推送密钥等敏感信息已转移至 Web 后台配置**
- 本代码库不包含任何私钥或敏感凭据
- 生产环境部署时请修改默认密码和密钥

### 生产环境建议

1. **修改默认密码**
   - 首次登录后立即修改管理员密码
   
2. **更改 SECRET_KEY**
   - 在 `.env` 文件中设置强密码作为 SECRET_KEY
   
3. **使用 HTTPS**
   - 生产环境配置 SSL 证书
   
4. **数据库备份**
   - 定期备份 SQLite 数据库文件
   
5. **防火墙配置**
   - 仅开放必要端口（80, 443）

## 🛠 开发指南

### 添加新币种

1. 在数据库 `cryptocurrencies` 表中添加新币种
2. 币种符号需要与交易所 API 一致（如 BTCUSDT）

### 添加新新闻源

1. 在数据库 `news_sources` 表中添加新闻源
2. 提供 RSS URL 和语言标识
3. 系统会自动抓取并翻译新闻

### 自定义通知渠道

系统支持通过 Webhook 发送通知，您可以：

1. 在系统设置中配置推送 API 地址
2. 实现自定义的 Webhook 接收端
3. 支持邮件、Telegram、微信等多种渠道

## 🐛 常见问题

### Q: 后端启动失败

A: 检查以下几点：
- Python 版本是否为 3.11+
- 是否安装了所有依赖
- 数据库文件权限是否正确

### Q: 前端无法连接后端

A: 检查以下几点：
- 后端服务是否正常运行
- 前端 `request.ts` 中的 baseURL 是否正确
- CORS 配置是否包含前端地址

### Q: 价格获取失败

A: 检查以下几点：
- 网络连接是否正常
- 币安/OKX API 是否可访问
- 币种符号是否正确

### Q: 新闻抓取失败

A: 检查以下几点：
- RSS 源是否可访问
- 网络连接是否正常
- 翻译服务是否可用

## 📝 更新日志

### v1.0.0 (2026-03-26)

- ✨ 初始版本发布
- ✨ 实时价格监控（币安/OKX）
- ✨ 智能预警系统
- ✨ 新闻聚合与翻译
- ✨ 资产管理
- ✨ 数据可视化仪表盘
- ✨ 系统设置功能
- ✨ Docker 容器化部署

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件至项目维护者

---

**Crypto-info** - 让数字货币投资更智能 🚀