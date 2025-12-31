# 通知模块接口（创建、发送、查询）
from flask import Blueprint, request, jsonify, g
from app.services.notify_sevice import NotifyServices
from app.middleware import (
    BusinessException, check_permission,
    ValidateCreateNotification, ValidateQueryNotification,
    ValidateSendNotification, ValidateUpdateNotificationStatus
)
from app.utils.common import validate_request
from app.models import User, RoleEnum

# 创建通知蓝图
notification_bp = Blueprint("notification", __name__)


@notification_bp.route("/create", methods=["POST"])
@check_permission(require_permit="edit_notification")
@validate_request(ValidateCreateNotification)
def create_notification():
    """
    创建通知接口（仅管理员）
    ---
    请求�?
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
    """
    try:
        data = request.validate_data
        
        # 根据target_ids获取目标用户对象
        target_ids = data.get("target_ids")
        targets = User.query.filter(User.id.in_(target_ids)).all()
        
        if len(targets) != len(target_ids):
            raise BusinessException("部分目标用户不存在", 400)
        
        result = NotifyServices.create_notification(
            notice_type=data.get("notice_type"),
            target_type=data.get("target_type"),
            targets=targets,
            title=data.get("title"),
            content=data.get("content"),
            send_channel=data.get("send_channel"),
            send_time=data.get("send_time"),
            is_batch=data.get("is_batch"),
            related_id=data.get("related_id")
        )
        
        return jsonify({
            "success": True,
            "message": "通知创建成功",
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
            "message": f"通知创建失败：{str(e)}",
            "code": 500
        }), 500


@notification_bp.route("/send", methods=["POST"])
@check_permission(require_permit="edit_notification")
@validate_request(ValidateSendNotification)
def send_notification():
    """
    发送通知接口（仅管理员）
    ---
    请求�?
    {
        "notification_id": 1  // 单发模式
        // �?
        "batch_id": "abc123"  // 群发模式
    }
    """
    try:
        data = request.validate_data
        
        # 获取Mail对象（如果需要发送邮件）
        from flask import current_app
        mail = current_app.extensions.get('mail')
        
        result = NotifyServices.send_notification(
            mail=mail,
            notification_id=data.get("notification_id"),
            batch_id=data.get("batch_id")
        )
        
        return jsonify({
            "success": True,
            "message": result.get("message"),
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
            "message": f"通知发送失败：{str(e)}",
            "code": 500
        }), 500


@notification_bp.route("/query", methods=["GET"])
@check_permission(require_permit="query_notification")
@validate_request(ValidateQueryNotification)
def query_notifications():
    """
    查询通知列表接口（需要登录）
    ---
    Query参数:
        user_id: 用户ID（可选，居民只能查自己的�?
        notify_type: 通知类型（可选）
        status: 通知状态（可选）
        is_unread_only: 是否只查询未读（默认false�?
        page: 页码（默�?�?
        per_page: 每页数量（默�?0�?
    """
    try:
        current_user_id = g.user_id
        data = request.validate_data
        
        # 获取用户角色
        user = User.query.get(current_user_id)
        user_role = user.role.name.value if user and user.role else "RESIDENT"
        
        # 居民只能查询自己的通知
        query_user_id = data.get("user_id")
        if user_role == "RESIDENT":
            query_user_id = current_user_id
        elif query_user_id:
            query_user_id = int(query_user_id)
        
        result = NotifyServices.query_notification(
            user_id=query_user_id,
            notify_type=data.get("notify_type"),
            status=data.get("status"),
            is_unread_only=data.get("is_unread_only"),
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


@notification_bp.route("/statistics", methods=["GET"])
@check_permission(require_permit="query_notification")
def get_notification_statistics():
    """
    获取通知统计接口（仅管理员）
    ---
    Query参数:
        notify_type: 通知类型（可选）
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）
    """
    try:
        notify_type = request.args.get("notify_type")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        
        # 日期格式转换
        from datetime import datetime
        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
        
        result = NotifyServices.get_notification_statistics(
            notify_type=notify_type,
            start_date=start_date,
            end_date=end_date
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


@notification_bp.route("/update-status", methods=["PUT"])
@check_permission(require_permit="edit_notification")
@validate_request(ValidateUpdateNotificationStatus)
def update_notification_status():
    """
    更新通知状态接口（需要登录）
    ---
    请求�?
    {
        "notification_id": 1,
        "action": "mark_read",  // �?"retry"
        "user_id": 1  // 可�?
    }
    """
    try:
        current_user_id = g.user_id
        data = request.validate_data
        
        # 获取用户角色
        user = User.query.get(current_user_id)
        user_role = user.role.name.value if user and user.role else "RESIDENT"
        
        # 如果是居民，只能操作自己的通知
        user_id = data.get("user_id")
        if user_role == "RESIDENT":
            user_id = current_user_id
        
        result = NotifyServices.update_notification_status(
            notification_id=data.get("notification_id"),
            action=data.get("action"),
            user_id=user_id
        )
        
        return jsonify({
            "success": True,
            "message": result.get("message"),
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
            "message": f"更新失败：{str(e)}",
            "code": 500
        }), 500

