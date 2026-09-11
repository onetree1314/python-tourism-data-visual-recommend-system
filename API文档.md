# 旅游数据分析系统 API 文档

## 基础信息

- **Base URL**: `http://localhost:5000`
- **认证方式**: JWT Token (Bearer Token)
- **响应格式**: JSON

## 通用响应格式

```json
{
  "code": 200,
  "message": "成功",
  "data": {}
}
```

---

## 1. 认证模块 (Auth)

### 1.1 用户注册
- **接口**: `POST /api/auth/register`
- **权限**: 无需认证
- **请求体**:
```json
{
  "username": "user",
  "password": "123456",
  "email": "user@example.com"
}
```
- **响应**:
```json
{
  "code": 200,
  "message": "注册成功",
  "data": {
    "id": 1,
    "username": "user",
    "email": "user@example.com",
    "role": "user"
  }
}
```

### 1.2 用户登录
- **接口**: `POST /api/auth/login`
- **权限**: 无需认证
- **请求体**:
```json
{
  "username": "admin",
  "password": "admin123"
}
```
- **响应**:
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "user": {
      "id": 1,
      "username": "admin",
      "role": "admin",
      "email": "admin@tourism.com"
    },
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

### 1.3 获取当前用户信息
- **接口**: `GET /api/auth/info`
- **权限**: 需要登录
- **Headers**: `Authorization: Bearer {token}`
- **响应**:
```json
{
  "code": 200,
  "data": {
    "id": 1,
    "username": "admin",
    "role": "admin",
    "email": "admin@tourism.com"
  }
}
```

### 1.4 用户登出
- **接口**: `POST /api/auth/logout`
- **权限**: 需要登录
- **响应**:
```json
{
  "code": 200,
  "message": "登出成功"
}
```

