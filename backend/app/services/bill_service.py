#计费业务（阶梯电价计算、账单生成）
from ..models import PricePolicy,Bill,BillDetail,User,Region,Meter
from app import db
from flask import session
from ..middleware import BusinessException,create_log, LogType, LogLevel
from datetime import datetime, timedelta
from sqlalchemy import and_, or_

class BillServices:
    @staticmethod
    def _find_region_policy(region_id, month_start, month_end):
        """
        递归查找片区的电价策略（包括上级片区）
        :param region_id: 片区ID
        :param month_start: 账单月份开始时间
        :param month_end: 账单月份结束时间
        :return: 符合条件的电价策略列表，如果没有则返回None
        """
        # 查询当前片区的电价策略
        policies = db.session.query(PricePolicy).filter(
            PricePolicy.region_id == region_id,
            PricePolicy.is_active == True,
            PricePolicy.start_time < month_end,
            or_(
                PricePolicy.end_time.is_(None),
                PricePolicy.end_time > month_start
            )
        ).order_by(PricePolicy.start_time).all()
        
        if policies:
            return policies
        
        # 如果当前片区没有策略，查找上级片区
        region = Region.query.get(region_id)
        if region and region.parent_id:
            # 递归查找上级片区的策略
            return BillServices._find_region_policy(region.parent_id, month_start, month_end)
        
        # 没有上级片区且当前片区没有策略
        return None
    
    @staticmethod
    def _find_region_policy(region_id, month_start, month_end):
        """
        递归查找片区的电价策略（包括上级片区）
        :param region_id: 片区ID
        :param month_start: 账单月份开始时间
        :param month_end: 账单月份结束时间
        :return: 符合条件的电价策略列表，如果没有则返回None
        """
        # 查询当前片区的电价策略
        policies = db.session.query(PricePolicy).filter(
            PricePolicy.region_id == region_id,
            PricePolicy.is_active == True,
            PricePolicy.start_time < month_end,
            or_(
                PricePolicy.end_time.is_(None),
                PricePolicy.end_time > month_start
            )
        ).order_by(PricePolicy.start_time).all()
        
        if policies:
            return policies
        
        # 如果当前片区没有策略，查找上级片区
        region = Region.query.get(region_id)
        if region and region.parent_id:
            # 递归查找上级片区的策略
            return BillServices._find_region_policy(region.parent_id, month_start, month_end)
        
        # 没有上级片区且当前片区没有策略
        return None
    
    @staticmethod
    def query_bills(user_id=None, meter_id=None, status=None, start_month=None, end_month=None, page=1, per_page=20, current_user_id=None, user_role="RESIDENT"):
        """
        查询账单列表（带分页）
        :param user_id: 用户ID（可选）
        :param meter_id: 电表ID（可选）
        :param status: 账单状态（可选）
        :param start_month: 开始月份（可选）
        :param end_month: 结束月份（可选）
        :param page: 页码
        :param per_page: 每页数量
        :param current_user_id: 当前用户ID
        :param user_role: 当前用户角色
        :return: 账单列表和分页信息
        """
        # 构建查询
        query = Bill.query
        
        # 权限过滤：普通用户只能查自己的账单
        if user_role == "RESIDENT":
            query = query.filter(Bill.user_id == current_user_id)
        elif user_id:
            query = query.filter(Bill.user_id == user_id)
        
        # 电表过滤
        if meter_id:
            query = query.filter(Bill.meter_id == meter_id)
        
        # 状态过滤
        if status:
            from ..models import BillStatus
            try:
                bill_status = BillStatus[status.upper()]
                query = query.filter(Bill.status == bill_status)
            except KeyError:
                pass
        
        # 时间范围过滤
        if start_month:
            try:
                start_date = datetime.strptime(start_month, "%Y-%m")
                query = query.filter(Bill.bill_month >= start_date)
            except ValueError:
                pass
        
        if end_month:
            try:
                end_date = datetime.strptime(end_month, "%Y-%m")
                query = query.filter(Bill.bill_month <= end_date)
            except ValueError:
                pass
        
        # 排序：最新的在前
        query = query.order_by(Bill.bill_month.desc())
        
        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # 构建返回数据
        bills = []
        for bill in pagination.items:
            meter = Meter.query.get(bill.meter_id)
            user = User.query.get(bill.user_id)
            
            bills.append({
                "id": bill.id,
                "bill_month": bill.bill_month.strftime("%Y-%m"),
                "meter_code": meter.meter_code if meter else "未知",
                "user_name": user.real_name if user and user.real_name else "未设置",
                "total_electricity": round(bill.total_electricity, 2),
                "total_amount": round(bill.total_amount, 2),
                "status": bill.status.name.upper(),  # 返回大写字符串如UNPAID、PAID
                "due_date": bill.due_date.strftime("%Y-%m-%d"),
                "create_time": bill.create_time.strftime("%Y-%m-%d %H:%M:%S")
            })
        
        return {
            "bills": bills,
            "pagination": {
                "total": pagination.total,
                "page": page,
                "per_page": per_page,
                "pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev
            }
        }
    
    @staticmethod
    def match_policy(bill_month, user_id):
        """
        匹配账单月份对应的价格政策（支持从上级片区继承）
        :param bill_month: 账单月份（datetime对象，通常是月初第一天）
        :param user_id: 用户ID
        :return: 与该月有重合的所有有效政策列表
        """
        user = db.session.query(User).get(user_id)
        if user is None:
            raise BusinessException("用户不存在", 404)
        
        region_id = user.region_id
        if not region_id:
            raise BusinessException("用户未分配片区", 400)
        
        # 计算账单月份的时间范围：从该月1日00:00:00到下月1日00:00:00
        if isinstance(bill_month, str):
            bill_month = datetime.strptime(bill_month, "%Y-%m-%d")
        
        # 确保bill_month是月初
        month_start = bill_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # 计算下个月的第一天
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1)
        
        # 递归查找该片区及其上级片区的电价策略
        policies = BillServices._find_region_policy(region_id, month_start, month_end)
        
        if not policies:
            # 查找用户所在片区的名称链（用于错误提示）
            region_chain = []
            current_region_id = region_id
            while current_region_id:
                region = Region.query.get(current_region_id)
                if region:
                    region_chain.append(region.region_name)
                    current_region_id = region.parent_id
                else:
                    break
            region_path = " -> ".join(reversed(region_chain))
            
            raise BusinessException(
                f"未找到{month_start.strftime('%Y年%m月')}符合条件的价格策略\n"
                f"片区路径：{region_path}\n"
                f"请联系管理员配置电价策略。", 
                404
            )
        
        # 返回政策列表及其有效期信息
        policy_list = []
        for policy in policies:
            # 计算该政策在这个月的实际有效时间段
            effective_start = max(policy.start_time, month_start)
            effective_end = min(policy.end_time if policy.end_time else month_end, month_end)
            
            # 获取策略所属的片区信息
            policy_region = Region.query.get(policy.region_id)
            is_inherited = policy.region_id != region_id  # 是否是从上级片区继承的
            
            policy_list.append({
                "policy_id": policy.id,
                "policy_name": policy.policy_name,
                "price_type": policy.price_type.name,
                "region_id": policy.region_id,
                "region_name": policy_region.region_name if policy_region else "未知片区",
                "is_inherited": is_inherited,  # 标记是否从上级片区继承
                "start_time": policy.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": policy.end_time.strftime("%Y-%m-%d %H:%M:%S") if policy.end_time else None,
                "effective_start": effective_start.strftime("%Y-%m-%d %H:%M:%S"),
                "effective_end": effective_end.strftime("%Y-%m-%d %H:%M:%S"),
                "effective_days": (effective_end - effective_start).days
            })
        
        # 获取用户片区信息
        user_region = Region.query.get(region_id)
        
        return {
            "bill_month": month_start.strftime("%Y-%m"),
            "month_start": month_start.strftime("%Y-%m-%d"),
            "month_end": month_end.strftime("%Y-%m-%d"),
            "user_region_id": region_id,
            "user_region_name": user_region.region_name if user_region else "未知片区",
            "policies": policy_list,
            "policy_count": len(policy_list),
            "has_inherited_policy": any(p["is_inherited"] for p in policy_list)
        }

    @staticmethod
    def create_bill(bill_month, meter_id):
        """
        创建月度账单
        :param bill_month: 账单月份（datetime对象，月初第一天）
        :param meter_id: 电表ID
        :return: 生成的账单信息
        """
        from ..models import IoTData, LadderPriceRules, TimeSharePriceRules, PriceType, LadderLevel, TimePeriod, BillStatus
        from flask import current_app
        
        # 1. 验证电表和用户
        meter = db.session.query(Meter).get(meter_id)
        if not meter:
            raise BusinessException("电表不存在", 404)
        
        if not meter.user_id:
            raise BusinessException("电表未绑定用户", 400)
        
        # 确保bill_month是月初
        if isinstance(bill_month, str):
            bill_month = datetime.strptime(bill_month, "%Y-%m-%d")
        month_start = bill_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # 计算月末
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1)
        
        # 检查是否已存在账单
        existing_bill = Bill.query.filter_by(
            meter_id=meter_id,
            bill_month=month_start
        ).first()
        if existing_bill:
            raise BusinessException(f"{month_start.strftime('%Y年%m月')}的账单已存在", 400)
        
        # 2. 获取该月的所有价格政策（已按时间排序）
        policy_result = BillServices.match_policy(month_start, meter.user_id)
        policies_info = policy_result["policies"]
        
        if not policies_info:
            raise BusinessException("未找到有效的价格政策", 404)
        
        # 3. 查询该月的所有IoT数据
        iot_data_list = IoTData.query.filter(
            IoTData.meter_id == meter_id,
            IoTData.collect_time >= month_start,
            IoTData.collect_time < month_end
        ).order_by(IoTData.collect_time).all()
        
        if len(iot_data_list) < 2:
            raise BusinessException("该月用电数据不足，无法生成账单", 400)
        
        # 4. 计算总用电量
        total_electricity = iot_data_list[-1].electricity - iot_data_list[0].electricity
        
        # 5. 准备存储账单详情
        bill_details_data = []
        total_amount = 0.0
        
        # 当月累计用电量（用于阶梯判断）
        accumulated_electricity = 0.0
        
        # 6. 按时间顺序处理每条IoT数据，毕竟不能确保是连续的，因此只能一条一条处理
        for i in range(len(iot_data_list) - 1):
            current_iot = iot_data_list[i]
            next_iot = iot_data_list[i + 1]
            
            # 计算这个时段的用电量
            period_electricity = next_iot.electricity - current_iot.electricity
            if period_electricity <= 0:
                continue
            
            # 更新累计用电量
            accumulated_electricity += period_electricity
            
            # 确定该时段使用的政策
            current_time = current_iot.collect_time
            applicable_policy = None
            
            for policy_info in policies_info:
                policy_start = datetime.strptime(policy_info["effective_start"], "%Y-%m-%d %H:%M:%S")
                policy_end = datetime.strptime(policy_info["effective_end"], "%Y-%m-%d %H:%M:%S")
                
                if policy_start <= current_time < policy_end:
                    applicable_policy = PricePolicy.query.get(policy_info["policy_id"])
                    break
            
            if not applicable_policy:
                # 记录日志但不阻塞计费流程
                continue
            
            # 7. 根据政策类型计算单价
            base_price = applicable_policy.base_unit_price
            time_ratio = 1.0
            ladder_ratio = 1.0
            time_period = None
            ladder_level = None
            
            # 获取时段比率（分时电价）
            if applicable_policy.price_type in [PriceType.time_share, PriceType.combined]:
                time_rules = TimeSharePriceRules.query.filter_by(policy_id=applicable_policy.id).all()
                current_hour = current_time.hour
                
                for rule in time_rules:
                    if rule.start_hour <= current_hour < rule.end_hour:
                        time_ratio = rule.ratio
                        time_period = rule.time_period
                        break
            
            # 获取阶梯比率（阶梯电价，基于月累计用电量）
            if applicable_policy.price_type in [PriceType.ladder, PriceType.combined]:
                ladder_rules = LadderPriceRules.query.filter_by(
                    policy_id=applicable_policy.id
                ).order_by(LadderPriceRules.min_electricity).all()
                
                for rule in ladder_rules:
                    if rule.min_electricity <= accumulated_electricity:
                        if rule.max_electricity is None or accumulated_electricity < rule.max_electricity:
                            ladder_ratio = rule.ratio
                            ladder_level = rule.ladder_level
                            break
            
            # 计算该时段的单价和金额
            unit_price = base_price * time_ratio * ladder_ratio
            amount = period_electricity * unit_price
            
            # 8. 创建账单详情数据
            detail_key = (applicable_policy.price_type, time_period, ladder_level, unit_price)
            
            # 查找是否已有相同类型的详情（合并同类项）
            existing_detail = None
            for detail in bill_details_data:
                if (detail["policy_id"] == applicable_policy.id and
                    detail["detail_type"] == applicable_policy.price_type and
                    detail["time_period"] == time_period and
                    detail["ladder_level"] == ladder_level and
                    abs(detail["unit_price"] - unit_price) < 0.0001):
                    existing_detail = detail
                    break
            
            if existing_detail:
                # 合并到已有详情
                existing_detail["electricity"] += period_electricity
                existing_detail["amount"] += amount
            else:
                # 创建新的详情
                bill_details_data.append({
                    "policy_id": applicable_policy.id,
                    "detail_type": applicable_policy.price_type,
                    "time_period": time_period,
                    "ladder_level": ladder_level,
                    "electricity": period_electricity,
                    "unit_price": unit_price,
                    "amount": amount
                })
            
            total_amount += amount
        
        # 9. 创建账单
        due_date = month_end + timedelta(days=15)  # 账单到期日为次月15日
        
        new_bill = Bill(
            user_id=meter.user_id,
            meter_id=meter_id,
            bill_month=month_start,
            total_amount=round(total_amount, 2),
            total_electricity=round(total_electricity, 2),
            policy_id=policies_info[0]["policy_id"],  # 主要政策ID
            status=BillStatus.unpaid,
            due_date=due_date
        )
        
        db.session.add(new_bill)
        db.session.flush()  # 获取bill_id
        
        # 10. 创建账单详情
        for detail_data in bill_details_data:
            bill_detail = BillDetail(
                bill_id=new_bill.id,
                detail_type=detail_data["detail_type"],
                ladder_level=detail_data["ladder_level"],
                time_period=detail_data["time_period"],
                electricity=round(detail_data["electricity"], 2),
                unit_price=round(detail_data["unit_price"], 4),
                amount=round(detail_data["amount"], 2)
            )
            db.session.add(bill_detail)
        
        try:
            db.session.commit()
            create_log(
                operator_id=None,
                operator_name="系统",
                log_type=LogType.CREATE,
                module="账单管理",
                action=f"账单创建成功：电表{meter_id}，月份{month_start.strftime('%Y-%m')}",
                log_level=LogLevel.INFO
            )
        except Exception as e:
            db.session.rollback()
            create_log(
                operator_id=None,
                operator_name="系统",
                log_type=LogType.ERROR,
                module="账单管理",
                action=f"账单创建失败：电表{meter_id}",
                error_message=str(e),
                log_level=LogLevel.ERROR
            )
            raise BusinessException("账单创建失败", 500)
        
        # 11. 返回账单信息
        return {
            "success": True,
            "bill_info": {
                "bill_id": new_bill.id,
                "meter_id": meter_id,
                "meter_code": meter.meter_code,
                "user_id": meter.user_id,
                "bill_month": month_start.strftime("%Y-%m"),
                "total_electricity": new_bill.total_electricity,
                "total_amount": new_bill.total_amount,
                "status": new_bill.status.name,
                "due_date": new_bill.due_date.strftime("%Y-%m-%d"),
                "details_count": len(bill_details_data)
            },
            "bill_details": [
                {
                    "detail_type": detail["detail_type"].name,
                    "time_period": detail["time_period"].name if detail["time_period"] else None,
                    "ladder_level": detail["ladder_level"].name if detail["ladder_level"] else None,
                    "electricity": detail["electricity"],
                    "unit_price": detail["unit_price"],
                    "amount": detail["amount"]
                }
                for detail in bill_details_data
            ]
        }
    
    @staticmethod
    def pay_bill(bill_id, user_id, payment_amount, payment_method="online"):
        """
        支付账单
        :param bill_id: 账单ID
        :param user_id: 支付用户ID
        :param payment_amount: 支付金额
        :param payment_method: 支付方式
        :return: 支付结果
        """
        from ..models import BillStatus
        from flask import current_app
        
        # 1. 查询账单
        bill = Bill.query.get(bill_id)
        if not bill:
            raise BusinessException("账单不存在", 404)
        
        # 2. 不验证用户权限
        
        # 3. 校验账单状态（防止重复支付）
        if bill.status == BillStatus.paid:
            raise BusinessException("该账单已支付，请勿重复支付", 400)
        
        # 4. 校验支付金额
        if abs(payment_amount - bill.total_amount) > 0.01:
            raise BusinessException(f"支付金额不正确，应付{bill.total_amount}元", 400)
        
        # 5. 更新账单状态
        old_status = bill.status
        bill.status = BillStatus.paid
        bill.payment_time = datetime.now()
        bill.payment_method = payment_method
        
        try:
            db.session.commit()
            create_log(
                operator_id=user_id,
                operator_name=user.real_name or user.mail,
                log_type=LogType.PAYMENT,
                module="账单管理",
                action=f"账单{bill_id}支付成功，金额{payment_amount}元",
                log_level=LogLevel.INFO
            )
        except Exception as e:
            db.session.rollback()
            create_log(
                operator_id=user_id,
                operator_name=user.real_name or user.mail,
                log_type=LogType.ERROR,
                module="账单管理",
                action=f"账单{bill_id}支付失败",
                error_message=str(e),
                log_level=LogLevel.ERROR
            )
            raise BusinessException("支付失败，请重试", 500)
        
        # 6. 如果是从逾期状态支付，发送通知
        if old_status == BillStatus.overdue:
            try:
                from services.notify_sevice import NotifyServices
                from ..models.notice import NoticeType, SendChannel
                
                user = User.query.get(user_id)
                if user:
                    NotifyServices.create_notification(
                        notice_type=NoticeType.ARREARS,
                        targets=[user],
                        title="逾期账单已支付",
                        content=f"您的{bill.bill_month.strftime('%Y年%m月')}账单已支付成功，感谢您的配合！",
                        send_channel=SendChannel.INNER,
                        send_time=datetime.now(),
                        is_batch=False,
                        related_id=bill_id
                    )
            except Exception as e:
                create_log(
                    operator_id=user_id,
                    operator_name=user.real_name or user.mail,
                    log_type=LogType.ERROR,
                    module="账单管理",
                    action=f"发送支付通知失败：账单{bill_id}",
                    error_message=str(e),
                    log_level=LogLevel.ERROR
                )
        
        return {
            "success": True,
            "message": "支付成功",
            "payment_info": {
                "bill_id": bill_id,
                "bill_month": bill.bill_month.strftime("%Y-%m"),
                "amount": bill.total_amount,
                "payment_time": bill.payment_time.strftime("%Y-%m-%d %H:%M:%S"),
                "payment_method": payment_method,
                "previous_status": old_status.name,
                "current_status": bill.status.name
            }
        }
    
    @staticmethod
    def get_bill_detail(bill_id, user_id):
        """
        获取账单详情
        :param bill_id: 账单ID
        :param user_id: 当前用户ID
        :return: 账单详情
        """
        from ..models import BillStatus
        
        # 1. 查询账单
        bill = Bill.query.get(bill_id)
        if not bill:
            raise BusinessException("账单不存在", 404)
        
        # 2. 权限验证：普通用户只能查自己的账单
        # 管理员可以查所有账单（这里简化处理，如需要可以加上role验证）
        
        # 3. 查询电表和用户信息
        meter = Meter.query.get(bill.meter_id)
        user = User.query.get(bill.user_id)
        
        # 4. 查询账单详情
        bill_details = BillDetail.query.filter_by(bill_id=bill_id).all()
        
        # 5. 构建返回数据
        return {
            "bill_id": bill.id,
            "meter_id": bill.meter_id,
            "meter_code": meter.meter_code if meter else "未知",
            "bill_no": f"BILL-{bill.id:06d}",  # 生成账单编号
            "bill_month": bill.bill_month.strftime("%Y-%m"),
            "user_name": user.real_name if user and user.real_name else "未设置",
            "total_usage": round(bill.total_electricity, 2),
            "bill_amount": round(bill.total_amount, 2),
            "status": bill.status.name.upper(),  # 返回大写字符串如UNPAID、PAID
            "generate_time": bill.create_time.strftime("%Y-%m-%d %H:%M:%S") if bill.create_time else None,
            "due_date": bill.due_date.strftime("%Y-%m-%d"),
            "payment_time": None,  # Bill模型中没有payment_time字段
            "details": [
                {
                    "detail_type": detail.detail_type.name,
                    "time_period": detail.time_period.name if detail.time_period else None,
                    "ladder_level": detail.ladder_level.name if detail.ladder_level else None,
                    "electricity": round(detail.electricity, 2),
                    "unit_price": round(detail.unit_price, 4),
                    "amount": round(detail.amount, 2)
                }
                for detail in bill_details
            ]
        }
    
    @staticmethod
    def refund_bill(bill_id, admin_id, refund_reason):
        """
        退款（仅管理员操作）
        :param bill_id: 账单ID
        :param admin_id: 管理员ID
        :param refund_reason: 退款原因
        :return: 退款结果
        """
        from ..models import BillStatus
        from flask import current_app
        
        # 1. 查询账单
        bill = Bill.query.get(bill_id)
        if not bill:
            raise BusinessException("账单不存在", 404)
        
        # 2. 校验账单状态（只有已支付的账单才能退款）
        if bill.status != BillStatus.paid:
            raise BusinessException("只有已支付的账单才能退款", 400)
        
        # 3. 更新账单状态
        bill.status = BillStatus.unpaid
        bill.refund_time = datetime.now()
        bill.refund_reason = refund_reason
        bill.refund_admin_id = admin_id
        bill.payment_time = None
        
        try:
            db.session.commit()
            create_log(
                operator_id=admin_id,
                operator_name="管理员",
                log_type=LogType.REFUND,
                module="账单管理",
                action=f"账单{bill_id}退款成功，原因：{refund_reason}",
                log_level=LogLevel.INFO
            )
        except Exception as e:
            db.session.rollback()
            create_log(
                operator_id=admin_id,
                operator_name="管理员",
                log_type=LogType.ERROR,
                module="账单管理",
                action=f"账单{bill_id}退款失败",
                error_message=str(e),
                log_level=LogLevel.ERROR
            )
            raise BusinessException("退款失败，请重试", 500)
        
        # 4. 发送退款通知
        try:
            from services.notify_sevice import NotifyServices
            from ..models.notice import NoticeType, SendChannel
            
            user = User.query.get(bill.user_id)
            if user:
                NotifyServices.create_notification(
                    notice_type=NoticeType.ARREARS,
                    targets=[user],
                    title="账单已退款",
                    content=f"您的{bill.bill_month.strftime('%Y年%m月')}账单已退款，原因：{refund_reason}",
                    send_channel=SendChannel.INNER,
                    send_time=datetime.now(),
                    is_batch=False,
                    related_id=bill_id
                )
        except Exception as e:
            create_log(
                operator_id=admin_id,
                operator_name="管理员",
                log_type=LogType.ERROR,
                module="账单管理",
                action=f"发送退款通知失败：账单{bill_id}",
                error_message=str(e),
                log_level=LogLevel.ERROR
            )
        
        return {
            "success": True,
            "message": "退款成功",
            "refund_info": {
                "bill_id": bill_id,
                "bill_month": bill.bill_month.strftime("%Y-%m"),
                "amount": bill.total_amount,
                "refund_time": bill.refund_time.strftime("%Y-%m-%d %H:%M:%S"),
                "refund_reason": refund_reason,
                "status": bill.status.name
            }
        }
    
    @staticmethod
    def update_overdue_bills():
        """
        更新逾期账单状态（定时任务调用）
        :return: 更新结果统计
        """
        from ..models import BillStatus
        from flask import current_app
        
        # 查询所有未付且已过期的账单
        current_time = datetime.now()
        overdue_bills = Bill.query.filter(
            Bill.status == BillStatus.unpaid,
            Bill.due_date < current_time
        ).all()
        
        updated_count = 0
        notification_count = 0
        
        for bill in overdue_bills:
            # 更新状态为逾期
            bill.status = BillStatus.overdue
            bill.overdue_time = current_time
            updated_count += 1
            
            # 发送欠费提醒
            try:
                user = User.query.get(bill.user_id)
                if user:
                    from services.notify_sevice import NotifyServices
                    from ..models.notice import NoticeType, SendChannel
                    
                    overdue_days = (current_time - bill.due_date).days
                    
                    NotifyServices.create_notification(
                        notice_type=NoticeType.OVERDUE,
                        targets=[user],
                        title=f"账单逾期提醒 - {bill.bill_month.strftime('%Y年%m月')}",
                        content=f"您的{bill.bill_month.strftime('%Y年%m月')}电费账单已逾期{overdue_days}天，"
                               f"应付金额：{bill.total_amount}元，请尽快支付，避免影响用电。",
                        send_channel=SendChannel.INNER,
                        send_time=current_time,
                        is_batch=False,
                        related_id=bill.id
                    )
                    notification_count += 1
            except Exception as e:
                create_log(
                    operator_id=None,
                    operator_name="系统",
                    log_type=LogType.ERROR,
                    module="账单管理",
                    action=f"发送逾期通知失败：账单{bill.id}",
                    error_message=str(e),
                    log_level=LogLevel.ERROR
                )
        
        try:
            db.session.commit()
            create_log(
                operator_id=None,
                operator_name="系统",
                log_type=LogType.UPDATE,
                module="账单管理",
                action=f"逾期账单状态更新完成：更新{updated_count}条，发送通知{notification_count}条",
                log_level=LogLevel.INFO
            )
        except Exception as e:
            db.session.rollback()
            create_log(
                operator_id=None,
                operator_name="系统",
                log_type=LogType.ERROR,
                module="账单管理",
                action=f"逾期账单状态更新失败",
                error_message=str(e),
                log_level=LogLevel.ERROR
            )
            raise BusinessException("逾期账单更新失败", 500)
        
        return {
            "success": True,
            "updated_count": updated_count,
            "notification_count": notification_count,
            "message": f"已更新{updated_count}条逾期账单，发送{notification_count}条通知"
        }
    
    @staticmethod
    def send_arrears_reminder(user_id=None, region_id=None):
        """
        发送欠费催收提醒
        :param user_id: 指定用户ID（可选）
        :param region_id: 指定片区ID（可选）
        :return: 发送结果
        """
        from ..models import BillStatus
        from flask import current_app
        
        # 构建查询
        query = Bill.query.filter(Bill.status.in_([BillStatus.unpaid, BillStatus.overdue]))
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        elif region_id:
            # 查询该片区所有用户的欠费账单
            users_in_region = User.query.filter_by(region_id=region_id).all()
            user_ids = [u.id for u in users_in_region]
            query = query.filter(Bill.user_id.in_(user_ids))
        
        overdue_bills = query.all()
        
        if not overdue_bills:
            return {
                "success": True,
                "message": "没有欠费账单需要催收",
                "sent_count": 0
            }
        
        # 按用户分组
        user_bills = {}
        for bill in overdue_bills:
            if bill.user_id not in user_bills:
                user_bills[bill.user_id] = []
            user_bills[bill.user_id].append(bill)
        
        sent_count = 0
        current_time = datetime.now()
        
        for user_id, bills in user_bills.items():
            user = User.query.get(user_id)
            if not user:
                continue
            
            # 计算总欠费金额
            total_arrears = sum(bill.total_amount for bill in bills)
            
            # 构建账单列表
            bill_list = "\n".join([
                f"- {bill.bill_month.strftime('%Y年%m月')}：{bill.total_amount}元（{bill.status.name}）"
                for bill in bills
            ])
            
            try:
                from services.notify_sevice import NotifyServices
                from ..models.notice import NoticeType, SendChannel
                
                NotifyServices.create_notification(
                    notice_type=NoticeType.ARREARS,
                    targets=[user],
                    title="电费欠费催收提醒",
                    content=f"尊敬的用户，您有{len(bills)}笔电费账单未支付，"
                           f"总计欠费：{total_arrears:.2f}元。\n\n账单明细：\n{bill_list}\n\n"
                           f"请尽快支付，避免影响正常用电。",
                    send_channel=SendChannel.INNER,
                    send_time=current_time,
                    is_batch=False
                )
                sent_count += 1
            except Exception as e:
                create_log(
                    operator_id=None,
                    operator_name="系统",
                    log_type=LogType.ERROR,
                    module="账单管理",
                    action=f"发送催收通知失败：用户{user_id}",
                    error_message=str(e),
                    log_level=LogLevel.ERROR
                )
        
        return {
            "success": True,
            "message": f"已发送{sent_count}条欠费催收提醒",
            "sent_count": sent_count,
            "total_users": len(user_bills),
            "total_bills": len(overdue_bills)
        }
    
    @staticmethod
    def check_power_cutoff_warning():
        """
        检查断电预警（欠费超7天）
        :return: 预警结果
        """
        from ..models import BillStatus
        from flask import current_app
        
        current_time = datetime.now()
        cutoff_threshold = current_time - timedelta(days=7)
        
        # 查询逾期超过7天的账单
        critical_bills = Bill.query.filter(
            Bill.status == BillStatus.overdue,
            Bill.due_date < cutoff_threshold
        ).all()
        
        if not critical_bills:
            return {
                "success": True,
                "message": "没有需要断电预警的账单",
                "warning_count": 0
            }
        
        # 按片区分组
        region_bills = {}
        for bill in critical_bills:
            meter = Meter.query.get(bill.meter_id)
            if meter and meter.region_id:
                if meter.region_id not in region_bills:
                    region_bills[meter.region_id] = []
                region_bills[meter.region_id].append({
                    "bill": bill,
                    "meter": meter,
                    "overdue_days": (current_time - bill.due_date).days
                })
        
        warning_count = 0
        
        # 通知片区管理员
        for region_id, bill_info_list in region_bills.items():
            region = Region.query.get(region_id)
            if not region or not region.manager_id:
                continue
            
            manager = User.query.get(region.manager_id)
            if not manager:
                continue
            
            # 构建预警列表
            warning_list = "\n".join([
                f"- 电表{info['meter'].meter_code}：欠费{info['bill'].total_amount}元，"
                f"逾期{info['overdue_days']}天（账单月份：{info['bill'].bill_month.strftime('%Y-%m')}）"
                for info in bill_info_list
            ])
            
            try:
                from services.notify_sevice import NotifyServices
                from ..models.notice import NoticeType, SendChannel
                
                NotifyServices.create_notification(
                    notice_type=NoticeType.OVERDUE,
                    targets=[manager],
                    title=f"断电预警 - {region.region_name}片区",
                    content=f"以下电表欠费超过7天，需要采取断电措施：\n\n{warning_list}\n\n"
                           f"共计{len(bill_info_list)}个电表需要处理，请及时跟进。",
                    send_channel=SendChannel.INNER,
                    send_time=current_time,
                    is_batch=False
                )
                warning_count += 1
            except Exception as e:
                create_log(
                    operator_id=None,
                    operator_name="系统",
                    log_type=LogType.ERROR,
                    module="账单管理",
                    action=f"发送断电预警失败：片区{region_id}",
                    error_message=str(e),
                    log_level=LogLevel.ERROR
                )
        
        # 同时通知用户（最后警告）
        for bill in critical_bills:
            user = User.query.get(bill.user_id)
            if not user:
                continue
            
            overdue_days = (current_time - bill.due_date).days
            
            try:
                from services.notify_sevice import NotifyServices
                from ..models.notice import NoticeType, SendChannel
                
                NotifyServices.create_notification(
                    notice_type=NoticeType.OVERDUE,
                    targets=[user],
                    title="【紧急】断电警告",
                    content=f"您的{bill.bill_month.strftime('%Y年%m月')}电费已逾期{overdue_days}天，"
                           f"欠费金额：{bill.total_amount}元。\n\n"
                           f"警告：如不及时支付，将采取停电措施，请立即缴费！",
                    send_channel=SendChannel.INNER,
                    send_time=current_time,
                    is_batch=False,
                    related_id=bill.id
                )
            except Exception as e:
                create_log(
                    operator_id=None,
                    operator_name="系统",
                    log_type=LogType.ERROR,
                    module="账单管理",
                    action=f"发送断电警告失败：账单{bill.id}",
                    error_message=str(e),
                    log_level=LogLevel.ERROR
                )
        
        return {
            "success": True,
            "message": f"已发送{warning_count}条断电预警给片区管理员",
            "warning_count": warning_count,
            "critical_bills_count": len(critical_bills),
            "affected_regions": len(region_bills)
        }
