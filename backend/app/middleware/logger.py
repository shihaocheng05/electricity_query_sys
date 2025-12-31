# 日志配置（访问日志、错误日志）
from datetime import datetime
from app import db
import enum

class LogType(enum.Enum):
    """日志类型"""
    LOGIN = "登录"
    LOGOUT = "登出"
    CREATE = "创建"
    UPDATE = "更新"
    DELETE = "删除"
    QUERY = "查询"
    EXPORT = "导出"
    PAYMENT = "支付"
    REFUND = "退款"
    ERROR = "错误"
    WARNING = "警告"

class LogLevel(enum.Enum):
    """日志级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class SystemLog(db.Model):
    """系统日志表"""
    __tablename__ = "SYSTEM_LOG"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    operator_id = db.Column(db.Integer, nullable=True, comment="操作人ID")
    operator_name = db.Column(db.String(50), comment="操作人姓名")
    log_type = db.Column(db.Enum(LogType), nullable=False, comment="操作类型")
    log_level = db.Column(db.Enum(LogLevel), default=LogLevel.INFO, comment="日志级别")
    module = db.Column(db.String(50), comment="模块名称")
    action = db.Column(db.String(100), nullable=False, comment="操作描述")
    request_method = db.Column(db.String(10), comment="请求方法")
    request_url = db.Column(db.String(200), comment="请求URL")
    request_ip = db.Column(db.String(50), comment="请求IP")
    request_params = db.Column(db.Text, comment="请求参数")
    response_status = db.Column(db.Integer, comment="响应状态码")
    error_message = db.Column(db.Text, comment="错误信息")
    execution_time = db.Column(db.Float, comment="执行时间(秒)")
    create_time = db.Column(db.DateTime, default=datetime.now, nullable=False, comment="创建时间")
    
    __table_args__ = (
        db.Index("idx_operator_id", "operator_id"),
        db.Index("idx_log_type", "log_type"),
        db.Index("idx_create_time", "create_time"),
        db.Index("idx_log_level", "log_level")
    )
    
    def __repr__(self):
        return f"<SystemLog {self.id}-{self.action}>"

def create_log(operator_id, operator_name, log_type, action, module=None, 
               log_level=LogLevel.INFO, request_method=None, request_url=None, 
               request_ip=None, request_params=None, response_status=None, 
               error_message=None, execution_time=None):
    """
    创建系统日志
    :param operator_id: 操作人ID
    :param operator_name: 操作人姓名
    :param log_type: 日志类型
    :param action: 操作描述
    :param module: 模块名称
    :param log_level: 日志级别
    :param request_method: 请求方法
    :param request_url: 请求URL
    :param request_ip: 请求IP
    :param request_params: 请求参数
    :param response_status: 响应状态码
    :param error_message: 错误信息
    :param execution_time: 执行时间
    :return: 日志对象
    """
    log = SystemLog(
        operator_id=operator_id,
        operator_name=operator_name,
        log_type=log_type,
        log_level=log_level,
        module=module,
        action=action,
        request_method=request_method,
        request_url=request_url,
        request_ip=request_ip,
        request_params=request_params,
        response_status=response_status,
        error_message=error_message,
        execution_time=execution_time
    )
    
    try:
        db.session.add(log)
        db.session.commit()
        return log
    except Exception as e:
        db.session.rollback()
        print(f"日志记录失败: {str(e)}")
        return None
