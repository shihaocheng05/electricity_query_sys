# 电表模块接口（安装、状态、报修）
from flask import Blueprint, request, jsonify, g
from app.services.meter_sevice import MeterServices
from app.middleware import BusinessException, check_permission
from app.middleware import (
    ValidateMeterInstall, 
    ValidateMeterUpdateStatus,
    ValidateAddMeterRecord,
    ValidateMeterRepair,
    ValidateMeterReading,
    ValidateQueryMeters,
    ValidateQueryMeterRecordsParams
)
from app.utils.common import validate_request
from app.models import RoleEnum,Region,Meter,User

# 创建电表蓝图
meter_bp = Blueprint("meter", __name__)


@meter_bp.route("/install", methods=["POST"])
@check_permission(target_param="target_user_id", require_permit="bind_meter")  # 需要bind_meter权限
@validate_request(ValidateMeterInstall)
def install_meter():
    """
    安装电表接口（仅管理员）
    ---
    请求�?
    {
        "target_user_id": 1,
        "region_id": 1,
        "current_region_id": 1,
        "install_address": "北京市朝阳区XX路XX�?
    }
    """
    try:
        data = request.validate_data
        
        result = MeterServices.meter_install(
            user_id=data.get("target_user_id"),
            region_id=data.get("region_id"),
            current_region_id=data.get("current_region_id"),
            install_address=data.get("install_address")
        )
        
        return jsonify({
            "success": True,
            "message": "电表安装成功",
            "data": result
        }), 201
        
    except BusinessException as e:
        return jsonify({
            "success": False,
            "message": e.msg,
            "code": e.code
        }), e.code
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"电表安装失败：{str(e)}",
            "code": 500
        }), 500


@meter_bp.route("/update-status", methods=["PUT"])
@check_permission(require_permit="edit_meter")  # 需要edit_meter权限，装饰器已处理片区检�?
@validate_request(ValidateMeterUpdateStatus)
def update_meter_status():
    """
    更新电表状态接口（仅管理员�?
    ---
    请求�?
    {
        "meter_id": 1,
        "new_status": "NORMAL"
    }
    """
    try:
        data = request.validate_data
        meter_id=data.get("meter_id")
            
        result = MeterServices.meter_update_status(
            meter_id=meter_id,
            new_status=data.get("new_status")
        )
        
        return jsonify({
            "success": True,
            "message": "电表状态更新成功",
            "data": result
        }), 200
        
    except BusinessException as e:
        return jsonify({
            "success": False,
            "message": e.msg,
            "code": e.code
        }), e.code
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"电表状态更新失败：{str(e)}",
            "code": 500
        }), 500


@meter_bp.route("/add-record", methods=["POST"])
@check_permission(require_permit="edit_meter")  # 需要edit_meter权限
@validate_request(ValidateAddMeterRecord)
def add_meter_record():
    """
    添加电表操作记录接口（仅管理员）
    ---
    请求�?
    {
        "meter_id": 1,
        "record_type": "MAINTAIN",
        "operator": "张三",
        "content": "更换电表",
        "attach_img": "http://example.com/image.jpg"
    }
    """
    try:
        data = request.validate_data
        
        result = MeterServices.add_meter_records(
            meter_id=data.get("meter_id"),
            record_type=data.get("record_type"),
            operator=data.get("operator"),
            content=data.get("content"),
            attach_img=data.get("attach_img")
        )
        
        return jsonify({
            "success": True,
            "message": "电表记录添加成功",
            "data": result
        }), 201
        
    except BusinessException as e:
        return jsonify({
            "success": False,
            "message": e.msg,
            "code": e.code
        }), e.code
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"电表记录添加失败：{str(e)}",
            "code": 500
        }), 500


@meter_bp.route("/repair", methods=["POST"])
@check_permission(require_permit="report_meter")  # 需要report_meter权限（新增权限编码）
@validate_request(ValidateMeterRepair)
def repair_meter():
    """
    电表报修接口（需要登录）
    ---
    请求�?
    {
        "meter_id": 1,
        "user_id": 1,
        "fault_address": "北京市朝阳区XX路XX�?,
        "fault_description": "电表无法读数",
        "attach_img": "http://example.com/image.jpg"
    }
    """
    try:
        user_id = g.user_id
        data = request.validate_data
        
        result = MeterServices.notify_meter_repair(
            meter_id=data.get("meter_id"),
            user_id=user_id,
            fault_address=data.get("fault_address"),
            fault_description=data.get("fault_description"),
            attach_img=data.get("attach_img")
        )
        
        return jsonify({
            "success": True,
            "message": result.get("message"),
            "data": result
        }), 201
        
    except BusinessException as e:
        return jsonify({
            "success": False,
            "message": e.msg,
            "code": e.code
        }), e.code
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"电表报修失败：{str(e)}",
            "code": 500
        }), 500


