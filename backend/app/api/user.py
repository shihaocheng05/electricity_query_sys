# 用户模块接口（注册、登录、电表绑定）
from flask import Blueprint, request, jsonify, g
from ..services import UserServices
from ..middleware import (BusinessException,check_permission,generate_user_token,
                        ValidateRegister,ValidateLogin,ValidateUpdateUser,
                        ValidateBindMeter,ValidateUnbindMeter,ValidateChangePassword,
                        ValidateGetUserList,ValidateSendResetCode,ValidateResetPassword)
from ..utils import validate_request

# 创建用户蓝图
user_bp = Blueprint("user", __name__)


@user_bp.route("/register", methods=["POST"])
@validate_request(ValidateRegister)
def register():
    """
    用户注册接口
    ---
    请求体:
    {
        "mail": "user@example.com",
        "password": "password123",
        "real_name": "张三",
        "idcard": "110101199001011234",
        "region_id": 1
    }
    """
    try:
        # 获取验证后的数据
        data = request.validate_data
        
        # 调用服务层
        result = UserServices.register(
            mail=data.get("mail"),
            password=data.get("password"),
            real_name=data.get("real_name"),
            idcard=data.get("idcard"),
            region_id=data.get("region_id")
        )
        
        return jsonify({
            "success": True,
            "message": "注册成功",
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
            "message": f"注册失败：{str(e)}",
            "code": 500
        }), 500


@user_bp.route("/login", methods=["POST"])
@validate_request(ValidateLogin)
def login():
    """
    用户登录接口
    ---
    请求体:
    {
        "mail": "user@example.com",
        "password": "password123"
    }
    """
    try:
        # 获取验证后的数据
        data = request.validate_data
        
        # 调用服务层
        result = UserServices.login(
            mail=data.get("mail"),
            password=data.get("password")
        )
        
        return jsonify({
            "success": True,
            "message": "登录成功",
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
        traceback.print_exc()  # 打印完整的错误堆栈到控制�?
        return jsonify({
            "success": False,
            "message": f"登录失败：{str(e)}",
            "code": 500
        }), 500


@user_bp.route("/refresh-token", methods=["POST"])
def RefreshToken():

    try:
        data=request.get_json()
        result=UserServices.refresh_token(
            refresh_token=data.get("refresh_token")
        )
        return jsonify({
            "success":True,
            "message":"token刷新成功",
            "data":result
        })
    except BusinessException as e:
        return jsonify({
            "success": False,
            "message": e.msg,
            "code": e.code
        }), e.code
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"token刷新失败",
            "code": 500
        }), 500

@user_bp.route("/info", methods=["GET"])
@check_permission(target_param="target_user_id", require_permit="query_user")
def get_user_info():
    """
    获取用户信息接口
    ---
    权限：居民可查自己，片区管理员可查本片区，超管可查所有用户
    
    Query参数:
        user_id: 目标用户ID（可选，默认当前用户)
    Headers:
        Authorization: Bearer <token>
    """
    try:
        # 从装饰器注入�?g 中获�?target_user_id（已完成权限校验�?
        target_user_id = g.get('target_user_id', g.user_id)
        
        # 调用服务层获取用户信�?
        result = UserServices.get_user_info(target_user_id)
        
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
            "message": f"获取用户信息失败：{str(e)}",
            "code": 500
        }), 500


@user_bp.route("/update", methods=["PUT"])
@check_permission(target_param="target_user_id",require_admin=False,require_permit="edit_user")
@validate_request(ValidateUpdateUser)
def update_user_info():
    """
    修改用户信息接口
    ---
    权限：居民可改自己，片区管理员可改本片区，超管可改所有用户
    
    请求体:
    {
        "user_id": 1,  // 可选，默认当前用户
        "mail": "new@example.com",
        "password": "newpassword",
        "real_name": "新名字",
        "idcard": "110101199001011234",
        "region_id": 1
    }
    """
    try:
        target_user_id = g.get('target_user_id', g.user_id)
        data = request.validate_data
        
        # 调用服务层
        result = UserServices.modify_user_msg(
            user_id=target_user_id,
            mail=data.get("mail"),
            real_name=data.get("real_name"),
            idcard=data.get("idcard"),
            region_id=data.get("region_id")
        )
        
        return jsonify({
            "success": True,
            "message": "修改成功",
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
            "message": f"修改用户信息失败：{str(e)}",
            "code": 500
        }), 500


