# 用户模型（User、Role）
import enum
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from sqlalchemy import event

class RoleEnum(enum.Enum):
    RESIDENT = "resident"           #普通居民
    AREA_ADMIN = "area_admin"       #区域管理员
    SUPER_ADMIN = "super_admin"     #超级管理员

class UserStatus(enum.Enum):
    NORMAL="normal"                 #正常
    ARREAR="arrear"                 #欠费
    CANCELED="canceled"             #销户

role_permissions=db.Table(
    "role_permissions",
    db.Column("role_id",db.Integer,db.ForeignKey("ROLE.id"),primary_key=True),
    db.Column("permission_id",db.Integer,db.ForeignKey("PERMISSION.id"),primary_key=True)
)

#角色表，包含id，名称，描述，创建时间，权限
class Role(db.Model):
    __tablename__="ROLE"
    id=db.Column(db.Integer,primary_key=True,autoincrement=True)
    name=db.Column(db.Enum(RoleEnum),nullable=False,unique=True)
    desc=db.Column(db.String(50),comment="角色描述，如普通居民")
    create_time=db.Column(db.DateTime,default=datetime.now(),comment="创建时间")
    permissions=db.relationship(
        "Permission",
        secondary="role_permissions",
        backref="Role",
        lazy="joined"
        )
    def __rerp__(self):
        return f"<Role {self.name}>"

class User(db.Model):
    __tablename__="USER"
    id=db.Column(db.Integer,primary_key=True,autoincrement=True)  # 修正拼写
    mail=db.Column(db.String(30),unique=True,nullable=False)
    password_hash=db.Column(db.String(256),nullable=False)
    real_name=db.Column(db.String(20))
    idcard=db.Column(db.String(18))
    region_id=db.Column(db.Integer,db.ForeignKey("REGION.id"))
    role_id=db.Column(db.Integer,db.ForeignKey("ROLE.id"),default=1)
    status=db.Column(db.Enum(UserStatus),default=UserStatus.NORMAL)
    create_time=db.Column(db.DateTime,default=datetime.now(),comment="创建时间")
    update_time=db.Column(db.DateTime,default=datetime.now(),comment="更新时间")

    #关联
    region=db.relationship("Region",foreign_keys=[region_id],backref="users")        #自动建立反向关联
    role=db.relationship("Role",backref="users")
    meters=db.relationship("Meter",backref="user")

    def __rerp__(self):
        return f"<User {self.id}>"

    @property
    def password(self):
        raise AttributeError("密码不可直接访问")
    
    @password.setter
    def password(self,password):
        self.password_hash=generate_password_hash(password)
    
    def check_password(self,password):
        return check_password_hash(self.password_hash,password)

#监听更新
@event.listens_for(User,"after_update")
def auto_update_time(mapper,connection,target):
    target.update_time=datetime.now