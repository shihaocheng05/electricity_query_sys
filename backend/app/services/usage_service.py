#用电数据采集业务
from ..models import IoTData,UsageData,IoTstatus,UsageType,Meter,User,NoticeType, SendChannel,MeterStatus
from ..services import MeterServices,NotifyServices
from ..middleware import BusinessException,create_log, LogType, LogLevel
from app import db
from flask import current_app
from datetime import datetime, timedelta
from sqlalchemy import func

class UsageService:
    @staticmethod
    def receive_iot_data(meter_id,electricity,collect_time,voltage=None,current=None):
        validate_result=MeterServices.validate_meter_reading(meter_id,electricity,collect_time)     #该函数中已检验电表是否存在
        status=IoTstatus.NORMAL
        if not validate_result["is_valid"]:
            raise BusinessException("无法写入的异常数据",400)
        if validate_result["warnings"]!=[]:
            status=IoTstatus.ABNORMAL
        
        new_iot_data=IoTData(
            meter_id=meter_id,
            electricity=electricity,
            collect_time=collect_time,
            voltage=voltage,
            current=current,
            status=status
        )

        try:
            db.session.add(new_iot_data)
        except Exception as e:
            db.session.rollback()
            create_log(
                operator_id=None,
                operator_name="IoT设备",
                log_type=LogType.ERROR,
                module="用电数据",
                action=f"IoT数据录入失败：电表{meter_id}",
                error_message=str(e),
                log_level=LogLevel.ERROR
            )
            raise BusinessException("IoT数据录入失败",500)
        
        return {
            "success":True,
            "warning":validate_result["warnings"],
            "IoTData_info":{
                "meter_id":meter_id,
                "electricity":electricity,
                "collect_time":collect_time,
                "voltage":voltage,
                "current":current,
                "status":status
            }
        }
    
    @staticmethod
    def aggregate_usage_data(meter_id, usage_type, target_date=None):
        """
        汇总用电数据：计算目标时段对应的总、高峰期、低谷期用电量，如果已经存在该数据，那么就更新，如果不存在就重新写入表
        :param meter_id: 电表ID
        :param usage_type: 汇总类型（DAY/MONTH）
        :param target_date: 目标日期，默认昨天/上月
        :return: 汇总结果和异常检测信息
        """
        # 验证电表是否存在
        meter = Meter.query.get(meter_id)
        if not meter:
            raise BusinessException("电表不存在", 404)
        
        # 确定汇总时间范围
        if target_date is None:
            if usage_type == UsageType.DAY:
                target_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
            else:  # MONTH
                today = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                target_date = today - timedelta(days=1)
                target_date = target_date.replace(day=1)
        
        # 设置时间范围
        if usage_type == UsageType.DAY:
            start_time = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = start_time + timedelta(days=1)
        else:  # MONTH
            start_time = target_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # 下个月第一天
            if start_time.month == 12:
                end_time = start_time.replace(year=start_time.year + 1, month=1)
            else:
                end_time = start_time.replace(month=start_time.month + 1)
        
        # 查询该时间段内的IoT数据
        iot_records = IoTData.query.filter(
            IoTData.meter_id == meter_id,
            IoTData.collect_time >= start_time,
            IoTData.collect_time < end_time
        ).order_by(IoTData.collect_time).all()
        
        if not iot_records:
            raise BusinessException(f"未找到{start_time.strftime('%Y-%m-%d')}的用电数据", 404)
        
        # 计算总用电量（使用差值法：最后一次读数 - 第一次读数）
        total_electricity = iot_records[-1].electricity - iot_records[0].electricity
        
        # 区分高峰/低谷时段用电量
        # 高峰时段：8:00-22:00（可配置）
        # 低谷时段：22:00-次日8:00
        peak_electricity = 0.0
        valley_electricity = 0.0
        
        for i in range(len(iot_records) - 1):
            current_record = iot_records[i]
            next_record = iot_records[i + 1]
            
            # 计算这个时间段的用电量
            period_usage = next_record.electricity - current_record.electricity
            
            # 判断是否在高峰时段（8:00-22:00）
            current_hour = current_record.collect_time.hour
            if 8 <= current_hour < 22:
                peak_electricity += period_usage
            else:
                valley_electricity += period_usage
        
        # 检查是否已存在该汇总数据
        existing_usage = UsageData.query.filter_by(
            meter_id=meter_id,
            usage_type=usage_type,
            usage_time=start_time
        ).first()
        
        if existing_usage:
            # 更新已有数据
            existing_usage.total_electricity = total_electricity
            existing_usage.peak_electricity = peak_electricity
            existing_usage.valley_electricity = valley_electricity
            usage_data = existing_usage
        else:
            # 创建新汇总数据
            usage_data = UsageData(
                meter_id=meter_id,
                usage_type=usage_type,
                usage_time=start_time,
                total_electricity=total_electricity,
                peak_electricity=peak_electricity,
                valley_electricity=valley_electricity
            )
            db.session.add(usage_data)
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            create_log(
                operator_id=None,
                operator_name="系统",
                log_type=LogType.ERROR,
                module="用电数据",
                action=f"用电数据汇总失败：电表{meter_id}",
                error_message=str(e),
                log_level=LogLevel.ERROR
            )
            raise BusinessException("用电数据汇总失败", 500)
        
        # 执行异常检测
        anomaly_detection = UsageService._detect_usage_anomaly(meter_id, usage_type, total_electricity, start_time)
        
        return {
            "success": True,
            "usage_summary": {
                "meter_id": meter_id,
                "usage_type": usage_type.name,
                "usage_time": start_time.strftime("%Y-%m-%d"),
                "total_electricity": round(total_electricity, 2),
                "peak_electricity": round(peak_electricity, 2),
                "valley_electricity": round(valley_electricity, 2),
                "data_points": len(iot_records)
            },
            "anomaly_detection": anomaly_detection
        }
    
    @staticmethod
    def _detect_usage_anomaly(meter_id, usage_type, current_usage, current_time):
        """
        异常检测：检测用电量是否超过历史均值
        :param meter_id: 电表ID
        :param usage_type: 汇总类型
        :param current_usage: 当前用电量
        :param current_time: 当前时间
        :return: 异常检测结果
        """
        # 查询历史同类型汇总数据（排除当前这条）
        historical_data = UsageData.query.filter(
            UsageData.meter_id == meter_id,
            UsageData.usage_type == usage_type,
            UsageData.usage_time < current_time
        ).order_by(UsageData.usage_time.desc()).limit(12).all()  # 最近12条记录
        
        if len(historical_data) < 3:
            return {
                "has_anomaly": False,
                "message": "历史数据不足，无法进行异常检测（至少需要3条历史记录）"
            }
        
        # 计算历史平均值和标准差
        historical_values = [data.total_electricity for data in historical_data]
        avg_usage = sum(historical_values) / len(historical_values)
        
        # 计算标准差
        variance = sum((x - avg_usage) ** 2 for x in historical_values) / len(historical_values)
        std_dev = variance ** 0.5
        
        # 异常检测规则：
        # 1. 超过平均值的150%
        # 2. 或超过平均值 + 2倍标准差（统计学上的异常值）
        threshold_1 = avg_usage * 1.5
        threshold_2 = avg_usage + 2 * std_dev
        
        is_anomaly = current_usage > threshold_1 or current_usage > threshold_2
        
        # 计算增长率
        growth_rate = ((current_usage - avg_usage) / avg_usage * 100) if avg_usage > 0 else 0
        
        result = {
            "has_anomaly": is_anomaly,
            "current_usage": round(current_usage, 2),
            "historical_average": round(avg_usage, 2),
            "standard_deviation": round(std_dev, 2),
            "growth_rate": round(growth_rate, 2),
            "historical_records_count": len(historical_data)
        }
        
        if is_anomaly:
            result["message"] = f"检测到异常用电！当前用电量({current_usage:.2f}度)超过历史平均值({avg_usage:.2f}度)的{growth_rate:.1f}%"
            result["severity"] = "high" if growth_rate > 100 else "medium"
            
            # 触发通知（可选）
            UsageService._notify_usage_anomaly(meter_id, usage_type, result)
        else:
            result["message"] = f"用电量正常，当前用电量为历史平均值的{(current_usage/avg_usage*100):.1f}%"
            result["severity"] = "normal"
        
        return result
    
    @staticmethod
    def _notify_usage_anomaly(meter_id, usage_type, anomaly_info):
        """
        触发异常用电通知
        :param meter_id: 电表ID
        :param usage_type: 汇总类型
        :param anomaly_info: 异常信息
        """
        try:
            meter = Meter.query.get(meter_id)
            if not meter or not meter.user_id:
                return
            
            user = User.query.get(meter.user_id)
            if not user:
                return
            
            # 创建异常用电通知
            period_name = "日" if usage_type == UsageType.DAY else "月"
            NotifyServices.create_notification(
                notice_type=NoticeType.PRICE_CHANGE,  # 可以新增一个异常用电类型
                targets=[user],
                title=f"异常用电提醒 - {meter.meter_code}",
                content=f"您的电表{period_name}度用电量异常：\n{anomaly_info['message']}\n建议检查用电设备是否正常。",
                send_channel=SendChannel.INNER,
                send_time=datetime.now(),
                is_batch=False,
                related_id=meter_id
            )
            
            create_log(
                operator_id=None,
                operator_name="系统",
                log_type=LogType.CREATE,
                module="用电数据",
                action=f"异常用电通知已创建：电表{meter_id}",
                log_level=LogLevel.INFO
            )
        except Exception as e:
            create_log(
                operator_id=None,
                operator_name="系统",
                log_type=LogType.ERROR,
                module="用电数据",
                action=f"创建异常用电通知失败：电表{meter_id}",
                error_message=str(e),
                log_level=LogLevel.ERROR
            )
            # 不抛出异常，不影响主流程
    
    @staticmethod
    def batch_aggregate_all_meters(usage_type, target_date=None):
        """
        批量汇总所有电表的用电数据
        :param usage_type: 汇总类型（DAY/MONTH）
        :param target_date: 目标日期
        :return: 批量汇总结果
        """ 
        # 获取所有正常状态的电表
        active_meters = Meter.query.filter_by(status=MeterStatus.NORMAL).all()
        
        success_count = 0
        failed_count = 0
        anomaly_count = 0
        failed_meters = []
        
        for meter in active_meters:
            try:
                result = UsageService.aggregate_usage_data(meter.id, usage_type, target_date)
                success_count += 1
                
                if result["anomaly_detection"]["has_anomaly"]:
                    anomaly_count += 1
                    
            except Exception as e:
                failed_count += 1
                failed_meters.append({
                    "meter_id": meter.id,
                    "meter_code": meter.meter_code,
                    "error": str(e)
                })
                create_log(
                    operator_id=None,
                    operator_name="系统",
                    log_type=LogType.ERROR,
                    module="用电数据",
                    action=f"电表{meter.meter_code}汇总失败",
                    error_message=str(e),
                    log_level=LogLevel.ERROR
                )
        
        return {
            "success": True,
            "summary": {
                "total_meters": len(active_meters),
                "success_count": success_count,
                "failed_count": failed_count,
                "anomaly_count": anomaly_count
            },
            "failed_meters": failed_meters
        }
    
    @staticmethod
    def manual_input_reading(meter_id, reading_value, reading_time, operator_id, voltage=None, current=None, proof_image=None):
        """
        人工录入电表读数
        权限校验已在API层完成，本层仅处理业务逻辑
        :param meter_id: 电表ID
        :param reading_value: 读数值
        :param reading_time: 读数时间
        :param operator_id: 录入人ID
        :param voltage: 电压（可选）
        :param current: 电流（可选）
        :param proof_image: 读数凭证图片URL（可选）
        :return: 录入结果
        """
        from models.meter import MeterRecord, RecordType
        
        # 1. 校验电表是否存在
        meter = Meter.query.get(meter_id)
        if not meter:
            raise BusinessException("电表不存在", 404)
        
        # 2. 校验读数有效性
        validate_result = MeterServices.validate_meter_reading(meter_id, reading_value, reading_time)
        
        status = IoTstatus.NORMAL
        if not validate_result["is_valid"]:
            raise BusinessException(f"读数无效：{', '.join(validate_result['warnings'])}", 400)
        
        if validate_result["warnings"]:
            status = IoTstatus.ABNORMAL
        
        # 4. 录入IoT数据
        new_iot_data = IoTData(
            meter_id=meter_id,
            electricity=reading_value,
            collect_time=reading_time,
            voltage=voltage,
            current=current,
            status=status
        )
        db.session.add(new_iot_data)
        
        # 5. 记录操作日志（如果有凭证图片）
        if proof_image:
            meter_record = MeterRecord(
                meter_id=meter_id,
                record_type=RecordType.CHECK,
                operator=f"用户_{operator_id}",
                content=f"人工录入读数：{reading_value}度，时间：{reading_time.strftime('%Y-%m-%d %H:%M:%S')}",
                attach_img=proof_image
            )
            db.session.add(meter_record)
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            create_log(
                operator_id=operator_id,
                operator_name="用户",
                log_type=LogType.ERROR,
                module="用电数据",
                action=f"人工录入数据失败：电表{meter_id}",
                error_message=str(e),
                log_level=LogLevel.ERROR
            )
            raise BusinessException("数据录入失败", 500)
        
        # 6. 自动触发汇总更新
        # 判断是否需要更新日汇总
        update_results = []
        try:
            # 更新当天的日汇总
            day_result = UsageService.aggregate_usage_data(
                meter_id=meter_id,
                usage_type=UsageType.DAY,
                target_date=reading_time.replace(hour=0, minute=0, second=0, microsecond=0)
            )
            update_results.append({"type": "DAY", "status": "success"})
        except Exception as e:
            create_log(
                operator_id=operator_id,
                operator_name="用户",
                log_type=LogType.WARNING,
                module="用电数据",
                action=f"日汇总更新失败：电表{meter_id}",
                error_message=str(e),
                log_level=LogLevel.WARNING
            )
            update_results.append({"type": "DAY", "status": "failed", "error": str(e)})
        
        # 更新当月的月汇总
        try:
            month_start = reading_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_result = UsageService.aggregate_usage_data(
                meter_id=meter_id,
                usage_type=UsageType.MONTH,
                target_date=month_start
            )
            update_results.append({"type": "MONTH", "status": "success"})
        except Exception as e:
            create_log(
                operator_id=operator_id,
                operator_name="用户",
                log_type=LogType.WARNING,
                module="用电数据",
                action=f"月汇总更新失败：电表{meter_id}",
                error_message=str(e),
                log_level=LogLevel.WARNING
            )
            update_results.append({"type": "MONTH", "status": "failed", "error": str(e)})
        
        return {
            "success": True,
            "message": "读数录入成功",
            "reading_info": {
                "id": new_iot_data.id,
                "meter_id": meter_id,
                "meter_code": meter.meter_code,
                "reading_value": reading_value,
                "reading_time": reading_time.strftime("%Y-%m-%d %H:%M:%S"),
                "voltage": voltage,
                "current": current,
                "status": status.name,
                "proof_image": proof_image
            },
            "warnings": validate_result["warnings"],
            "usage_update": update_results
        }
    
    @staticmethod
    def query_usage_data(meter_id, start_date=None, end_date=None, 
                        format_type="hour", page=1, per_page=100):
        """
        查询用电数据
        权限校验已在API层完成，本层仅处理业务逻辑
        :param meter_id: 电表ID（必填）
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param format_type: 数据格式类型（hour/day/month）
        :param page: 页码
        :param per_page: 每页数量
        :return: 用电数据列表
        """
        # 1. 校验电表是否存在
        meter = Meter.query.get(meter_id)
        if not meter:
            raise BusinessException("电表不存在", 404)
        
        # 2. 设置默认时间范围（最近30天）
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # 确保时间范围合理
        if start_date > end_date:
            raise BusinessException("开始日期不能晚于结束日期", 400)
        
        # 3. 直接查询该电表的数据
        queryable_meter_ids = [meter_id]
        if format_type == "hour":
            # 查询IoTData原始数据，按小时展示
            query = IoTData.query.filter(
                IoTData.meter_id.in_(queryable_meter_ids),
                IoTData.collect_time >= start_date,
                IoTData.collect_time <= end_date
            ).order_by(IoTData.collect_time.desc())
            
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            
            data_list = []
            for record in pagination.items:
                meter = Meter.query.get(record.meter_id)
                data_list.append({
                    "meter_id": record.meter_id,
                    "meter_code": meter.meter_code if meter else "未知",
                    "reading": record.electricity,
                    "voltage": record.voltage,
                    "current": record.current,
                    "collect_time": record.collect_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "status": record.status.name
                })
            
            # 计算统计数据
            total_records = pagination.total
            if pagination.items:
                first_reading = min(item.electricity for item in pagination.items)
                last_reading = max(item.electricity for item in pagination.items)
                total_electricity = last_reading - first_reading
            else:
                total_electricity = 0
            
        elif format_type == "day":
            # 查询UsageData日汇总数据
            query = UsageData.query.filter(
                UsageData.meter_id.in_(queryable_meter_ids),
                UsageData.usage_type == UsageType.DAY,
                UsageData.usage_time >= start_date,
                UsageData.usage_time <= end_date
            ).order_by(UsageData.usage_time.desc())
            
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            
            data_list = []
            total_electricity = 0
            for record in pagination.items:
                meter = Meter.query.get(record.meter_id)
                data_list.append({
                    "meter_id": record.meter_id,
                    "meter_code": meter.meter_code if meter else "未知",
                    "usage_date": record.usage_time.strftime("%Y-%m-%d"),
                    "total_electricity": round(record.total_electricity, 2),
                    "peak_electricity": round(record.peak_electricity, 2) if record.peak_electricity else 0,
                    "valley_electricity": round(record.valley_electricity, 2) if record.valley_electricity else 0,
                    "create_time": record.create_time.strftime("%Y-%m-%d %H:%M:%S") if record.create_time else None
                })
                total_electricity += record.total_electricity
            
            total_records = pagination.total
            
        elif format_type == "month":
            # 查询UsageData月汇总数据
            query = UsageData.query.filter(
                UsageData.meter_id.in_(queryable_meter_ids),
                UsageData.usage_type == UsageType.MONTH,
                UsageData.usage_time >= start_date,
                UsageData.usage_time <= end_date
            ).order_by(UsageData.usage_time.desc())
            
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            
            data_list = []
            total_electricity = 0
            for record in pagination.items:
                meter = Meter.query.get(record.meter_id)
                data_list.append({
                    "meter_id": record.meter_id,
                    "meter_code": meter.meter_code if meter else "未知",
                    "usage_month": record.usage_time.strftime("%Y-%m"),
                    "total_electricity": round(record.total_electricity, 2),
                    "peak_electricity": round(record.peak_electricity, 2) if record.peak_electricity else 0,
                    "valley_electricity": round(record.valley_electricity, 2) if record.valley_electricity else 0,
                    "create_time": record.create_time.strftime("%Y-%m-%d %H:%M:%S") if record.create_time else None
                })
                total_electricity += record.total_electricity
            
            total_records = pagination.total
        else:
            raise BusinessException(f"不支持的格式类型：{format_type}", 400)
        
        # 4. 返回格式化数据
        return {
            "success": True,
            "format_type": format_type,
            "time_range": {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d")
            },
            "data": data_list,
            "summary": {
                "total_records": total_records,
                "total_electricity": round(total_electricity, 2),
                "avg_electricity": round(total_electricity / total_records, 2) if total_records > 0 else 0
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