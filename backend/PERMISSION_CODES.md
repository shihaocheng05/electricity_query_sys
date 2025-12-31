# 权限编码系统文档

## 权限逻辑总览

权限系统采用三层级权限模型：

1. **超级管理员(SUPER_ADMIN)**：拥有所有权限，无需权限检查
2. **片区管理员(AREA_ADMIN)**：拥有被赋予的权限，可操作本片区内的用户和资源
3. **普通居民(RESIDENT)**：拥有被赋予的权限，仅可操作自己的资源

## 权限编码表

### 查询模块（Query）
| 权限编码 | 说明 | 适用角色 | 操作范围 |
|---------|------|---------|---------|
| `query_user` | 查询用户信息 | AREA_ADMIN, RESIDENT | 本片区用户/自己 |
| `query_meter` | 查询电表信息 | AREA_ADMIN, RESIDENT | 本片区电表/自己的电表 |
| `query_iot` | 查询用电数据及分析 | AREA_ADMIN, RESIDENT | 本片区数据/自己的数据 |
| `query_bill` | 查询账单信息 | AREA_ADMIN, RESIDENT | 本片区账单/自己的账单 |
| `query_notification` | 查询通知与统计 | AREA_ADMIN, RESIDENT | 本片区通知/自己的通知 |
| `query_permission` | 查询系统权限和日志 | AREA_ADMIN | 系统权限管理 |

### 修改模块（Edit）
| 权限编码 | 说明 | 适用角色 | 操作范围 |
|---------|------|---------|---------|
| `edit_user` | 修改用户信息、修改密码 | AREA_ADMIN, RESIDENT | 本片区用户/自己 |
| `edit_meter` | 修改电表状态、添加记录、验证读数 | AREA_ADMIN | 本片区电表 |
| `edit_bill` | 生成账单、支付、发送提醒、批量生成 | AREA_ADMIN | 本片区账单 |
| `edit_iot` | 汇总用电数据、手工录入 | AREA_ADMIN | 本片区数据 |
| `edit_notification` | 创建、发送、更新通知 | AREA_ADMIN | 本片区用户 |

### 绑定模块（Bind/Unbind）
| 权限编码 | 说明 | 适用角色 | 操作范围 |
|---------|------|---------|---------|
| `bind_meter` | 为用户绑定电表 | AREA_ADMIN | 本片区用户 |
| `unbind_meter` | 为用户解绑电表 | AREA_ADMIN, RESIDENT | 本片区用户/自己 |

### 报修模块（Report）
| 权限编码 | 说明 | 适用角色 | 操作范围 |
|---------|------|---------|---------|
| `report_meter` | 电表报修 | AREA_ADMIN, RESIDENT | 本片区电表/自己的电表 |

## 完整API权限映射表

### User 模块
| 接口 | 方法 | 路由 | 权限编码 | 说明 |
|------|------|------|---------|------|
| register | POST | /user/register | - | 无权限限制（公开接口） |
| login | POST | /user/login | - | 无权限限制（公开接口） |
| get_user_info | GET | /user/info | `query_user` | 查询用户信息 |
| update_user_info | PUT | /user/update | `edit_user` | 修改用户信息 |
| bind_meter | POST | /user/bind-meter | `bind_meter` | 为用户绑定电表 |
| unbind_meter | POST | /user/unbind-meter | `unbind_meter` | 为用户解绑电表 |
| get_user_meters | GET | /user/meters | `query_meter` | 查询用户电表列表 |
| change_password | POST | /user/change-password | `edit_user` | 修改密码 |
| get_user_list | GET | /user/list | `query_user` | 查询用户列表（管理员） |

### Meter 模块
| 接口 | 方法 | 路由 | 权限编码 | 说明 |
|------|------|------|---------|------|
| install_meter | POST | /meter/install | `bind_meter` | 安装电表 |
| update_meter_status | PUT | /meter/update-status | `edit_meter` | 更新电表状态 |
| add_meter_record | POST | /meter/add-record | `edit_meter` | 添加电表记录 |
| repair_meter | POST | /meter/repair | `report_meter` | 电表报修 |
| validate_meter_reading | POST | /meter/validate-reading | `edit_meter` | 验证电表读数 |
| query_meters | GET | /meter/query | `query_meter` | 查询电表列表 |
| query_meter_records | GET | /meter/records/<id> | `query_meter` | 查询电表记录 |

