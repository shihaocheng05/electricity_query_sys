# 计费账单接口（生成、支付、提醒）
from flask import Blueprint, request, jsonify, g
from app.services.bill_service import BillServices
from app.middleware import (
    BusinessException, check_permission,
    ValidateCreateBill, ValidatePayBill, ValidateQueryBills
)
from app.utils.common import validate_request
from datetime import datetime

# 创建账单蓝图
bill_bp = Blueprint("bill", __name__)


@bill_bp.route("/create", methods=["POST"])
@check_permission(require_admin=True,require_permit="edit_bill")
@validate_request(ValidateCreateBill)
def create_bill():
    """
    生成账单接口（仅管理员）
    ---
    请求�?
    {
        "bill_month": "2025-12-01",
        "meter_id": 1
    }
    """
    try:
        data = request.validate_data
        
        bill_month = datetime.strptime(data.get("bill_month"), "%Y-%m-%d")
        
        result = BillServices.create_bill(
            bill_month=bill_month,
            meter_id=data.get("meter_id")
        )
        
        return jsonify({
            "success": True,
            "message": "账单生成成功",
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
            "message": f"账单生成失败：{str(e)}",
            "code": 500
        }), 500


@bill_bp.route("/pay", methods=["POST"])
@check_permission(require_permit="pay_bill")
@validate_request(ValidatePayBill)
def pay_bill():
    """
    支付账单接口（需要登录）
    ---
    请求�?
    {
        "bill_id": 1,
        "payment_amount": 100.50,
        "payment_method": "ALIPAY",
        "transaction_id": "TXN123456"
    }
    """
    try:
        user_id = g.user_id
        data = request.validate_data
        
        result = BillServices.pay_bill(
            bill_id=data.get("bill_id"),
            user_id=user_id,
            payment_amount=data.get("payment_amount"),
            payment_method=data.get("payment_method")
        )
        
        return jsonify({
            "success": True,
            "message": "账单支付成功",
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
            "message": f"账单支付失败：{str(e)}",
            "code": 500
        }), 500


@bill_bp.route("/query", methods=["GET"])
@check_permission(require_permit="query_bill")
def query_bills():
    """
    查询账单列表接口
    """
    try:
        current_user_id = g.user_id
        
        # 获取用户角色（返回枚举的字符串值，如"resident"）
        from ..models import User
        user = User.query.get(current_user_id)
        # user.role.name.value 返回小写字符串如"resident"，需要转为大写匹配
        user_role = user.role.name.value.upper() if user and user.role else "RESIDENT"
        
        # 获取查询参数
        user_id = request.args.get("user_id", type=int)
        meter_id = request.args.get("meter_id", type=int)
        status = request.args.get("status")
        start_month = request.args.get("start_month")
        end_month = request.args.get("end_month")
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        
        # 调用服务�?
        result = BillServices.query_bills(
            user_id=user_id,
            meter_id=meter_id,
            status=status,
            start_month=start_month,
            end_month=end_month,
            page=page,
            per_page=per_page,
            current_user_id=current_user_id,
            user_role=user_role
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


@bill_bp.route("/detail/<int:bill_id>", methods=["GET"])
@check_permission(require_permit="query_bill")
def get_bill_detail(bill_id):
    """
    获取账单详情接口（需要登录）
    ---
    URL参数:
        bill_id: 账单ID
    """
    try:
        user_id = g.user_id
        
        result = BillServices.get_bill_detail(
            bill_id=bill_id,
            user_id=user_id
        )
        
        return jsonify({
            "success": True,
            "message": "获取成功",
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
            "message": f"获取账单详情失败：{str(e)}",
            "code": 500
        }), 500


@bill_bp.route("/reminder/<int:bill_id>", methods=["POST"])
@check_permission(require_admin=True,require_permit="edit_bill")
def send_reminder(bill_id):
    """
    发送账单提醒接口（仅管理员）
    ---
    URL参数:
        bill_id: 账单ID
    """
    try:
        admin_id = g.user_id
        
        result = BillServices.send_payment_reminder(
            bill_id=bill_id,
            admin_id=admin_id
        )
        
        return jsonify({
            "success": True,
            "message": "提醒发送成功",
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
            "message": f"提醒发送失败：{str(e)}",
            "code": 500
        }), 500


@bill_bp.route("/batch-create", methods=["POST"])
@check_permission(require_admin=True,require_permit="edit_bill")
def batch_create_bills():
    """
    批量生成账单接口（仅管理员）
    ---
    请求�?
    {
        "bill_month": "2025-12-01",
        "region_id": 1
    }
    """
    try:
        data = request.get_json()
        
        if not data or "bill_month" not in data:
            raise BusinessException("账单月份不能为空", 400)
        
        bill_month = datetime.strptime(data.get("bill_month"), "%Y-%m-%d")
        region_id = data.get("region_id")
        
        result = BillServices.batch_create_bills(
            bill_month=bill_month,
            region_id=region_id
        )
        
        return jsonify({
            "success": True,
            "message": "批量账单生成完成",
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
            "message": f"批量生成账单失败：{str(e)}",
            "code": 500
        }), 500
