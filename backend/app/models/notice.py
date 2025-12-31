#通知模型
from . import db
import enum
from .user import RoleEnum,User
from datetime import datetime

class NoticeType(enum.Enum):
    REPAIR=0            #报修通知
    ARREARS=1           #欠费通知
    PRICE_CHANGE=2      #电价调整
    OVERDUE=3           #逾期通知

class NoticeStatus(enum.Enum):
    PENDING=0           #发送中
    SENT=1              #已发送
    FAILED=2            #失败
    READ=3              #已读

class SendChannel(enum.Enum):
    MAIL=0
    INNER=1

class Notifications(db.Model):
    __tablename__="NOTIFICATIONS"
    id=db.Column(db.Integer,primary_key=True,autoincrement=True)
    notify_type=db.Column(db.Enum(NoticeType),default=NoticeType.REPAIR,nullable=False)
    target_type=db.Column(db.Enum(RoleEnum),nullable=False,comment="通知对象类型")
    target_id=db.Column(db.Integer,db.ForeignKey(User.id),nullable=False,comment="通知对象id")
    related_id=db.Column(db.Integer,comment="关联业务id，例如报修关联meter的id")
    title=db.Column(db.String(100),nullable=False,comment="标题")
    content=db.Column(db.String(),nullable=False,comment="内容")
    status=db.Column(db.Enum(NoticeStatus),default=NoticeStatus.PENDING,nullable=False,comment="通知状态")
    send_channel=db.Column(db.Enum(SendChannel),default=SendChannel.INNER,nullable=False)
    create_time=db.Column(db.DateTime,default=datetime.now())
    send_time=db.Column(db.DateTime)
    read_time=db.Column(db.DateTime)
    #群发功能字段
    is_batch=db.Column(db.Boolean,nullable=False,default=False)
    batch_id=db.Column(db.String(20),unique=True)


    user=db.relationship("User",backref="notice")