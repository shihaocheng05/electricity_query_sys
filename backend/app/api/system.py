# 系统管理接口（权限、电价调整）
from flask import Blueprint, request, jsonify, g
from app.services.system_service import SystemServices
from app.middleware import (
    BusinessException, check_permission,
    ValidateCreatePricePolicy, ValidateUpdatePricePolicy,
    ValidateCreateRegion, ValidateUpdateRegion,
    ValidateUpdateUserRole, ValidateGetPricePolicyList,
    ValidateGetRegionList, ValidateGetSystemLogs
)
from app.utils.common import validate_request
from datetime import datetime

# 创建系统管理蓝图
system_bp = Blueprint("system", __name__)


@system_bp.route("/price-policy/create", methods=["POST"])
@check_permission(require_super_admin=True)
@validate_request(ValidateCreatePricePolicy)
def create_price_policy():
    """
    创建电价策略接口（仅超级管理员）
    ---
    请求体:
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
        ],
        "time_share_rules": null
    }
    """
    try:
        validated_data = request.validate_data
        
        result = SystemServices.create_price_policy(
            policy_name=validated_data.get("policy_name"),
            price_type=validated_data.get("price_type"),
            region_id=validated_data.get("region_id"),
            base_unit_price=validated_data.get("base_unit_price"),
            start_time=validated_data.get("start_time"),
            end_time=validated_data.get("end_time"),
            ladder_rules=validated_data.get("ladder_rules"),
            time_share_rules=validated_data.get("time_share_rules")
        )
        
        return jsonify({
            "success": True,
            "message": "电价策略创建成功",
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
            "message": f"电价策略创建失败：{str(e)}",
            "code": 500
        }), 500


@system_bp.route("/price-policy/update", methods=["PUT"])
@check_permission(require_super_admin=True)
@validate_request(ValidateUpdatePricePolicy)
def update_price_policy():
    """
    更新电价策略接口（仅超级管理员）
    ---
    请求体:
    {
        "policy_id": 1,
        "policy_name": "新策略名称",
        "base_unit_price": 0.6,
        "is_active": true,
        "end_time": "2026-12-31 23:59:59"
    }
    """
    try:
        validated_data = request.validate_data
        print(f"[DEBUG] 更新价格策略收到的数据: {validated_data}")
        
        policy_id = validated_data.pop("policy_id")
        print(f"[DEBUG] policy_id: {policy_id}, 剩余数据: {validated_data}")
        
        result = SystemServices.update_price_policy(
            policy_id=policy_id,
            **validated_data
        )
        
        return jsonify({
            "success": True,
            "message": "电价策略更新成功",
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
            "message": f"电价策略更新失败：{str(e)}",
            "code": 500
        }), 500


