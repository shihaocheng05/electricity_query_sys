# API 使用说明

## 基础信息

- **Base URL**: `http://localhost:5000/api/v1`
- **认证方式**: Bearer Token (JWT)
- **Content-Type**: `application/json`
- **权限系统**: 细粒度权限控制（详见 [权限编码文档](./PERMISSION_CODES.md)）

## 权限系统简介

系统采用三层级权限模型：

1. **超级管理员(SUPER_ADMIN)**: 拥有全部权限，无需权限检查
2. **片区管理员(AREA_ADMIN)**: 拥有被赋予的权限，可操作本片区内的资源
3. **普通居民(RESIDENT)**: 拥有被赋予的权限，仅可操作自己的资源

所有需要权限校验的接口都会在装饰器中指定 `require_permit` 参数，系统会自动检查用户是否拥有相应权限。

## API 概览

系统共包含 **6大模块**，**48+个API接口**：

| 模块 | 接口数量 | 主要功能 |
|------|---------|---------|
| 用户模块 (`/user`) | 13个 | 注册、登录、用户信息管理、电表绑定、密码重置 |
| 电表模块 (`/meter`) | 8个 | 电表安装、状态管理、维修、查询、空闲电表查询 |
| 账单模块 (`/bill`) | 5个 | 账单生成、支付、查询、详情 |
| 用电数据模块 (`/usage`) | 4个 | IoT数据上传、数据聚合、查询、人工录入 |
| 查询分析模块 (`/query`) | 4个 | 统计概览、用户分析、片区分析、用电排名 |
| 系统管理模块 (`/system`) | 11个 | 电价策略、片区管理、用户角色管理 |
| 通知模块 (`/notification`) | 5个 | 通知创建、发送、查询、统计 |

### 接口快速参考

<details>
<summary>点击展开完整接口列表</summary>

#### 用户模块 (13个接口)
- `POST /user/register` - 用户注册
- `POST /user/login` - 用户登录
- `POST /user/refresh-token` - 刷新Token
- `GET /user/info` - 获取用户信息
- `PUT /user/update` - 更新用户信息
- `POST /user/bind-meter` - 绑定电表
- `POST /user/unbind-meter` - 解绑电表
- `GET /user/meters` - 查询绑定电表
- `POST /user/logout` - 退出登录
- `POST /user/change-password` - 修改密码
- `POST /user/send-reset-code` - 发送重置密码验证码
- `POST /user/reset-password` - 重置密码
- `GET /user/list` - 用户列表（管理员）

#### 电表模块 (8个接口)
- `POST /meter/install` - 安装电表（管理员）
- `PUT /meter/update-status` - 更新电表状态（管理员）
- `POST /meter/add-record` - 添加操作记录（管理员）
- `POST /meter/repair` - 电表维修（管理员）
- `POST /meter/validate-reading` - 验证电表读数（管理员）
- `GET /meter/query` - 查询电表列表
- `GET /meter/records/<meter_id>` - 查询电表操作记录
- `GET /meter/available` - 查询空闲电表列表（管理员）

#### 账单模块 (5个接口)
- `POST /bill/create` - 生成账单（管理员）
- `POST /bill/pay` - 支付账单
- `GET /bill/query` - 查询账单列表
- `GET /bill/detail/<bill_id>` - 获取账单详情
- `GET /bill/summary` - 账单汇总（管理员）

#### 用电数据模块 (4个接口)
- `POST /usage/iot-upload` - IoT数据上传
- `POST /usage/aggregate` - 数据聚合（管理员）
- `GET /usage/query` - 查询用电数据
- `POST /usage/manual-input` - 人工录入数据（管理员）

#### 查询分析模块 (4个接口)
- `GET /query/statistics/summary` - 统计概览（用户/片区）
- `GET /query/analyze/user` - 个人用电分析
- `GET /query/analyze/region` - 片区用电分析（管理员）
- `GET /query/ranking` - 用电排名

#### 系统管理模块 (11个接口)
- `POST /system/price-policy/create` - 创建电价策略（超管）
- `PUT /system/price-policy/update` - 更新电价策略（超管）
- `GET /system/price-policy/list` - 获取电价策略列表
- `DELETE /system/price-policy/<policy_id>` - 删除电价策略（超管）
- `POST /system/region/create` - 创建片区（超管）
- `PUT /system/region/update` - 更新片区（超管）
- `GET /system/region/list` - 获取片区列表
- `DELETE /system/region/<region_id>` - 删除片区（超管）
- `PUT /system/user/update-role` - 更新用户角色（超管）
- `GET /system/logs` - 查询系统日志（管理员）
- `GET /system/logs/abnormal` - 查询异常日志（管理员）

#### 通知模块 (5个接口)
- `POST /notification/create` - 创建通知（管理员）
- `POST /notification/send` - 发送通知（管理员）
- `GET /notification/query` - 查询通知
- `GET /notification/statistics` - 通知统计（管理员）
- `PUT /notification/update-status` - 更新通知状态

</details>

## 目录

