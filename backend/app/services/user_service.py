#用户业务（权限校验、电表绑定逻辑）
from ..models import User,Role,RoleEnum,UserStatus,Region,Meter,Bill,BillStatus
from app import db
from ..middleware import BusinessException,create_log,LogType,LogLevel,generate_user_token
from flask import session,current_app,g
from app.utils import verify_jwt
from dotenv import load_dotenv
import os
import time

load_dotenv()

class UserServices:
    @staticmethod
    def register(mail,password,real_name=None,idcard=None,region_id=None)->dict: 
        """
        注册功能：校验邮箱与身份证号唯一性、密码加密后写入数据库、初始化用户角色、写入用户表
        :param mail: 邮箱
        :param password: 密码
        :param real_name: 真名
        :param idcard: 身份证
        :param region_id: 片区号
        :return: 用户信息
        :rtype: dict
        """
        if db.session.query(User).filter_by(mail=mail).first() is not None:
            raise BusinessException("当前邮箱已被注册！")
        # 只有当身份证号不为空时才检查唯一性
        if idcard and db.session.query(User).filter_by(idcard=idcard).first() is not None:
            raise BusinessException("当前身份证号已有人注册！")
        if not db.session.query(Region).filter_by(id=region_id).first():
            raise BusinessException("片区id不存在！")

        #获取默认角色（居民）id
        default_role=db.session.query(Role).filter_by(name=RoleEnum.RESIDENT).first()
        if not default_role:
            default_role=Role(
                name=RoleEnum.RESIDENT,
                desc="普通居民"
            )
            db.session.add(default_role)
            db.session.flush()
        
        new_user=User(
            mail=mail,
            real_name=real_name,
            idcard=idcard,
            region_id=region_id,
            role_id=default_role.id
        )
        """
        模型类中的逻辑自始至终都没有提供password的字段，实际上是将加密后的字段存储在password_hash字段中
        需要校验密码时本质是调用check_password函数将当前传入字段hash过后的结果进行比较
        """
        new_user.password=password
        db.session.add(new_user)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            create_log(
                operator_id=None,
                operator_name="系统",
                log_type=LogType.ERROR,
                module="用户管理",
                action=f"用户注册失败：{mail}",
                error_message=str(e),
                log_level=LogLevel.ERROR
            )
            raise BusinessException("用户注册失败",500)

        return {
            "success":True,
            "user_info":{
                "user_id": new_user.id,
                "mail": new_user.mail,
                "real_name": new_user.real_name or "",
                "region_id": new_user.region_id or "",
                "role": default_role.name.value,
                "create_time": new_user.create_time.strftime("%Y-%m-%d %H:%M:%S")
            }
        }
    
    #目前支持邮箱登录
    @staticmethod
    def login(mail,password)->dict:
        """
        登录功能：校验邮箱是否存在、校验密码正确性、生成JWT、返回用户基本信息和令牌
        :param mail: 说明
        :param password: 说明
        :return: 说明
        :rtype: dict
        """
        login_user=db.session.query(User).filter_by(mail=mail).first()        #在注册时保证唯一性
        if not login_user:
            create_log(
                operator_id=None,
                operator_name="系统",
                log_type=LogType.ERROR,
                module="用户管理",
                action=f"登录失败：该邮箱未注册 - {mail}",
                log_level=LogLevel.WARNING
            )
            raise BusinessException("用户未注册",404)
        if login_user.status==UserStatus.CANCELED:
            create_log(
                operator_id=login_user.id,
                operator_name=login_user.real_name or mail,
                log_type=LogType.ERROR,
                module="用户管理",
                action=f"登录失败：该用户已销户",
                log_level=LogLevel.WARNING
            )
            raise BusinessException("用户已销户",403)
        if not login_user.check_password(password):
            create_log(
                operator_id=login_user.id,
                operator_name=login_user.real_name or mail,
                log_type=LogType.ERROR,
                module="用户管理",
                action=f"登录失败：密码错误",
                log_level=LogLevel.WARNING
            )
            raise BusinessException("密码错误",401)
        
        token=generate_user_token(login_user.id,2)      #token有效时间两小时
        refresh_token=generate_user_token(login_user.id,10)         #9小时过期，用于刷新token

        return {
            "token":token,
            "refresh_token":refresh_token,
            "user_info": {
                "user_id": login_user.id,
                "mail": login_user.mail,
                "real_name": login_user.real_name or "",    #防止因None出现渲染异常
                "role": login_user.role.name.value,
                "status": login_user.status.value
            }
        }
    
    #刷新token
    @staticmethod
    def refresh_token(refresh_token):
        payload=verify_jwt(refresh_token,os.getenv("REFRESH_TOKEN_SECRET_KEY","default_REFRESH_TOKEN_SECRET_KEY"))      #refresh_token有效
        exp_time=payload.get("exp")
        current_time=int(time.time())
        if 0<exp_time-current_time<7200:            #如果refresh_token马上过期
            new_refresh_token=generate_user_token(payload.get("sub"),expire_hours=9)        #刷新refresh_token
        #刷新token
        token=generate_user_token(payload.get("sub"),expire_hours=2)
        return {
            "token":token,
            "refresh_token":new_refresh_token
        }
    
    #查询某用户是否有某权限
    @staticmethod
    def check_permission(user_id,required_permission:str)->bool:
        """
        查询用户是否具有某权限，每个权限原则上都使用特定代码（如query、edit等），
        创建权限需要校验（需要限定角色），但是这个被查询的权限字段就无所谓，随他查什么
        :param user_id: 说明
        :param required_permission: 说明
        :type required_permission: str
        :return: 说明
        :rtype: bool
        """
        user=db.session.query(User).get(user_id)
        if user is None:
            raise BusinessException("用户不存在",404)
        if user.role==RoleEnum.SUPER_ADMIN:
            return True
        permissions=[perm.per_code for perm in user.role.permissions]   #当前角色的权限表
        # 遍历所有权限，检查是否有元素包含 required_permission，支持部分匹配（如果per_code一个对应多个权限代码字段）
        for perm in permissions:
            if required_permission in perm:  # 部分匹配（子字符串）
                return True
        return False
    
    @staticmethod
    def modify_user_msg(user_id,mail,real_name=None,idcard=None,region_id=None)->dict:
        """
        修改个人信息：权限已在接口层校验，不包括修改密码，修改密码调用专门的视图函数
        :param user_id: 被修改者id
        :param mail: 邮箱
        :param password: 密码
        :param real_name: 真实姓名
        :param idcard: 身份证
        :param region_id: 片区ID
        :return: 用户信息
        :rtype: dict
        """
        user=User.query.get(user_id)

        if user is None:
            raise BusinessException("用户不存在",404)
        if mail==user.mail and real_name==real_name and idcard==idcard and region_id==region_id:
            raise BusinessException("没有需要修改的信息")
        mailuser=db.session.query(User).filter_by(mail=mail).first()
        if mailuser is not None and mailuser.id!=user_id:
            raise BusinessException("当前邮箱已被他人注册！")
        idcarduser=db.session.query(User).filter_by(idcard=idcard).first()
        if idcarduser is not None and idcarduser.id!=user_id:
            raise BusinessException("当前身份证已被他人注册！")
        if not db.session.query(Region).filter_by(id=region_id).first():
            raise BusinessException("片区id不存在！")        
        
        user.mail=mail
        user.real_name=real_name
        user.idcard=idcard
        user.region_id=region_id

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            create_log(
                operator_id=user_id,
                operator_name=user.real_name or user.mail,
                log_type=LogType.ERROR,
                module="用户管理",
                action=f"修改用户信息失败",
                error_message=str(e),
                log_level=LogLevel.ERROR
            )
            raise BusinessException("用户修改个人信息失败",500)

        return {
            "user_id": user.id,
            "mail": user.mail,
            "real_name": user.real_name or "",
            "region_id": user.region_id or "",
            "role": user.role.name.value,
            "update_time": user.update_time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    @staticmethod
    def get_user_info(user_id)->dict:
        """获取用户信息：判定用户是否存在，若存在脱敏处理身份证，返回用户信息"""
        user = User.query.get(user_id)
        
        if not user:
            raise BusinessException("用户不存在", 404)
        
        # 脱敏处理身份证
        id_card = user.idcard
        if id_card:
            id_card = id_card[:6] + "********" + id_card[-4:]
        
        return {
            "user_id": user.id,
            "mail": user.mail,
            "real_name": user.real_name or "",
            "id_card": id_card or "",
            "region_id": user.region_id or "",
            "region_name": user.region.region_name if user.region else "",
            "role": user.role.name.value,
            "status": user.status.value,
            "create_time": user.create_time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    @staticmethod
    def get_user_meters(user_id)->dict:
        """获取用户绑定的电表列表：判定用户是否存在，若存在返回用户绑定电表列表"""
        user = User.query.get(user_id)
        
        if not user:
            raise BusinessException("用户不存在", 404)
        
        meters = Meter.query.filter_by(user_id=user_id).all()
        
        meter_list = []
        for meter in meters:
            meter_list.append({
                "meter_id": meter.id,
                "meter_code": meter.meter_code,
                "meter_type": meter.meter_type.value,
                "install_address": meter.install_address,
                "status": meter.status.value,
                "install_date": meter.install_date.strftime("%Y-%m-%d") if meter.install_date else None
            })
        
        return {
            "total": len(meter_list),
            "meters": meter_list
        }
    
    
    @staticmethod
    def bind_meter(user_id,meter_code)->dict:
        """
        绑定电表：绑定用户
        :param user_id: 被绑定用户
        :param meter_code: 电表编号
        :return: 说明
        :rtype: dict
        """
        user=User.query.get(user_id)
        meter=db.session.query(Meter).filter_by(meter_code=meter_code).first()  #数据表中已经保证电表编号唯一

        if not user:
            raise BusinessException("被绑定用户不存在",404)
        if user.status!=UserStatus.NORMAL:
            raise BusinessException("用户状态异常，无法绑定")
        if not meter:
            raise BusinessException("电表不存在",404)
        if meter.user_id is not None:
            if meter.user_id!=user_id:
                raise BusinessException("该电表已绑定到其他用户")
            raise BusinessException("该电表已经绑定到该用户")
        if meter.region_id!=user.region_id:
            raise BusinessException("该电表无法绑定到该区域的用户")
        
        meter.user_id=user_id

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            create_log(
                operator_id=user_id,
                operator_name=user.real_name or user.mail,
                log_type=LogType.ERROR,
                module="用户管理",
                action=f"电表绑定失败：电表{meter.meter_code}",
                error_message=str(e),
                log_level=LogLevel.ERROR
            )
            raise BusinessException("电表绑定失败",500)
        
        return {
            "msg": "电表绑定成功",
            "meter_info": {
                "meter_code": meter.meter_code,
                "install_address": meter.install_address,
                "status": meter.status.value
            }
        }
    
    @staticmethod
    def unbind_meter(user_id, meter_id)->dict:
        """解绑电表：检测用户是否存在以及电表是否存在以及电表是否被绑定当前用户，若都满足检测电表是否还有未交账单，若无则设置该电表的user_id为空"""
        user = User.query.get(user_id)
        meter = Meter.query.get(meter_id)
        
        if not user:
            raise BusinessException("用户不存在", 404)
        if not meter:
            raise BusinessException("电表不存在", 404)
        if meter.user_id != user_id:
            raise BusinessException("该电表不属于当前用户", 403)
        
        # 检查是否有未支付的账单
        unpaid_bills = Bill.query.filter_by(
            meter_id=meter_id,
            status=BillStatus.unpaid
        ).first()
        
        if unpaid_bills is not None:
            raise BusinessException("该电表还有未支付的账单，无法解绑", 400)
        
        meter.user_id = None
        
        try:
            db.session.commit()
            
            create_log(
                operator_id=user_id,
                operator_name=user.real_name or user.mail,
                log_type=LogType.UPDATE,
                module="用户管理",
                action=f"解绑电表：{meter.meter_code}",
                log_level=LogLevel.INFO
            )
        except Exception as e:
            db.session.rollback()
            create_log(
                operator_id=user_id,
                operator_name=user.real_name or user.mail,
                log_type=LogType.ERROR,
                module="用户管理",
                action=f"电表解绑失败：电表{meter.meter_code}",
                error_message=str(e),
                log_level=LogLevel.ERROR
            )
            raise BusinessException("电表解绑失败", 500)
        
        return {
            "message": "电表解绑成功",
            "meter_info": {
                "meter_code": meter.meter_code,
                "meter_id": meter.id
            }
        }
    
    @staticmethod
    def change_password(user_id, old_password, new_password)->dict:
        """修改密码：只能用户本人修改，分为验证旧密码和设置新密码两步"""
        user = User.query.get(user_id)
        
        if not user:
            raise BusinessException("用户不存在", 404)
        
        # 验证旧密码
        if not user.check_password(old_password):
            create_log(
                operator_id=user_id,                  #虽然理论上管理员也可以修改，但是麻烦，还要给管理员提供查旧id的服务，就算了
                operator_name=user.real_name or user.mail,
                log_type=LogType.ERROR,
                module="用户管理",
                action=f"修改密码失败：旧密码错误",
                log_level=LogLevel.WARNING
            )
            raise BusinessException("旧密码错误", 401)
        
        # 设置新密码
        user.password = new_password
        
        try:
            db.session.commit()
            
            create_log(
                operator_id=user_id,
                operator_name=user.real_name or user.mail,
                log_type=LogType.UPDATE,
                module="用户管理",
                action=f"修改密码成功",
                log_level=LogLevel.INFO
            )
        except Exception as e:
            db.session.rollback()
            create_log(
                operator_id=user_id,
                operator_name=user.real_name or user.mail,
                log_type=LogType.ERROR,
                module="用户管理",
                action=f"修改密码失败",
                error_message=str(e),
                log_level=LogLevel.ERROR
            )
            raise BusinessException("修改密码失败", 500)
        
        return {
            "message": "密码修改成功",
            "user_id": user_id
        }
    
    @staticmethod
    def modify_user_status(user_id,new_status:UserStatus):
        """
        修改用户状态，由管理员修改
        :param user_id: 说明
        :param new_status: 说明
        :type new_status: UserStatus
        """
        user=User.query.get(user_id)
        if user is None:
            raise BusinessException("被修改状态的用户不存在！",404)
        if new_status==UserStatus.CANCELED:
            for meter in user.meters:
                unpaid_bill=Bill.query.filter_by(meter_id=meter.id,status=BillStatus.unpaid).first()
                if unpaid_bill is None:
                    raise BusinessException("该用户有未缴账单，无法销户！")
        
        user.status=new_status

        try:
            db.session.commit()
            
            create_log(
                operator_id=g.user_id,
                operator_name="管理员",
                log_type=LogType.UPDATE,
                module="用户管理",
                action=f"修改用户状态成功",
                log_level=LogLevel.INFO
            )
        except Exception as e:
            db.session.rollback()
            create_log(
                operator_id=g.user_id,
                operator_name="管理员",
                log_type=LogType.ERROR,
                module="用户管理",
                action=f"修改用户状态失败",
                error_message=str(e),
                log_level=LogLevel.ERROR
            )
            raise BusinessException("修改用户状态失败", 500)
        
        return {
            "user_id": user_id
        }
    
    @staticmethod
    def send_reset_code(mail: str) -> dict:
        """
        发送重置密码验证码
        :param mail: 邮箱地址
        :return: 发送结果
        """
        from ..utils.redis_util import generate_verification_code, save_verification_code
        from ..utils.mail_util import send_mail
        from flask_mail import Mail
        
        # 检查邮箱是否存在
        user = User.query.filter_by(mail=mail).first()
        if not user:
            raise BusinessException("该邮箱未注册", 404)
        
        # 生成6位数字验证码
        code = generate_verification_code(6)
        
        # 保存到缓存（5分钟有效）
        save_verification_code(mail, code, expire=300)
        
        # 尝试发送邮件（不阻塞主流程）
        mail_sent = False
        try:
            mail_instance = Mail(current_app)
            email_content = f"""
            <h2>重置密码验证码</h2>
            <p>尊敬的用户 {user.real_name or mail}，</p>
            <p>您正在进行密码重置操作，验证码为：</p>
            <h1 style="color: #4CAF50; letter-spacing: 5px;">{code}</h1>
            <p>验证码有效期为 <strong>5分钟</strong>，请尽快使用。</p>
            <p>如果这不是您本人的操作，请忽略此邮件。</p>
            <br>
            <p>电费查询系统</p>
            """
            
            send_mail(
                mail_instance,
                subject="重置密码验证码",
                recipients=[mail],
                cc=[],
                bcc=[],
                html=email_content
            )
            mail_sent = True
            
            create_log(
                operator_id=None,
                operator_name="系统",
                log_type=LogType.CREATE,
                module="用户管理",
                action=f"发送重置密码验证码到: {mail}",
                log_level=LogLevel.INFO
            )
            
        except Exception as e:
            # 邮件发送失败，记录日志但不影响验证码功能
            create_log(
                operator_id=None,
                operator_name="系统",
                log_type=LogType.ERROR,
                module="用户管理",
                action=f"发送验证码邮件失败: {mail}",
                error_message=str(e),
                log_level=LogLevel.ERROR
            )
            print(f"邮件发送失败: {str(e)}")
        
        # 无论邮件是否发送成功，验证码都已保存，返回成功
        # 测试环境下如果邮件失败，可以从日志或控制台查看验证码
        if not mail_sent:
            print(f"【调试信息】验证码: {code}")
        
        return {
            "success": True,
            "message": "验证码已发送到您的邮箱" if mail_sent else "验证码已生成（邮件发送失败，请查看后台日志）",
            "email": mail
        }
    
    @staticmethod
    def reset_password(mail: str, code: str, new_password: str) -> dict:
        """
        重置密码
        :param mail: 邮箱地址
        :param code: 验证码
        :param new_password: 新密码
        :return: 重置结果
        """
        from ..utils.redis_util import verify_code
        
        # 验证验证码
        if not verify_code(mail, code):
            raise BusinessException("验证码错误或已过期", 400)
        
        # 查找用户
        user = User.query.filter_by(mail=mail).first()
        if not user:
            raise BusinessException("用户不存在", 404)
        
        # 更新密码
        user.password = new_password  # 使用property setter自动加密
        
        try:
            db.session.commit()
            
            create_log(
                operator_id=user.id,
                operator_name=user.real_name or user.mail,
                log_type=LogType.UPDATE,
                module="用户管理",
                action=f"用户 {mail} 重置密码成功",
                log_level=LogLevel.INFO
            )
            
            return {
                "success": True,
                "message": "密码重置成功",
                "user_id": user.id
            }
            
        except Exception as e:
            db.session.rollback()
            create_log(
                operator_id=None,
                operator_name="系统",
                log_type=LogType.ERROR,
                module="用户管理",
                action=f"重置密码失败: {mail}",
                error_message=str(e),
                log_level=LogLevel.ERROR
            )
            raise BusinessException("密码重置失败", 500)
