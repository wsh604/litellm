# LiteLLM 外部认证关联设计

本文档描述了LiteLLM与外部认证系统的集成设计方案。

## 数据表设计

### 1. 外部用户映射表 (External_User_Mapping)

```prisma
model External_User_Mapping {
    id                String      @id @default(uuid())
    litellm_user_id  String      // LiteLLM内部用户ID
    external_user_id  String      // 外部系统用户ID
    provider         String      // 认证提供方(如:'wuban', 'github'等)
    metadata         Json?       // 额外的用户元数据
    created_at       DateTime    @default(now())
    updated_at       DateTime    @updatedAt

    // 关联到LiteLLM用户表
    litellm_user     LiteLLM_UserTable @relation(fields: [litellm_user_id], references: [user_id])

    @@unique([provider, external_user_id])
    @@map("external_user_mapping")
}
```

### 2. 认证提供方表 (Auth_Provider)

```prisma
model Auth_Provider {
    id              String    @id @default(uuid())
    provider_name   String    @unique  // 认证提供方名称
    provider_type   String    // 认证类型(jwt, oauth2等)
    config          Json      // 提供方配置信息
    is_active       Boolean   @default(true)
    created_at      DateTime  @default(now())
    updated_at      DateTime  @updatedAt

    @@map("auth_provider")
}
```

## 字段说明

### External_User_Mapping

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | String | 主键,UUID |
| litellm_user_id | String | LiteLLM用户ID |
| external_user_id | String | 外部系统用户ID |
| provider | String | 认证提供方标识 |
| metadata | Json | 存储额外的用户信息 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### Auth_Provider

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | String | 主键,UUID |
| provider_name | String | 提供方名称,唯一 |
| provider_type | String | 认证类型 |
| config | Json | 配置信息(密钥等) |
| is_active | Boolean | 是否启用 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

## 关联关系

- External_User_Mapping.litellm_user_id -> LiteLLM_UserTable.user_id (多对一)
- External_User_Mapping.provider -> Auth_Provider.provider_name (逻辑关联)


## 认证流程
    User->>ExternalAuth: 1. 登录外部系统
    ExternalAuth->>User: 2. 返回JWT token
    User->>LiteLLM: 3. 请求API(带JWT token)
    LiteLLM->>LiteLLM: 4. 验证JWT token
    LiteLLM->>Database: 5. 查找/创建用户映射
    Database->>LiteLLM: 6. 返回LiteLLM用户ID
    LiteLLM->>User: 7. 返回API响应