1. [用户模块接口](#用户模块接口)
2. [电表模块接口](#电表模块接口)
3. [账单模块接口](#账单模块接口)
4. [用电数据模块接口](#用电数据模块接口)
5. [查询分析模块接口](#查询分析模块接口)
6. [系统管理模块接口](#系统管理模块接口)
7. [通知模块接口](#通知模块接口)
8. [错误响应格式](#错误响应格式)
9. [参数校验说明](#参数校验说明)
10. [中间件说明](#中间件说明)
11. [权限编码参考](#权限编码参考)

---

## 用户模块接口 (`/api/v1/user`)

### 1. 用户注册

**接口**: `POST /api/v1/user/register`

**请求头**: 无需认证

**请求体**:
```json
{
    "mail": "user@example.com",
    "password": "password123",
    "real_name": "张三",
    "idcard": "110101199001011234",
    "region_id": 1
}
```

**响应示例**:
```json
{
    "success": true,
    "message": "注册成功",
    "data": {
        "user_id": 1,
        "mail": "user@example.com",
        "real_name": "张三",
        "region_id": 1,
        "role": "RESIDENT",
        "create_time": "2025-12-18 10:00:00"
    }
}
```

---

### 2. 用户登录

**接口**: `POST /api/v1/user/login`

**请求头**: 无需认证

**请求体**:
```json
{
    "mail": "user@example.com",
    "password": "password123"
}
```

**响应示例**:
```json
{
    "success": true,
    "message": "登录成功",
    "data": {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "user_info": {
            "user_id": 1,
            "phone": null,
            "real_name": "张三",
            "role": "RESIDENT",
            "status": "NORMAL"
        }
    }
}
```

---

### 3. 刷新Token

**接口**: `POST /api/v1/user/refresh-token`

**请求头**: 无需认证

**请求体**:
```json
{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**响应示例**:
```json
{
    "success": true,
    "message": "token刷新成功",
    "data": {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
}
```

---

### 4. 获取用户信息

**接口**: `GET /api/v1/user/info`

**请求头**: 
```
Authorization: Bearer <token>
```

**响应示例**:
```json
{
    "success": true,
    "message": "获取成功",
    "data": {
        "user_id": 1,
        "mail": "user@example.com",
        "real_name": "张三",
        "id_card": "110101********1234",
        "region_id": 1,
        "region_name": "朝阳区",
        "role": "RESIDENT",
        "status": "NORMAL",
        "create_time": "2025-12-18 10:00:00"
    }
}
```

---

### 5. 修改用户信息

**接口**: `PUT /api/v1/user/update`

**请求头**: 
```
Authorization: Bearer <token>
```

**请求体**:
```json
{
    "mail": "newemail@example.com",
    "password": "newpassword",
    "real_name": "李四",
    "idcard": "110101199001011234",
    "region_id": 1
}
```

**响应示例**:
```json
{
    "success": true,
    "message": "修改成功",
    "data": {
        "user_id": 1,
        "mail": "newemail@example.com",
        "real_name": "李四",
        "region_id": 1,
        "role": "RESIDENT",
        "update_time": "2025-12-18 11:00:00"
    }
}
```

---

### 6. 绑定电表

**接口**: `POST /api/v1/user/bind-meter`

**权限**: 需要 `bind_meter` 权限

**功能说明**: 将一个已存在但尚未分配给任何用户的电表（`user_id=null`）绑定到指定用户。此功能主要用于**电表更换**或**电表过户**场景。

**使用场景**:
- 电表更换：旧电表损坏，需要更换新电表
- 电表过户：用户搬家或房屋转让，需要将现有电表绑定到新用户
- 电表重新分配：电表已解绑，需要重新分配给用户

**注意事项**:
- 只能绑定未分配的电表（`user_id` 为空）
- 电表和用户必须在同一片区
- 如果需要新安装电表，请使用 `/meter/install` 接口

**请求头**: 
```
Authorization: Bearer <token>
```

**请求体**:
```json
{
    "target_user_id": 1,
    "meter_code": "001-12345"
}
```

**参数说明**:
- `target_user_id`: 目标用户ID（必填）
- `meter_code`: 电表编号（必填）

**响应示例**:
```json
{
    "success": true,
    "message": "绑定成功",
    "data": {
        "success": true,
        "msg": "电表绑定成功",
        "meter_info": {
            "meter_code": "001-12345",
            "install_address": "北京市朝阳区XX路XX号",
            "status": "NORMAL"
        }
    }
}
```

---

### 7. 解绑电表

**接口**: `POST /api/v1/user/unbind-meter`

**请求头**: 
```
Authorization: Bearer <token>
```

**请求体**:
```json
{
    "target_user_id": 1,
    "meter_id": 1
}
```

**响应示例**:
```json
{
    "success": true,
    "message": "解绑成功",
    "data": {
        "success": true,
        "message": "电表解绑成功",
        "meter_info": {
            "meter_code": "001-12345",
            "meter_id": 1
        }
    }
}
```

---

### 8. 获取用户电表列表

**接口**: `GET /api/v1/user/meters`

**请求头**: 
```
Authorization: Bearer <token>
```

**响应示例**:
```json
{
    "success": true,
    "message": "获取成功",
    "data": {
        "success": true,
        "total": 2,
        "meters": [
            {
                "meter_id": 1,
                "meter_code": "001-12345",
                "meter_type": "SMART",
                "install_address": "北京市朝阳区XX路XX号",
                "status": "NORMAL",
                "install_date": "2025-01-01"
            },
            {
                "meter_id": 2,
                "meter_code": "001-12346",
                "meter_type": "SMART",
                "install_address": "北京市朝阳区YY路YY号",
                "status": "NORMAL",
                "install_date": "2025-01-02"
            }
        ]
    }
}
```

---

### 9. 修改密码

**接口**: `POST /api/v1/user/change-password`

**请求头**: 
```
Authorization: Bearer <token>
```

**请求体**:
```json
{
    "old_password": "oldpassword",
    "new_password": "newpassword"
}
```

**响应示例**:
```json
{
    "success": true,
    "message": "密码修改成功",
    "data": {
        "success": true,
        "message": "密码修改成功",
        "user_id": 1
    }
}
```

---

### 10. 发送重置密码验证码

**接口**: `POST /api/v1/user/send-reset-code`

**请求头**: 无需认证

**说明**: 向指定邮箱发送6位数字验证码，用于密码重置。验证码有效期为5分钟。

**请求体**:
```json
{
    "mail": "user@example.com"
}
```

**参数说明**:
- `mail`: 已注册的邮箱地址（必填）

**响应示例**:
```json
{
    "success": true,
    "message": "验证码已发送到您的邮箱",
    "data": {
        "success": true,
        "message": "验证码已发送到您的邮箱",
        "email": "user@example.com"
    }
}
```

**错误响应**:
```json
{
    "success": false,
    "message": "该邮箱未注册",
    "code": 404
}
```

---

### 11. 重置密码

**接口**: `POST /api/v1/user/reset-password`

**请求头**: 无需认证

**说明**: 使用邮箱验证码重置密码。验证码单次使用，验证后自动失效。

**请求体**:
```json
{
    "mail": "user@example.com",
    "code": "123456",
    "new_password": "newpassword123"
}
```

**参数说明**:
- `mail`: 邮箱地址（必填）
- `code`: 6位数字验证码（必填）
- `new_password`: 新密码，长度6-20位（必填）

**响应示例**:
```json
{
    "success": true,
    "message": "密码重置成功",
    "data": {
        "success": true,
        "message": "密码重置成功",
        "user_id": 1
    }
}
```

**错误响应**:
```json
{
    "success": false,
    "message": "验证码错误或已过期",
    "code": 400
}
```

---

### 12. 获取用户列表（管理员）

**接口**: `GET /api/v1/user/list`

**请求头**: 
```
Authorization: Bearer <token>
```

**Query参数**:
```
page=1&per_page=20&region_id=1&keyword=test
```

**响应示例**:
```json
{
    "success": true,
    "message": "获取成功",
    "data": {
        "users": [
            {
                "user_id": 1,
                "mail": "admin@example.com",
                "real_name": "管理员",
                "id_card": "110101********1234",
                "region_id": 1,
                "region_name": "朝阳区",
                "role": "AREA_ADMIN",
                "status": "NORMAL",
                "create_time": "2025-12-18 10:00:00"
            }
        ],
        "pagination": {
            "total": 1,
            "page": 1,
            "per_page": 20,
            "pages": 1,
            "has_next": false,
            "has_prev": false
        }
    }
}
```

---

### 13. 用户登出

**接口**: `POST /api/v1/user/logout`

**请求头**: 
```
Authorization: Bearer <token>
```

**响应示例**:
```json
{
    "success": true,
    "message": "登出成功",
    "data": {
        "user_id": 1
    }
}
```

---

---

## 电表模块接口 (`/api/v1/meter`)

### 1. 安装电表

**接口**: `POST /api/v1/meter/install`

**权限**: 需要 `bind_meter` 权限（管理员）

**功能说明**: 为用户安装全新的电表，系统将自动生成唯一电表编号，并自动绑定到指定用户。这是创建新电表并分配给用户的主要方式。

**请求头**: 
```
Authorization: Bearer <token>
```

**请求体**:
```json
{
    "target_user_id": 1,
    "region_id": 1,
    "install_address": "北京市朝阳区XX路XX号"
}
```

**参数说明**:
- `target_user_id`: 目标用户ID（必填）
- `region_id`: 片区ID（必填）
- `install_address`: 安装地址（必填，5-100字符）

**响应示例**:
```json
{
    "success": true,
    "message": "电表安装成功",
    "data": {
        "meter_id": 1,
        "meter_code": "001-12345",
        "user_id": 1,
        "meter_type": "SMART",
        "install_address": "北京市朝阳区XX路XX号",
        "status": "NORMAL",
        "install_date": "2025-12-18"
    }
}
```

---

### 2. 更新电表状态

**接口**: `PUT /api/v1/meter/update-status`

**请求头**: 
```
Authorization: Bearer <token>
```

**请求体**:
```json
{
    "meter_id": 1,
    "new_status": "NORMAL"
}
```

**响应示例**:
```json
{
    "success": true,
    "message": "电表状态更新成功",
    "data": {
        "meter_id": 1,
        "status": "NORMAL"
    }
}
```

---

### 3. 添加电表操作记录

**接口**: `POST /api/v1/meter/add-record`

**请求头**: 
```
Authorization: Bearer <token>
```

**请求体**:
```json
{
    "meter_id": 1,
    "record_type": "MAINTAIN",
    "operator": "张三",
    "content": "更换电表",
    "attach_img": "http://example.com/image.jpg"
}
```

**响应示例**:
```json
{
    "success": true,
    "message": "电表记录添加成功",
    "data": {
        "record_id": 1,
        "meter_id": 1,
        "record_type": "MAINTAIN",
        "operator": "张三",
        "content": "更换电表",
        "create_time": "2025-12-18 10:00:00"
    }
}
```

---

### 4. 电表报修

**接口**: `POST /api/v1/meter/repair`

**请求头**: 
```
Authorization: Bearer <token>
```

**请求体**:
```json
{
    "meter_id": 1,
    "fault_address": "北京市朝阳区XX路XX号",
    "fault_description": "电表无法读数",
    "attach_img": "http://example.com/image.jpg"
}
```

**响应示例**:
```json
{
    "success": true,
    "message": "电表报修成功",
    "data": {
        "repair_id": 1,
        "meter_id": 1,
        "status": "PENDING"
    }
}
```

---

### 5. 校验电表读数

**接口**: `POST /api/v1/meter/validate-reading`

**请求头**: 
```
Authorization: Bearer <token>
```

**请求体**:
```json
{
    "meter_id": 1,
    "new_reading": 1234.5,
    "reading_time": "2025-12-18 10:00:00"
}
```

**响应示例**:
```json
{
    "success": true,
    "message": "读数校验完成",
    "data": {
        "meter_id": 1,
        "old_reading": 1200.5,
        "new_reading": 1234.5,
        "usage": 34.0
    }
}
```

---

### 6. 查询电表列表

**接口**: `GET /api/v1/meter/query`

**请求头**: 
```
Authorization: Bearer <token>
```

**Query参数**:
```
region_id=1&meter_status=NORMAL&page=1&per_page=20
```

**响应示例**:
```json
{
    "success": true,
    "message": "查询成功",
    "data": {
        "meters": [
            {
                "meter_id": 1,
                "meter_code": "001-12345",
                "user_id": 1,
                "meter_type": "SMART",
                "install_address": "北京市朝阳区XX路XX号",
                "status": "NORMAL",
                "install_date": "2025-01-01"
            }
        ],
        "pagination": {
            "total": 1,
            "page": 1,
            "per_page": 20
        }
    }
}
```

---

### 7. 查询电表操作记录

**接口**: `GET /api/v1/meter/records/<meter_id>`

**请求头**: 
```
Authorization: Bearer <token>
```

**URL参数**:
```
meter_id: 电表ID
```

**Query参数**:
```
record_type=MAINTAIN&page=1&per_page=20
```

**响应示例**:
```json
{
    "success": true,
    "message": "查询成功",
    "data": {
        "records": [
            {
                "record_id": 1,
                "meter_id": 1,
                "record_type": "MAINTAIN",
                "operator": "张三",
                "content": "更换电表",
                "create_time": "2025-12-18 10:00:00"
            }
        ],
        "pagination": {
            "total": 1,
            "page": 1,
            "per_page": 20
        }
    }
}
```

---

### 8. 查询空闲电表列表

**接口**: `GET /api/v1/meter/available`

**权限**: 需要管理员权限（`require_admin=True`）和 `query_meter` 权限

**功能说明**: 查询未分配给任何用户的电表（`user_id` 为空且状态为正常的电表）。片区管理员只能查询本片区的空闲电表，超级管理员可以查询所有片区或指定片区的空闲电表。

**使用场景**:
- 查看可用于分配的电表
- 为新用户分配电表前查看可用电表
- 电表更换或过户前查看空闲电表编号

**请求头**: 
```
Authorization: Bearer <token>
```

**Query参数**:
- `region_id` (integer, 可选): 片区ID，超级管理员可指定片区筛选，片区管理员自动使用所属片区
- `page` (integer, 默认: 1): 页码
- `per_page` (integer, 默认: 20): 每页数量

**请求示例**:
```
GET /api/v1/meter/available?region_id=1&page=1&per_page=20
```

**响应示例**:
```json
{
    "success": true,
    "message": "查询成功",
    "data": {
        "meters": [
            {
                "meter_id": 5,
                "meter_code": "BJ-CY-S-202601021200-001",
                "meter_type": "smart",
                "install_address": "北京市朝阳区XX路XX号",
                "install_time": "2026-01-02 12:00:00",
                "region_name": "朝阳区",
                "region_id": 1,
                "status": "normal"
            }
        ],
        "pagination": {
            "total": 1,
            "page": 1,
            "per_page": 20,
            "pages": 1,
            "has_next": false,
            "has_prev": false
        }
    }
}
```

**错误响应**:
- 权限不足 (403):
```json
{
    "success": false,
    "message": "此操作仅管理员可执行",
    "code": 403
}
```

---

## 账单模块接口 (`/api/v1/bill`)

### 1. 生成账单

**接口**: `POST /api/v1/bill/create`

**请求头**: 
```
Authorization: Bearer <token>
```

**请求体**:
```json
{
    "bill_month": "2025-12-01",
    "meter_id": 1
}
```

**响应示例**:
```json
{
    "success": true,
    "message": "账单生成成功",
    "data": {
        "bill_id": 1,
        "meter_id": 1,
        "bill_month": "2025-12-01",
        "total_usage": 150.5,
        "bill_amount": 500.00,
        "status": "UNPAID"
    }
}
```

---

### 2. 支付账单

**接口**: `POST /api/v1/bill/pay`

**请求头**: 
```
Authorization: Bearer <token>
```

**请求体**:
```json
{
    "bill_id": 1,
    "payment_amount": 500.00,
    "payment_method": "ALIPAY",
    "transaction_id": "TXN123456"
}
```

**响应示例**:
```json
{
    "success": true,
    "message": "账单支付成功",
    "data": {
        "bill_id": 1,
        "status": "PAID",
        "payment_time": "2025-12-18 10:00:00",
        "payment_amount": 500.00
    }
}
```

---

### 3. 查询账单列表

**接口**: `GET /api/v1/bill/query`

**权限**: 需要 `query_bill` 权限

**请求头**: 
```
Authorization: Bearer <token>
```

**Query参数**:
- `user_id` (integer, 可选): 用户ID（管理员可查询其他用户账单）
- `meter_id` (integer, 可选): 电表ID
- `status` (string, 可选): 账单状态
  - `unpaid`: 未支付
  - `paid`: 已支付
  - `overdue`: 逾期
- `start_month` (string, 可选): 开始月份 (格式: YYYY-MM-DD)
- `end_month` (string, 可选): 结束月份 (格式: YYYY-MM-DD)
- `page` (integer, 默认: 1): 页码
- `per_page` (integer, 默认: 20): 每页数量

**权限说明**:
- 普通用户：只能查询自己的账单
- 片区管理员：可查询本片区内所有用户的账单
- 超级管理员：可查询所有账单

**响应示例**:
```json
{
    "success": true,
    "message": "查询成功",
    "data": {
        "bills": [
            {
                "bill_id": 1,
                "user_id": 1,
                "meter_id": 1,
                "bill_month": "2025-12",
                "total_usage": 150.5,
                "bill_amount": 500.00,
                "status": "unpaid",
                "generate_time": "2025-12-18 10:30:00",
                "due_date": "2026-01-18"
            }
        ],
        "pagination": {
            "total": 15,
            "page": 1,
            "per_page": 20,
            "pages": 1
        }
    }
}
```

---

### 4. 获取账单详情

**接口**: `GET /api/v1/bill/detail/<bill_id>`

**请求头**: 
```
Authorization: Bearer <token>
```

**URL参数**:
```
bill_id: 账单ID
```

**响应示例**:
```json
{
    "success": true,
    "message": "获取成功",
    "data": {
        "bill_id": 1,
        "user_id": 1,
        "meter_id": 1,
        "bill_month": "2025-12-01",
        "total_usage": 150.5,
        "unit_price": 0.5,
        "bill_amount": 500.00,
        "status": "UNPAID",
        "generate_time": "2025-12-18",
        "due_date": "2025-12-31"
    }
}
```

---

### 5. 发送账单提醒

**接口**: `POST /api/v1/bill/reminder/<bill_id>`

**请求头**: 
```
Authorization: Bearer <token>
```

**URL参数**:
```
bill_id: 账单ID
```

**响应示例**:
```json
{
    "success": true,
    "message": "提醒发送成功",
    "data": {
        "bill_id": 1,
        "send_status": "SUCCESS"
    }
}
```

---

### 6. 批量生成账单

**接口**: `POST /api/v1/bill/batch-create`

**请求头**: 
```
Authorization: Bearer <token>
```

**请求体**:
```json
{
    "bill_month": "2025-12-01",
    "region_id": 1
}
```

**响应示例**:
```json
{
    "success": true,
    "message": "批量账单生成完成",
    "data": {
        "total_count": 10,
        "success_count": 10,
        "failed_count": 0,
        "bills": [...]
    }
}
```

---

## 用电数据模块接口 (`/api/v1/usage`)

### 1. IoT设备上传用电数据

**接口**: `POST /api/v1/usage/iot-upload`

**请求头**: 无需认证

**请求体**:
```json
{
    "meter_id": 1,
    "electricity": 1234.5,
    "collect_time": "2025-12-18 10:00:00",
    "voltage": 220.5,
    "current": 5.2
}
```

**响应示例**:
```json
{
    "success": true,
    "message": "数据上传成功",
    "data": {
        "usage_id": 1,
        "meter_id": 1,
        "electricity": 1234.5,
        "collect_time": "2025-12-18 10:00:00"
    }
}
```

---

### 2. 汇总用电数据

**接口**: `POST /api/v1/usage/aggregate`

**请求头**: 
```
Authorization: Bearer <token>
```

**请求体**:
```json
{
    "meter_id": 1,
    "usage_type": "DAY",
    "target_date": "2025-12-18"
}
```

**响应示例**:
```json
{
    "success": true,
    "message": "数据汇总成功",
    "data": {
        "meter_id": 1,
        "total_electricity": 150.5,
        "usage_type": "DAY",
        "target_date": "2025-12-18"
    }
}
```

---

### 3. 查询用电数据

**接口**: `GET /api/v1/usage/query`

**请求头**: 
```
Authorization: Bearer <token>
```

**Query参数**:
```
meter_id=1&usage_type=DAY&start_date=2025-12-01&end_date=2025-12-31&page=1&per_page=20
```

**响应示例**:
```json
{
    "success": true,
    "message": "查询成功",
    "data": {
        "usages": [
            {
                "meter_id": 1,
                "electricity": 1234.5,
                "collect_time": "2025-12-18 10:00:00"
            }
        ],
        "pagination": {
            "total": 100,
            "page": 1,
            "per_page": 20
        }
    }
}
```

---

### 4. 人工录入用电数据

**接口**: `POST /api/v1/usage/manual-input`

**请求头**: 
```
Authorization: Bearer <token>
```

**请求体**:
```json
{
    "meter_id": 1,
    "electricity": 1234.5,
    "collect_time": "2025-12-18 10:00:00",
    "voltage": 220.5,
    "current": 5.2
}
```

**响应示例**:
```json
{
    "success": true,
    "message": "数据录入成功",
    "data": {
        "usage_id": 1,
        "meter_id": 1,
        "electricity": 1234.5,
        "record_type": "MANUAL"
    }
}
```

---

## 查询分析模块接口 (`/api/v1/query`)

### 1. 用电统计概览

**接口**: `GET /api/v1/query/statistics/summary`

**权限**: 需要 `query_iot` 权限

**请求头**: 需要认证

**Query参数**:
- `scope` (string, 可选): 统计范围
  - `user`: 用户统计（默认）
  - `region`: 片区统计（仅管理员）
- `scope_id` (integer, 可选): 对应的ID（用户ID或片区ID），不传则使用当前用户ID

**响应示例**（用户统计）:
```json
{
  "success": true,
  "message": "查询成功",
  "data": {
    "total_usage": 1250.5,
    "current_month_usage": 120.3,
    "total_cost": 850.2,
    "unpaid_bills": 2,
    "meter_count": 1
  }
}
```

**响应示例**（片区统计）:
```json
{
  "success": true,
  "message": "查询成功",
  "data": {
    "region_name": "嘉定区",
    "total_usage": 15230.8,
    "user_count": 85,
    "meter_count": 92,
    "arrear_users": 5
  }
}
```

### 2. 个人用电分析

**接口**: `GET /api/v1/query/analyze/user`

**请求头**: 
```
Authorization: Bearer <token>
```

**Query参数**:
```
user_id=1&analysis_period=month&compare_period=false
```

**响应示例**:
```json
{
    "success": true,
    "message": "分析完成",
    "data": {
        "user_id": 1,
        "analysis_period": "month",
        "total_electricity": 150.5,
        "average_daily_usage": 5.0,
        "peak_usage_time": "18:00-22:00",
        "total_cost": 500.00,
        "comparison": {
            "last_period_usage": 140.0,
            "growth_rate": 7.5
        }
    }
}
```

---

### 2. 片区用电分析

**接口**: `GET /api/v1/query/analyze/region`

**权限**: 需要 `query_iot` 权限（仅管理员）

**请求头**: 
```
Authorization: Bearer <token>
```

**Query参数**:
- `region_id` (integer, 必填): 片区ID
- `analysis_period` (string, 默认: month): 分析周期
  - `day`: 日（最近7天）
  - `month`: 月（最近12个月）
  - `year`: 年（最近5年）
- `compare_period` (boolean, 默认: false): 是否对比同期数据

**响应示例**:
```json
{
    "success": true,
    "message": "分析完成",
    "data": {
        "region_info": {
            "region_id": 1,
            "region_name": "朝阳区",
            "analysis_period": "month"
        },
        "trend_data": [
            {
                "period": "2025-01",
                "total_electricity": 5230.5,
                "peak_electricity": 2100.0,
                "valley_electricity": 1800.0
            },
            {
                "period": "2025-02",
                "total_electricity": 4890.2,
                "peak_electricity": 1950.0,
                "valley_electricity": 1700.0
            }
        ],
        "comparison": {
            "current_period_total": 5230.5,
            "compare_period_total": 4890.2,
            "difference": 340.3,
            "change_rate": 6.96,
            "trend": "上升"
        },
        "peak_hours": [
            {
                "hour": 18,
                "avg_usage": 450.5,
                "is_peak": true
            },
            {
                "hour": 19,
                "avg_usage": 520.3,
                "is_peak": true
            }
        ],
        "summary": {
            "total_electricity": 62350.8,
            "avg_electricity": 5195.9,
            "max_electricity": 6200.5,
            "min_electricity": 4100.2,
            "avg_per_meter": 678.4
        }
    }
}
```

---

### 3. 用电排名

**接口**: `GET /api/v1/query/ranking`

**请求头**: 
```
Authorization: Bearer <token>
```

**Query参数**:
```
region_id=1&ranking_type=electricity&time_range=month&limit=10
```

**响应示例**:
```json
{
    "success": true,
    "message": "查询成功",
    "data": {
        "ranking_type": "electricity",
        "time_range": "month",
        "rankings": [
            {
                "rank": 1,
                "user_id": 1,
                "user_name": "张三",
                "meter_id": 1,
                "total_usage": 250.5,
                "total_cost": 1000.00
            }
        ]
    }
}
```

---

### 4. 用电统计概览

**接口**: `GET /api/v1/query/statistics/summary`

**请求头**: 
```
Authorization: Bearer <token>
```

**Query参数**:
```
scope=user&scope_id=1
```

**响应示例**:
```json
{
    "success": true,
    "message": "查询成功",
    "data": {
        "scope": "user",
        "scope_id": 1,
        "total_usage": 150.5,
        "total_cost": 500.00,
        "monthly_average": 5.0,
        "trend": "stable"
    }
}
```

---

### 5. 导出用电数据

**接口**: `GET /api/v1/query/export`

**请求头**: 
```
Authorization: Bearer <token>
```

**Query参数**:
```
export_type=usage&region_id=1&start_date=2025-12-01&end_date=2025-12-31&format=csv
```

**响应示例**:
```json
{
    "success": true,
    "message": "导出成功",
    "data": {
        "download_url": "http://localhost:5000/downloads/export_123456.csv",
        "file_name": "export_123456.csv",
        "export_time": "2025-12-18 10:00:00"
    }
}
```

---

## 系统管理模块接口 (`/api/v1/system`)

### 1. 创建电价策略

**接口**: `POST /api/v1/system/price-policy/create`

**请求头**: 
```
Authorization: Bearer <token>
```

**请求体**:
```json
{
    "policy_name": "阶梯电价策略2025",
    "price_type": "ladder",
    "region_id": 1,
    "base_unit_price": 0.5,
    "start_time": "2025-01-01 00:00:00",
    "end_time": "2025-12-31 23:59:59",
    "ladder_rules": [
        {"ladder_level": "low", "min_electricity": 0, "max_electricity": 200, "ratio": 1.0},
        {"ladder_level": "middle", "min_electricity": 200, "max_electricity": 400, "ratio": 1.5},
        {"ladder_level": "high", "min_electricity": 400, "max_electricity": null, "ratio": 2.0}
    ]
}
```

**响应示例**:
```json
{
    "success": true,
    "message": "电价策略创建成功",
    "data": {
        "policy_id": 1,
        "policy_name": "阶梯电价策略2025",
        "price_type": "ladder",
        "is_active": true
    }
}
```

---

### 2. 更新电价策略

**接口**: `PUT /api/v1/system/price-policy/update`

**请求头**: 
```
Authorization: Bearer <token>
```

**请求体**:
```json
{
    "policy_id": 1,
    "policy_name": "新策略名称",
    "base_unit_price": 0.6,
    "is_active": true,
    "end_time": "2026-12-31 23:59:59"
}
```

**响应示例**:
```json
{
    "success": true,
    "message": "电价策略更新成功",
    "data": {
        "policy_id": 1,
        "policy_name": "新策略名称",
        "base_unit_price": 0.6
    }
}
```

---

### 3. 获取电价策略列表

**接口**: `GET /api/v1/system/price-policy/list`

**权限**: 需要 `query_permission` 权限

**请求头**: 
```
Authorization: Bearer <token>
```

**Query参数**:
- `region_id` (integer, 可选): 片区ID，筛选特定片区的策略
- `is_active` (boolean, 可选): 是否激活，true/false
- `page` (integer, 默认: 1): 页码
- `per_page` (integer, 默认: 20): 每页数量

**响应示例**:
```json
{
    "success": true,
    "message": "查询成功",
    "data": {
        "policies": [
            {
                "policy_id": 1,
                "policy_name": "阶梯电价策略2025",
                "price_type": "ladder",
                "region_id": 1,
                "region_name": "朝阳区",
                "base_unit_price": 0.5,
                "start_time": "2025-01-01 00:00:00",
                "end_time": "2025-12-31 23:59:59",
                "is_active": true,
                "create_time": "2025-12-18 10:00:00"
            }
        ],
        "pagination": {
            "total": 1,
            "page": 1,
            "per_page": 20,
            "pages": 1,
            "has_next": false,
            "has_prev": false
        }
    }
}
```

---

### 4. 删除电价策略

**接口**: `DELETE /api/v1/system/price-policy/<policy_id>`

**权限**: 仅超级管理员

**请求头**: 
```
Authorization: Bearer <token>
```

**URL参数**:
- `policy_id` (integer, 必需): 电价策略ID

**请求示例**:
```
DELETE /api/v1/system/price-policy/1
```

**响应示例**:
```json
{
    "success": true,
    "message": "删除成功",
    "data": {
        "success": true,
        "message": "价格策略删除成功"
    }
}
```

**错误响应**:
- 策略不存在 (404):
```json
{
    "success": false,
    "message": "价格策略不存在",
    "code": 404
}
```

- 策略被账单使用 (400):
```json
{
    "success": false,
    "message": "该价格策略已被账单使用，无法删除",
    "code": 400
}
```

---

### 5. 创建片区

**接口**: `POST /api/v1/system/region/create`

**请求头**: 
```
Authorization: Bearer <token>
```

**请求体**:
```json
{
    "region_name": "朝阳区",
    "region_code": "BJ-CY",
    "manager_id": 2,
    "description": "北京市朝阳区"
}
```

**响应示例**:
```json
{
    "success": true,
    "message": "片区创建成功",
    "data": {
        "region_id": 1,
        "region_name": "朝阳区",
        "region_code": "BJ-CY",
        "manager_id": 2,
        "create_time": "2025-12-18 10:00:00"
    }
}
```

---

### 6. 更新片区

**接口**: `PUT /api/v1/system/region/update`

**请求头**: 
```
Authorization: Bearer <token>
```

**请求体**:
```json
{
    "region_id": 1,
    "region_name": "新片区名称",
    "manager_id": 3,
    "description": "更新的描述"
}
```

**响应示例**:
```json
{
    "success": true,
    "message": "片区更新成功",
    "data": {
        "region_id": 1,
        "region_name": "新片区名称",
        "manager_id": 3
    }
}
```

---

### 7. 获取片区列表

**接口**: `GET /api/v1/system/region/list`

**权限**: 需要 `query_permission` 权限

**请求头**: 
```
Authorization: Bearer <token>
```

**Query参数**:
- `page` (integer, 默认: 1): 页码
- `per_page` (integer, 默认: 20): 每页数量

**响应示例**:
```json
{
    "success": true,
    "message": "查询成功",
    "data": {
        "regions": [
            {
                "region_id": 1,
                "region_code": "BJ-CY",
                "region_name": "朝阳区",
                "parent_id": null,
                "parent_name": null,
                "manager_id": 2,
                "manager_name": "管理员张三",
                "create_time": "2025-12-18 10:00:00"
            }
        ],
        "pagination": {
            "total": 1,
            "page": 1,
            "per_page": 20,
            "pages": 1,
            "has_next": false,
            "has_prev": false
        }
    }
}
```

---

### 8. 删除片区

**接口**: `DELETE /api/v1/system/region/<region_id>`

**权限**: 仅超级管理员

**请求头**: 
```
Authorization: Bearer <token>
```

**URL参数**:
- `region_id` (integer, 必需): 片区ID

**请求示例**:
```
DELETE /api/v1/system/region/1
```

**响应示例**:
```json
{
    "success": true,
    "message": "删除成功",
    "data": {
        "success": true,
        "message": "片区删除成功"
    }
}
```

**错误响应**:
- 片区不存在 (404):
```json
{
    "success": false,
    "message": "片区不存在",
    "code": 404
}
```

- 存在下级片区 (400):
```json
{
    "success": false,
    "message": "该片区存在下级片区，无法删除",
    "code": 400
}
```

- 被价格策略使用 (400):
```json
{
    "success": false,
    "message": "该片区已被价格策略使用，无法删除",
    "code": 400
}
```

---

### 9. 更新用户角色

**接口**: `PUT /api/v1/system/user/update-role`

**请求头**: 
```
Authorization: Bearer <token>
```

**请求体**:
```json
{
    "user_id": 1,
    "new_role": "AREA_ADMIN"
}
```

**响应示例**:
```json
{
    "success": true,
    "message": "用户角色更新成功",
    "data": {
        "user_id": 1,
        "new_role": "AREA_ADMIN",
        "update_time": "2025-12-18 10:00:00"
    }
}
```

---

### 10. 获取系统日志

**接口**: `GET /api/v1/system/logs`

**请求头**: 
```
Authorization: Bearer <token>
```

**Query参数**:
```
log_type=API&log_level=INFO&module=user&start_time=2025-12-01 00:00:00&end_time=2025-12-31 23:59:59&page=1&per_page=20
```

**响应示例**:
```json
{
    "success": true,
    "message": "查询成功",
    "data": {
        "logs": [
            {
                "log_id": 1,
                "log_type": "API",
                "log_level": "INFO",
                "module": "user",
                "message": "用户登录成功",
                "create_time": "2025-12-18 10:00:00"
            }
        ],
        "pagination": {
            "total": 100,
            "page": 1,
            "per_page": 20
        }
    }
}
```

---

## 通知模块接口 (`/api/v1/notification`)

### 1. 创建通知

**接口**: `POST /api/v1/notification/create`

**请求头**: 
```
Authorization: Bearer <token>
```

**请求体**:
```json
{
    "notice_type": "REPAIR",
    "target_type": "AREA_ADMIN",
    "target_ids": [1, 2, 3],
    "title": "通知标题",
    "content": "通知内容",
    "send_channel": "INNER",
    "send_time": "2025-12-19 10:00:00",
    "is_batch": true,
    "related_id": 1
}
```

**响应示例**:
```json
{
    "success": true,
    "message": "通知创建成功",
    "data": {
        "notification_id": 1,
        "notice_type": "REPAIR",
        "title": "通知标题",
        "status": "PENDING"
    }
}
```

---

### 2. 发送通知

**接口**: `POST /api/v1/notification/send`

**请求头**: 
```
Authorization: Bearer <token>
```

**请求体**:
```json
{
    "notification_id": 1
}
```

或批量发送：
```json
{
    "batch_id": "abc123"
}
```

**响应示例**:
```json
{
    "success": true,
    "message": "通知发送成功",
    "data": {
        "notification_id": 1,
        "send_count": 3,
        "status": "SENT"
    }
}
```

---

### 3. 查询通知列表

**接口**: `GET /api/v1/notification/query`

**请求头**: 
```
Authorization: Bearer <token>
```

**Query参数**:
```
user_id=1&notify_type=REPAIR&status=UNREAD&is_unread_only=true&page=1&per_page=20
```

**响应示例**:
```json
{
    "success": true,
    "message": "查询成功",
    "data": {
        "notifications": [
            {
                "notification_id": 1,
                "user_id": 1,
                "notice_type": "REPAIR",
                "title": "通知标题",
                "content": "通知内容",
                "status": "UNREAD",
                "create_time": "2025-12-18 10:00:00"
            }
        ],
        "pagination": {
            "total": 5,
            "page": 1,
            "per_page": 20
        }
    }
}
```

---

### 4. 获取通知统计

**接口**: `GET /api/v1/notification/statistics`

**请求头**: 
```
Authorization: Bearer <token>
```

**Query参数**:
```
notify_type=REPAIR&start_date=2025-12-01&end_date=2025-12-31
```

**响应示例**:
```json
{
    "success": true,
    "message": "查询成功",
    "data": {
        "total_count": 100,
        "unread_count": 15,
        "by_type": {
            "REPAIR": 30,
            "BILL": 50,
            "SYSTEM": 20
        },
        "by_status": {
            "UNREAD": 15,
            "READ": 85
        }
    }
}
```

---

### 5. 更新通知状态

**接口**: `PUT /api/v1/notification/update-status`

**请求头**: 
```
Authorization: Bearer <token>
```

**请求体**:
```json
{
    "notification_id": 1,
    "action": "mark_read",
    "user_id": 1
}
```

**响应示例**:
```json
{
    "success": true,
    "message": "通知已标记为已读",
    "data": {
        "notification_id": 1,
        "status": "READ",
        "update_time": "2025-12-18 10:00:00"
    }
}
```

---

## API完整性说明

### 已实现的API模块

✅ **用户模块** (`user.py`) - 11个接口
- 用户注册、登录、登出、刷新Token
- 获取/修改用户信息
- 电表绑定/解绑
- 获取用户电表列表
- 修改密码
- 获取用户列表（管理员）

✅ **电表模块** (`meter.py`) - 7个接口
- 电表安装、状态更新、操作记录
- 电表报修、读数校验
- 查询电表列表和操作记录

✅ **账单模块** (`bill.py`) - 6个接口
- 账单生成（单个/批量）
- 账单支付、查询、详情
- 账单提醒

✅ **用电数据模块** (`usage.py`) - 4个接口
- IoT数据上传、人工录入
- 数据汇总、查询

✅ **查询分析模块** (`query.py`) - 5个接口
- 个人/片区用电分析
- 用电排名、统计概览
- 数据导出

✅ **系统管理模块** (`system.py`) - 8个接口
- 电价策略管理（创建、更新、查询）
- 片区管理（创建、更新、查询）
- 用户角色管理
- 系统日志查询

✅ **通知模块** (`notification.py`) - 5个接口
- 通知创建、发送
- 通知查询与统计
- 更新通知状态

**总计**: 46个API接口全部实现完毕

---

## 参数校验工具使用

所有API都使用了middleware中的参数校验工具：

### 使用方式
```python
from middleware.validator import ValidateLogin, ValidateRegister
from utils.common import validate_request

@user_bp.route("/register", methods=["POST"])
@validate_request(ValidateRegister)
def register():
    data = request.validate_date  # 获取验证后的数据
    # ... 业务逻辑
```

### 已定义的Validator模型

**用户相关**:
- `ValidateRegister` / `ValidateUpdateUser`: 注册、修改用户信息
- `ValidateLogin`: 用户登录
- `ValidateBindMeter` / `ValidateUnbindMeter`: 绑定/解绑电表
- `ValidateChangePassword`: 修改密码
- `ValidateGetUserList`: 查询用户列表

**电表相关**:
- `ValidateMeterInstall`: 电表安装
- `ValidateMeterUpdateStatus`: 更新电表状态
- `ValidateAddMeterRecord`: 添加电表记录
- `ValidateMeterRepair`: 电表报修
- `ValidateMeterReading`: 电表读数校验
- `ValidateQueryMeters`: 查询电表列表
- `ValidateQueryMeterRecords` / `ValidateQueryMeterRecordsParams`: 查询电表记录

**通知相关**:
- `ValidateCreateNotification`: 创建通知
- `ValidateSendNotification`: 发送通知
- `ValidateQueryNotification`: 查询通知
- `ValidateUpdateNotificationStatus`: 更新通知状态

**用电数据相关**:
- `ValidateIoTData`: IoT数据上传、人工录入
- `ValidateQueryUsageData`: 查询用电数据
- `ValidateAggregateUsage`: 汇总用电数据

**其他模块**:
- 账单、查询、系统模块中也定义了相应的validator模型

所有validator都使用Pydantic进行参数校验，确保数据的准确性和安全性。

---

## 更新日志

**v1.0.0** (2025-12-18)
- ✅ 完成所有6个模块共40个API接口的实现
- ✅ 所有接口都使用参数校验中间件
- ✅ 所有接口都实现了认证和权限控制
- ✅ 更新完整的API使用文档

**v2.0.0** (2025-12-19)
- ✅ 升级权限系统，实现细粒度权限控制
- ✅ 新增权限编码体系（12个权限编码）
- ✅ 上移权限检查到API层，服务层专注业务逻辑
- ✅ 完成所有API接口的权限装饰器配置
- ✅ 更新权限编码文档和API使用文档

**v2.1.0** (2025-12-20)
- ✅ 新增通知模块接口（创建、发送、查询、统计、状态变更）
- ✅ 增补通知权限编码并同步文档
- ✅ 用户绑定/解绑/修改密码/列表接口补充参数校验
- ✅ 用电数据查询和人工录入接口重构，权限校验上移到API层

**v2.2.0** (2025-12-31)
- ✅ 新增系统管理模块API实现
  - 电价策略列表查询接口 `GET /system/price-policy/list`
  - 片区列表查询接口 `GET /system/region/list`
- ✅ 新增查询分析模块完整实现
  - 统计概览接口 `GET /query/statistics/summary`（支持用户和片区统计）
  - 片区用电分析接口 `GET /query/analyze/region`（含趋势、对比、高峰时段）
- ✅ 新增账单查询接口 `GET /bill/query`（支持多条件筛选和权限控制）
- ✅ 更新BillStatus枚举值为小写格式（unpaid/paid/overdue）
- ✅ 完善API文档，补充缺失接口文档和参数说明
- ✅ 修复所有已知的500错误问题

---

## 权限编码参考

详见 [权限编码文档](./PERMISSION_CODES.md) 了解完整的权限编码系统。

常用权限编码包括：`query_user`, `edit_user`, `query_meter`, `edit_meter`, `bind_meter`, `unbind_meter`, `query_bill`, `edit_bill`, `pay_bill`, `query_iot`, `edit_iot`, `report_meter`, `query_notification`, `edit_notification`, `query_permission`

权限检查流程：`请求 → JWT认证 → 权限装饰器检查权限编码 → 角色校验（超管直接通过，管理员检查权限+片区，用户检查自操作+权限）→ 处理请求`

---

所有接口的错误响应格式统一为：

```json
{
        "success": false,
        "message": "错误描述信息",
        "code": 400
}
```

常见错误码：
- `400`: 请求参数错误
- `401`: 未授权（token无效或过期）
- `403`: 权限不足
- `404`: 资源不存在
- `500`: 服务器内部错误

---

## 参数校验说明

### 注册/修改用户信息
- `mail`: 必填，邮箱格式
- `password`: 必填，6-20位字符
- `real_name`: 可选，2-20位字符
- `idcard`: 可选，18位身份证号码
- `region_id`: 可选，大于0的整数

### 登录
- `mail`: 必填，邮箱格式
- `password`: 必填，6-20位字符

---

## 使用示例

### Python示例

```python
import requests

# 1. 注册
register_data = {
        "mail": "test@example.com",
        "password": "123456",
        "real_name": "测试用户",
        "region_id": 1
}
response = requests.post(
        "http://localhost:5000/api/v1/user/register",
        json=register_data
)
print(response.json())

# 2. 登录
login_data = {
        "mail": "test@example.com",
        "password": "123456"
}
response = requests.post(
        "http://localhost:5000/api/v1/user/login",
        json=login_data
)
token = response.json()["data"]["token"]

# 3. 获取用户信息（需要token）
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
        "http://localhost:5000/api/v1/user/info",
        headers=headers
)
print(response.json())

# 4. 绑定电表
bind_data = {"meter_code": "001-12345"}
response = requests.post(
        "http://localhost:5000/api/v1/user/bind-meter",
        json=bind_data,
        headers=headers
)
print(response.json())
```

### cURL示例

```bash
# 1. 注册
curl -X POST http://localhost:5000/api/v1/user/register \
    -H "Content-Type: application/json" \
    -d '{
        "mail": "test@example.com",
        "password": "123456",
        "real_name": "测试用户",
        "region_id": 1
    }'

# 2. 登录
curl -X POST http://localhost:5000/api/v1/user/login \
    -H "Content-Type: application/json" \
    -d '{
        "mail": "test@example.com",
        "password": "123456"
    }'

# 3. 获取用户信息（需要替换token）
curl -X GET http://localhost:5000/api/v1/user/info \
    -H "Authorization: Bearer YOUR_TOKEN_HERE"

# 4. 绑定电表（需要替换token）
curl -X POST http://localhost:5000/api/v1/user/bind-meter \
    -H "Authorization: Bearer YOUR_TOKEN_HERE" \
    -H "Content-Type: application/json" \
    -d '{
        "meter_code": "001-12345"
    }'
```

---

## 中间件说明

### 1. 参数校验中间件 (`@validate_request`)
- 自动验证请求参数
- 使用Pydantic模型进行验证
- 验证失败自动返回错误信息

### 2. 认证中间件 (`@login_required`)
- 验证JWT token
- 自动提取用户ID存储到`g.user_id`
- token无效自动返回401错误

### 3. 权限验证中间件 (`@check_permission`)
- 基于 `require_permit` 的细粒度权限校验
- 自动注入 `g.user_id`、`g.user_role`、`g.target_user_id`
- 支持通过 `target_param` 指定权限校验的目标参数（如电表ID）
- 居民仅能操作本人资源，片区管理员受限于片区，超管放行

---

## 注意事项

1. **Token过期时间**: 默认2小时，过期后需要重新登录
2. **密码安全**: 密码在数据库中加密存储，不可逆
3. **身份证脱敏**: 返回的身份证号中间8位已脱敏处理
4. **电表绑定**: 一个电表只能绑定一个用户，同一片区才能绑定
5. **解绑限制**: 有未支付账单的电表无法解绑
6. **角色权限**: 
     - `RESIDENT`: 普通居民，只能查看和操作自己的数据
     - `AREA_ADMIN`: 片区管理员，可管理所属片区的数据
     - `SUPER_ADMIN`: 超级管理员，拥有所有权限
