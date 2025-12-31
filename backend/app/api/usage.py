# 用电采集接口（IoT接收、人工录入）
from flask import Blueprint, request, jsonify, g
from app.services.usage_service import UsageService
from app.middleware import (
    BusinessException, check_permission,
    ValidateIoTData, ValidateQueryUsageData, ValidateAggregateUsage
)
from app.utils.common import validate_request
from datetime import datetime

# 创建用电数据蓝图
usage_bp = Blueprint("usage", __name__)


@usage_bp.route("/iot-upload", methods=["POST"])
@validate_request(ValidateIoTData)
def receive_iot_data():
    """
    IoT设备上传用电数据接口
    ---
    请求�?
    {
        "meter_id": 1,
        "electricity": 1234.5,
        "collect_time": "2025-12-18 10:00:00",
        "voltage": 220.5,
        "current": 5.2
    }
    """
    try:
        data = request.validate_data
        
        collect_time = data.get("collect_time")
        if isinstance(collect_time, str):
            collect_time = datetime.strptime(collect_time, "%Y-%m-%d %H:%M:%S")
        
        result = UsageService.receive_iot_data(
            meter_id=data.get("meter_id"),
            electricity=data.get("electricity"),
            collect_time=collect_time,
            voltage=data.get("voltage"),
            current=data.get("current")
        )
        
        return jsonify({
            "success": True,
            "message": "数据上传成功",
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
            "message": f"数据上传失败：{str(e)}",
            "code": 500
        }), 500


@usage_bp.route("/aggregate", methods=["POST"])
@check_permission(require_permit="edit_iot")
@validate_request(ValidateAggregateUsage)
def aggregate_usage():
    """
    汇总用电数据接�?
    ---
    请求�?
    {
        "meter_id": 1,
        "usage_type": "DAY",
        "target_date": "2025-12-18"
    }
    """
    try:
        data = request.validate_data
        
        target_date = data.get("target_date")
        if target_date:
            target_date = datetime.strptime(target_date, "%Y-%m-%d")
        
        result = UsageService.aggregate_usage_data(
            meter_id=data.get("meter_id"),
            usage_type=data.get("usage_type"),
            target_date=target_date
        )
        
        return jsonify({
            "success": True,
            "message": "数据汇总成功",
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
            "message": f"数据汇总失败：{str(e)}",
            "code": 500
        }), 500


@usage_bp.route("/query", methods=["GET"])
@check_permission(target_param="meter_id", require_permit="query_iot")
def query_usage_data():
    """
    查询用电数据接口（需要登录）
    ---
    Query参数:
        meter_id: 电表ID（必填）
        usage_type: 汇总类型（可选，DAY/MONTH�?
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）
        page: 页码（默�?�?
        per_page: 每页数量（默�?0�?
    """
    try:
        # 构建查询参数
        meter_id = request.args.get("meter_id")
        if not meter_id:
            raise BusinessException("电表ID不能为空", 400)
        
        query_params = {
            "meter_id": int(meter_id),
            "usage_type": request.args.get("usage_type"),
            "start_date": request.args.get("start_date"),
            "end_date": request.args.get("end_date"),
            "page": int(request.args.get("page", 1)),
            "per_page": int(request.args.get("per_page", 20))
        }
        
        # 使用validator验证
        validated_data = ValidateQueryUsageData(**query_params).model_dump()
        
        # 转换日期格式
        start_date = validated_data.get("start_date")
        end_date = validated_data.get("end_date")
        if start_date and isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date and isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
        
        result = UsageService.query_usage_data(
            meter_id=validated_data.get("meter_id"),
            start_date=start_date,
            end_date=end_date,
            format_type=validated_data.get("usage_type", "hour"),
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


@usage_bp.route("/manual-input", methods=["POST"])
@check_permission(require_permit="edit_iot")
@validate_request(ValidateIoTData)
def manual_input_data():
    """
    人工录入用电数据接口（仅管理员）
    ---
    请求�?
    {
        "meter_id": 1,
        "electricity": 1234.5,
        "collect_time": "2025-12-18 10:00:00",
        "voltage": 220.5,
        "current": 5.2
    }
    """
    try:
        operator_id = g.user_id
        data = request.validate_data
        
        collect_time = data.get("collect_time")
        if isinstance(collect_time, str):
            collect_time = datetime.strptime(collect_time, "%Y-%m-%d %H:%M:%S")
        
        result = UsageService.manual_input_reading(
            meter_id=data.get("meter_id"),
            reading_value=data.get("electricity"),
            reading_time=collect_time,
            operator_id=operator_id,
            voltage=data.get("voltage"),
            current=data.get("current")
        )
        
        return jsonify({
            "success": True,
            "message": "数据录入成功",
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
            "message": f"数据录入失败：{str(e)}",
            "code": 500
        }), 500
