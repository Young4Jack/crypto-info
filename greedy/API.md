# Crypto-info API 完整文档

> 数字货币价格监控和预警系统 - 完整 API 参考文档

## 基础信息

| 项目 | 说明 |
|------|------|
| **Base URL** | `http://<服务器IP>:8000` |
| **本地访问** | `http://localhost:8000` |
| **Swagger 文档** | `http://localhost:8000/docs` |
| **认证方式** | JWT Bearer Token |
| **Token 有效期** | 24 小时 (1440 分钟) |
| **数据格式** | JSON |
| **CORS** | 允许所有来源 |
| **时区** | Asia/Shanghai |

---

## 目录

1. [鉴权机制](#鉴权机制)
2. [通用错误响应](#通用错误响应)
3. [认证模块 (Auth)](#3-认证模块-auth)
4. [币种管理 (Cryptocurrencies)](#4-币种管理-cryptocurrencies)
5. [预警管理 (Alerts)](#5-预警管理-alerts)
6. [资产管理 (Assets)](#6-资产管理-assets)
7. [仪表盘 (Dashboard)](#7-仪表盘-dashboard)
8. [关注列表 (Watchlist)](#8-关注列表-watchlist)
9. [K线数据 (Klines)](#9-k线数据-klines)
10. [通知渠道管理 (Notification Channels)](#10-通知渠道管理-notification-channels)
11. [旧通知设置 (已废弃)](#11-旧通知设置-已废弃)
12. [API设置 (API Settings)](#12-api设置-api-settings)
13. [系统设置 (System Settings)](#13-系统设置-system-settings)
14. [预警历史 (Alert Histories)](#14-预警历史-alert-histories)
15. [账户管理 (Account)](#15-账户管理-account)
16. [价格搜索 (Price Search)](#16-价格搜索-price-search)
17. [健康检查与系统](#17-健康检查与系统)
18. [变更日志](#变更日志)
19. [快速调用示例](#快速调用示例)

---

## 变更日志

### 最近重大更新

| 日期 | 变更内容 |
|------|----------|
| 2024-04 | 新增价格搜索接口 `GET /api/price-search/`（需鉴权，支持主备 failover） |
| 2024-04 | 安全加固：通知设置、API设置接口添加认证保护 |
| 2024-04 | 新增系统设置 `base_url`、`backend_port`、`frontend_port`、`timezone` 公开字段 |
| 2024-04 | 修复密钥掩码覆盖 bug，GET 返回真实值 |
| 2024-04 | 预警引擎：修复5个已知问题（AlertHistory写入、死代码删除、方向文字修复、失败重试机制） |
| 2024-04 | 通知渠道重构：支持多渠道+多频道，预警级别独立选择 |
| 2024-04 | 旧通知推送设置废弃，统一使用渠道管理 API |

---

## 鉴权机制

### JWT Token 认证

**获取 Token：**
```bash
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your_password",
  "login_type": "email"
}
```

**成功响应 (200)：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**使用 Token：**
所有需要认证的接口，在请求头中添加：
```
Authorization: Bearer <your_access_token>
```

### 系统写操作认证

系统设置（`/api/system-settings/`）的写操作支持两种认证方式：
1. **Bearer Token**：与普通接口相同
2. **Shared Secret**：在请求头中添加 `X-API-Secret: <shared_secret>`

### 无需认证的接口（公开）

以下接口**不需要**任何认证即可访问：

| 接口 | 说明 |
|------|------|
| `GET /api/watchlist/public` | 公开关注列表 |
| `GET /api/watchlist/all` | 全部去重关注列表 |
| `GET /api/klines/{symbol}` | K线数据 |
| `GET /api/klines/watchlist/all` | 关注列表K线 |
| `WS /api/klines/ws/{symbol}` | 实时K线推送 |
| `GET /api/system-settings/public` | 公开系统设置 |
| `GET /` | 欢迎信息 |
| `GET /health` | 健康检查 |
| `GET /scheduler/status` | 定时任务状态 |

### 需要认证的接口（安全加固）

以下接口**必须**提供 `Authorization: Bearer <token>` 或 `X-Shared-Secret`：

| 接口 | 说明 |
|------|------|
| `GET /api/system-settings/` | 系统设置（完整，返回真实密钥） |
| `POST/PUT/DELETE /api/system-settings/` | 系统设置写操作 |
| `GET/POST/PUT/DELETE /api/settings/notification` | 通知设置（已废弃，使用渠道管理代替） |
| `GET/POST/PUT/DELETE /api/settings/notification-channels/` | 通知渠道管理（全部） |
| `GET/POST/PUT/DELETE /api/api-settings/` | API设置（全部） |
| 其他所有业务接口 | 币种、预警、资产、仪表盘、关注列表、预警历史、价格搜索 |

---

## 通用错误响应

### 401 未认证
```json
{
  "detail": "Not authenticated"
}
```

### 403 权限不足
```json
{
  "detail": "没有权限访问该资源"
}
```

### 404 资源不存在
```json
{
  "detail": "资源不存在"
}
```

### 500 服务器错误
```json
{
  "error": "服务器内部错误",
  "detail": "详细错误信息"
}
```

---

## 3. 认证模块 (Auth)

**前缀：** `/api/auth`

### 1.1 用户登录

```
POST /api/auth/login
```

**认证：** 不需要

**请求体：**
```json
{
  "email": "user@example.com",
  "password": "string",
  "captchaAnswer": 0,
  "captchaId": "string",
  "login_type": "email"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| email | string | 是 | 邮箱或用户名 |
| password | string | 是 | 密码 |
| captchaAnswer | int | 否 | 验证码答案 |
| captchaId | string | 否 | 验证码ID |
| login_type | string | 否 | "email" 或 "username" |

**成功响应 (200)：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**失败响应 (401)：**
```json
{
  "detail": "邮箱/用户名或密码错误"
}
```

### 1.2 获取当前用户信息

```
GET /api/auth/me
```

**认证：** 需要 `Authorization: Bearer <token>`

**成功响应 (200)：**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00"
}
```

### 1.3 获取验证码

```
GET /api/auth/captcha
```

**认证：** 不需要

**成功响应 (200)：**
```json
{
  "captcha_id": "uuid-string",
  "captcha_image": "base64_encoded_image",
  "enabled": true
}
```

### 1.4 验证验证码

```
POST /api/auth/verify-captcha?captcha_id=xxx&answer=123
```

**认证：** 不需要

**查询参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| captcha_id | string | 是 | 验证码ID |
| answer | int | 是 | 验证码答案 |

**成功响应 (200)：**
```json
{
  "valid": true
}
```

### 1.5 更新账户信息

```
PUT /api/auth/account
```

**认证：** 需要 `Authorization: Bearer <token>`

**请求体：**
```json
{
  "username": "new_username",
  "email": "new@example.com",
  "current_password": "old_password",
  "new_password": "new_password",
  "confirm_new_password": "new_password"
}
```

**成功响应 (200)：**
```json
{
  "success": true,
  "message": "账户信息已更新",
  "user": {
    "id": 1,
    "username": "new_username",
    "email": "new@example.com"
  }
}
```

---

## 4. 币种管理 (Cryptocurrencies)

**前缀：** `/api/cryptocurrencies`

**认证：** 所有接口均需要 `Authorization: Bearer <token>`

### 2.1 获取激活币种列表

```
GET /api/cryptocurrencies/
```

**成功响应 (200)：**
```json
[
  {
    "id": 1,
    "symbol": "BTCUSDT",
    "name": "BTC",
    "logo_url": null,
    "is_active": true,
    "created_at": "2024-01-01T00:00:00"
  }
]
```

### 2.2 获取所有币种（含非激活）

```
GET /api/cryptocurrencies/all
```

### 2.3 获取单个币种

```
GET /api/cryptocurrencies/{crypto_id}
```

**路径参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| crypto_id | int | 是 | 币种ID |

### 2.4 创建币种

```
POST /api/cryptocurrencies/?symbol=BTCUSDT&name=BTC&logo_url=xxx
```

**查询参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| symbol | string | 是 | 交易对符号 |
| name | string | 是 | 币种名称 |
| logo_url | string | 否 | Logo URL |

### 2.5 更新币种

```
PUT /api/cryptocurrencies/{crypto_id}?symbol=xxx&name=xxx&is_active=true
```

### 2.6 删除币种

```
DELETE /api/cryptocurrencies/{crypto_id}
```

**成功响应 (200)：**
```json
{
  "message": "币种已删除"
}
```

---

## 5. 预警管理 (Alerts)

**前缀：** `/api/alerts`

**认证：** 所有接口均需要 `Authorization: Bearer <token>`

### 3.1 获取预警列表

```
GET /api/alerts/
```

**成功响应 (200)：**
```json
[
  {
    "id": 1,
    "crypto_id": 1,
    "crypto_symbol": "BTCUSDT",
    "crypto_name": "BTC",
    "alert_type": "above",
    "threshold_price": 70000.0,
    "current_price": 69500.0,
    "is_active": true,
    "triggered_at": null,
    "created_at": "2024-01-01T00:00:00",
    "sort_order": 0,
    "base_price": 68000.0,
    "threshold_value": 70000.0,
    "is_continuous": false,
    "interval_minutes": 5,
    "max_notifications": 1,
    "notified_count": 0,
    "last_triggered_at": null
  }
]
```

**alert_type 枚举值：**
| 值 | 说明 |
|----|------|
| above | 价格超过阈值 |
| below | 价格低于阈值 |
| amplitude | 振幅预警 |
| percent_up | 涨幅预警 |
| percent_down | 跌幅预警 |

### 3.2 获取单个预警

```
GET /api/alerts/{alert_id}
```

### 3.3 创建预警

```
POST /api/alerts/
```

**请求体：**
```json
{
  "crypto_symbol": "BTCUSDT",
  "alert_type": "above",
  "threshold_price": 70000.0,
  "webhook_url": null,
  "base_price": 68000.0,
  "threshold_value": 70000.0,
  "is_continuous": false,
  "interval_minutes": 5,
  "max_notifications": 1,
  "notification_channel": "自建Webhook",
  "notification_group": "urgent"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| crypto_symbol | string | 是 | 交易对符号 |
| alert_type | string | 是 | 预警类型 |
| threshold_price | float | 是 | 阈值价格 |
| webhook_url | string | 否 | 通知URL（已废弃） |
| base_price | float | 否 | 基准价格 |
| threshold_value | float | 否 | 阈值 |
| is_continuous | bool | 否 | 是否连续触发 |
| interval_minutes | int | 否 | 触发间隔(分钟) |
| max_notifications | int | 否 | 最大通知次数 |
| notification_channel | string | 否 | 通知渠道名称 |
| notification_group | string | 否 | 通知频道名称 |

### 3.4 更新预警

```
PUT /api/alerts/{alert_id}
```

**请求体：**
```json
{
  "alert_type": "above",
  "threshold_price": 71000.0,
  "webhook_url": null,
  "is_active": true,
  "base_price": 68000.0,
  "threshold_value": 71000.0,
  "is_continuous": false,
  "interval_minutes": 10,
  "max_notifications": 5
}
```

### 3.5 批量更新排序

```
PUT /api/alerts/sort-order
```

**请求体：**
```json
{
  "items": [
    {"id": 1, "sort_order": 0},
    {"id": 2, "sort_order": 1}
  ]
}
```

### 3.6 删除单个预警

```
DELETE /api/alerts/{alert_id}
```

### 3.7 删除所有预警

```
DELETE /api/alerts/all
```

**成功响应 (200)：**
```json
{
  "message": "已删除 5 条预警规则"
}
```

---

## 6. 资产管理 (Assets)

**前缀：** `/api/assets`

**认证：** 所有接口均需要 `Authorization: Bearer <token>`

### 4.1 获取资产列表

```
GET /api/assets/
```

**成功响应 (200)：**
```json
[
  {
    "id": 1,
    "crypto_id": 1,
    "crypto_symbol": "BTCUSDT",
    "crypto_name": "BTC",
    "buy_price": 65000.0,
    "quantity": 0.5,
    "notes": "长期持有",
    "total_value": 32500.0,
    "current_price": 69500.0,
    "sort_order": 0,
    "created_at": "2024-01-01T00:00:00"
  }
]
```

### 4.2 获取单个资产

```
GET /api/assets/{asset_id}
```

### 4.3 创建资产

```
POST /api/assets/
```

**请求体：**
```json
{
  "crypto_symbol": "BTCUSDT",
  "buy_price": 65000.0,
  "quantity": 0.5,
  "notes": "长期持有"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| crypto_symbol | string | 是 | 交易对符号 |
| buy_price | float | 是 | 买入价格 |
| quantity | float | 是 | 数量 |
| notes | string | 否 | 备注 |

### 4.4 更新资产

```
PUT /api/assets/{asset_id}
```

**请求体：**
```json
{
  "buy_price": 66000.0,
  "quantity": 0.6,
  "notes": "追加仓位"
}
```

### 4.5 批量更新排序

```
PUT /api/assets/sort-order
```

### 4.6 删除单个资产

```
DELETE /api/assets/{asset_id}
```

### 4.7 删除所有资产

```
DELETE /api/assets/all
```

---

## 7. 仪表盘 (Dashboard)

**前缀：** `/api/dashboard`

**认证：** 所有接口均需要 `Authorization: Bearer <token>`

### 5.1 获取仪表盘综合数据

```
GET /api/dashboard/summary
```

**成功响应 (200)：**
```json
{
  "total_value": 100000.0,
  "total_profit_loss": 5000.0,
  "total_profit_loss_percentage": 5.26,
  "active_alerts_count": 3,
  "asset_allocation": [
    {
      "crypto_symbol": "BTCUSDT",
      "crypto_name": "BTC",
      "quantity": 0.5,
      "buy_price": 65000.0,
      "current_price": 69500.0,
      "holding_value": 34750.0,
      "buy_value": 32500.0,
      "profit_loss": 2250.0,
      "profit_loss_percentage": 6.92,
      "sort_order": 0,
      "created_at": "2024-01-01T00:00:00"
    }
  ],
  "watchlist": [
    {
      "id": 1,
      "crypto_symbol": "BTCUSDT",
      "crypto_name": "BTC",
      "current_price": 69500.0,
      "sort_order": 0
    }
  ],
  "alerts": [
    {
      "id": 1,
      "crypto_symbol": "BTCUSDT",
      "crypto_name": "BTC",
      "alert_type": "above",
      "threshold_price": 70000.0,
      "current_price": 69500.0,
      "is_active": true,
      "sort_order": 0
    }
  ],
  "latest_news": [],
  "summary": {
    "total_assets": 2,
    "total_cryptocurrencies": 2
  }
}
```

### 5.2 获取资产配置占比

```
GET /api/dashboard/allocation
```

**成功响应 (200)：**
```json
[
  {
    "name": "BTC",
    "symbol": "BTCUSDT",
    "value": 34750.0,
    "quantity": 0.5
  }
]
```

---

## 8. 关注列表 (Watchlist)

**前缀：** `/api/watchlist`

### 6.1 获取个人关注列表

```
GET /api/watchlist/
```

**认证：** 需要 `Authorization: Bearer <token>`

**成功响应 (200)：**
```json
[
  {
    "id": 1,
    "crypto_id": 1,
    "crypto_symbol": "BTCUSDT",
    "crypto_name": "BTC",
    "notes": "重点关注",
    "created_at": "2024-01-01T00:00:00",
    "current_price": 69500.0,
    "sort_order": 0,
    "is_public": false
  }
]
```

### 6.2 获取公开关注列表

```
GET /api/watchlist/public
```

**认证：** 不需要

**说明：** 返回所有用户的关注项，按币种去重

### 6.3 获取所有关注列表（去重）

```
GET /api/watchlist/all
```

**认证：** 不需要

### 6.4 创建关注项

```
POST /api/watchlist/
```

**认证：** 需要 `Authorization: Bearer <token>`

**请求体：**
```json
{
  "crypto_symbol": "BTCUSDT",
  "notes": "重点关注",
  "is_public": false
}
```

### 6.5 更新关注项

```
PUT /api/watchlist/{watchlist_id}
```

**请求体：**
```json
{
  "notes": "更新备注",
  "is_public": true
}
```

### 6.6 批量更新排序

```
PUT /api/watchlist/sort-order
```

**请求体：**
```json
{
  "items": [
    {"id": 1, "sort_order": 0},
    {"id": 2, "sort_order": 1}
  ]
}
```

### 6.7 删除单个关注项

```
DELETE /api/watchlist/{watchlist_id}
```

**成功响应 (200)：**
```json
{
  "message": "记录已删除"
}
// 或
{
  "message": "记录及冗余币种已删除"
}
```

### 6.8 删除所有关注项

```
DELETE /api/watchlist/all
```

---

## 9. K线数据 (Klines)

**前缀：** `/api/klines`

**认证：** 所有接口均**不需要**认证

### 7.1 获取单个币种K线数据

```
GET /api/klines/{symbol}?interval=1h&limit=100
```

**路径参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| symbol | string | 是 | 交易对符号，如 BTCUSDT |

**查询参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| interval | string | 1h | 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M |
| limit | int | 100 | 返回数量，最大1000 |

**成功响应 (200)：**
```json
{
  "success": true,
  "data": {
    "symbol": "BTCUSDT",
    "interval": "1h",
    "klines": [
      {
        "open_time": 1704067200000,
        "open": 69000.0,
        "high": 69500.0,
        "low": 68800.0,
        "close": 69200.0,
        "volume": 1234.56
      }
    ]
  }
}
```

**失败响应 (200)：**
```json
{
  "success": false,
  "error": "错误信息"
}
```

### 7.2 获取关注列表所有K线数据

```
GET /api/klines/watchlist/all?interval=1h&limit=50
```

**查询参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| interval | string | 1h | K线周期 |
| limit | int | 50 | 每个币种返回数量，最大500 |

**成功响应 (200)：**
```json
{
  "success": true,
  "data": {
    "BTCUSDT": {
      "name": "BTC",
      "klines": [...]
    },
    "ETHUSDT": {
      "name": "ETH",
      "klines": [...]
    }
  }
}
```

### 7.3 WebSocket 实时K线推送

```
WebSocket /api/klines/ws/{symbol}
```

**路径参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| symbol | string | 是 | 交易对符号 |

**推送数据格式：**
```json
{
  "open_time": 1704067200000,
  "open": 69000.0,
  "high": 69500.0,
  "low": 68800.0,
  "close": 69200.0,
  "volume": 1234.56
}
```

**说明：** 连接后会自动从币安WebSocket流获取实时数据并推送给客户端

---

## 10. 通知渠道管理 (Notification Channels)

**前缀：** `/api/settings/notification-channels`

**认证：** 所有接口均**需要** `Authorization: Bearer <token>`

### 8.1 获取所有通知渠道

```
GET /api/settings/notification-channels/
```

**成功响应 (200)：**
```json
[
  {
    "name": "自建Webhook",
    "api_url": "https://push.gosu.cc/push/jacket",
    "auth_token": "7E4DBBD5A47D61252C6D0FB4BE9770DF",
    "is_default": true,
    "default_group": "yes",
    "groups": ["yes", "urgent", "test"]
  },
  {
    "name": "短信通知",
    "api_url": "https://sms-api.example.com/send",
    "auth_token": "",
    "is_default": false,
    "default_group": "default",
    "groups": ["default"]
  }
]
```

### 8.2 获取默认渠道

```
GET /api/settings/notification-channels/default
```

### 8.3 创建通知渠道

```
POST /api/settings/notification-channels/
```

**请求体：**
```json
{
  "name": "短信通知",
  "api_url": "https://sms-api.example.com/send",
  "auth_token": "",
  "is_default": false,
  "default_group": "default",
  "groups": ["default"]
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 渠道名称，唯一 |
| api_url | string | 是 | Webhook 推送地址 |
| auth_token | string | 否 | 认证令牌 |
| is_default | bool | 否 | 是否为默认渠道 |
| default_group | string | 否 | 默认频道名 |
| groups | string[] | 否 | 可用频道列表 |

### 8.4 更新通知渠道

```
PUT /api/settings/notification-channels/{channel_name}
```

**路径参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| channel_name | string | 是 | 渠道名称（原始名称） |

**请求体（所有字段可选）：**
```json
{
  "name": "新名称",
  "api_url": "https://new-url.com",
  "auth_token": "new_token",
  "is_default": true,
  "default_group": "urgent",
  "groups": ["yes", "urgent"]
}
```

### 8.5 删除通知渠道

```
DELETE /api/settings/notification-channels/{channel_name}
```

**注意：** 不能删除唯一的默认渠道

### 8.6 测试通知渠道

```
POST /api/settings/notification-channels/{channel_name}/test
```

**成功响应 (200)：**
```json
{
  "success": true,
  "message": "渠道 '自建Webhook' 测试成功",
  "status_code": 200
}
```

---

## 11. 旧通知设置 (已废弃)

**前缀：** `/api/settings`

**状态：** ⚠️ 已废弃，请使用 [通知渠道管理 API](#10-通知渠道管理-notification-channels)

## 12. API设置 (API Settings)

**前缀：** `/api/api-settings`

**认证：** 所有接口均**需要** `Authorization: Bearer <token>`

### 12.1 获取API设置

```
GET /api/api-settings/
```

**成功响应 (200)：**
```json
{
  "primary_api_url": "https://www.okx.com",
  "backup_api_url": "https://api.binance.com",
  "api_key": "",
  "api_secret": ""
}
```

### 12.2 创建/更新API设置

```
POST /api/api-settings/
```

### 12.3 测试主API

```
POST /api/api-settings/test-primary
```

### 12.4 测试备用API

```
POST /api/api-settings/test-backup
```

---

## 13. 系统设置 (System Settings)

**前缀：** `/api/system-settings`

### 13.1 获取系统设置（完整，返回真实密钥）

```
GET /api/system-settings/
```

**认证：** 需要 `Authorization: Bearer <token>` 或 `X-Shared-Secret: <secret>`

**成功响应 (200)：**
```json
{
  "refresh_interval": 8,
  "enable_captcha": false,
  "site_title": "CryptoMSG",
  "site_description": "数字货币价格监控和预警系统",
  "base_url": "http://192.168.31.77:5173",
  "log_level": "INFO",
  "enable_logging": true,
  "default_dark_mode": false,
  "api_shared_secret": "your_real_secret_value",
  "timezone": "Asia/Shanghai",
  "backend_port": 8000,
  "frontend_port": 5173
}
```

> **注意：** 此接口返回真实密钥值（非掩码），因为前端编辑表单需要完整值进行保存操作。

### 13.2 获取公开系统设置

```
GET /api/system-settings/public
```

**认证：** 不需要

**成功响应 (200)：**
```json
{
  "site_title": "CryptoMSG",
  "site_description": "数字货币价格监控和预警系统",
  "base_url": "http://192.168.31.77:5173",
  "refresh_interval": 8,
  "default_dark_mode": false,
  "backend_port": 8000,
  "frontend_port": 5173,
  "timezone": "Asia/Shanghai",
  "current_pricing_currency": "CNY",
  "available_currencies": ["USD", "CNY", "EUR", "JPY"],
  "exchange_rates": {
    "CNY": 6.84,
    "EUR": 0.86,
    "JPY": 158.5
  },
  "exchange_rates_date": "2026-04-09"
}
```

### 13.3 创建系统设置

```
POST /api/system-settings/
```

**认证：** 需要 `Authorization: Bearer <token>` 或 `X-API-Secret: <secret>`

**请求体：**
```json
{
  "refresh_interval": 8,
  "enable_captcha": false,
  "site_title": "CryptoMSG",
  "site_description": "数字货币价格监控和预警系统",
  "base_url": "http://192.168.31.77:5173",
  "log_level": "INFO",
  "enable_logging": true,
  "default_dark_mode": false,
  "api_shared_secret": "your_secret",
  "timezone": "Asia/Shanghai",
  "current_pricing_currency": "CNY",
  "available_currencies": ["USD", "CNY", "EUR", "JPY"]
}
```

### 13.4 更新系统设置

```
PUT /api/system-settings/
```

**认证：** 需要 `Authorization: Bearer <token>` 或 `X-API-Secret: <secret>`

**请求体（所有字段可选，只更新提供的字段）：**
```json
{
  "base_url": "http://192.168.31.77:5173",
  "site_title": "新标题",
  "refresh_interval": 10
}
```

**可更新字段：**
| 字段 | 类型 | 说明 |
|------|------|------|
| refresh_interval | int | 刷新间隔（秒） |
| enable_captcha | bool | 是否启用验证码 |
| site_title | string | 网站标题 |
| site_description | string | 网站描述 |
| base_url | string | 应用基础URL |
| log_level | string | 日志级别 (DEBUG/INFO/WARNING/ERROR) |
| enable_logging | bool | 是否启用日志 |
| default_dark_mode | bool | 默认暗黑模式 |
| api_shared_secret | string | API共享密钥 |
| timezone | string | 时区 |
| current_pricing_currency | string | 当前计价货币 (USD/CNY/EUR/JPY) |
| available_currencies | array | 支持的货币列表 |

### 13.5 删除系统设置

```
DELETE /api/system-settings/
```

**认证：** 需要 `Authorization: Bearer <token>` 或 `X-API-Secret: <secret>`

### 13.6 手动刷新汇率

```
POST /api/system-settings/refresh-exchange-rates
```

**认证：** 需要 `Authorization: Bearer <token>` 或 `X-Shared-Secret: <secret>`

**说明：** 强制重新获取汇率数据。汇率每天自动更新一次，此接口用于手动刷新。

**成功响应 (200)：**
```json
{
  "exchange_rates": {
    "CNY": 6.84,
    "EUR": 0.86,
    "JPY": 158.5
  },
  "exchange_rates_date": "2026-04-09"
}
```

---

## 14. 预警历史 (Alert Histories)

**前缀：** `/api/alert-histories`

**认证：** 所有接口均需要 `Authorization: Bearer <token>`

### 14.1 获取预警历史列表

```
GET /api/alert-histories/?skip=0&limit=50&alert_id=1
```

**查询参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| skip | int | 0 | 跳过的记录数 |
| limit | int | 50 | 返回的记录数 |
| alert_id | int | null | 按预警ID过滤 |

**成功响应 (200)：**
```json
[
  {
    "id": 1,
    "alert_id": 1,
    "crypto_symbol": "BTCUSDT",
    "crypto_name": "BTC",
    "alert_type": "above",
    "threshold_price": 70000.0,
    "trigger_price": 70100.0,
    "status": "triggered",
    "notification_sent": true,
    "created_at": "2024-01-01T00:00:00"
  }
]
```

### 14.2 获取单条预警历史

```
GET /api/alert-histories/{history_id}
```

### 14.3 删除单条预警历史

```
DELETE /api/alert-histories/{history_id}
```

### 14.4 批量删除预警历史

```
DELETE /api/alert-histories/?alert_id=1
```

---

## 15. 账户管理 (Account)

**前缀：** `/api/auth`

**认证：** 所有接口均需要 `Authorization: Bearer <token>`

### 15.1 获取账户信息

```
GET /api/auth/account
```

**成功响应 (200)：**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00"
}
```

### 15.2 更新账户信息

```
PUT /api/auth/account
```

**请求体：**
```json
{
  "email": "new@example.com",
  "current_password": "old_password",
  "new_password": "new_password"
}
```

---

## 16. 价格搜索 (Price Search)

**前缀：** `/api/price-search`

**认证：** 需要 `Authorization: Bearer <token>`

### 16.1 搜索币种实时价格

```
GET /api/price-search/?symbol=BTC
```

**查询参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| symbol | string | 是 | 交易对符号（支持容错：填 `btc` 自动转为 `BTCUSDT`） |

**成功响应 (200)：**
```json
{
  "symbol": "BTCUSDT",
  "name": "BTC",
  "display_name": "Bitcoin",
  "price": 84321.50,
  "source": "https://www.okx.com"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| symbol | string | 标准化后的交易对符号 |
| name | string | 币种简称 |
| display_name | string | 币种全称 |
| price | float | 实时价格 |
| source | string | 数据来源 API 地址 |

**Failover 机制：**
1. 优先使用 `config.json` 中配置的 `primary_api_url`
2. 主 API 失败时切换到 `backup_api_url`
3. 主备均失败时使用默认 API（OKX → Binance）

**失败响应 (502)：**
```json
{
  "detail": "无法获取 BTCUSDT 的价格，请检查网络或 API 配置"
}
```

**失败响应 (400)：**
```json
{
  "detail": "交易对符号不能为空"
}
```

**说明：**
- 如果币种不在数据库中，会自动创建币种记录
- 支持的交易对后缀：USDT、USDC、BTC、ETH、FDUSD
- 输入不区分大小写，自动转大写

---

## 17. 健康检查与系统

### 17.1 根路径

```
GET /
```

**成功响应 (200)：**
```json
{
  "message": "Welcome to Crypto-info API"
}
```

### 17.2 健康检查

```
GET /health
```

**成功响应 (200)：**
```json
{
  "status": "healthy",
  "message": "Crypto-info API is running",
  "version": "1.0.0"
}
```

### 17.3 定时任务调度器状态

```
GET /scheduler/status
```

---

## 快速调用示例

### 1. 登录获取 Token

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "admin123", "login_type": "email"}'
```

### 2. 使用 Token 访问受保护接口

```bash
curl -X GET http://localhost:8000/api/watchlist/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

### 3. 访问公开接口（无需 Token）

```bash
curl -X GET http://localhost:8000/api/watchlist/public
```

### 4. 创建新的关注项

```bash
curl -X POST http://localhost:8000/api/watchlist/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{"crypto_symbol": "BTCUSDT", "notes": "重点关注"}'
```

### 5. 获取K线数据

```bash
curl -X GET "http://localhost:8000/api/klines/BTCUSDT?interval=1h&limit=100"
```

### 6. 获取关注列表所有K线数据

```bash
curl -X GET "http://localhost:8000/api/klines/watchlist/all?interval=1d&limit=50"
```

### 7. 获取仪表盘综合数据

```bash
curl -X GET http://localhost:8000/api/dashboard/summary \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

### 8. 创建预警规则

```bash
curl -X POST http://localhost:8000/api/alerts/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{
    "crypto_symbol": "BTCUSDT",
    "alert_type": "above",
    "threshold_price": 70000.0,
    "is_continuous": false,
    "interval_minutes": 5,
    "max_notifications": 1
  }'
```

### 9. 搜索币种实时价格

```bash
# 搜索 BTC（自动补齐为 BTCUSDT）
curl "http://localhost:8000/api/price-search/?symbol=btc" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."

# 搜索完整交易对
curl "http://localhost:8000/api/price-search/?symbol=ETHUSDT" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

---

## 注意事项

1. **Token 有效期**：默认 1440 分钟（24小时），过期后需重新登录
2. **时区设置**：系统默认使用 `Asia/Shanghai` 时区
3. **价格数据源**：默认使用 OKX 作为主数据源，Binance 作为备用
4. **数据库**：使用 SQLite，文件位于 `backend/crypto.db`
5. **CORS**：开发环境允许所有来源，生产环境建议限制
6. **WebSocket**：支持实时K线数据推送，连接币安WebSocket流
7. **自动创建币种**：在创建关注项、预警、资产、价格搜索时，如果币种不存在会自动创建
8. **价格搜索 Failover**：`GET /api/price-search/` 支持主备 API 自动切换，所有 API 地址从 `config.json` 读取

---

## 已知问题

1. **路由冲突**：`PUT /api/auth/account` 在 `auth.py` 和 `account.py` 中都有定义，`account.py` 的版本可能被覆盖无法访问
2. **安全风险（已修复）**：通知设置和API设置接口现已全部需要认证
3. **数据库**：使用 SQLite，高并发场景建议切换到 PostgreSQL 或 MySQL
4. **价格搜索**：每次请求都会实时请求交易所 API，高频率调用可能触发交易所限流
