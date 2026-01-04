# 用电数据模型（UsageData、IoTData）
from . import db
from .meter import Meter
import enum
from datetime import datetime

class IoTstatus(enum.Enum):
    NORMAL=0
    ABNORMAL=1

class UsageType(enum.Enum):
    DAY=0
    MONTH=1

#实时用电数据表
class IoTData(db.Model):
    __tablename__="IoTData"
    id=db.Column(db.Integer,primary_key=True,autoincrement=True)  # 修正拼写
    meter_id=db.Column(db.Integer,db.ForeignKey(Meter.id),nullable=False)
    electricity=db.Column(db.Float,nullable=False)          #本次采集用电量
    collect_time=db.Column(db.DateTime,nullable=False)      #采集时间（小时）
    voltage=db.Column(db.Float)                             #电压
    current=db.Column(db.Float)                             #电流
    status=db.Column(db.Enum(IoTstatus),default=IoTstatus.NORMAL)

    meter=db.relationship("Meter",backref="iotdatas")

    __table_arg__=(
        db.UniqueConstraint("meter_id","collect_time","uniquecstr"),
        db.Index("meter_collect_id","meter_id","collect_time")
    )

    def __repr__(self):
        return f"<IoTData {self.meter_id}-{self.collect_time}>"

class UsageData(db.Model):
    id=db.Column(db.Integer,primary_key=True,autoincrement=True)
    meter_id=db.Column(db.Integer,db.ForeignKey(Meter.id),nullable=False)
    usage_type=db.Column(db.Enum(UsageType),nullable=False)     #汇总类型
    usage_time=db.Column(db.DateTime,nullable=False)            #汇总日期
    total_electricity=db.Column(db.Float,nullable=False)        #汇总周期用电量
    peak_electricity=db.Column(db.Float)                        #高峰期用电量
    valley_electricity=db.Column(db.Float)                      #低谷期用电量
    create_time=db.Column(db.DateTime,default=datetime.now())

    __table_arg__=(
        db.UniqueConstraint("meter_id","usage_type","usage_time","uq_meter_usage"),
        db.Index("meter_usage_type_time_id","meter_id","usage_type","usage_time")
    )
    def __repr__(self):
        return f"<UsageData {self.meter_id}-{self.usage_type}-{self.usage_time}>"