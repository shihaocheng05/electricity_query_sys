# 参数校验（Pydantic封装�?
from pydantic import BaseModel,field_validator,Field
from typing import Optional, List
from datetime import datetime
import re
from ..models import NoticeType, SendChannel,MeterStatus, MeterType, RecordType,RoleEnum

#服务基本�?
class BaseServerModel(BaseModel):
    model_config={
        "extra":"ignore",
        "str_strip_whitespace":True,
        "validate_assignment":True
    }

# ============ 用户相关验证 ============
#注册和修改都用这个好�?
class ValidateRegister(BaseServerModel):
    mail:str=Field(...,description="邮箱",pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    password:str=Field(...,min_length=6,max_length=20,description="密码")
    real_name:Optional[str]=Field(default=None,min_length=2,max_length=20,description="真名")
    idcard:Optional[str]=Field(default=None,description="身份证号")
    region_id:Optional[int]=Field(default=None,gt=0,description="片区编号")

    @field_validator("idcard")
    def validate_idcard(cls,v):
        if v is None or v == "":
            return None
        # 放宽验证：支持15位或18位身份证号
        v = v.strip()
        if len(v) not in [15, 18]:
            raise ValueError("身份证号码应为15位或18位")
        # 18位身份证：前17位数字，最后一位数字或X
        if len(v) == 18:
            if not v[:17].isdigit():
                raise ValueError("身份证号码格式错误")
            if not (v[17].isdigit() or v[17].upper() == 'X'):
                raise ValueError("身份证号码最后一位应为数字或X")
        # 15位身份证：全部为数字
        elif len(v) == 15:
            if not v.isdigit():
                raise ValueError("15位身份证号码应全为数字")
        return v

#修改用户信息时的模型类（不包含密码修改）
class ValidateUpdateUser(BaseServerModel):
    mail: Optional[str] = Field(default=None, description="邮箱", pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    real_name: Optional[str] = Field(default=None, min_length=2, max_length=20, description="真名")
    idcard: Optional[str] = Field(default=None, description="身份证号")
    region_id: Optional[int] = Field(default=None, gt=0, description="片区编号")

    @field_validator("idcard")
    def validate_idcard(cls, v):
        if v is None or v == "":
            return None
        if len(v) != 18 or not v[:-1].isdigit():
            raise ValueError("身份证号码格式错误！")
        return v
    
#登录的pydantic模型�?
class ValidateLogin(BaseServerModel):
    mail:str=Field(...,description="邮箱",pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    password:str=Field(...,min_length=6,max_length=20,description="密码")

# 发送重置密码验证码的模型类
class ValidateSendResetCode(BaseServerModel):
    mail: str = Field(..., description="邮箱", pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

# 重置密码的模型类
class ValidateResetPassword(BaseServerModel):
    mail: str = Field(..., description="邮箱", pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    code: str = Field(..., min_length=6, max_length=6, description="验证码", pattern=r"^\d{6}$")
    new_password: str = Field(..., min_length=6, max_length=20, description="新密码")


#绑定电表的模型类
class ValidateBindMeter(BaseServerModel):
    target_user_id: int = Field(..., gt=0, description="目标用户ID")
    meter_code: str = Field(..., min_length=1, max_length=50, description="电表编码")

#解绑电表的模型类
class ValidateUnbindMeter(BaseServerModel):
    target_user_id: int = Field(..., gt=0, description="目标用户ID")
    meter_id: int = Field(..., gt=0, description="电表ID")

#修改密码的模型类
class ValidateChangePassword(BaseServerModel):
    old_password: str = Field(..., min_length=6, max_length=20, description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=20, description="新密码")

#查询用户列表的模型类
class ValidateGetUserList(BaseServerModel):
    page: int = Field(default=1, gt=0, description="页码")
    per_page: int = Field(default=20, gt=0, le=100, description="每页数量")
    region_id: Optional[int] = Field(default=None, gt=0, description="片区ID")
    keyword: Optional[str] = Field(default=None, max_length=50, description="搜索关键字")

# ============ 通知相关验证 ============
#创建通知时的模型�?
class ValidateCreateNotification(BaseServerModel):
    notice_type: NoticeType = Field(..., description="通知类型")
    target_type:RoleEnum=Field(...,description="通知对象类型")
    target_ids: List[int] = Field(..., min_length=1, description="目标用户ID列表")
    title: str = Field(..., min_length=1, max_length=100, description="通知标题")
    content: str = Field(..., min_length=1, max_length=1000, description="通知内容")
    send_channel: SendChannel = Field(..., description="发送渠道")
    send_time: Optional[datetime] = Field(default=None, description="发送时间")
    is_batch: bool = Field(default=False, description="是否群发")
    related_id: Optional[int] = Field(default=None, gt=0, description="关联业务ID")

#查询通知的模型类
class ValidateQueryNotification(BaseServerModel):
    user_id: Optional[int] = Field(default=None, gt=0, description="用户ID")
    notify_type: Optional[str] = Field(default=None, description="通知类型")
    status: Optional[str] = Field(default=None, description="通知状态")
    is_unread_only: bool = Field(default=False, description="是否只查询未读通知")
    page: int = Field(default=1, gt=0, description="页码")
    per_page: int = Field(default=20, gt=0, le=100, description="每页数量")

#发送通知的模型类
class ValidateSendNotification(BaseServerModel):
    notification_id: Optional[int] = Field(default=None, gt=0, description="通知ID")
    batch_id: Optional[str] = Field(default=None, min_length=1, max_length=20, description="批次ID")
    
    @field_validator("notification_id", "batch_id")
    def validate_ids(cls, v, info):
        # 确保至少提供一个ID
        if info.field_name == "batch_id":
            return v
        return v

#更新通知状态的模型�?
class ValidateUpdateNotificationStatus(BaseServerModel):
    notification_id: int = Field(..., gt=0, description="通知ID")
    action: str = Field(..., pattern="^(mark_read|retry)$", description="操作类型")
    user_id: Optional[int] = Field(default=None, gt=0, description="用户ID")

# ============ 电表相关验证 ============
#电表安装的模型类
class ValidateMeterInstall(BaseServerModel):
    user_id: int = Field(..., gt=0, description="用户ID")
    region_id: int = Field(..., gt=0, description="片区ID")
    current_region_id: int = Field(..., gt=0, description="当前片区ID")
    install_address: str = Field(..., min_length=5, max_length=100, description="安装地址")

#更新电表状态的模型�?
class ValidateMeterUpdateStatus(BaseServerModel):
    meter_id: int = Field(..., gt=0, description="电表ID")
    new_status: MeterStatus = Field(..., description="新状态")

#添加电表记录的模型类
class ValidateAddMeterRecord(BaseServerModel):
    meter_id: int = Field(..., gt=0, description="电表ID")
    record_type: RecordType = Field(..., description="记录类型")
    operator: str = Field(..., min_length=2, max_length=20, description="操作人员")
    content: Optional[str] = Field(default=None, max_length=200, description="操作内容")
    attach_img: Optional[str] = Field(default=None, max_length=256, description="附件图片URL")

#电表报修的模型类
class ValidateMeterRepair(BaseServerModel):
    meter_id: int = Field(..., gt=0, description="电表ID")
    user_id: int = Field(..., gt=0, description="用户ID")
    fault_address: str = Field(..., min_length=5, max_length=100, description="故障地址")
    fault_description: str = Field(..., min_length=5, max_length=500, description="故障描述")
    attach_img: Optional[str] = Field(default=None, max_length=256, description="附件图片URL")

#电表读数校验的模型类
class ValidateMeterReading(BaseServerModel):
    meter_id: int = Field(..., gt=0, description="电表ID")
    new_reading: float = Field(..., ge=0, description="新读数")
    reading_time: Optional[datetime] = Field(default=None, description="读数时间")

#电表查询的模型类
class ValidateQueryMeters(BaseServerModel):
    user_id: Optional[int] = Field(default=None, gt=0, description="用户ID")
    region_id: Optional[int] = Field(default=None, gt=0, description="片区ID")
    meter_status: Optional[MeterStatus] = Field(default=None, description="电表状态")
    meter_type: Optional[MeterType] = Field(default=None, description="电表类型")
    page: int = Field(default=1, gt=0, description="页码")
    per_page: int = Field(default=20, gt=0, le=100, description="每页数量")

#查询电表记录的模型类
class ValidateQueryMeterRecords(BaseServerModel):
    meter_id: int = Field(..., gt=0, description="电表ID")
    record_type: Optional[RecordType] = Field(default=None, description="记录类型")
    page: int = Field(default=1, gt=0, description="页码")
    per_page: int = Field(default=20, gt=0, le=100, description="每页数量")

#查询电表记录的Query参数模型类（不包含meter_id，因为meter_id在URL路径中）
class ValidateQueryMeterRecordsParams(BaseServerModel):
    record_type: Optional[RecordType] = Field(default=None, description="记录类型")
    page: int = Field(default=1, gt=0, description="页码")
    per_page: int = Field(default=20, gt=0, le=100, description="每页数量")

# ============ 用电数据相关验证 ============
#IoT数据上传的模型类
class ValidateIoTData(BaseServerModel):
    meter_id: int = Field(..., gt=0, description="电表ID")
    electricity: float = Field(..., ge=0, description="用电量")
    collect_time: datetime = Field(..., description="采集时间")
    voltage: Optional[float] = Field(default=None, ge=0, le=500, description="电压")
    current: Optional[float] = Field(default=None, ge=0, le=1000, description="电流")

#用电数据查询的模型类
class ValidateQueryUsageData(BaseServerModel):
    meter_id: int = Field(..., gt=0, description="电表ID")
    usage_type: Optional[str] = Field(default=None, pattern="^(DAY|MONTH)$", description="汇总类型")
    start_date: Optional[datetime] = Field(default=None, description="开始日期")
    end_date: Optional[datetime] = Field(default=None, description="结束日期")
    page: int = Field(default=1, gt=0, description="页码")
    per_page: int = Field(default=20, gt=0, le=100, description="每页数量")
    
    @field_validator("end_date")
    def validate_date_range(cls, v, info):
        if v and info.data.get("start_date") and v < info.data["start_date"]:
            raise ValueError("结束日期不能早于开始日期")
        return v

# ============ 账单相关验证 ============
class ValidateCreateBill(BaseServerModel):
    bill_month: str = Field(..., description="账单月份", pattern=r"^\d{4}-\d{2}-\d{2}$")
    meter_id: int = Field(..., gt=0, description="电表ID")


class ValidatePayBill(BaseServerModel):
    bill_id: int = Field(..., gt=0, description="账单ID")
    payment_amount: float = Field(..., gt=0, description="支付金额")
    payment_method: str = Field(..., description="支付方式")


class ValidateQueryBills(BaseServerModel):
    user_id: Optional[int] = Field(default=None, gt=0, description="用户ID")
    meter_id: Optional[int] = Field(default=None, gt=0, description="电表ID")
    status: Optional[str] = Field(default=None, description="账单状态")
    start_month: Optional[str] = Field(default=None, description="开始月份")
    end_month: Optional[str] = Field(default=None, description="结束月份")
    page: int = Field(default=1, gt=0, description="页码")
    per_page: int = Field(default=20, gt=0, le=100, description="每页数量")


# ============ 用电汇总相关验�?============
class ValidateAggregateUsage(BaseServerModel):
    meter_id: int = Field(..., gt=0, description="电表ID")
    usage_type: str = Field(..., pattern="^(DAY|MONTH)$", description="汇总类型")
    target_date: Optional[str] = Field(default=None, description="目标日期")


# ============ 查询分析相关验证 ============
class ValidateAnalyzeUser(BaseServerModel):
    user_id: Optional[int] = Field(default=None, gt=0, description="用户ID")
    analysis_period: str = Field("month", pattern="^(day|month|year)$", description="分析周期")
    compare_period: bool = Field(default=False, description="是否对比同期")


class ValidateAnalyzeRegion(BaseServerModel):
    region_id: int = Field(..., gt=0, description="片区ID")
    analysis_period: str = Field("month", pattern="^(day|month|year)$", description="分析周期")
    compare_period: bool = Field(default=False, description="是否对比同期")


class ValidateRanking(BaseServerModel):
    region_id: Optional[int] = Field(default=None, gt=0, description="片区ID")
    ranking_type: str = Field(..., pattern="^(electricity|cost)$", description="排名类型")
    time_range: str = Field("month", pattern="^(day|week|month|year)$", description="时间范围")
    limit: int = Field(default=10, gt=0, le=100, description="返回数量")


# ============ 系统管理相关验证 ============
class ValidateCreatePricePolicy(BaseServerModel):
    policy_name: str = Field(..., min_length=2, max_length=50, description="策略名称")
    price_type: str = Field(..., description="价格类型")
    region_id: int = Field(..., gt=0, description="片区ID")
    base_unit_price: float = Field(..., gt=0, description="基础单价")
    start_time: str = Field(..., description="开始时间")
    end_time: Optional[str] = Field(default=None, description="结束时间")
    ladder_rules: Optional[List[dict]] = Field(default=None, description="阶梯规则")
    time_share_rules: Optional[List[dict]] = Field(default=None, description="分时规则")


class ValidateUpdatePricePolicy(BaseServerModel):
    policy_id: int = Field(..., gt=0, description="策略ID")
    policy_name: Optional[str] = Field(default=None, min_length=2, max_length=50, description="策略名称")
    base_unit_price: Optional[float] = Field(default=None, gt=0, description="基础单价")
    is_active: Optional[bool] = Field(default=None, description="是否激活")
    end_time: Optional[str] = Field(default=None, description="结束时间")


class ValidateCreateRegion(BaseServerModel):
    region_name: str = Field(..., min_length=2, max_length=50, description="片区名称")
    region_code: str = Field(..., min_length=2, max_length=20, description="片区编码")
    manager_id: Optional[int] = Field(default=None, gt=0, description="管理员ID")
    description: Optional[str] = Field(default=None, max_length=200, description="描述")


class ValidateUpdateRegion(BaseServerModel):
    region_id: int = Field(..., gt=0, description="片区ID")
    region_name: Optional[str] = Field(default=None, min_length=2, max_length=50, description="片区名称")
    manager_id: Optional[int] = Field(default=None, gt=0, description="管理员ID")
    description: Optional[str] = Field(default=None, max_length=200, description="描述")


class ValidateUpdateUserRole(BaseServerModel):
    user_id: int = Field(..., gt=0, description="用户ID")
    new_role: str = Field(..., description="新角色")


class ValidateGetPricePolicyList(BaseServerModel):
    region_id: Optional[int] = Field(default=None, gt=0, description="片区ID")
    is_active: Optional[bool] = Field(default=None, description="是否激�?")
    page: int = Field(default=1, gt=0, description="页码")
    per_page: int = Field(default=20, gt=0, le=100, description="每页数量")


class ValidateGetRegionList(BaseServerModel):
    page: int = Field(default=1, gt=0, description="页码")
    per_page: int = Field(default=20, gt=0, le=100, description="每页数量")


class ValidateGetSystemLogs(BaseServerModel):
    log_type: Optional[str] = Field(default=None, description="日志类型")
    log_level: Optional[str] = Field(default=None, description="日志级别")
    module: Optional[str] = Field(default=None, description="模块名称")
    start_time: Optional[str] = Field(default=None, description="开始时间")
    end_time: Optional[str] = Field(default=None, description="结束时间")
    page: int = Field(default=1, gt=0, description="页码")
    per_page: int = Field(default=20, gt=0, le=100, description="每页数量")


# ============ 通用分页查询验证 ============
class ValidatePagination(BaseServerModel):
    page: int = Field(default=1, gt=0, description="页码")
    per_page: int = Field(default=20, gt=0, le=100, description="每页数量")


# ============ 数据导出验证 ============
class ValidateExportData(BaseServerModel):
    export_type: str = Field("usage", description="导出类型（usage/bill）")
    region_id: Optional[int] = Field(default=None, gt=0, description="片区ID（可选）")
    start_date: Optional[str] = Field(default=None, description="开始日期（YYYY-MM-DD格式）")
    end_date: Optional[str] = Field(default=None, description="结束日期（YYYY-MM-DD格式）")
    format: str = Field("csv", description="导出格式（csv/excel）")

    @field_validator("export_type")
    def validate_export_type(cls, v):
        if v not in ["usage", "bill"]:
            raise ValueError("导出类型只能是usage或bill")
        return v

    @field_validator("format")
    def validate_format(cls, v):
        if v not in ["csv", "excel"]:
            raise ValueError("导出格式只能�?csv �?excel")
        return v

