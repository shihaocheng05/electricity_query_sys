# 接口层（按模块拆分子蓝图�?
# 注册所有子蓝图，统一接口前缀/api/v1
from flask import Blueprint

# 创建主蓝�?
api_bp = Blueprint("api", __name__, url_prefix="/api/v1")

# 导入各个子模块的蓝图
from .user import user_bp
from .meter import meter_bp
from .usage import usage_bp
from .bill import bill_bp
from .query import query_bp
from .system import system_bp
from .notification import notification_bp

# 注册所有子蓝图到主蓝图
def register_blueprints():
    """注册所有子蓝图"""
    api_bp.register_blueprint(user_bp, url_prefix="/user")
    api_bp.register_blueprint(meter_bp, url_prefix="/meter")
    api_bp.register_blueprint(usage_bp, url_prefix="/usage")
    api_bp.register_blueprint(bill_bp, url_prefix="/bill")
    api_bp.register_blueprint(query_bp, url_prefix="/query")
    api_bp.register_blueprint(system_bp, url_prefix="/system")
    api_bp.register_blueprint(notification_bp, url_prefix="/notification")

# 立即注册子蓝�?
register_blueprints()


