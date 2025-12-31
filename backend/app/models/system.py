# 系统配置模型（Region、Permission）
from . import db
from .user import User

#权限表，包含id，权限说明，权限标识
class Permission(db.Model):
    __tablename__="PERMISSION"
    id=db.Column(db.Integer,primary_key=True)
    per_name=db.Column(db.String(50),nullable=False,unique=True,comment="权限说明，如查询用电数据，修改用电数据等")
    per_code=db.Column(db.String(50),unique=True,nullable=False,comment="权限标识，如query、edit，原则上一条记录只能单个权限")

    def __repr__(self):
        return f"<Region {self.per_name}>"

class Region(db.Model):
    __tablename__="REGION"
    id=db.Column(db.Integer,primary_key=True,autoincrement=True)                      # 修正拼写
    region_code=db.Column(db.String(3),nullable=False,unique=True,comment="数字编码，不超过3位，用于生成电表编码")                     
    region_name=db.Column(db.String(50),nullable=False)                                 #可能有重名区域，但是id不能重名
    parent_id=db.Column(db.Integer,db.ForeignKey("REGION.id"),comment="上级片区id")
    manager_id=db.Column(db.Integer,db.ForeignKey("USER.id"),comment="区域管理员id")      # 修正拼写：commend -> comment

    parent=db.relationship("Region",remote_side=[id],backref="children")        #自关联到上级
    manager=db.relationship("User",foreign_keys=[manager_id],backref="manage_region")

    def __repr__(self):
        return f"<Region {self.region_name}>"
