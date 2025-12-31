# JWT认证、权限拦截
from ..utils import generate_jwt, verify_jwt
import time
from flask import current_app, request, jsonify, g
from functools import wraps
from .exception import BusinessException
from ..models import User,RoleEnum,Permission


def generate_user_token(user_id, expire_hours=2):
    """
    生成用户token
    :param user_id: 用户ID
    :param expire_hours: 过期时间（小时）
    :return: JWT token
    """
    payload = {
        "sub": str(user_id),
        "exp": int(time.time()) + expire_hours * 3600,
        "iat": int(time.time())
    }
    return generate_jwt(payload, current_app.config.get("SECRET_KEY", "default-secret-key"))

def check_permission(target_param="target_user_id", require_admin=False, require_super_admin=False, require_permit=None):
    """
    细粒度权限校验装饰器:
    最终权限逻辑改成这样：超管有所有权限，不更改；片区管理员由对应片区部分权限，普通用户有对应部分权限，
    （比如片区管理员有query权限，那么可以查询所管辖片区所有用户的信息，
    如果没有，那么不能查询；如果普通用户有query权限，可以查询自己信息；如果没有，那么不能查询）。
    权限规则：
    - 超级管理员(SUPER_ADMIN)：全局所有权限
    - 片区管理员(AREA_ADMIN)：本片区内所有权限
    - 普通居民(RESIDENT)：只能操作自己的资源
    
    :param target_param: 目标用户ID的参数名（从请求体或query取）
    :param require_admin: 是否强制要求管理员权限（True=居民完全禁止，片区管理员或超级管理员可执行）
    :param require_super_admin: 是否强制要求超级管理员权限（True=仅超级管理员可执行）
    :param require_permit: 所需的权限编码
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 1. 检查是否已认证
            if not hasattr(g, 'user_id'):
                return jsonify({
                    "success": False,
                    "message": "请先进行身份认证",
                    "code": 401
                }), 401
            
            current_user_id = g.user_id
            
            # 2. 获取当前用户信息
            current_user = User.query.get(current_user_id)
            
            if not current_user:
                return jsonify({
                    "success": False,
                    "message": "用户不存在",
                    "code": 404
                }), 404
            
            current_role = current_user.role.name if current_user.role else None
            
            # 3. 如果强制要求超级管理员
            if require_super_admin:
                if current_role != RoleEnum.SUPER_ADMIN:
                    return jsonify({
                        "success": False,
                        "message": "此操作仅超级管理员可执行",
                        "code": 403
                    }), 403
                g.user_role = current_role.value
                return func(*args, **kwargs)
            
            # 4. 超级管理员：直接放行
            if current_role == RoleEnum.SUPER_ADMIN:
                g.user_role = current_role.value
                return func(*args, **kwargs)
            
            # 5. 提取目标用户ID
            target_user_id = None
            if request.method in ['POST', 'PUT', 'DELETE']:
                data = request.get_json() or {}
                target_user_id = data.get(target_param)
            else:  # GET
                target_user_id = request.args.get(target_param)
            
            # 如果没有显式指定 target，默认为当前用户自己
            if target_user_id is None:
                target_user_id = current_user_id
            else:
                try:
                    target_user_id = int(target_user_id)
                except (ValueError, TypeError):
                    return jsonify({
                        "success": False,
                        "message": "目标用户ID格式错误",
                        "code": 400
                    }), 400
            
            # 6. 如果强制要求管理员
            if require_admin:
                if current_role not in [RoleEnum.AREA_ADMIN, RoleEnum.SUPER_ADMIN]:
                    return jsonify({
                        "success": False,
                        "message": "此操作仅管理员可执行",
                        "code": 403
                    }), 403
            
            # 7. 片区管理员：检查权限和片区
            if current_role == RoleEnum.AREA_ADMIN:
                # 检查是否有所需权限
                if require_permit:
                    has_permission = False
                    for permission in current_user.role.permissions:
                        if require_permit in permission.per_code:
                            has_permission = True
                            break
                    
                    if not has_permission:
                        return jsonify({
                            "success": False,
                            "message": "当前片区管理员没有所需权限",
                            "code": 403
                        }), 403
                
                # 检查是否操作自己或本片区用户
                target_user = User.query.get(target_user_id)
                if not target_user:
                    return jsonify({
                        "success": False,
                        "message": "目标用户不存在",
                        "code": 404
                    }), 404
                
                if target_user.region_id != current_user.region_id:
                    return jsonify({
                        "success": False,
                        "message": "无权操作其他片区的用户",
                        "code": 403
                    }), 403
                
                g.user_role = current_role.value
                g.target_user_id = target_user_id
                return func(*args, **kwargs)
            
            # 8. 普通居民：只能操作自己且需要权限
            if current_role == RoleEnum.RESIDENT:
                if target_user_id != current_user_id:
                    return jsonify({
                        "success": False,
                        "message": "普通用户只能操作自己的资源",
                        "code": 403
                    }), 403
                
                # 检查是否有所需权限
                if require_permit:
                    has_permission = False
                    for permission in current_user.role.permissions:
                        if require_permit in permission.per_code:
                            has_permission = True
                            break
                    
                    if not has_permission:
                        return jsonify({
                            "success": False,
                            "message": "当前用户没有所需权限",
                            "code": 403
                        }), 403
                
                g.user_role = current_role.value
                g.target_user_id = target_user_id
                return func(*args, **kwargs)
            
            # 9. 其他情况：拒绝
            return jsonify({
                "success": False,
                "message": "权限不足",
                "code": 403
            }), 403
        
        return wrapper
    return decorator


class AuthMiddleware:
    """
    WSGI认证中间件（全局拦截）
    可选使用，如果使用装饰器就不需要这个
    """
    def __init__(self, app, secret_key):
        self.app = app
        self.secret_key = secret_key
        # 无需认证的路径
        self.public_paths = [
            "/api/v1/user/login",
            "/api/v1/user/register",
            "/api/v1/user/send-reset-code",
            "/api/v1/user/reset-password",
            "/api/v1/usage/iot-upload",  # IoT 设备上报无需登录
            "/health",
            "/static"
        ]
    
    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "")
        method = environ.get("REQUEST_METHOD", "")
        
        # OPTIONS 请求（CORS 预检）直接放行
        if method == "OPTIONS":
            return self.app(environ, start_response)
        
        # 检查是否是公开路径
        is_public = any(path.startswith(public_path) for public_path in self.public_paths)
        
        if is_public:
            return self.app(environ, start_response)
        
        # 获取token
        auth_header = environ.get("HTTP_AUTHORIZATION", "")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            start_response("401 Unauthorized", [
                ("Content-Type", "application/json")
            ])
            return [b'{"success": false, "message": "Unauthorized", "code": 401}']
        
        token = auth_header.split(" ")[1]
        
        # 验证token
        try:
            payload = verify_jwt(token, self.secret_key)
            # 将用户ID添加到environ中
            environ["user_id"] = payload.get("sub")
        except Exception:
            start_response("401 Unauthorized", [
                ("Content-Type", "application/json")
            ])
            return [b'{"success": false, "message": "Invalid token", "code": 401}']
        
        return self.app(environ, start_response)