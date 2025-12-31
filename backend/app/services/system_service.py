# 系统管理业务（电价策略、片区管理、权限管理、日志查询）
from app.models import (PricePolicy, Region, User, Permission, Role, Bill,
            PriceType, LadderPriceRules, TimeSharePriceRules, BillStatus,RoleEnum,
            NoticeType, SendChannel)
from ..middleware import BusinessException,SystemLog, LogType, LogLevel, create_log
from app import db
from flask import current_app
from datetime import datetime, timedelta
from sqlalchemy import or_

class SystemServices:
    
    # ==================== 电价策略管理 ====================
    
    @staticmethod
    def create_price_policy(policy_name, price_type, region_id,
                           base_unit_price, start_time, end_time=None,
                           ladder_rules:list=None, time_share_rules:list=None):
        """
        新增电价策略
        :param policy_name: 策略名称
        :param price_type: 价格类型（ladder/time_share/combined）
        :param region_id: 片区ID
        :param base_unit_price: 基础单价
        :param start_time: 开始时间
        :param end_time: 结束时间（可选）
        :param ladder_rules: 阶梯规则列表 [{"ladder_level": "low", "min_electricity": 0, "max_electricity": 200, "ratio": 1.0}]
        :param time_share_rules: 分时规则列表 [{"time_period": "valley", "start_hour": 0, "end_hour": 8, "ratio": 0.8}]
        :return: 创建结果
        """
        # 1. 验证片区是否存在
        region = Region.query.get(region_id)
        if not region:
            raise BusinessException("片区不存在", 404)
        
        # 2. 校验策略生效时间不能与同片区现有策略冲突
        if isinstance(start_time, str):
            start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        if end_time and isinstance(end_time, str):
            end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
        
        # 查询冲突的策略
        conflict_query = PricePolicy.query.filter(
            PricePolicy.region_id == region_id,
            PricePolicy.is_active == True,
            PricePolicy.start_time < (end_time if end_time else datetime(2099, 12, 31))
        )
        
        if end_time:
            conflict_query = conflict_query.filter(
                or_(
                    PricePolicy.end_time.is_(None),
                    PricePolicy.end_time > start_time
                )
            )
        
        conflicts = conflict_query.all()
        
        if conflicts:
            conflict_info = ", ".join([f"{c.policy_name}({c.start_time.strftime('%Y-%m-%d')}~{c.end_time.strftime('%Y-%m-%d') if c.end_time else '永久'})" 
                                      for c in conflicts])
            raise BusinessException(f"策略时间与现有策略冲突：{conflict_info}", 400)
        
        # 3. 转换price_type字符串为枚举
        if isinstance(price_type, str):
            try:
                price_type = PriceType[price_type]
            except KeyError:
                raise BusinessException(f"无效的价格类型：{price_type}", 400)
        
        # 4. 创建价格策略
        new_policy = PricePolicy(
            policy_name=policy_name,
            price_type=price_type,
            region_id=region_id,
            base_unit_price=base_unit_price,
            start_time=start_time,
            end_time=end_time,
            is_active=True
        )
        
        db.session.add(new_policy)
        db.session.flush()  # 获取policy_id
        
        # 4. 创建阶梯规则
        if price_type in [PriceType.ladder, PriceType.combined] and ladder_rules:
            for rule in ladder_rules:
                ladder_rule = LadderPriceRules(
                    policy_id=new_policy.id,
                    ladder_level=rule["ladder_level"],
                    min_electricity=rule["min_electricity"],
                    max_electricity=rule.get("max_electricity"),
                    ratio=rule["ratio"]
                )
                db.session.add(ladder_rule)
        
        # 5. 创建分时规则
        if price_type in [PriceType.time_share, PriceType.combined] and time_share_rules:
            for rule in time_share_rules:
                time_rule = TimeSharePriceRules(
                    policy_id=new_policy.id,
                    time_period=rule["time_period"],
                    start_hour=rule["start_hour"],
                    end_hour=rule["end_hour"],
                    ratio=rule["ratio"]
                )
                db.session.add(time_rule)
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise BusinessException("电价策略创建失败", 500)
        
        return {
            "success": True,
            "message": "电价策略创建成功",
            "policy_info": {
                "policy_id": new_policy.id,
                "policy_name": policy_name,
                "price_type": price_type.name,
                "region_name": region.region_name,
                "base_unit_price": base_unit_price,
                "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S") if end_time else None
            }
        }
    
    @staticmethod
    def update_price_policy(policy_id, **kwargs):
        """
        修改电价策略
        :param policy_id: 策略ID
        :param kwargs: 要更新的字段
        :return: 更新结果
        """
        print(f"[DEBUG] update_price_policy called with policy_id={policy_id}, kwargs={kwargs}")
        
        policy = PricePolicy.query.get(policy_id)
        if not policy:
            raise BusinessException("电价策略不存在", 404)
        
        print(f"[DEBUG] 找到策略: {policy.policy_name}, current values: name={policy.policy_name}, price={policy.base_unit_price}, active={policy.is_active}")
        
        # 转换时间字符串为datetime对象
        if 'end_time' in kwargs and kwargs['end_time'] is not None:
            if isinstance(kwargs['end_time'], str):
                try:
                    kwargs['end_time'] = datetime.strptime(kwargs['end_time'], "%Y-%m-%d %H:%M:%S")
                    print(f"[DEBUG] 转换end_time字符串为datetime对象: {kwargs['end_time']}")
                except ValueError as e:
                    print(f"[DEBUG] end_time格式转换失败: {e}")
                    raise BusinessException(f"结束时间格式错误: {str(e)}", 400)
        
        # 记录修改内容
        changes = []
        
        # 可修改字段（价格类型和规则不可修改，如需修改需要删除重建）
        allowed_fields = ['policy_name', 'base_unit_price', 'end_time', 'is_active']
        
        for field, value in kwargs.items():
            if field in allowed_fields and hasattr(policy, field):
                old_value = getattr(policy, field)
                if old_value != value:
                    print(f"[DEBUG] 更新字段 {field}: {old_value} -> {value}")
                    setattr(policy, field, value)
                    changes.append(f"{field}: {old_value} -> {value}")
        
        if not changes:
            print("[DEBUG] 没有需要更新的内容")
            return {
                "success": True,
                "message": "没有需要更新的内容"
            }
        
        try:
            print(f"[DEBUG] 准备提交更改: {changes}")
            db.session.commit()
            print("[DEBUG] 更新成功")
        except Exception as e:
            print(f"[DEBUG] 更新失败: {str(e)}")
            db.session.rollback()
            raise BusinessException(f"电价策略更新失败: {str(e)}", 500)
        
        return {
            "success": True,
            "message": "电价策略更新成功",
            "changes": changes
        }
    
    @staticmethod
    def get_price_policy_list(region_id=None, is_active=None, page=1, per_page=20):
        """
        获取电价策略列表
        :param region_id: 片区ID（可选）
        :param is_active: 是否激活（可选）
        :param page: 页码
        :param per_page: 每页数量
        :return: 策略列表
        """
        query = db.session.query(PricePolicy)
        
        if region_id:
            query = query.filter(PricePolicy.region_id == region_id)
        
        if is_active is not None:
            query = query.filter(PricePolicy.is_active == is_active)
        
        query = query.order_by(PricePolicy.create_time.desc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        policies = []
        for policy in pagination.items:
            region = db.session.query(Region).get(policy.region_id)
            
            # 获取阶梯规则
            ladder_rules = []
            for rule in policy.ladder_rule:
                ladder_rules.append({
                    "ladder_level": rule.ladder_level.name if hasattr(rule.ladder_level, 'name') else rule.ladder_level,
                    "min_electricity": float(rule.min_electricity),
                    "max_electricity": float(rule.max_electricity) if rule.max_electricity else None,
                    "ratio": float(rule.ratio)
                })
            
            # 获取分时规则
            time_share_rules = []
            for rule in policy.time_share_rule:
                time_share_rules.append({
                    "time_period": rule.time_period.name if hasattr(rule.time_period, 'name') else rule.time_period,
                    "start_hour": rule.start_hour,
                    "end_hour": rule.end_hour,
                    "ratio": float(rule.ratio)
                })
            
            policies.append({
                "policy_id": policy.id,
                "policy_name": policy.policy_name,
                "price_type": policy.price_type.name if hasattr(policy.price_type, 'name') else policy.price_type,
                "region_id": policy.region_id,
                "region_name": region.region_name if region else None,
                "base_unit_price": float(policy.base_unit_price),
                "start_time": policy.start_time.strftime("%Y-%m-%d %H:%M:%S") if policy.start_time else None,
                "end_time": policy.end_time.strftime("%Y-%m-%d %H:%M:%S") if policy.end_time else None,
                "is_active": policy.is_active,
                "create_time": policy.create_time.strftime("%Y-%m-%d %H:%M:%S") if hasattr(policy.create_time, 'strftime') and policy.create_time else None,
                "ladder_rules": ladder_rules,
                "time_share_rules": time_share_rules
            })
        
        return {
            "policies": policies,
            "pagination": {
                "total": pagination.total,
                "page": pagination.page,
                "per_page": pagination.per_page,
                "pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev
            }
        }
    
    @staticmethod
    def delete_price_policy(policy_id):
        """
        删除电价策略
        :param policy_id: 策略ID
        :return: 删除结果
        """
        policy = PricePolicy.query.get(policy_id)
        if not policy:
            raise BusinessException("价格策略不存在", 404)
        
        # 检查是否有账单使用该策略
        bills = Bill.query.filter_by(policy_id=policy_id).first()
        if bills:
            raise BusinessException("该价格策略已被账单使用，无法删除", 400)
        
        try:
            # 删除关联的阶梯规则
            LadderPriceRules.query.filter_by(policy_id=policy_id).delete()
            # 删除关联的分时规则
            TimeSharePriceRules.query.filter_by(policy_id=policy_id).delete()
            # 删除策略本身
            db.session.delete(policy)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise BusinessException(f"删除价格策略失败：{str(e)}", 500)
        
        return {
            "success": True,
            "message": "价格策略删除成功"
        }
    
    @staticmethod
    def deactivate_price_policy(policy_id, reason=""):
        """
        停用电价策略
        :param policy_id: 策略ID
        :param reason: 停用原因
        :return: 停用结果
        """
        policy = PricePolicy.query.get(policy_id)
        if not policy:
            raise BusinessException("电价策略不存在", 404)
        
        if not policy.is_active:
            raise BusinessException("该策略已停用", 400)
        
        policy.is_active = False
        policy.end_time = datetime.now()
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise BusinessException("电价策略停用失败", 500)
        
        # 同步更新未生成账单的计费规则（标记需要重新计算）
        # 这里可以触发一个后台任务或标记
        SystemServices._sync_billing_rules_after_policy_change(policy_id)
        
        return {
            "success": True,
            "message": "电价策略已停用",
            "policy_name": policy.policy_name
        }
    
    @staticmethod
    def _sync_billing_rules_after_policy_change(policy_id):
        """策略变更后同步未生成账单的计费规则"""
        # 查找使用该策略且未支付的账单
        unpaid_bills = Bill.query.filter(
            Bill.policy_id == policy_id,
            Bill.status == BillStatus.unpaid
        ).all()
        
        if unpaid_bills:
            create_log(
                operator_id=None,
                operator_name="系统",
                log_type=LogType.WARNING,
                module="电价策略管理",
                action=f"策略{policy_id}变更，影响{len(unpaid_bills)}个未支付账单，需要管理员审核",
                log_level=LogLevel.WARNING
            )
            
            # 发送通知给所有超级管理员和相关片区管理员
            try:
                from services.notify_sevice import NotifyServices
                
                # 获取策略关联的片区
                policy = PricePolicy.query.get(policy_id)
                if not policy:
                    return
                
                # 获取该片区的所有管理员（包括超级管理员和片区管理员）
                admins = User.query.filter(
                    User.role_id.in_([
                        db.session.query(Role.id).filter(Role.name == RoleEnum.SUPER_ADMIN).scalar(),
                        db.session.query(Role.id).filter(Role.name == RoleEnum.AREA_ADMIN).scalar()
                    ])
                ).filter(
                    or_(
                        User.role.has(name=RoleEnum.SUPER_ADMIN),
                        User.region_id == policy.region_id
                    )
                ).all()
                
                if not admins:
                    return
                
                # 创建通知标题和内容
                title = f"电价策略变更提醒"
                content = (f"电价策略《{policy.policy_name}》已停用，"
                          f"影响{len(unpaid_bills)}个未支付账单，请及时审核处理。")
                
                # 创建并发送通知
                NotifyServices.create_notification(
                    notice_type=NoticeType.PRICE_CHANGE,
                    target_type=RoleEnum.AREA_ADMIN,
                    targets=admins,
                    title=title,
                    content=content,
                    send_channel=SendChannel.INNER,
                    send_time=datetime.now(),
                    is_batch=True,
                    related_id=policy_id
                )
                
            except Exception as e:
                # 通知失败不影响主流程，只记录日志
                create_log(
                    operator_id=None,
                    operator_name="系统",
                    log_type=LogType.ERROR,
                    module="电价策略管理",
                    action=f"发送策略变更通知失败：{str(e)}",
                    error_message=str(e),
                    log_level=LogLevel.ERROR
                )
    
    # ==================== 片区管理 ====================
    
    @staticmethod
    def create_region(region_code, region_name, parent_id=None, manager_id=None):
        """
        新增片区
        :param region_code: 片区编码（3位数字）
        :param region_name: 片区名称
        :param parent_id: 上级片区ID
        :param manager_id: 片区管理员ID
        :return: 创建结果
        """
        # 1. 校验片区编码唯一性
        existing_region = Region.query.filter_by(region_code=region_code).first()
        if existing_region:
            raise BusinessException(f"片区编码{region_code}已存在", 400)
        
        # 2. 验证上级片区
        if parent_id:
            parent_region = Region.query.get(parent_id)
            if not parent_region:
                raise BusinessException("上级片区不存在", 404)
        
        # 3. 验证管理员
        if manager_id:
            manager = User.query.get(manager_id)
            if not manager:
                raise BusinessException("管理员不存在", 404)
            if manager.role.name not in [RoleEnum.AREA_ADMIN, RoleEnum.SUPER_ADMIN]:
                raise BusinessException("该用户不是管理员角色", 400)
        
        # 4. 创建片区
        new_region = Region(
            region_code=region_code,
            region_name=region_name,
            parent_id=parent_id,
            manager_id=manager_id
        )
        
        db.session.add(new_region)
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise BusinessException("片区创建失败", 500)
        
        return {
            "success": True,
            "message": "片区创建成功",
            "region_info": {
                "region_id": new_region.id,
                "region_code": region_code,
                "region_name": region_name,
                "parent_id": parent_id,
                "manager_id": manager_id
            }
        }
    
    @staticmethod
    def update_region(region_id, **kwargs):
        """
        修改片区信息
        :param region_id: 片区ID
        :param kwargs: 要更新的字段
        :return: 更新结果
        """
        region = Region.query.get(region_id)
        if not region:
            raise BusinessException("片区不存在", 404)
        
        changes = []
        allowed_fields = ['region_name', 'parent_id', 'manager_id']
        
        for field, value in kwargs.items():
            if field in allowed_fields and hasattr(region, field):
                old_value = getattr(region, field)
                
                # 特殊校验
                if field == 'parent_id' and value:
                    # 检查是否会形成循环引用
                    if SystemServices._check_region_circular_reference(region_id, value):
                        raise BusinessException("不能将片区的父级设置为自己的子级", 400)
                
                if field == 'manager_id' and value:
                    manager = User.query.get(value)
                    if not manager:
                        raise BusinessException("管理员不存在", 404)
                
                if old_value != value:
                    setattr(region, field, value)
                    changes.append(f"{field}: {old_value} -> {value}")
        
        if not changes:
            return {"success": True, "message": "没有需要更新的内容"}
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise BusinessException("片区更新失败", 500)
        
        return {
            "success": True,
            "message": "片区更新成功",
            "changes": changes
        }
    
    @staticmethod
    def _check_region_circular_reference(region_id, new_parent_id):
        """检查片区是否会形成循环引用"""
        current_id = new_parent_id
        visited = set()
        
        while current_id:
            if current_id == region_id:
                return True  # 发现循环
            
            if current_id in visited:
                return True  # 发现循环
            
            visited.add(current_id)
            
            parent_region = Region.query.get(current_id)
            if not parent_region:
                break
            
            current_id = parent_region.parent_id
        
        return False
    
    @staticmethod
    def get_region_list(page=1, per_page=20):
        """
        获取片区列表
        :param page: 页码
        :param per_page: 每页数量
        :return: 片区列表
        """
        query = db.session.query(Region).order_by(Region.id.asc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        regions = []
        for region in pagination.items:
            manager = db.session.query(User).get(region.manager_id) if region.manager_id else None
            parent = db.session.query(Region).get(region.parent_id) if region.parent_id else None
            
            regions.append({
                "region_id": region.id,
                "region_code": region.region_code,
                "region_name": region.region_name,
                "parent_id": region.parent_id,
                "parent_name": parent.region_name if parent else None,
                "manager_id": region.manager_id,
                "manager_name": manager.real_name if manager and manager.real_name else (manager.mail if manager else None)
            })
        
        return {
            "regions": regions,
            "pagination": {
                "total": pagination.total,
                "page": pagination.page,
                "per_page": pagination.per_page,
                "pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev
            }
        }
    
    @staticmethod
    def delete_region(region_id):
        """
        删除片区
        :param region_id: 片区ID
        :return: 删除结果
        """
        region = Region.query.get(region_id)
        if not region:
            raise BusinessException("片区不存在", 404)
        
        # 检查是否有下级片区
        children = Region.query.filter_by(parent_id=region_id).first()
        if children:
            raise BusinessException("该片区存在下级片区，无法删除", 400)
        
        # 检查是否有价格策略使用该片区
        policies = PricePolicy.query.filter_by(region_id=region_id).first()
        if policies:
            raise BusinessException("该片区已被价格策略使用，无法删除", 400)
        
        try:
            db.session.delete(region)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise BusinessException(f"删除片区失败：{str(e)}", 500)
        
        return {
            "success": True,
            "message": "片区删除成功"
        }
    
    # ==================== 权限管理 ====================
    
    @staticmethod
    def create_permission(per_name, per_code):
        """
        创建权限
        :param per_name: 权限名称
        :param per_code: 权限编码
        :return: 创建结果
        """
        # 校验权限编码唯一性
        existing_permission = Permission.query.filter_by(per_code=per_code).first()
        if existing_permission:
            raise BusinessException(f"权限编码{per_code}已存在", 400)
        
        new_permission = Permission(
            per_name=per_name,
            per_code=per_code
        )
        
        db.session.add(new_permission)
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise BusinessException("权限创建失败", 500)
        
        return {
            "success": True,
            "message": "权限创建成功",
            "permission_info": {
                "permission_id": new_permission.id,
                "per_name": per_name,
                "per_code": per_code
            }
        }
    
    @staticmethod
    def assign_role_permissions(role_id, permission_ids, mode="add"):
        """
        给角色分配/移除权限
        :param role_id: 角色ID
        :param permission_ids: 权限ID列表
        :param mode: 模式（add=添加, remove=移除, replace=替换）
        :return: 分配结果
        """
        role = Role.query.get(role_id)
        if not role:
            raise BusinessException("角色不存在", 404)
        
        # 获取权限对象
        permissions = Permission.query.filter(Permission.id.in_(permission_ids)).all()
        if len(permissions) != len(permission_ids):
            raise BusinessException("部分权限不存在", 404)
        
        if mode == "add":
            # 添加权限
            for permission in permissions:
                if permission not in role.permissions:
                    role.permissions.append(permission)
            action_desc = f"为角色{role.name.value}添加权限：{', '.join([p.per_name for p in permissions])}"
            
        elif mode == "remove":
            # 移除权限
            for permission in permissions:
                if permission in role.permissions:
                    role.permissions.remove(permission)
            action_desc = f"从角色{role.name.value}移除权限：{', '.join([p.per_name for p in permissions])}"
            
        elif mode == "replace":
            # 替换权限
            role.permissions = permissions
            action_desc = f"替换角色{role.name.value}的权限为：{', '.join([p.per_name for p in permissions])}"
        else:
            raise BusinessException("不支持的操作模式", 400)
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise BusinessException("角色权限更新失败", 500)
        
        return {
            "success": True,
            "message": f"角色权限{mode}成功",
            "role_name": role.name.value,
            "current_permissions": [
                {"id": p.id, "name": p.per_name, "code": p.per_code}
                for p in role.permissions
            ]
        }
    
    # ==================== 系统日志查询 ====================
    
    @staticmethod
    def query_system_logs(operator_id=None, log_type=None, log_level=None, 
                         start_date=None, end_date=None, keyword=None,
                         page=1, per_page=50):
        """
        查询系统日志
        :param operator_id: 操作人ID
        :param log_type: 日志类型
        :param log_level: 日志级别
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param keyword: 关键词搜索（操作描述）
        :param page: 页码
        :param per_page: 每页数量
        :return: 日志列表
        """
        query = SystemLog.query
        
        # 按操作人筛选
        if operator_id:
            query = query.filter_by(operator_id=operator_id)
        
        # 按日志类型筛选
        if log_type:
            query = query.filter_by(log_type=log_type)
        
        # 按日志级别筛选
        if log_level:
            query = query.filter_by(log_level=log_level)
        
        # 按时间范围筛选
        if start_date:
            query = query.filter(SystemLog.create_time >= start_date)
        if end_date:
            query = query.filter(SystemLog.create_time <= end_date)
        
        # 关键词搜索
        if keyword:
            query = query.filter(
                or_(
                    SystemLog.action.like(f"%{keyword}%"),
                    SystemLog.module.like(f"%{keyword}%"),
                    SystemLog.error_message.like(f"%{keyword}%")
                )
            )
        
        # 按时间倒序排列
        query = query.order_by(SystemLog.create_time.desc())
        
        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        logs = []
        for log in pagination.items:
            logs.append({
                "id": log.id,
                "operator_id": log.operator_id,
                "operator_name": log.operator_name,
                "log_type": log.log_type.value if log.log_type else None,
                "log_level": log.log_level.value if log.log_level else None,
                "module": log.module,
                "action": log.action,
                "request_method": log.request_method,
                "request_url": log.request_url,
                "request_ip": log.request_ip,
                "response_status": log.response_status,
                "error_message": log.error_message,
                "execution_time": log.execution_time,
                "create_time": log.create_time.strftime("%Y-%m-%d %H:%M:%S")
            })
        
        return {
            "success": True,
            "logs": logs,
            "pagination": {
                "total": pagination.total,
                "page": pagination.page,
                "per_page": pagination.per_page,
                "pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev
            }
        }
    
    @staticmethod
    def query_abnormal_logs(days=7, page=1, per_page=50):
        """
        筛选异常操作日志
        :param days: 查询最近几天的日志
        :param page: 页码
        :param per_page: 每页数量
        :return: 异常日志列表
        """
        start_date = datetime.now() - timedelta(days=days)
        
        # 查询错误和警告级别的日志
        query = SystemLog.query.filter(
            SystemLog.create_time >= start_date,
            SystemLog.log_level.in_([LogLevel.ERROR, LogLevel.CRITICAL, LogLevel.WARNING])
        ).order_by(SystemLog.create_time.desc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        abnormal_logs = []
        for log in pagination.items:
            abnormal_logs.append({
                "id": log.id,
                "operator_id": log.operator_id,
                "operator_name": log.operator_name,
                "log_type": log.log_type.value if log.log_type else None,
                "log_level": log.log_level.value if log.log_level else None,
                "module": log.module,
                "action": log.action,
                "error_message": log.error_message,
                "create_time": log.create_time.strftime("%Y-%m-%d %H:%M:%S")
            })
        
        # 统计异常类型分布
        error_stats = db.session.query(
            SystemLog.log_level,
            db.func.count(SystemLog.id).label('count')
        ).filter(
            SystemLog.create_time >= start_date,
            SystemLog.log_level.in_([LogLevel.ERROR, LogLevel.CRITICAL, LogLevel.WARNING])
        ).group_by(SystemLog.log_level).all()
        
        stats = {stat.log_level.value: stat.count for stat in error_stats}
        
        return {
            "success": True,
            "abnormal_logs": abnormal_logs,
            "statistics": {
                "total": pagination.total,
                "error_count": stats.get("error", 0),
                "critical_count": stats.get("critical", 0),
                "warning_count": stats.get("warning", 0)
            },
            "pagination": {
                "total": pagination.total,
                "page": pagination.page,
                "per_page": pagination.per_page,
                "pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev
            }
        }
