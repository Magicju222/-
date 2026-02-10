# 第三阶段：API 接口规范

为了规范前后端交互，本系统遵循 RESTful API 设计原则。
后端服务将使用 FastAPI 开发，并自动生成 `/docs` (Swagger UI) 文档。

## 1. 基础约定

*   **Base URL**: `/api/v1`
*   **Content-Type**: `application/json`
*   **Authentication**: Bearer Token (JWT from Supabase Auth)
    *   Header: `Authorization: Bearer <token>`
*   **Date Format**: ISO 8601 (`YYYY-MM-DDTHH:mm:ssZ`)

## 2. 响应格式 (Standard Response)

所有接口（除文件下载外）统一返回如下 JSON 结构：

```json
{
  "code": 200,          // 业务状态码 (200=成功, 400=错误, 401=未授权, 500=系统错误)
  "message": "success", // 提示信息
  "data": { ... }       // 业务数据
}
```

## 3. 核心接口定义

### 3.1 认证与用户 (Auth & Users)

| Method | Endpoint | Description | Permission |
| :--- | :--- | :--- | :--- |
| `GET` | `/users/me` | 获取当前登录用户信息 | Login Required |
| `GET` | `/users` | 获取用户列表 (支持分页, 搜索) | Admin |
| `GET` | `/users/{id}` | 获取特定用户详情 | Admin |
| `POST` | `/users/{id}/ban` | 封禁用户 | Admin |
| `POST` | `/users/{id}/unban` | 解封用户 | Admin |
| `PUT` | `/users/{id}/role` | 修改用户角色 | Super Admin |

### 3.2 数据清洗 (Cleaning)

*注：清洗的核心逻辑在 Streamlit 中，但可以通过 API 暴露给外部调用，或用于记录日志。*

| Method | Endpoint | Description | Permission |
| :--- | :--- | :--- | :--- |
| `POST` | `/clean/upload` | 上传文件并清洗 (API模式) | Login Required |
| `GET` | `/clean/logs` | 获取清洗日志列表 | Admin |
| `GET` | `/clean/logs/stats` | 获取清洗统计数据 (Dashboard用) | Admin |

### 3.3 系统配置 (Config)

| Method | Endpoint | Description | Permission |
| :--- | :--- | :--- | :--- |
| `GET` | `/config` | 获取所有系统配置 | Admin |
| `PUT` | `/config` | 批量更新配置 | Admin |
| `GET` | `/config/public` | 获取公开配置 (如公告) | Public |

### 3.4 审计 (Audit)

| Method | Endpoint | Description | Permission |
| :--- | :--- | :--- | :--- |
| `GET` | `/audit/logs` | 获取管理员操作日志 | Super Admin |

## 4. 错误码定义

| Code | Message | Description |
| :--- | :--- | :--- |
| 200 | Success | 成功 |
| 400 | Bad Request | 参数错误 |
| 401 | Unauthorized | Token 无效或过期 |
| 403 | Forbidden | 权限不足 (如普通用户访问管理接口) |
| 404 | Not Found | 资源不存在 |
| 429 | Too Many Requests | 请求频率过高 |
| 500 | Internal Server Error | 服务器内部错误 |

## 5. 接口示例

### 获取用户列表
`GET /api/v1/users?page=1&size=10&keyword=test`

Response:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 50,
    "items": [
      {
        "id": "uuid-123",
        "email": "user@example.com",
        "nickname": "TestUser",
        "role": "user",
        "status": "active",
        "created_at": "2024-01-01T12:00:00Z"
      }
    ]
  }
}
```