@meter_bp.route("/validate-reading", methods=["POST"])
@check_permission(require_permit="edit_meter")  # 需要edit_meter权限
@validate_request(ValidateMeterReading)
def validate_meter_reading():
    """
    校验电表读数接口（仅管理员）
    ---
    请求�?
    {
        "meter_id": 1,
        "new_reading": 1234.5,
        "reading_time": "2025-12-18 10:00:00"
    }
    """
    try:
        data = request.validate_data
        
        result = MeterServices.validate_meter_reading(
            meter_id=data.get("meter_id"),
            new_reading=data.get("new_reading"),
            reading_time=data.get("reading_time")
        )
        
        return jsonify({
            "success": True,
            "message": "读数校验完成",
            "data": result
        }), 200
        
    except BusinessException as e:
        return jsonify({
            "success": False,
            "message": e.msg,
            "code": e.code
        }), e.code
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"读数校验失败：{str(e)}",
            "code": 500
        }), 500


@meter_bp.route("/query", methods=["GET"])
@check_permission(require_permit="query_meter")  # 需要query_meter权限
@validate_request(ValidateQueryMeters)
def query_meters():
    """
    查询电表列表接口（需要登录）
    ---
    Query参数:
        region_id: 片区ID（可选）
        meter_status: 电表状态（可选）
        meter_type: 电表类型（可选）
        page: 页码（默�?�?
        per_page: 每页数量（默�?0�?
    """
    try:
        user_id = g.user_id
        data = request.validate_data
        
        # 获取用户角色和片区信�?
        from ..models import User, Region
        user = User.query.get(user_id)
        user_role = user.role.name.value if user and user.role else "RESIDENT"
        
        # 根据角色调整查询参数
        query_user_id = None
        region_id = data.get("region_id")
        
        if user_role == "RESIDENT":
            # 居民只能查询自己的电�?
            query_user_id = user_id
            region_id = None  # 居民不能跨片区查�?
        elif user_role == "AREA_ADMIN":
            # 片区管理员查询所管辖片区的电�?
            manage_region = Region.query.filter_by(manager_id=user_id).first()
            if manage_region:
                region_id = manage_region.id
            else:
                raise BusinessException("片区管理员未分配片区", 403)
        # SUPER_ADMIN 可以查询所有电表，可以指定片区筛�?
        
        result = MeterServices.query_meters(
            user_id=query_user_id,
            region_id=region_id,
            meter_status=data.get("meter_status"),
            meter_type=data.get("meter_type"),
            page=data.get("page"),
            per_page=data.get("per_page")
        )
        
        return jsonify({
            "success": True,
            "message": "查询成功",
            "data": result
        }), 200
        
    except BusinessException as e:
        return jsonify({
            "success": False,
            "message": e.msg,
            "code": e.code
        }), e.code
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"查询失败：{str(e)}",
            "code": 500
        }), 500


@meter_bp.route("/records/<int:meter_id>", methods=["GET"])
@check_permission(require_permit="query_meter")  # 需要query_meter权限
@validate_request(ValidateQueryMeterRecordsParams)
def query_meter_records(meter_id):
    """
    查询电表操作记录接口（需要登录）
    ---
    URL参数:
        meter_id: 电表ID
    Query参数:
        record_type: 记录类型（可选）
        page: 页码（默�?�?
        per_page: 每页数量（默�?0�?
    """
    try:
        data = request.validate_data
        
        result = MeterServices.query_meter_records(
            meter_id=meter_id,
            record_type=data.get("record_type"),
            page=data.get("page"),
            per_page=data.get("per_page")
        )
        
        return jsonify({
            "success": True,
            "message": "查询成功",
            "data": result
        }), 200
        
    except BusinessException as e:
        return jsonify({
            "success": False,
            "message": e.msg,
            "code": e.code
        }), e.code
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"查询失败：{str(e)}",
            "code": 500
        }), 500
