#电表业务（状态更新、IoT数据校验）
from ..models import Meter,MeterType,MeterStatus,MeterRecord,RecordType,Region,BillStatus,RoleEnum,User,NoticeType,SendChannel
from flask import current_app,session
from datetime import datetime
import random
from ..middleware import BusinessException,create_log, LogType, LogLevel
from app import db
from .notify_sevice import NotifyServices

class MeterServices:
    #安装电表（初始化）
    @staticmethod
    def generate_unique_meter_code(region_id, meter_type):
        region = Region.query.get(region_id)
        region_code = region.region_code                                #片区码
        type_flag = "S" if meter_type==MeterType.SMART else "T"         #电表类型   
        timestamp = datetime.now().strftime("%Y%m%d%H%M")               #时间戳   
        random_num = str(random.randint(0, 999)).zfill(3)               #随机数  
        meter_code = f"{region_code}-{type_flag}-{timestamp}-{random_num}"
    
        while Meter.query.filter_by(meter_code=meter_code).first():     #保底措施，万一还是有重复的电表码
            random_num = str(random.randint(0, 999)).zfill(3)
            meter_code = f"{region_code}-{type_flag}-{timestamp}-{random_num}"

        return meter_code

    @staticmethod
    def meter_install(user_id,region_id,install_address:str):       #相当于电表注册，初始化第一次写入表，编号初始化之后不会再改变，如果电表过户到时候写过户的逻辑
        new_meter=Meter(
            meter_code=MeterServices.generate_unique_meter_code(region_id,MeterType.SMART),     #默认只能电表（IoT电表，省的人工去录数据）
            user_id=user_id,
            region_id=region_id,
            install_address=install_address
        )
        db.session.add(new_meter)
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            create_log(
                operator_id=user_id,
                operator_name="用户",
                log_type=LogType.ERROR,
                module="电表管理",
                action=f"电表安装初始化失败，片区{region_id}",
                error_message=str(e),
                log_level=LogLevel.ERROR
            )
            raise BusinessException("电表初始化失败",500)
        
        return {
            "success":True,
            "meter_info":{
                "meter_id":new_meter.id,
                "meter_code":new_meter.meter_code,
                "user_id":new_meter.user_id,
                "meter_type":new_meter.meter_type.value,
                "region_id":new_meter.region_id,
                "install_address":new_meter.install_address,
                "install_time":new_meter.install_time,
                "status":new_meter.status.value,
                "init_time":new_meter.init_time
            }
        }

    #更新电表状态（如果报废需要电表所有账单都交清）
    @staticmethod
    def meter_update_status(meter_id,new_status:MeterStatus):
        meter=Meter.query.get(meter_id)

        if meter is None:
            raise BusinessException("更新的电表不存在")
        if new_status==MeterStatus.SCRAPPED:
            for bill in meter.bills:
                if bill.status==BillStatus.unpaid or bill.status==BillStatus.overdue:
                    raise BusinessException("该电表还有未交清的账单")
        
        meter.status=new_status
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            create_log(
                operator_id=None,
                operator_name="系统",
                log_type=LogType.ERROR,
                module="电表管理",
                action=f"电表更新状态失败：电表{meter_id}",
                error_message=str(e),
                log_level=LogLevel.ERROR
            )
            raise BusinessException("电表更新状态失败",500)

        return {
            "success":True,
            "new_status":new_status
        }
    #增加电表操作记录（写入操作表）
    @staticmethod
    def add_meter_records(meter_id:str,record_type:RecordType,operator:str,content=None,attach_img:str=None):
        meter=Meter.query.get(meter_id)
        
        if meter is None:
            raise BusinessException("未找到该电表！")
        new_meter_record=MeterRecord(
            meter_id=meter.id,
            record_type=record_type,
            operator=operator,
            content=content,
            attach_img=attach_img
        )

        db.session.add(new_meter_record)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            create_log(
                operator_id=None,
                operator_name=operator,
                log_type=LogType.ERROR,
                module="电表管理",
                action=f"操作记录上传失败：电表{meter_id}",
                error_message=str(e),
                log_level=LogLevel.ERROR
            )
            raise BusinessException("操作记录上传失败",500)
        
        return {
            "success":True,
            "record_id":new_meter_record.id,
            "meter_id":meter.id,
            "record_type":record_type.value,
            "operator":operator,
            "content":content,
            "create_time":new_meter_record.record_time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    #电表故障报修（检验报修用户是否为电表绑定用户，若是，推送通知给本地管理员）
    @staticmethod
    def notify_meter_repair(meter_id, user_id, fault_address, fault_description, attach_img=None):
        """
        电表故障报修
        :param meter_id: 电表ID
        :param user_id: 报修用户ID
        :param fault_address: 故障地址
        :param fault_description: 故障描述
        :param attach_img: 附件图片URL
        :return: 报修结果
        """
        # 1. 校验电表是否存在
        meter = Meter.query.get(meter_id)
        if meter is None:
            raise BusinessException("电表不存在", 404)
        
        # 2. 校验报修用户是否为电表绑定用户
        if meter.user_id != user_id:
            raise BusinessException("您不是该电表的绑定用户，无权报修", 403)
        
        # 3. 记录报修信息
        repair_record = MeterRecord(
            meter_id=meter_id,
            record_type=RecordType.REPAIR,
            operator=f"用户_{user_id}",
            content=f"故障地址：{fault_address}；故障描述：{fault_description}",
            attach_img=attach_img
        )
        db.session.add(repair_record)
        
        # 4. 更新电表状态为异常
        meter.status = MeterStatus.ABNORMAL
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            create_log(
                operator_id=user_id,
                operator_name="用户",
                log_type=LogType.ERROR,
                module="电表管理",
                action=f"报修记录创建失败：电表{meter_id}",
                error_message=str(e),
                log_level=LogLevel.ERROR
            )
            raise BusinessException("报修记录创建失败", 500)
        
        # 5. 推送报修通知给片区管理员
        
        region = Region.query.get(meter.region_id)
        if region and region.manager_id:
            manager = User.query.get(region.manager_id)
            if manager:
                try:
                    # 创建通知
                    notification_result = NotifyServices.create_notification(
                        notice_type=NoticeType.REPAIR,
                        targets=[manager],
                        title=f"电表报修通知 - {meter.meter_code}",
                        content=f"电表编号：{meter.meter_code}\n故障地址：{fault_address}\n故障描述：{fault_description}\n报修用户ID：{user_id}",
                        send_channel=SendChannel.INNER,
                        send_time=datetime.now(),
                        is_batch=False,
                        related_id=meter_id
                    )
                    create_log(
                        operator_id=user_id,
                        operator_name="用户",
                        log_type=LogType.CREATE,
                        module="电表管理",
                        action=f"报修通知已创建，通知ID：{notification_result['notification_info']['id']}",
                        log_level=LogLevel.INFO
                    )
                except Exception as e:
                    create_log(
                        operator_id=user_id,
                        operator_name="用户",
                        log_type=LogType.ERROR,
                        module="电表管理",
                        action=f"推送报修通知失败：电表{meter_id}",
                        error_message=str(e),
                        log_level=LogLevel.ERROR
                    )
                    # 不影响报修流程，仅记录日志
        
        return {
            "success": True,
            "message": "报修成功，已通知片区管理员",
            "repair_info": {
                "record_id": repair_record.id,
                "meter_id": meter_id,
                "meter_code": meter.meter_code,
                "fault_address": fault_address,
                "fault_description": fault_description,
                "record_time": repair_record.record_time.strftime("%Y-%m-%d %H:%M:%S"),
                "meter_status": meter.status.value
            }
        }
    
    #电表数据校验
    @staticmethod
    def validate_meter_reading(meter_id, new_reading, reading_time=None):
        """
        校验电表读数的合理性
        :param meter_id: 电表ID
        :param new_reading: 新读数
        :param reading_time: 读数时间，默认当前时间
        :return: 校验结果
        """
        from ..models.usage import IoTData, UsageData
        
        meter = Meter.query.get(meter_id)
        if meter is None:
            raise BusinessException("电表不存在", 404)
        
        if reading_time is None:
            reading_time = datetime.now()
        
        # 获取最近一次读数
        last_reading = IoTData.query.filter_by(meter_id=meter_id)\
            .order_by(IoTData.collect_time.desc()).first()
        
        warnings = []
        is_valid = True
        
        if last_reading:
            # 1. 校验读数不能早于上次读数时间
            if reading_time <= last_reading.collect_time:
                warnings.append("读数时间不能早于上次读数时间")
                is_valid = False
            
            # 2. 校验读数不能小于上次读数（电表读数只增不减）
            if new_reading < last_reading.electricity:
                warnings.append(f"新读数({new_reading})不能小于上次读数({last_reading.electricity})")
                is_valid = False
            
            # 3. 校验读数增长是否异常（突增50%以上触发预警）
            time_diff = (reading_time - last_reading.collect_time).total_seconds() / 3600  # 小时
            if time_diff > 0:
                reading_diff = new_reading - last_reading.electricity
                hourly_increase = reading_diff / time_diff
                
                # 获取历史10小时平均小时用电量
                historical_data = IoTData.query.filter_by(meter_id=meter_id)\
                    .order_by(IoTData.collect_time.desc()).limit(10).all()
                
                if len(historical_data) >= 2:
                    total_historical = 0
                    total_hours = 0
                    for i in range(len(historical_data) - 1):
                        diff = historical_data[i].electricity - historical_data[i + 1].electricity
                        hours = (historical_data[i].collect_time - historical_data[i + 1].collect_time).total_seconds() / 3600
                        if hours > 0:
                            total_historical += diff
                            total_hours += hours
                    
                    if total_hours > 0:
                        avg_hourly = total_historical / total_hours
                        if avg_hourly > 0 and hourly_increase > avg_hourly * 1.5:
                            warnings.append(f"读数增长异常：平均每小时{hourly_increase:.2f}度，超过历史10小时平均值({avg_hourly:.2f}度)的50%")
                            # 异常增长不一定是错误，只是预警
        
        return {
            "success": True,
            "is_valid": is_valid,
            "warnings": warnings,
            "validation_info": {
                "meter_id": meter_id,
                "new_reading": new_reading,
                "reading_time": reading_time.strftime("%Y-%m-%d %H:%M:%S"),
                "last_reading": last_reading.electricity if last_reading else None,
                "last_reading_time": last_reading.collect_time.strftime("%Y-%m-%d %H:%M:%S") if last_reading else None
            }
        }
    
    #电表查询
    @staticmethod
    def query_meters(user_id=None, region_id=None, meter_status=None, meter_type=None, page=1, per_page=20):
        """
        查询电表信息（权限已在API层控制）
        :param user_id: 用户ID筛选（可选，用于居民查询自己的电表）
        :param region_id: 片区ID筛选（可选）
        :param meter_status: 电表状态筛选（可选）
        :param meter_type: 电表类型筛选（可选）
        :param page: 页码
        :param per_page: 每页数量
        :return: 电表列表
        """
        query = Meter.query
        
        # 按条件筛选
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        if region_id:
            query = query.filter_by(region_id=region_id)
        
        if meter_status:
            query = query.filter_by(status=meter_status)
        
        if meter_type:
            query = query.filter_by(meter_type=meter_type)
        
        # 按安装时间倒序
        query = query.order_by(Meter.install_time.desc())
        
        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        meters_list = []
        for meter in pagination.items:
            # 获取用户信息
            user = User.query.get(meter.user_id) if meter.user_id else None
            # 获取片区信息
            region = Region.query.get(meter.region_id) if meter.region_id else None
            
            meters_list.append({
                "meter_id": meter.id,
                "meter_code": meter.meter_code,
                "user_id": meter.user_id,
                "meter_type": meter.meter_type.value,
                "install_address": meter.install_address,
                "install_time": meter.install_time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": meter.status.value,
                "init_time": meter.init_time.strftime("%Y-%m-%d %H:%M:%S") if meter.init_time else None,
                "update_time": meter.update_time.strftime("%Y-%m-%d %H:%M:%S") if meter.update_time else None
            })
        
        return {
            "success": True,
            "meters": meters_list,
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
    def query_available_meters(region_id=None, page=1, per_page=20):
        """
        查询空闲电表（未分配给用户的电表）
        :param region_id: 片区ID（可选）
        :param page: 页码
        :param per_page: 每页数量
        :return: 空闲电表列表
        """
        # 构建查询：user_id为空的电表
        query = Meter.query.filter(Meter.user_id.is_(None))
        
        # 按片区筛选
        if region_id:
            query = query.filter_by(region_id=region_id)
        
        # 只查询正常状态的电表
        query = query.filter_by(status=MeterStatus.NORMAL)
        
        # 分页
        pagination = query.order_by(Meter.install_time.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        meters_list = []
        for meter in pagination.items:
            region = Region.query.get(meter.region_id)
            meters_list.append({
                "meter_id": meter.id,
                "meter_code": meter.meter_code,
                "meter_type": meter.meter_type.value,
                "install_address": meter.install_address,
                "install_time": meter.install_time.strftime("%Y-%m-%d %H:%M:%S") if meter.install_time else None,
                "region_name": region.region_name if region else "未知片区",
                "region_id": meter.region_id,
                "status": meter.status.value
            })
        
        return {
            "meters": meters_list,
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
    def query_meter_records(meter_id, record_type=None, page=1, per_page=20):
        """
        :param record_type: 记录类型筛选（可选）
        :param page: 页码
        :param per_page: 每页数量
        :return: 操作记录列表
        """
        meter = Meter.query.get(meter_id)
        if meter is None:
            raise BusinessException("电表不存在", 404)
        
        query = MeterRecord.query.filter_by(meter_id=meter_id)
        
        if record_type:
            query = query.filter_by(record_type=record_type)
        
        query = query.order_by(MeterRecord.record_time.desc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        records_list = []
        for record in pagination.items:
            records_list.append({
                "record_id": record.id,
                "meter_id": record.meter_id,
                "record_type": record.record_type.value,
                "operator": record.operator,
                "content": record.content,
                "create_time": record.record_time.strftime("%Y-%m-%d %H:%M:%S")
            })
        
        return {
            "success": True,
            "meter_code": meter.meter_code,
            "records": records_list,
            "pagination": {
                "total": pagination.total,
                "page": pagination.page,
                "per_page": pagination.per_page,
                "pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev
            }
        }