### Bill 模块
| 接口 | 方法 | 路由 | 权限编码 | 说明 |
|------|------|------|---------|------|
| create_bill | POST | /bill/create | `edit_bill` | 生成账单 |
| pay_bill | POST | /bill/pay | `pay_bill` | 支付账单 |
| query_bills | GET | /bill/query | `query_bill` | 查询账单列表 |
| get_bill_detail | GET | /bill/detail/<id> | `query_bill` | 获取账单详情 |
| send_reminder | POST | /bill/reminder/<id> | `edit_bill` | 发送账单提醒 |
| batch_create_bills | POST | /bill/batch-create | `edit_bill` | 批量生成账单 |

### Usage 模块
| 接口 | 方法 | 路由 | 权限编码 | 说明 |
|------|------|------|---------|------|
| receive_iot_data | POST | /usage/iot-upload | - | IoT数据上传（无权限限制） |
| aggregate_usage | POST | /usage/aggregate | `edit_iot` | 汇总用电数据 |
| query_usage_data | GET | /usage/query | `query_iot` | 查询用电数据 |
| get_iot_data | GET | /usage/iot-data/<id> | `query_iot` | 获取IoT数据 |
| manual_input_data | POST | /usage/manual-input | `edit_iot` | 手工录入数据 |

### Query 模块
| 接口 | 方法 | 路由 | 权限编码 | 说明 |
|------|------|------|---------|------|
| analyze_user_electricity | GET | /query/analyze/user | `query_iot` | 个人用电分析 |
| analyze_region_electricity | GET | /query/analyze/region | `query_iot` | 片区用电分析 |
| get_ranking | GET | /query/ranking | `query_iot` | 用电排名 |
| get_statistics_summary | GET | /query/statistics/summary | `query_iot` | 统计概览 |
| export_data | GET | /query/export | `query_iot` | 导出数据（片区管理员导出其管辖的片区数据） |

### Notification 模块
| 接口 | 方法 | 路由 | 权限编码 | 说明 |
|------|------|------|---------|------|
| create_notification | POST | /notification/create | `edit_notification` | 创建通知 |
| send_notification | POST | /notification/send | `edit_notification` | 发送/重试通知 |
| query_notifications | GET | /notification/query | `query_notification` | 查询通知列表 |
| get_notification_statistics | GET | /notification/statistics | `query_notification` | 查询通知统计 |
| update_notification_status | PUT | /notification/update-status | `edit_notification` | 更新通知状态 |

### System 模块
| 接口 | 方法 | 路由 | 权限编码 | 说明 |
|------|------|------|---------|------|
| create_price_policy | POST | /system/price-policy/create | - | 创建电价策略（超管专属） |
| update_price_policy | PUT | /system/price-policy/update | - | 更新电价策略（超管专属） |
| get_price_policy_list | GET | /system/price-policy/list | `query_permission` | 查询电价策略列表 |
| create_region | POST | /system/region/create | - | 创建片区（超管专属） |
| update_region | PUT | /system/region/update | - | 更新片区（超管专属） |
| get_region_list | GET | /system/region/list | `query_permission` | 查询片区列表 |
| update_user_role | PUT | /system/user/update-role | - | 更新用户角色（超管专属） |
| get_system_logs | GET | /system/logs | `query_permission` | 查询系统日志 |

注：系统管理服务层函数不接收 `admin_id`/`admin_name`，权限与日志由 API 层统一处理。

## 装饰器参数说明

### check_permission 装饰器参数

```python
@check_permission(target_param="target_user_id", require_admin=False, require_permit=None)
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `target_param` | str | 从请求中提取目标用户ID的参数名（默认"target_user_id"） |
| `require_admin` | bool | 是否强制要求管理员权限（已弃用，由require_permit替代） |
| `require_permit` | str | 所需的权限编码（None表示无特定权限要求） |

## 权限检查流程

```
请求到达
  ↓
AuthMiddleware 验证JWT token
  ↓
check_permission 装饰器
  ├─ 是否认证 → 否 → 401
  ├─ 用户是否存在 → 否 → 404
  ├─ 是否超管 → 是 → 通过
  ├─ 提取目标用户ID
  └─ 根据角色检查权限
      ├─ AREA_ADMIN
      │   ├─ 检查权限编码 → 无 → 403
      │   ├─ 检查片区 → 不同 → 403
      │   └─ 通过
      └─ RESIDENT
          ├─ 检查是否操作自己 → 否 → 403
          ├─ 检查权限编码 → 无 → 403
          └─ 通过
  ↓
API处理函数
```

## 权限写入说明

超级管理员可通过系统API将权限写入权限表。权限表记录结构：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int | 权限ID |
| `perm_code` | str | 权限编码（如 "query_meter", "edit_user"） |
| `perm_name` | str | 权限名称 |
| `perm_desc` | str | 权限描述 |
| `role_id` | int | 角色ID（与该权限关联的角色） |

超管可创建权限 → 分配给角色 → 系统检查用户权限。
