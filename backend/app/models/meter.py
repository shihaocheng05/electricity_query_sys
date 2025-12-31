# 电表模型（Meter、MeterRecord）
from . import db
from .user import User 
from datetime import datetime 
import enum
from sqlalchemy import event
from .system import Region

class MeterStatus(enum.Enum):
    NORMAL="normal"             #正常
    ABNORMAL="abnormal"         #异常
    REPLACED="replaced"         #已更换，一个电表被更换了的话就放到别的地方去了，用新的电表
    SCRAPPED="scrapped"         #已报废

class MeterType(enum.Enum):
    SMART="smart"               #智能电表
    TRADITIONAL="traditional"   #传统电表

class RecordType(enum.Enum):    #操作类型
    REPLACE="replace"
    REPAIR="repair"
    CHECK="check"

class Meter(db.Model):
    __tablename__="METER"
    id=db.Column(db.Integer,primary_key=True,autoincrement=True)  # 修正拼写
    meter_code=db.Column(db.String(20),unique=True,nullable=False,comment="电表编号")
    user_id=db.Column(db.Integer,db.ForeignKey(User.id))
    old_meter_id=db.Column(db.Integer,db.ForeignKey("METER.id"),default=None)
    region_id=db.Column(db.Integer,db.ForeignKey(Region.id))
    install_address=db.Column(db.String(100),nullable=False)
    install_time=db.Column(db.DateTime,default=datetime.now(),nullable=False)
    status=db.Column(db.Enum(MeterStatus),default=MeterStatus.NORMAL)
    meter_type=db.Column(db.Enum(MeterType),default=MeterType.SMART)
    init_time=db.Column(db.DateTime,default=datetime.now())
    update_time=db.Column(db.DateTime,default=datetime.now())
    #关联
    bills=db.relationship("Bill",backref="meter")
    meter_records=db.relationship("MeterRecord",backref="meter")
    old_meter=db.relationship("Meter",remote_side=[id],backref="new_meter")         #关联旧电表
    def __repr__(self):
        return f"<Meter {self.nmeter_code}>"

@event.listens_for(Meter,"before_update")
def before_update_time(mapper,connection,target):
    target.update_time=datetime.now()

class MeterRecord(db.Model):
    __tablename__="MeterRecord"
    id=db.Column(db.Integer,primary_key=True,autoincrement=True)  # 修正拼写
    meter_id=db.Column(db.Integer,db.ForeignKey(Meter.id),nullable=False)
    record_type=db.Column(db.Enum(RecordType),nullable=False)
    operator=db.Column(db.String(20),nullable=False,comment="操作人员")
    content=db.Column(db.String(200),comment="操作详细记录，可选")
    record_time=db.Column(db.DateTime,default=datetime.now())
    attach_img=db.Column(db.String(256),comment="维修凭证URL")

    def __repr__(self):
        return f"<MeterRecord {self.id}>"