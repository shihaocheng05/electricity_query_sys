from flask import session,current_app
from app import db
from ..models import NoticeStatus,Notifications,NoticeType,User,Meter,PricePolicy,Bill,RoleEnum,SendChannel
from ..middleware import BusinessException,create_log, LogType, LogLevel
from ..utils import send_mail
from flask_mail import Mail
from datetime import datetime
import uuid

class NotifyServices:
    @staticmethod
    #同时支持创建单发通知以及群发通知的功能，将制造群发通知的功能理解为批量制造单发通知的功能
    def create_notification(notice_type:NoticeType,target_type:RoleEnum,targets:list,title,content,send_channel,send_time,is_batch:bool,related_id=None)->dict:
        """
        创建通知：
        :param notice_type: 说明
        :type notice_type: NoticeType
        :param targets: 说明
        :type targets: list
        :param title: 说明
        :param content: 说明
        :param send_channel: 说明
        :param send_time: 说明
        :param is_batch: 说明
        :type is_batch: bool
        :param related_id: 说明
        :return: 说明
        :rtype: dict
        """
        # 如果是群发，生成唯一的batch_id
        batch_id = str(uuid.uuid4())[:20] if is_batch else None         #重复率极低，应该不会重复吧
        
        if related_id is not None:
            if notice_type==NoticeType.REPAIR:      #有些通知是全体居民广播，有些不是
                target_type=RoleEnum.AREA_ADMIN
                meter=Meter.query.get(related_id)
                if meter==None:
                    raise BusinessException("要维修的电表不存在")
            elif notice_type==NoticeType.ARREARS:
                target_type=RoleEnum.RESIDENT       #发送通知给目标用户
                user=User.query.get(related_id)
                if user==None:
                    raise BusinessException("欠费用户不存在")
            elif notice_type==NoticeType.PRICE_CHANGE:
                target_type=RoleEnum.RESIDENT       #发送通知给全体用户
                policy=PricePolicy.query.get(related_id)
                if policy==None:
                    raise BusinessException("变更的政策不存在")
            elif notice_type==NoticeType.OVERDUE:
                target_type=RoleEnum.RESIDENT       #发送通知给目标用户
                bill=PricePolicy.query.get(related_id)
                if bill==None:
                    raise BusinessException("逾期账单不存在")
        
        for target in targets:
            new_notification=Notifications(
                notify_type=notice_type,
                target_type=target_type,
                target_id=target.id,
                related_id=related_id,
                title=title,
                content=content,
                send_channel=send_channel,
                send_time=send_time,
                is_batch=is_batch,
                batch_id=batch_id
            )
    
            db.session.add(new_notification)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            create_log(
                operator_id=None,
                operator_name="系统",
                log_type=LogType.ERROR,
                module="通知管理",
                action=f"通知创建失败：{str(e)}",
                error_message=str(e),
                log_level=LogLevel.ERROR
            )
            raise BusinessException("通知创建失败",500)

        return {
            "success":True,
            "notification_info":{
                "id":new_notification.id,
                "notify_type":new_notification.notify_type,
                "target_type":new_notification.target_type,
                "related_id":new_notification.related_id,
                "title":new_notification.title,
                "content":new_notification.content,
                "send_channel":new_notification.send_channel,
                "send_time":new_notification.send_time,
                "is_batch":is_batch,
                "batch_id":batch_id
            }
        }
    
    @staticmethod
    def send_notification(mail:Mail=None,notification_id=None,batch_id=None):
        """发送通知：支持单发(notification_id)和群发(batch_id)，同时支持邮件和站内消息"""
        if notification_id is None and batch_id is None:
            raise BusinessException("必须提供notification_id或batch_id",400)
        
        if notification_id and batch_id:
            raise BusinessException("不能同时提供notification_id和batch_id",400)
        
        # 获取要发送的通知列表（如果单发就只有一条消息，群发就一个消息列表）
        notifications = []
        if notification_id:
            # 单发模式
            notification = Notifications.query.get(notification_id)
            if notification is None:
                raise BusinessException("未找到该通知",404)
            notifications = [notification]
        else:
            # 群发模式
            notifications = Notifications.query.filter_by(batch_id=batch_id).all()
            if not notifications:
                raise BusinessException("未找到该批次的通知",404)
        
        # 发送通知
        success_count = 0
        failed_count = 0
        
        for notification in notifications:
            try:
                # 确定邮件主题（邮件和站内信都可能需要）
                subject = "系统通知"
                if notification.notify_type == NoticeType.REPAIR:
                    subject = "维修通知"
                elif notification.notify_type == NoticeType.ARREARS:
                    subject = "欠费通知"
                elif notification.notify_type == NoticeType.PRICE_CHANGE:
                    subject = "价格策略变更通知"
                elif notification.notify_type == NoticeType.OVERDUE:
                    subject = "欠费逾期通知"
                
                # 获取目标用户
                target_user = User.query.get(notification.target_id)
                if not target_user:
                    create_log(
                        operator_id=None,
                        operator_name="系统",
                        log_type=LogType.ERROR,
                        module="通知管理",
                        action=f"通知{notification.id}的目标用户不存在",
                        log_level=LogLevel.ERROR
                    )
                    notification.status = NoticeStatus.FAILED
                    failed_count += 1
                    continue
                
                # 根据发送渠道处理
                if notification.send_channel == SendChannel.MAIL:
                    # 邮件发送
                    if target_user.email:
                        send_mail(
                            mail,
                            subject=subject,
                            recipients=[target_user.email],
                            cc=[],
                            bcc=[],
                            body=notification.content
                        )
                        notification.status = NoticeStatus.SENT
                        notification.send_time = datetime.now()
                        success_count += 1
                    else:
                        create_log(
                            operator_id=None,
                            operator_name="系统",
                            log_type=LogType.ERROR,
                            module="通知管理",
                            action=f"用户{target_user.id}没有邮箱地址",
                            log_level=LogLevel.WARNING
                        )
                        notification.status = NoticeStatus.FAILED
                        failed_count += 1
                        
                elif notification.send_channel == SendChannel.INNER:
                    # 站内信：直接标记为已发送（数据已在create_notification中创建）
                    notification.status = NoticeStatus.SENT
                    notification.send_time = datetime.now()
                    success_count += 1
                    
            except Exception as e:
                create_log(
                    operator_id=None,
                    operator_name="系统",
                    log_type=LogType.ERROR,
                    module="通知管理",
                    action=f"通知{notification.id}发送失败",
                    error_message=str(e),
                    log_level=LogLevel.ERROR
                )
                notification.status = NoticeStatus.FAILED
                failed_count += 1
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            create_log(
                operator_id=None,
                operator_name="系统",
                log_type=LogType.ERROR,
                module="通知管理",
                action=f"通知状态更新失败",
                error_message=str(e),
                log_level=LogLevel.ERROR
            )
            raise BusinessException("通知状态更新失败",500)
        
        return {
            "success": True,
            "total": len(notifications),
            "success_count": success_count,
            "failed_count": failed_count,
            "message": f"成功发送{success_count}条，失败{failed_count}条"
        }

    @staticmethod
    def query_notification(user_id=None, notify_type=None, status=None, is_unread_only=False, page=1, per_page=20):
        """
        查询通知
        :param user_id: 用户ID，查询该用户的站内信通知，如果是管理员的话随便查，如果是用户本人的话就锁定自己（user_id一开始就设定为查询用户）了，
        提供多种筛选逻辑，实现分页查询功能
        :param notify_type: 通知类型筛选
        :param status: 通知状态筛选
        :param is_unread_only: 是否只查询未读通知
        :param page: 页码
        :param per_page: 每页数量
        :return: 通知列表和分页信息
        """
        query = Notifications.query.filter_by(send_channel=SendChannel.INNER)       
        
        # 按用户ID筛选
        if user_id:
            query = query.filter_by(target_id=user_id)
        
        # 按通知类型筛选
        if notify_type:
            query = query.filter_by(notify_type=notify_type)
        
        # 按状态筛选
        if status:
            query = query.filter_by(status=status)
        
        # 只查询未读通知（状态为PENDING或SENT，且没有read_time）
        if is_unread_only:
            query = query.filter(
                Notifications.status.in_([NoticeStatus.PENDING, NoticeStatus.SENT]),
                Notifications.read_time.is_(None)
            )
        
        # 按创建时间倒序排列
        query = query.order_by(Notifications.create_time.desc())
        
        # 分页查询
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        notifications_list = []
        for notification in pagination.items:
            notifications_list.append({
                "id": notification.id,
                "notify_type": notification.notify_type.name,
                "target_type": notification.target_type.name,
                "target_id": notification.target_id,
                "related_id": notification.related_id,
                "title": notification.title,
                "content": notification.content,
                "status": notification.status.name,
                "send_channel": notification.send_channel.name,
                "create_time": notification.create_time.strftime("%Y-%m-%d %H:%M:%S") if notification.create_time else None,
                "send_time": notification.send_time.strftime("%Y-%m-%d %H:%M:%S") if notification.send_time else None,
                "read_time": notification.read_time.strftime("%Y-%m-%d %H:%M:%S") if notification.read_time else None,
                "is_batch": notification.is_batch,
                "batch_id": notification.batch_id
            })
        
        return {
            "success": True,
            "notifications": notifications_list,
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
    def get_notification_statistics(notify_type=None, start_date=None, end_date=None):
        """
        统计通知发送成功率，提供多种筛选逻辑
        :param notify_type: 通知类型，不传则统计所有类型
        :param start_date: 开始日期
        :param end_date: 结束日期
        :return: 统计数据
        """
        query = Notifications.query
        
        # 按通知类型筛选
        if notify_type:
            query = query.filter_by(notify_type=notify_type)
        
        # 按日期范围筛选
        if start_date:
            query = query.filter(Notifications.create_time >= start_date)
        if end_date:
            query = query.filter(Notifications.create_time <= end_date)
        
        # 统计各状态数量
        total_count = query.count()
        sent_count = query.filter_by(status=NoticeStatus.SENT).count()
        failed_count = query.filter_by(status=NoticeStatus.FAILED).count()
        pending_count = query.filter_by(status=NoticeStatus.PENDING).count()
        read_count = query.filter_by(status=NoticeStatus.READ).count()
        
        # 计算成功率
        success_rate = (sent_count + read_count) / total_count * 100 if total_count > 0 else 0
        failure_rate = failed_count / total_count * 100 if total_count > 0 else 0
        
        # 按通知类型分组统计
        type_statistics = {}
        for ntype in NoticeType:
            type_query = query.filter_by(notify_type=ntype)
            type_total = type_query.count()
            if type_total > 0:
                type_sent = type_query.filter_by(status=NoticeStatus.SENT).count()
                type_failed = type_query.filter_by(status=NoticeStatus.FAILED).count()
                type_read = type_query.filter_by(status=NoticeStatus.READ).count()
                
                type_statistics[ntype.name] = {
                    "total": type_total,
                    "sent": type_sent,
                    "failed": type_failed,
                    "read": type_read,
                    "success_rate": (type_sent + type_read) / type_total * 100,
                    "failure_rate": type_failed / type_total * 100
                }
        
        return {
            "success": True,
            "overall_statistics": {
                "total_count": total_count,
                "sent_count": sent_count,
                "failed_count": failed_count,
                "pending_count": pending_count,
                "read_count": read_count,
                "success_rate": round(success_rate, 2),
                "failure_rate": round(failure_rate, 2)
            },
            "type_statistics": type_statistics
        }

    @staticmethod
    def update_notification_status(notification_id, action, user_id=None):
        """
        更新通知状态
        :param notification_id: 通知ID
        :param action: 操作类型 'mark_read'(标记已读) 或 'retry'(重试发送)
        :param user_id: 直接传入当前用户ID，用于验证权限
        :return: 操作结果
        """
        notification = Notifications.query.get(notification_id)
        if not notification:
            raise BusinessException("未找到该通知", 404)
        
        # 验证用户权限（用户只能操作自己的通知）
        if user_id and notification.target_id != user_id:
            raise BusinessException("无权操作此通知", 403)
        
        if action == "mark_read":
            # 标记为已读（仅站内信支持）
            if notification.send_channel != SendChannel.INNER:
                raise BusinessException("只有站内信支持标记已读", 400)
            
            if notification.status == NoticeStatus.READ:
                return {
                    "success": True,
                    "message": "通知已经是已读状态"
                }
            
            notification.status = NoticeStatus.READ
            notification.read_time = datetime.now()
            
            try:
                db.session.commit()
                create_log(
                    operator_id=None,
                    operator_name="系统",
                    log_type=LogType.UPDATE,
                    module="通知管理",
                    action=f"通知{notification_id}已标记为已读",
                    log_level=LogLevel.INFO
                )
            except Exception as e:
                db.session.rollback()
                create_log(
                    operator_id=None,
                    operator_name="系统",
                    log_type=LogType.ERROR,
                    module="通知管理",
                    action=f"标记已读失败",
                    error_message=str(e),
                    log_level=LogLevel.ERROR
                )
                raise BusinessException("标记已读失败", 500)
            
            return {
                "success": True,
                "message": "已标记为已读",
                "notification": {
                    "id": notification.id,
                    "status": notification.status.name,
                    "read_time": notification.read_time.strftime("%Y-%m-%d %H:%M:%S")
                }
            }
        
        elif action == "retry":
            # 重试发送（仅失败的通知支持）
            if notification.status != NoticeStatus.FAILED:
                raise BusinessException("只有发送失败的通知才能重试", 400)
            
            # 重置状态为待发送
            notification.status = NoticeStatus.PENDING
            notification.send_time = None
            
            try:
                db.session.commit()
                create_log(
                    operator_id=None,
                    operator_name="系统",
                    log_type=LogType.UPDATE,
                    module="通知管理",
                    action=f"通知{notification_id}已重置为待发送状态，准备重试",
                    log_level=LogLevel.INFO
                )
            except Exception as e:
                db.session.rollback()
                create_log(
                    operator_id=None,
                    operator_name="系统",
                    log_type=LogType.ERROR,
                    module="通知管理",
                    action=f"重试准备失败",
                    error_message=str(e),
                    log_level=LogLevel.ERROR
                )
                raise BusinessException("重试准备失败", 500)
            
            return {
                "success": True,
                "message": "已重置为待发送状态，请调用send_notification重新发送",
                "notification": {
                    "id": notification.id,
                    "status": notification.status.name
                }
            }
        
        else:
            raise BusinessException(f"不支持的操作类型：{action}", 400)