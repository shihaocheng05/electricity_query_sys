# 查询分析接口（用电统计、趋势）
from flask import Blueprint, request, jsonify, g
from app.services.analyze_service import AnalyzeServices
from app.middleware import (
    BusinessException, check_permission,ValidateExportData,
    ValidateAnalyzeUser, ValidateAnalyzeRegion, ValidateRanking
)
from app.utils.common import validate_request

# 创建查询蓝图
query_bp = Blueprint("query", __name__)


@query_bp.route("/statistics/summary", methods=["GET"])
@check_permission(require_permit="query_iot")
def get_statistics_summary():
    """
    用电统计概览接口
    """
    try:
        current_user_id = g.user_id
        
        # 获取用户角色
        from ..models import User
        user = User.query.get(current_user_id)
        user_role = user.role.name.value if user and user.role else "RESIDENT"
        
        scope = request.args.get("scope", "user")
        scope_id = request.args.get("scope_id", type=int)
        
        if scope == "user":
            # 用户统计
            if not scope_id:
                scope_id = current_user_id
            else:
                # 非管理员只能查询自己的数据
                if user_role == "RESIDENT" and scope_id != current_user_id:
                    raise BusinessException("无权查询其他用户的数据", 403)
            
            result = AnalyzeServices.get_user_statistics_summary(scope_id)
        
        elif scope == "region":
            # 片区统计（需要管理员权限）
            if user_role == "RESIDENT":
                raise BusinessException("无权查询片区数据", 403)
            
            if not scope_id:
                raise BusinessException("片区ID不能为空", 400)
            
            result = AnalyzeServices.get_region_statistics_summary(scope_id)
        
        else:
            raise BusinessException("不支持的统计范围", 400)
        
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
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": f"查询失败：{str(e)}",
            "code": 500
        }), 500


@query_bp.route("/analyze/user", methods=["GET"])
@check_permission(target_param="target_user_id", require_permit="query_iot")
@validate_request(ValidateAnalyzeUser)
def analyze_user_electricity():
    """
    个人用电分析接口
    """
    try:
        current_user_id = g.user_id
        
        # 构建查询参数
        user_id = request.args.get("user_id", current_user_id, type=int)
        analysis_period = request.args.get("analysis_period", "month")
        compare_period = request.args.get("compare_period", "false").lower() == "true"
        
        # 调用服务层函数，进行分析
        result = AnalyzeServices.analyze_user_electricity(
            user_id=user_id,
            analysis_period=analysis_period,
            compare_period=compare_period
        )
        
        return jsonify({
            "success": True,
            "message": "分析完成",
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
            "message": f"分析失败：{str(e)}",
            "code": 500
        }), 500


@query_bp.route("/analyze/region", methods=["GET"])
@check_permission(require_permit="query_iot")
def analyze_region_electricity():
    """
    片区用电分析接口（仅管理员）
    ---
    Query参数:
        region_id: 片区ID（必填）
        analysis_period: 分析周期（day/month/year，默认month）
        compare_period: 是否对比同期（true/false，默认false）
    """
    try:
        # 构建查询参数
        region_id = request.args.get("region_id")
        if not region_id:
            raise BusinessException("片区ID不能为空", 400)
        
        query_params = {
            "region_id": int(region_id),
            "analysis_period": request.args.get("analysis_period", "month"),
            "compare_period": request.args.get("compare_period", "false").lower() == "true"
        }
        
        # 使用validator验证
        validated_data = ValidateAnalyzeRegion(**query_params).model_dump()
        
        result = AnalyzeServices.analyze_region_electricity(
            region_id=validated_data.get("region_id"),
            analysis_period=validated_data.get("analysis_period"),
            compare_period=validated_data.get("compare_period")
        )
        
        return jsonify({
            "success": True,
            "message": "分析完成",
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
            "message": f"分析失败：{str(e)}",
            "code": 500
        }), 500


@query_bp.route("/ranking", methods=["GET"])
@check_permission(require_permit="query_iot")
def get_ranking():
    """
    用电排名接口（仅管理员）
    ---
    Query参数:
        region_id: 片区ID（可选）
        ranking_type: 排名类型（electricity/cost，默认electricity）
        time_range: 时间范围（day/week/month/year，默认month�?
        limit: 返回数量（默�?0�?
    """
    try:
        # 构建查询参数
        query_params = {
            "region_id": request.args.get("region_id"),
            "ranking_type": request.args.get("ranking_type", "electricity"),
            "time_range": request.args.get("time_range", "month"),
            "limit": int(request.args.get("limit", 10))
        }
        
        if query_params["region_id"]:
            query_params["region_id"] = int(query_params["region_id"])
        
        # 使用validator验证
        validated_data = ValidateRanking(**query_params).model_dump()
        
        result = AnalyzeServices.get_ranking(
            region_id=validated_data.get("region_id"),
            ranking_type=validated_data.get("ranking_type"),
            time_range=validated_data.get("time_range"),
            limit=validated_data.get("limit")
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

@query_bp.route("/export", methods=["GET"])
@check_permission(require_permit="query_iot")
@validate_request(ValidateExportData)
def export_data():
    """
    导出用电数据接口（需要登录）
    ---
    Query参数:
        export_type: 导出类型（usage/bill，默认usage�?
        region_id: 片区ID（可选，不指定则使用管理员的第一个管辖片区）
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）
        format: 导出格式（csv/excel，默认csv�?
    """
    try:
        current_user_id = g.user_id
        validated_data = request.validate_data
        
        # 调用服务层函数，导出数据
        result = AnalyzeServices.export_data(
            user_id=current_user_id,
            export_type=validated_data.get("export_type", "usage"),
            region_id=validated_data.get("region_id"),
            start_date=validated_data.get("start_date"),
            end_date=validated_data.get("end_date"),
            format_type=validated_data.get("format", "csv")
        )
        
        return jsonify({
            "success": True,
            "message": "导出成功",
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
            "message": f"导出失败：{str(e)}",
            "code": 500
        }), 500
