# 电力查询系统 API 文档

## 📋 项目概览

电力查询系统后端API，提供用户管理、电表管理、账单管理、用电数据采集、查询分析和系统管理等功能。

**技术栈**: Flask + SQLAlchemy + Pydantic + JWT

**完成情况**: ✅ 7个模块，46个API接口全部实现（含通知模块）

---

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑.env文件配置数据库等信息
```

### 2. 数据库初始化

```bash
# 数据库迁移
flask db upgrade
```

### 3. 启动服务

```bash
# 开发环境
python run.py

# 生产环境
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

### 4. 测试API

```bash
# 用户注册
curl -X POST http://localhost:5000/api/v1/user/register \
  -H "Content-Type: application/json" \
  -d '{"mail":"test@example.com","password":"123456"}'

# 用户登录
curl -X POST http://localhost:5000/api/v1/user/login \
  -H "Content-Type: application/json" \
  -d '{"mail":"test@example.com","password":"123456"}'
```

---

## 📚 API模块说明

### 已实现的7个模块

| 模块 | 路径前缀 | 接口数 | 说明 |
|------|---------|--------|------|
| 用户模块 | `/api/v1/user` | 10个 | 注册、登录、信息管理、电表绑定 |
| 电表模块 | `/api/v1/meter` | 7个 | 电表安装、状态管理、报修、查询 |
| 账单模块 | `/api/v1/bill` | 6个 | 账单生成、支付、查询、提醒 |
| 用电数据 | `/api/v1/usage` | 5个 | IoT数据上传、汇总、查询 |
| 查询分析 | `/api/v1/query` | 5个 | 用电分析、排名、统计、导出 |
| 系统管理 | `/api/v1/system` | 8个 | 电价策略、片区管理、日志查询 |
| 通知模块 | `/api/v1/notification` | 5个 | 创建、发送、查询、统计通知 |

**详细API文档请查看**: [API_USAGE.md](./API_USAGE.md)

---

## 🔐 认证和权限

### 1. JWT认证

所有需要认证的接口都需要在请求头中携带token：

```
Authorization: Bearer <token>
```

**Token获取**：通过登录接口获取
**Token有效期**：默认2小时

### 2. 角色权限

系统支持三种角色：

- **RESIDENT**: 普通居民，只能查看和操作自己的数据
- **AREA_ADMIN**: 片区管理员，可管理其管辖的片区的数据（通过 Region.manager_id == user_id 确定）
- **SUPER_ADMIN**: 超级管理员，拥有所有权限

说明：除系统日志查询外，系统管理的写操作仅允许 `SUPER_ADMIN` 执行；服务层保持纯业务实现，不接收 `admin_id`/`admin_name`，统一由 API 层完成权限校验与日志记录。

### 3. 使用装饰器

```python
from middleware import check_permission

# 需要登录+权限
@bp.route("/info", methods=["GET"])
@check_permission(require_permit="query_user")
def get_info():
    user_id = g.user_id      # 当前用户ID
    target_id = g.target_user_id  # 装饰器解析出的目标用户ID
    # ... 业务逻辑
```

`check_permission` 会自动完成JWT认证、权限编码校验、片区/自我操作约束，并向 `g` 注入 `user_id`、`user_role`、`target_user_id`。

---

## ✅ 参数校验

所有API都使用Pydantic模型进行参数校验，自动验证类型和格式。

### 使用方式

```python
from middleware.validator import ValidateRegister
from utils.common import validate_request

@bp.route("/register", methods=["POST"])
@validate_request(ValidateRegister)
def register():
    data = request.validate_date  # 获取验证后的数据
    # ... 业务逻辑
```

### 已定义的Validator

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

**账单、查询、系统模块也有相应的validator模型**

---

## 📊 统一响应格式

### 成功响应

```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        // 具体数据
    }
}
```

### 错误响应

```json
{
    "success": false,
    "message": "错误描述信息",
    "code": 400
}
```

### 常见错误码

- `400`: 请求参数错误
- `401`: 未授权（token无效或过期）
- `403`: 权限不足
- `404`: 资源不存在
- `500`: 服务器内部错误

---

## 🎯 核心功能示例

### 1. 用户注册和登录

```python
import requests

BASE_URL = "http://localhost:5000/api/v1"

# 注册
register_data = {
    "mail": "test@example.com",
    "password": "123456",
    "real_name": "测试用户",
    "region_id": 1
}
response = requests.post(f"{BASE_URL}/user/register", json=register_data)
print(response.json())

# 登录
login_data = {
    "mail": "test@example.com",
    "password": "123456"
}
response = requests.post(f"{BASE_URL}/user/login", json=login_data)
token = response.json()["data"]["token"]

# 使用token访问受保护的接口
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(f"{BASE_URL}/user/info", headers=headers)
```

### 2. 电表报修

```python
# 电表报修（需要登录）
repair_data = {
    "meter_id": 1,
    "user_id": 1,
    "fault_address": "北京市朝阳区XX路XX号",
    "fault_description": "电表无法读数",
    "attach_img": "http://example.com/image.jpg"
}
response = requests.post(
    f"{BASE_URL}/meter/repair",
    json=repair_data,
    headers=headers
)
```