@user_bp.route("/bind-meter", methods=["POST"])
@check_permission(target_param="target_user_id", require_permit="bind_meter")
@validate_request(ValidateBindMeter)
def bind_meter():
    """
    绑定电表接口（需要登录）
    ---
    Headers:
        Authorization: Bearer <token>
    请求�?
    {
        "target_user_id": 1,
        "meter_code": "001-12345"
    }
    """
    try:
        data = request.validate_data
        target_id = data.get("target_user_id")
        meter_code = data.get("meter_code")
        
        # 调用服务�?
        result = UserServices.bind_meter(
            user_id=target_id,
            meter_code=meter_code
        )
        
        return jsonify({
            "success": True,
            "message": "绑定成功",
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
            "message": f"绑定电表失败：{str(e)}",
            "code": 500
        }), 500


@user_bp.route("/unbind-meter", methods=["POST"])
@check_permission(target_param="target_user_id", require_permit="unbind_meter")
@validate_request(ValidateUnbindMeter)
def unbind_meter():
    """
    解绑电表接口（需要登录）
    ---
    请求�?
    {
        "target_user_id": 1,
        "meter_id": 1
    }
    """
    try:
        data = request.validate_data
        target_user_id = data.get("target_user_id")
        meter_id = data.get("meter_id")
        
        # 调用服务�?
        result = UserServices.unbind_meter(
            user_id=target_user_id,
            meter_id=meter_id
        )
        
        return jsonify({
            "success": True,
            "message": "解绑成功",
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
            "message": f"解绑电表失败：{str(e)}",
            "code": 500
        }), 500


@user_bp.route("/meters", methods=["GET"])
@check_permission(target_param="target_user_id",require_admin=False,require_permit="query_meter")
def get_user_meters():
    """
    获取用户绑定的电表列�?
    ---
    权限：居民可查自己，片区管理员可查本片区，超管可查所�?
    
    Query参数:
        user_id: 目标用户ID（可选，默认当前用户�?
    """
    try:
        target_user_id = g.get('target_user_id', g.user_id)
        
        # 调用服务�?
        result = UserServices.get_user_meters(target_user_id)
        
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
            "message": f"获取电表列表失败：{str(e)}",
            "code": 500
        }), 500


