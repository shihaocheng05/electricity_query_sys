# 账单模型（Bill、BillDetail、PricePolicy）
from . import db
import enum
from .system import Region  # 修正导入：使用相对导入
from datetime import datetime
from .user import User
from .meter import Meter

class PriceType(enum.Enum):
    #电价类型，如果选了阶梯电价则所有时间段的费用相同，阶梯电价计算的是该月份的累计用电量。反过来用分时电价的话同理
    ladder=0
    time_share=1
    combined=2

class LadderLevel(enum.Enum):
    #阶梯等级
    low=0
    middle=1
    high=2

class TimePeriod(enum.Enum):
    #时段
    peak=0
    flat=1
    valley=2

class BillStatus(enum.Enum):
    #账单类型,逾期账单除了缴纳该收的费用还要缴纳罚款
    unpaid=0
    paid=1
    overdue=2

class PricePolicy(db.Model):
    id=db.Column(db.Integer,primary_key=True,autoincrement=True)  # 修正拼写
    policy_name=db.Column(db.String(50),nullable=False)
    price_type=db.Column(db.Enum(PriceType),default=PriceType.combined)     #政策种类，如果不是混合的话，则一种固定一种不固定
    region_id=db.Column(db.Integer,db.ForeignKey(Region.id),nullable=False)
    start_time=db.Column(db.DateTime,nullable=False)                        #限定开始时间以及结尾时间必须要是整点
    end_time=db.Column(db.DateTime)
    is_active=db.Column(db.Boolean,default=True)                            #是否激活
    create_time=db.Column(db.DateTime,default=datetime.now())
    base_unit_price=db.Column(db.Float,nullable=False)                      #该政策的基础费用（最低阶梯且低谷期的单价）

    ladder_rule=db.relationship("LadderPriceRules",backref="policy")
    time_share_rule=db.relationship("TimeSharePriceRules",backref="policy")
    bill=db.relationship("Bill",backref="policy")
    def __repr__(self):
        return f"<PricePolicy {self.policy_name}>"

#阶梯电价规则表
class LadderPriceRules(db.Model):
    id=db.Column(db.Integer,primary_key=True,autoincrement=True)  # 修正拼写
    policy_id=db.Column(db.Integer,db.ForeignKey(PricePolicy.id),nullable=False)
    ladder_level=db.Column(db.Enum(LadderLevel),nullable=False)
    min_electricity=db.Column(db.Float,nullable=False)          #该阶梯最低用电量
    max_electricity=db.Column(db.Float)                         #该阶梯最高用电量
    ratio=db.Column(db.Float,nullable=False,default=1.0)        #该阶梯电价相对于基础电价的比率
    def __repr__(self):
        return f"<LadderRule {self.policy_id}-{self.ladder_level}>"

#分时电价规则表
class TimeSharePriceRules(db.Model):
    id=db.Column(db.Integer,primary_key=True,autoincrement=True)  # 修正拼写
    policy_id=db.Column(db.Integer,db.ForeignKey(PricePolicy.id),nullable=False)
    time_period=db.Column(db.Enum(TimePeriod),nullable=False)
    start_hour=db.Column(db.Integer,nullable=False)
    end_hour=db.Column(db.Integer,nullable=False)
    ratio=db.Column(db.Float,nullable=False,default=1.0)
    def __repr__(self):
        return f"<Bill {self.user_id}-{self.bill_month}>"

class Bill(db.Model):                                                   #账单绑定到电表，是电表的账单
    id=db.Column(db.Integer,primary_key=True,autoincrement=True)  # 修正拼写
    user_id=db.Column(db.Integer,db.ForeignKey(User.id),nullable=False)
    meter_id=db.Column(db.Integer,db.ForeignKey(Meter.id),nullable=False)
    bill_month=db.Column(db.DateTime,nullable=False)                    #按月计费
    total_amount=db.Column(db.Float,nullable=False)
    total_electricity=db.Column(db.Float,nullable=False)
    policy_id=db.Column(db.Integer,db.ForeignKey(PricePolicy.id))
    status=db.Column(db.Enum(BillStatus),default=BillStatus.unpaid)
    due_date=db.Column(db.DateTime,nullable=False)
    create_time=db.Column(db.DateTime,default=datetime.now())

    # meter 关系已经由 Meter.bills 的 backref 自动创建，不需要重复定义
    bill_details=db.relationship("BillDetail",backref="bill")          
    """
    一个账单对应若干个账单详情，
    每个账单详情记录了某个同一时段同一阶梯的单价和总价，
    因此一般一个账单对应多个账单详情
    """
    __table_arg__=(
        db.UniqueConstraint("user_id","meter_id","bill_month","uq_user_meter_bill"),  # 修正拼写：UniqueConstrict -> UniqueConstraint
        db.Index("user_meter_bill_id","user_id","meter_id","bill_month"),
        db.Index("idx_user_status", "user_id", "status")
    )
    def __repr__(self):
        return f"<Bill {self.user_id}-{self.bill_month}>"

class BillDetail(db.Model):
    id=db.Column(db.Integer,primary_key=True,autoincrement=True)  # 修正拼写
    bill_id=db.Column(db.Integer,db.ForeignKey(Bill.id),nullable=False)
    #计价策略二选一，或者混合
    detail_type=db.Column(db.Enum(PriceType),nullable=False)
    ladder_level=db.Column(db.Enum(LadderLevel))
    time_period=db.Column(db.Enum(TimePeriod))

    electricity=db.Column(db.Float,nullable=False)
    unit_price=db.Column(db.Float,nullable=False)
    amount=db.Column(db.Float,nullable=False)

    def __repr__(self):
        return f"<BillDetail {self.bill_id}-{self.detail_type.value}>"