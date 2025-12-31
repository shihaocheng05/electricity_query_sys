# 核心应用目录
# Flask应用初始化（注册蓝图、配置、中间件）
import os
from flask import Flask, jsonify, request, g
from .models import db, migrate
from .config import dev, proc, test
from .middleware import BusinessException, AuthMiddleware
from flask_cors import CORS


def create_app():
    """创建并配置Flask应用"""
    app = Flask(__name__)
    
    # 加载配置
    env = os.getenv("FLASK_ENV", "dev")  # 默认开发环境dev
    if env == "dev":
        app.config.from_object(dev)
    elif env == "proc":
        app.config.from_object(proc)
    else:
        app.config.from_object(test)
    
    # 配置跨域资源共享（CORS）- 允许所有来源和认证头
    CORS(app, 
         resources={r"/api/*": {"origins": "*"}},
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    
    # 注册WSGI认证中间件（全局认证）
    app.wsgi_app = AuthMiddleware(app.wsgi_app, app.config["SECRET_KEY"])
    
    # 初始化数据库（延迟绑定）
    db.init_app(app)
    migrate.init_app(app, db)

    # 注册全局异常处理器
    register_error_handlers(app)
    
    # 注册所有蓝图
    register_blueprints(app)
    
    # 将中间件注入的用户ID同步到 g 上下文
    @app.before_request
    def inject_user_from_env():
        uid = request.environ.get("user_id")
        if uid is not None:
            try:
                g.user_id = int(uid)
            except Exception:
                g.user_id = uid

    # 注册健康检查路由
    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({
            "success": True,
            "message": "Service is running",
            "env": env
        }), 200

    return app


def register_blueprints(app):
    """注册所有蓝图"""
    from .api import api_bp
    
    # 注册主蓝图（已包含所有子蓝图，统一前缀 /api/v1）
    app.register_blueprint(api_bp)


def register_error_handlers(app):
    """注册全局异常处理器"""
    
    @app.errorhandler(BusinessException)
    def handle_business_exception(e):
        """处理业务异常"""
        return jsonify({
            "success": False,
            "message": e.msg,
            "code": e.code
        }), e.code
    
    @app.errorhandler(404)
    def handle_404(e):
        """处理404错误"""
        return jsonify({
            "success": False,
            "message": "资源未找到",
            "code": 404
        }), 404
    
    @app.errorhandler(500)
    def handle_500(e):
        """处理500错误"""
        return jsonify({
            "success": False,
            "message": "服务器内部错误",
            "code": 500
        }), 500
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        """处理所有未捕获的异常"""
        app.logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "message": f"服务器错误: {str(e)}",
            "code": 500
        }), 500