@user_bp.route("/logout", methods=["POST"])
def logout():
    """
    用户登出接口（需要登录）
    ---
    Headers:
        Authorization: Bearer <token>
    """
    try:
        user_id = g.user_id
        
        # 可以在这里添加登出逻辑，比如将token加入黑名�?
        # 目前简化处理，只返回成功消�?
        
        return jsonify({
            "success": True,
            "message": "登出成功",
            "data": {
                "user_id": user_id
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"登出失败：{str(e)}",
            "code": 500
        }), 500


@user_bp.route("/change-password", methods=["POST"])
@check_permission(require_admin=False)  # 仅允许修改自己的密码
@validate_request(ValidateChangePassword)
def change_password():
    """
    修改密码接口
    ---
    权限：仅可修改自己的密码（即使管理员也不能改别人的密码）
    
    请求�?
    {
        "old_password": "oldpassword",
        "new_password": "newpassword"
    }
    """
    try:
        # 修改密码只能操作自己，使用当前登录用户ID
        user_id = g.user_id  # 直接使用当前用户ID
        data = request.validate_data
        
        old_password = data.get("old_password")
        new_password = data.get("new_password")
        
        # 调用服务�?
        result = UserServices.change_password(
            user_id=user_id,
            old_password=old_password,
            new_password=new_password
        )
        
        return jsonify({
            "success": True,
            "message": "密码修改成功",
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
            "message": f"修改密码失败：{str(e)}",
            "code": 500
        }), 500


@user_bp.route("/list", methods=["GET"])
@check_permission(require_permit="query_user")
@validate_request(ValidateGetUserList)
def get_user_list():
    """
    获取用户列表（仅管理员）
    ---
    Headers:
        Authorization: Bearer <token>
    Query参数:
        page: 页码（默�?�?
        per_page: 每页数量（默�?0�?
        region_id: 片区ID（可选）
        keyword: 搜索关键词（可选）
    """
    try:
        admin_id = g.user_id
        admin_role = g.user_role
        data = request.validate_data
        
        # 获取查询参数
        page = data.get("page")
        per_page = data.get("per_page")
        region_id = data.get("region_id")
        keyword = data.get("keyword")
        
        from ..models import User
        
        # 构建查询
        query = User.query
        
        # 如果是片区管理员，只能查看自己片区的用户
        if admin_role == "AREA_ADMIN":
            admin_user = User.query.get(admin_id)
            if admin_user and admin_user.region_id:
                query = query.filter_by(region_id=admin_user.region_id)
        elif region_id:
            # 超级管理员可以按片区筛�?
            query = query.filter_by(region_id=region_id)
        
        # 关键词搜�?
        if keyword:
            from sqlalchemy import or_
            query = query.filter(
                or_(User.mail.like(f"%{keyword}%"), User.real_name.like(f"%{keyword}%"))
            )
        
        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        users = []
        for user in pagination.items:
            # 脱敏处理
            id_card = user.idcard
            if id_card:
                id_card = id_card[:6] + "********" + id_card[-4:]
            
            users.append({
                "user_id": user.id,
                "mail": user.mail,
                "real_name": user.real_name or "",
                "id_card": id_card or "",
                "region_id": user.region_id,
                "region_name": user.region.region_name if user.region else "",
                "role": user.role.name.value if user.role else "",
                "status": user.status.value,
                "create_time": user.create_time.strftime("%Y-%m-%d %H:%M:%S")
            })
        
        return jsonify({
            "success": True,
            "message": "获取成功",
            "data": {
                "users": users,
                "pagination": {
                    "total": pagination.total,
                    "page": pagination.page,
                    "per_page": pagination.per_page,
                    "pages": pagination.pages,
                    "has_next": pagination.has_next,
                    "has_prev": pagination.has_prev
                }
            }
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
            "message": f"获取用户列表失败：{str(e)}",
            "code": 500
        }), 500


@user_bp.route("/send-reset-code", methods=["POST"])
@validate_request(ValidateSendResetCode)
def send_reset_code():
    """
    发送重置密码验证码
    ---
    请求体:
    {
        "mail": "user@example.com"
    }
    """
    try:
        data = request.validate_data
        result = UserServices.send_reset_code(mail=data.get("mail"))
        
        return jsonify({
            "success": True,
            "message": result["message"],
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
            "message": f"发送验证码失败：{str(e)}",
            "code": 500
        }), 500


@user_bp.route("/reset-password", methods=["POST"])
@validate_request(ValidateResetPassword)
def reset_password():
    """
    重置密码
    ---
    请求体:
    {
        "mail": "user@example.com",
        "code": "123456",
        "new_password": "newpassword123"
    }
    """
    try:
        data = request.validate_data
        result = UserServices.reset_password(
            mail=data.get("mail"),
            code=data.get("code"),
            new_password=data.get("new_password")
        )
        
        return jsonify({
            "success": True,
            "message": result["message"],
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
            "message": f"重置密码失败：{str(e)}",
            "code": 500
        }), 500