### 1.5 刷新Token
- **接口**: `POST /api/auth/refresh`
- **权限**: 需要refresh_token
- **响应**:
```json
{
  "code": 200,
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

---

## 2. 景点模块 (Attractions)

### 2.1 获取景点列表
- **接口**: `GET /api/attractions/list`
- **权限**: 无需认证
- **查询参数**:
  - `page`: 页码（默认1）
  - `page_size`: 每页数量（默认20）
  - `keyword`: 搜索关键词
  - `city`: 城市筛选
  - `min_score`: 最低评分
  - `is_free`: 是否免费（true/false）
  - `sort_by`: 排序方式（heat_score/comment_score/comment_count）
- **响应**:
```json
{
  "code": 200,
  "data": {
    "total": 100,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": 1,
        "poi_id": "B0FFFAB6RY",
        "poi_name": "西湖",
        "city": "杭州",
        "comment_score": 4.8,
        "comment_count": 5000,
        "heat_score": 9500,
        "tag_list": "自然风光,5A景区",
        "price": "免费",
        "is_free": true
      }
    ]
  }
}
```

### 2.2 获取景点详情
- **接口**: `GET /api/attractions/{poi_id}`
- **权限**: 可选登录（登录后记录浏览历史）
- **响应**: 返回景点完整信息

### 2.3 获取城市列表
- **接口**: `GET /api/attractions/cities`
- **权限**: 无需认证
- **响应**:
```json
{
  "code": 200,
  "data": [
    {
      "city": "杭州",
      "count": 150
    }
  ]
}
```

### 2.4 添加收藏
- **接口**: `POST /api/attractions/favorite`
- **权限**: 需要登录
- **请求体**:
```json
{
  "poi_id": "B0FFFAB6RY"
}
```

### 2.5 取消收藏
- **接口**: `DELETE /api/attractions/favorite/{poi_id}`
- **权限**: 需要登录

### 2.6 获取收藏列表
- **接口**: `GET /api/attractions/favorites`
- **权限**: 需要登录
- **查询参数**: `page`, `page_size`

### 2.7 获取浏览历史
- **接口**: `GET /api/attractions/history`
- **权限**: 需要登录
- **查询参数**: `page`, `page_size`

---

## 3. 推荐模块 (Recommendation)

### 3.1 智能推荐
- **接口**: `POST /api/recommendation/intelligent`
- **权限**: 需要登录
- **请求体**:
```json
{
  "preferences": {
    "budget": "中等",
    "interests": ["自然风光", "历史文化"]
  },
  "limit": 10
}
```
- **响应**:
```json
{
  "code": 200,
  "data": {
    "recommendations": [...],
    "ai_analysis": "基于您的浏览历史和偏好..."
  }
}
```

### 3.2 相似景点推荐
- **接口**: `GET /api/recommendation/similar/{poi_id}`
- **权限**: 无需认证

### 3.3 热门推荐
- **接口**: `GET /api/recommendation/hot`
- **权限**: 无需认证
- **查询参数**: `limit`（默认20）

### 3.4 生成旅游规划
- **接口**: `POST /api/recommendation/travel-plan`
- **权限**: 需要登录
- **请求体**:
```json
{
  "destination": "杭州",
  "days": 3,
  "preferences": "喜欢自然风光和历史文化"
}
```
- **响应**:
```json
{
  "code": 200,
  "data": {
    "plan": "第一天：...\n第二天：...",
    "attractions": [...]
  }
}
```

---

## 4. 数据分析模块 (Analytics)

### 4.1 数据概览
- **接口**: `GET /api/analytics/overview`
- **权限**: 无需认证
- **响应**:
```json
{
  "code": 200,
  "data": {
    "total_attractions": 2476,
    "total_cities": 17,
    "avg_score": 2.65,
    "total_comments": 415895
  }
}
```

### 4.2 评分分布分析
- **接口**: `GET /api/analytics/score-distribution`
- **权限**: 无需认证
- **响应**:
```json
{
  "code": 200,
  "data": {
    "distribution": [
      {"range": "0-2分", "count": 100},
      {"range": "2-3分", "count": 200}
    ],
    "avg_score": 4.2,
    "top_attractions": [...]
  }
}
```

### 4.3 城市分析
- **接口**: `GET /api/analytics/city-analysis`
- **权限**: 无需认证
- **响应**:
```json
{
  "code": 200,
  "data": {
    "city_data": [
      {
        "city": "杭州",
        "count": 150,
        "avg_score": 4.5,
        "avg_heat": 8500
      }
    ],
    "level_stats": [...]
  }
}
```

### 4.4 价格销量分析
- **接口**: `GET /api/analytics/price-sales-analysis`
- **权限**: 无需认证

### 4.5 标签分析（词云）
- **接口**: `GET /api/analytics/tag-analysis`
- **权限**: 无需认证
- **响应**:
```json
{
  "code": 200,
  "data": {
    "wordcloud_data": [
      {"name": "自然风光", "value": 500},
      {"name": "历史文化", "value": 300}
    ],
    "total_tags": 5000,
    "unique_tags": 200
  }
}
```

---

## 5. 管理员模块 (Admin)

**所有接口都需要管理员权限**

### 5.1 获取用户列表
- **接口**: `GET /api/admin/users`
- **权限**: 管理员
- **查询参数**: `page`, `page_size`, `keyword`

### 5.2 更新用户信息
- **接口**: `PUT /api/admin/users/{user_id}`
- **权限**: 管理员
- **请求体**:
```json
{
  "status": true,
  "role": "user",
  "email": "new@example.com"
}
```

### 5.3 删除用户
- **接口**: `DELETE /api/admin/users/{user_id}`
- **权限**: 管理员

### 5.4 获取景点列表（管理）
- **接口**: `GET /api/admin/attractions`
- **权限**: 管理员
- **查询参数**: `page`, `page_size`, `keyword`

### 5.5 删除景点
- **接口**: `DELETE /api/admin/attractions/{attraction_id}`
- **权限**: 管理员

### 5.6 获取爬虫任务记录
- **接口**: `GET /api/admin/spider-tasks`
- **权限**: 管理员

### 5.7 获取系统日志
- **接口**: `GET /api/admin/logs`
- **权限**: 管理员

### 5.8 获取统计数据
- **接口**: `GET /api/admin/statistics`
- **权限**: 管理员
- **响应**:
```json
{
  "code": 200,
  "data": {
    "total_users": 100,
    "active_users": 95,
    "total_attractions": 2476,
    "today_users": 5,
    "today_attractions": 10,
    "login_trend": [
      {"date": "2026-01-21", "count": 50}
    ]
  }
}
```

---

## 6. 文件上传模块 (Upload)

### 6.1 上传图片
- **接口**: `POST /api/upload/image`
- **权限**: 需要登录
- **请求**: multipart/form-data
- **字段**: `file`
- **支持格式**: png, jpg, jpeg, gif, webp

### 6.2 上传头像
- **接口**: `POST /api/upload/avatar`
- **权限**: 需要登录
- **请求**: multipart/form-data
- **字段**: `file`

---

## 错误码说明

- `200`: 成功
- `400`: 请求参数错误
- `401`: 未认证或认证失败
- `403`: 权限不足
- `404`: 资源不存在
- `500`: 服务器内部错误

---

## 测试账号

- **管理员**: admin / admin123
- **普通用户**: user / 123456