### 3. 查询账单并支付

```python
# 查询账单列表
response = requests.get(
    f"{BASE_URL}/bill/query?status=unpaid",
    headers=headers
)
bills = response.json()["data"]

# 支付账单
pay_data = {
    "bill_id": 1,
    "payment_method": "ALIPAY",
    "transaction_id": "TXN123456"
}
response = requests.post(
    f"{BASE_URL}/bill/pay",
    json=pay_data,
    headers=headers
)
```

### 4. 用电数据分析

```python
# 个人用电分析
response = requests.get(
    f"{BASE_URL}/query/analyze/user?analysis_period=month&compare_period=true",
    headers=headers
)
analysis_result = response.json()["data"]

# 导出用电数据
response = requests.get(
    f"{BASE_URL}/query/export?export_type=user&format=csv",
    headers=headers
)
```

---

## 🏗️ 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── api/                  # API接口层
│   │   ├── user.py          # 用户模块 ✅
│   │   ├── meter.py         # 电表模块 ✅
│   │   ├── bill.py          # 账单模块 ✅
│   │   ├── usage.py         # 用电数据模块 ✅
│   │   ├── query.py         # 查询分析模块 ✅
│   │   ├── system.py        # 系统管理模块 ✅
│   │   └── notification.py  # 通知模块 ✅
│   ├── services/            # 业务逻辑层
│   ├── models/              # 数据模型层
│   ├── middleware/          # 中间件
│   │   ├── auth.py         # 认证中间件
│   │   ├── validator.py    # 参数校验
│   │   ├── exception.py    # 异常处理
│   │   └── logger.py       # 日志记录
│   └── utils/              # 工具函数
│       └── common.py       # 通用工具
├── migrations/             # 数据库迁移
├── tests/                  # 测试
├── run.py                  # 启动文件
├── requirements.txt        # 依赖列表
├── README.md              # 本文件
└── API_USAGE.md           # 详细API文档
```

---

## 📝 开发说明

### 代码规范

- 遵循PEP 8规范
- 所有API接口都有详细的文档字符串
- 统一使用Pydantic进行参数校验
- 统一的错误处理机制

### 安全特性

- ✅ JWT token认证
- ✅ 角色权限控制
- ✅ 参数校验防止注入
- ✅ 密码加密存储
- ✅ 身份证信息脱敏
- ✅ 请求日志记录

### 代码质量

- ✅ 零语法错误
- ✅ 零类型错误
- ✅ 完整的参数校验
- ✅ 统一的错误处理
- ✅ 详细的代码注释

---

## 📈 性能优化建议

1. **缓存优化**
   - 使用Redis缓存热点数据
   - 缓存用户信息和权限

2. **数据库优化**
   - 添加必要的索引
   - 使用分页查询
   - 避免N+1查询问题

3. **并发处理**
   - 使用Gunicorn多进程部署
   - 考虑使用Celery处理异步任务

---

## 🧪 测试

### 单元测试

```bash
# 运行所有测试
pytest tests/

# 运行特定模块测试
pytest tests/test_user_api.py

# 查看测试覆盖率
pytest --cov=app tests/
```

### 接口测试

推荐使用Postman或类似工具测试API接口，导入API文档即可快速测试。

---

## 📖 文档

- **[API_USAGE.md](./API_USAGE.md)**: 详细的API使用文档，包含所有接口的请求示例和响应格式
- **README.md**: 本文件，快速入门和概览

---

## 🔄 版本历史

### v1.0.0 (2025-12-18)

- ✅ 完成所有6个模块共40个API接口的实现
- ✅ 所有接口都使用参数校验中间件
- ✅ 所有接口都实现了认证和权限控制
- ✅ 更新完整的API使用文档

### v2.1.0 (2025-12-20)

- ✅ 新增通知模块接口（创建、发送、查询、统计、状态变更）
- ✅ 增补通知权限编码并同步文档
- ✅ 用户绑定/解绑/修改密码/列表接口补充参数校验
- ✅ 用电数据查询和人工录入接口重构，权限校验上移到API层

### v2.1.0 (2025-12-20)

- ✅ 新增通知模块（创建、发送、查询、统计、状态变更）
- ✅ 补充通知相关权限编码与校验
- ✅ 用户绑定/解绑/修改密码/用户列表接口补充参数校验

---

## ⚠️ 注意事项

1. **Token管理**: Token默认2小时过期，过期后需要重新登录
2. **密码安全**: 密码在数据库中加密存储，不可逆
3. **数据脱敏**: 身份证号返回时中间8位已脱敏
4. **电表绑定**: 一个电表只能绑定一个用户，且必须在同一片区
5. **账单限制**: 有未支付账单的电表无法解绑

---

## 📞 联系方式

如有问题或建议，请提交Issue或联系开发团队。

---

**开发完成时间**: 2025年12月18日  
**总接口数**: 40个  
**代码行数**: 2000+行  
**文档完整性**: ✅ 完整