@system_bp.route("/price-policy/list", methods=["GET"])
@check_permission(require_permit="query_permission")
@validate_request(ValidateGetPricePolicyList)
def get_price_policy_list():
    """
    获取电价策略列表接口（仅管理员）
    ---
    Query参数:
        region_id: 片区ID（可选）
        is_active: 是否激活（可选，true/false�?
        page: 页码（默�?�?
        per_page: 每页数量（默�?0�?
    """
    try:
        validated_data = request.validate_data
        
        result = SystemServices.get_price_policy_list(
            region_id=validated_data.get("region_id"),
            is_active=validated_data.get("is_active"),
            page=validated_data.get("page", 1),
            per_page=validated_data.get("per_page", 20)
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


@system_bp.route("/price-policy/<int:policy_id>", methods=["DELETE"])
@check_permission(require_super_admin=True)
def delete_price_policy(policy_id):
    """
    删除电价策略接口（仅超级管理员）
    ---
    URL参数:
        policy_id: 策略ID
    """
    try:
        result = SystemServices.delete_price_policy(policy_id)
        
        return jsonify({
            "success": True,
            "message": "删除成功",
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
            "message": f"删除失败：{str(e)}",
            "code": 500
        }), 500


@system_bp.route("/region/create", methods=["POST"])
@check_permission(require_super_admin=True)
@validate_request(ValidateCreateRegion)
def create_region():
    """
    创建片区接口（仅超级管理员）
    ---
    请求�?
    {
        "region_name": "朝阳�?,
        "region_code": "BJ-CY",
        "manager_id": 2,
        "description": "北京市朝阳区"
    }
    """
    try:
        validated_data = request.validate_data
        
        result = SystemServices.create_region(
            **validated_data
        )
        
        return jsonify({
            "success": True,
            "message": "片区创建成功",
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
            "message": f"片区创建失败：{str(e)}",
            "code": 500
        }), 500


@system_bp.route("/region/update", methods=["PUT"])
@check_permission(require_super_admin=True)
@validate_request(ValidateUpdateRegion)
def update_region():
    """
    更新片区接口（仅超级管理员）
    ---
    请求�?
    {
        "region_id": 1,
        "region_name": "新片区名�?,
        "manager_id": 3,
        "description": "更新的描�?
    }
    """
    try:
        validated_data = request.validate_data
        
        region_id = validated_data.pop("region_id")
        
        result = SystemServices.update_region(
            region_id=region_id,
            **validated_data
        )
        
        return jsonify({
            "success": True,
            "message": "片区更新成功",
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
            "message": f"片区更新失败：{str(e)}",
            "code": 500
        }), 500


@system_bp.route("/region/list", methods=["GET"])
@check_permission(require_permit="query_permission")
@validate_request(ValidateGetRegionList)
def get_region_list():
    """
    获取片区列表接口（需要登录）
    ---
    Query参数:
        page: 页码（默�?�?
        per_page: 每页数量（默�?0�?
    """
    try:
        validated_data = request.validate_data
        
        result = SystemServices.get_region_list(
            page=validated_data.get("page", 1),
            per_page=validated_data.get("per_page", 20)
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


@system_bp.route("/region/<int:region_id>", methods=["DELETE"])
@check_permission(require_super_admin=True)
def delete_region(region_id):
    """
    删除片区接口（仅超级管理员）
    ---
    URL参数:
        region_id: 片区ID
    """
    try:
        result = SystemServices.delete_region(region_id)
        
        return jsonify({
            "success": True,
            "message": "删除成功",
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
            "message": f"删除失败：{str(e)}",
            "code": 500
        }), 500


@system_bp.route("/user/update-role", methods=["PUT"])
@check_permission(require_super_admin=True)
@validate_request(ValidateUpdateUserRole)
def update_user_role():
    """
    更新用户角色接口（仅超级管理员）
    ---
    请求�?
    {
        "user_id": 1,
        "new_role": "AREA_ADMIN"
    }
    """
    try:
        admin_id = g.user_id
        validated_data = request.validate_data
        
        result = SystemServices.update_user_role(
            admin_id=admin_id,
            user_id=validated_data.get("user_id"),
            new_role=validated_data.get("new_role")
        )
        
        return jsonify({
            "success": True,
            "message": "用户角色更新成功",
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
            "message": f"用户角色更新失败：{str(e)}",
            "code": 500
        }), 500


@system_bp.route("/logs", methods=["GET"])
@check_permission(require_permit="query_permission")
@validate_request(ValidateGetSystemLogs)
def get_system_logs():
    """
    获取系统日志接口（仅管理员）
    ---
    Query参数:
        log_type: 日志类型（可选）
        log_level: 日志级别（可选）
        module: 模块名称（可选）
        start_time: 开始时间（可选）
        end_time: 结束时间（可选）
        page: 页码（默�?�?
        per_page: 每页数量（默�?0�?
    """
    try:
        validated_data = request.validate_data
        
        start_time = validated_data.get("start_time")
        end_time = validated_data.get("end_time")
        
        if start_time:
            start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        if end_time:
            end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
        
        result = SystemServices.query_system_logs(
            log_type=validated_data.get("log_type"),
            log_level=validated_data.get("log_level"),
            module=validated_data.get("module"),
            start_time=start_time,
            end_time=end_time,
            page=validated_data.get("page"),
            per_page=validated_data.get("per_page")
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
