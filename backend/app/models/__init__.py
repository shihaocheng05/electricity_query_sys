# 数据库模型层（对应MySQL表）
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db=SQLAlchemy()
migrate=Migrate()

from .user import User,Role,RoleEnum,UserStatus
from .meter import Meter,MeterRecord,MeterStatus,MeterType,RecordType
from .bill import Bill,BillDetail,PricePolicy,TimeSharePriceRules,\
    LadderPriceRules,PriceType,TimePeriod,LadderLevel,BillStatus
from .system import Region,Permission
from .usage import UsageData,IoTData,IoTstatus,UsageType
from .notice import Notifications,NoticeType,NoticeStatus,SendChannel