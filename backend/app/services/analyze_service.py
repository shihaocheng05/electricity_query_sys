#分析业务（数据统计、趋势计算）
from ..models import UsageData, UsageType, Bill, Meter, User, Region, IoTData,BillDetail
from app import db
from ..middleware import BusinessException
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from flask import current_app
import csv
import io

class AnalyzeServices:
    
    @staticmethod
    def _get_all_sub_regions(region_id):
        """
        递归获取某个片区及其所有子片区的ID列表
        :param region_id: 片区ID
        :return: 包含该片区及所有子片区的ID列表
        """
        result = [region_id]
        
        # 查找直接子片区
        sub_regions = Region.query.filter_by(parent_id=region_id).all()
        
        # 递归查找每个子片区的子片区
        for sub_region in sub_regions:
            result.extend(AnalyzeServices._get_all_sub_regions(sub_region.id))
        
        return result
    
    @staticmethod
    def get_user_statistics_summary(user_id):
        """
        获取用户统计摘要（Dashboard用）
        :param user_id: 用户ID
        :return: 统计摘要数据
        """
        user = User.query.get(user_id)
        if not user:
            raise BusinessException("用户不存在", 404)
        
        # 获取用户的所有电表
        meters = Meter.query.filter_by(user_id=user_id).all()
        meter_ids = [m.id for m in meters] if meters else []
        
        # 当月范围
        current_time = datetime.now()
        month_start = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # 1. 总用电量（所有时间）
        total_usage = db.session.query(func.sum(UsageData.total_electricity)).filter(
            UsageData.meter_id.in_(meter_ids)
        ).scalar() or 0
        
        # 2. 当月用电量
        current_month_usage = db.session.query(func.sum(UsageData.total_electricity)).filter(
            UsageData.meter_id.in_(meter_ids),
            UsageData.usage_time >= month_start
        ).scalar() or 0
        
        # 3. 总费用（所有账单）
        total_cost = db.session.query(func.sum(Bill.total_amount)).filter(
            Bill.user_id == user_id
        ).scalar() or 0
        
        # 4. 未支付账单数
        from ..models import BillStatus
        unpaid_bills = Bill.query.filter(
            Bill.user_id == user_id,
            Bill.status.in_([BillStatus.unpaid, BillStatus.overdue])
        ).count()
        
        return {
            "total_usage": round(total_usage, 2),
            "current_month_usage": round(current_month_usage, 2),
            "total_cost": round(total_cost, 2),
            "unpaid_bills": unpaid_bills,
            "meter_count": len(meters)
        }
    
    @staticmethod
    def get_region_statistics_summary(region_id):
        """
        获取片区统计摘要（管理员Dashboard用）
        包含该片区及所有下级片区的汇总数据
        :param region_id: 片区ID
        :return: 统计摘要数据
        """
        region = Region.query.get(region_id)
        if not region:
            raise BusinessException("片区不存在", 404)
        
        # 获取该片区及所有子片区的ID列表
        all_region_ids = AnalyzeServices._get_all_sub_regions(region_id)
        
        # 获取这些片区的所有电表
        meters = Meter.query.filter(Meter.region_id.in_(all_region_ids)).all()
        meter_ids = [m.id for m in meters] if meters else []
        
        # 获取这些片区的所有用户（通过电表关联）
        user_ids = list(set([m.user_id for m in meters if m.user_id]))
        
        # 当月范围
        current_time = datetime.now()
        month_start = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # 1. 片区总用电量（当月）
        total_usage = db.session.query(func.sum(UsageData.total_electricity)).filter(
            UsageData.meter_id.in_(meter_ids),
            UsageData.usage_time >= month_start
        ).scalar() or 0
        
        # 2. 欠费用户数
        from ..models import BillStatus, UserStatus
        arrear_users = db.session.query(func.count(func.distinct(Bill.user_id))).filter(
            Bill.meter_id.in_(meter_ids),
            Bill.status.in_([BillStatus.overdue])
        ).scalar() or 0
        
        return {
            "region_name": region.region_name,
            "total_usage": round(total_usage, 2),
            "user_count": len(user_ids),
            "meter_count": len(meters),
            "arrear_users": arrear_users
        }
    
    @staticmethod
    def analyze_user_electricity(user_id, analysis_period="month", compare_period=False):
        """
        个人用电分析
        :param user_id: 用户ID
        :param analysis_period: 分析周期（day/month/year）
        :param compare_period: 是否对比同期
        :return: 分析结果
        """
        user = User.query.get(user_id)
        if not user:
            raise BusinessException("用户不存在", 404)
        
        # 获取用户的所有电表
        meters = Meter.query.filter_by(user_id=user_id).all()
        if not meters:
            # 用户没有电表时返回空数据而不是错误
            return {
                "user_id": user_id,
                "analysis_period": analysis_period,
                "trend_data": [],
                "summary": {
                    "total_electricity": 0,
                    "avg_electricity": 0,
                    "peak_electricity": 0,
                    "valley_electricity": 0
                },
                "comparison": None
            }
        
        meter_ids = [m.id for m in meters]
        current_time = datetime.now()
        
        # 1. 查询历史用电数据并生成趋势
        if analysis_period == "day":
            # 查询最近30天的日用电数据
            start_date = current_time - timedelta(days=30)
            usage_type = UsageType.DAY
            compare_start = start_date - timedelta(days=30) if compare_period else None
            
        elif analysis_period == "month":
            # 查询最近12个月的月用电数据
            start_date = current_time - timedelta(days=365)
            usage_type = UsageType.MONTH
            compare_start = start_date - timedelta(days=365) if compare_period else None
            
        elif analysis_period == "year":
            # 查询最近5年的年度数据（需要汇总月数据）
            start_date = current_time.replace(year=current_time.year - 5, month=1, day=1)
            usage_type = UsageType.MONTH
            compare_start = None
        else:
            raise BusinessException("不支持的分析周期", 400)
        
        # 查询当前周期数据
        current_data = UsageData.query.filter(
            UsageData.meter_id.in_(meter_ids),
            UsageData.usage_type == usage_type,
            UsageData.usage_time >= start_date
        ).order_by(UsageData.usage_time).all()
        
        # 构建趋势数据
        trend_data = []
        if analysis_period == "year":
            # 按年汇总
            year_data = {}
            for record in current_data:
                year = record.usage_time.year
                if year not in year_data:
                    year_data[year] = {
                        "total_electricity": 0,
                        "peak_electricity": 0,
                        "valley_electricity": 0
                    }
                year_data[year]["total_electricity"] += record.total_electricity
                year_data[year]["peak_electricity"] += record.peak_electricity or 0
                year_data[year]["valley_electricity"] += record.valley_electricity or 0
            
            for year in sorted(year_data.keys()):
                # 计算该年的电费估算  
                estimated_cost = round(year_data[year]["total_electricity"] * 0.6, 2)
                
                trend_data.append({
                    "period": str(year),
                    "total_electricity": round(year_data[year]["total_electricity"], 2),
                    "peak_electricity": round(year_data[year]["peak_electricity"], 2),
                    "valley_electricity": round(year_data[year]["valley_electricity"], 2),
                    "cost": estimated_cost
                })
        else:
            for record in current_data:
                if analysis_period == "day":
                    period_str = record.usage_time.strftime("%Y-%m-%d")
                else:
                    period_str = record.usage_time.strftime("%Y-%m")
                
                # 计算该时期的电费（简单按0.6元/度计算，实际应查询账单）
                estimated_cost = round(record.total_electricity * 0.6, 2)
                
                trend_data.append({
                    "period": period_str,
                    "total_electricity": round(record.total_electricity, 2),
                    "peak_electricity": round(record.peak_electricity or 0, 2),
                    "valley_electricity": round(record.valley_electricity or 0, 2),
                    "cost": estimated_cost
                })
        
        # 2. 对比同期用电量
        comparison = None
        if compare_period and compare_start:
            compare_data = UsageData.query.filter(
                UsageData.meter_id.in_(meter_ids),
                UsageData.usage_type == usage_type,
                UsageData.usage_time >= compare_start,
                UsageData.usage_time < start_date
            ).all()
            
            current_total = sum(d.total_electricity for d in current_data)
            compare_total = sum(d.total_electricity for d in compare_data)
            
            if compare_total > 0:
                change_rate = ((current_total - compare_total) / compare_total) * 100
            else:
                change_rate = 0
            
            comparison = {
                "current_period_total": round(current_total, 2),
                "compare_period_total": round(compare_total, 2),
                "difference": round(current_total - compare_total, 2),
                "change_rate": round(change_rate, 2),
                "trend": "增长" if change_rate > 0 else "下降" if change_rate < 0 else "持平"
            }
        
        # 3. 计算用电成本占比
        cost_breakdown = AnalyzeServices._calculate_cost_breakdown(user_id, meter_ids, start_date)
        
        return {
            "analysis_period": analysis_period,
            "user_info": {
                "user_id": user_id,
                "user_name": user.real_name or "未设置",
                "meter_count": len(meters)
            },
            "trend_data": trend_data,
            "comparison": comparison,
            "cost_breakdown": cost_breakdown,
            "summary": {
                "total_electricity": round(sum(d["total_electricity"] for d in trend_data), 2),
                "avg_electricity": round(sum(d["total_electricity"] for d in trend_data) / len(trend_data), 2) if trend_data else 0,
                "max_electricity": max((d["total_electricity"] for d in trend_data), default=0),
                "min_electricity": min((d["total_electricity"] for d in trend_data), default=0)
            }
        }
    
    @staticmethod
    def _calculate_cost_breakdown(user_id, meter_ids, start_date):
        """计算用电成本占比（阶梯/分时费用）"""
        from ..models.bill import PriceType, LadderLevel, TimePeriod
        
        # 查询该时间段的账单详情
        bills = Bill.query.filter(
            Bill.user_id == user_id,
            Bill.meter_id.in_(meter_ids),
            Bill.bill_month >= start_date
        ).all()
        
        if not bills:
            return None
        
        bill_ids = [b.id for b in bills]
        details = BillDetail.query.filter(BillDetail.bill_id.in_(bill_ids)).all()
        
        # 按阶梯分类统计
        ladder_cost = {
            "low": 0,
            "middle": 0,
            "high": 0
        }
        
        # 按时段分类统计
        time_cost = {
            "peak": 0,
            "flat": 0,
            "valley": 0
        }
        
        total_cost = 0
        
        for detail in details:
            total_cost += detail.amount
            
            if detail.ladder_level:
                ladder_cost[detail.ladder_level.name] += detail.amount
            
            if detail.time_period:
                time_cost[detail.time_period.name] += detail.amount
        
        if total_cost == 0:
            return None
        
        return {
            "total_cost": round(total_cost, 2),
            "ladder_breakdown": {
                "low": {
                    "amount": round(ladder_cost["low"], 2),
                    "percentage": round(ladder_cost["low"] / total_cost * 100, 2)
                },
                "middle": {
                    "amount": round(ladder_cost["middle"], 2),
                    "percentage": round(ladder_cost["middle"] / total_cost * 100, 2)
                },
                "high": {
                    "amount": round(ladder_cost["high"], 2),
                    "percentage": round(ladder_cost["high"] / total_cost * 100, 2)
                }
            },
            "time_breakdown": {
                "peak": {
                    "amount": round(time_cost["peak"], 2),
                    "percentage": round(time_cost["peak"] / total_cost * 100, 2)
                },
                "flat": {
                    "amount": round(time_cost["flat"], 2),
                    "percentage": round(time_cost["flat"] / total_cost * 100, 2)
                },
                "valley": {
                    "amount": round(time_cost["valley"], 2),
                    "percentage": round(time_cost["valley"] / total_cost * 100, 2)
                }
            }
        }
    
    @staticmethod
    def analyze_region_electricity(region_id, analysis_period="month", compare_period=False):
        """
        片区用电分析（管理员专用）
        包含该片区及所有下级片区的汇总数据
        :param region_id: 片区ID
        :param analysis_period: 分析周期（day/month/year）
        :param compare_period: 是否对比同期
        :return: 分析结果
        """
        region = Region.query.get(region_id)
        if not region:
            raise BusinessException("片区不存在", 404)
        
        # 获取该片区及所有子片区的ID列表
        all_region_ids = AnalyzeServices._get_all_sub_regions(region_id)
        
        # 获取这些片区的所有电表
        meters = Meter.query.filter(Meter.region_id.in_(all_region_ids)).all()
        if not meters:
            return {
                "success": True,
                "analysis_period": analysis_period,
                "region_info": {
                    "region_id": region_id,
                    "region_name": region.region_name,
                    "meter_count": 0,
                    "user_count": 0
                },
                "trend_data": [],
                "comparison": None,
                "summary": {
                    "total_electricity": 0,
                    "avg_electricity": 0,
                    "max_electricity": 0,
                    "min_electricity": 0
                }
            }
        
        meter_ids = [m.id for m in meters]
        user_ids = list(set([m.user_id for m in meters if m.user_id]))
        current_time = datetime.now()
        
        # 1. 查询历史用电数据并生成趋势
        if analysis_period == "day":
            # 查询最近30天的日用电数据
            start_date = current_time - timedelta(days=30)
            usage_type = UsageType.DAY
            compare_start = start_date - timedelta(days=30) if compare_period else None
            
        elif analysis_period == "month":
            # 查询最近12个月的月用电数据
            start_date = current_time - timedelta(days=365)
            usage_type = UsageType.MONTH
            compare_start = start_date - timedelta(days=365) if compare_period else None
            
        elif analysis_period == "year":
            # 查询最近5年的年度数据（需要汇总月数据）
            start_date = current_time.replace(year=current_time.year - 5, month=1, day=1)
            usage_type = UsageType.MONTH
            compare_start = None
        else:
            raise BusinessException("不支持的分析周期", 400)
        
        # 查询当前周期数据
        current_data = UsageData.query.filter(
            UsageData.meter_id.in_(meter_ids),
            UsageData.usage_type == usage_type,
            UsageData.usage_time >= start_date
        ).order_by(UsageData.usage_time).all()
        
        # 构建趋势数据
        trend_data = []
        if analysis_period == "year":
            # 按年汇总
            year_data = {}
            for record in current_data:
                year = record.usage_time.year
                if year not in year_data:
                    year_data[year] = {
                        "total_electricity": 0,
                        "peak_electricity": 0,
                        "valley_electricity": 0
                    }
                year_data[year]["total_electricity"] += record.total_electricity
                year_data[year]["peak_electricity"] += record.peak_electricity or 0
                year_data[year]["valley_electricity"] += record.valley_electricity or 0
            
            for year in sorted(year_data.keys()):
                trend_data.append({
                    "period": str(year),
                    "total_electricity": round(year_data[year]["total_electricity"], 2),
                    "peak_electricity": round(year_data[year]["peak_electricity"], 2),
                    "valley_electricity": round(year_data[year]["valley_electricity"], 2)
                })
        else:
            # 按时间段汇总（日或月）
            period_data = {}
            for record in current_data:
                if analysis_period == "day":
                    period_str = record.usage_time.strftime("%Y-%m-%d")
                else:
                    period_str = record.usage_time.strftime("%Y-%m")
                
                if period_str not in period_data:
                    period_data[period_str] = {
                        "total_electricity": 0,
                        "peak_electricity": 0,
                        "valley_electricity": 0
                    }
                
                period_data[period_str]["total_electricity"] += record.total_electricity
                period_data[period_str]["peak_electricity"] += record.peak_electricity or 0
                period_data[period_str]["valley_electricity"] += record.valley_electricity or 0
            
            for period in sorted(period_data.keys()):
                trend_data.append({
                    "period": period,
                    "total_electricity": round(period_data[period]["total_electricity"], 2),
                    "peak_electricity": round(period_data[period]["peak_electricity"], 2),
                    "valley_electricity": round(period_data[period]["valley_electricity"], 2)
                })
        
        # 2. 对比同期用电量
        comparison = None
        if compare_period and compare_start:
            compare_data = UsageData.query.filter(
                UsageData.meter_id.in_(meter_ids),
                UsageData.usage_type == usage_type,
                UsageData.usage_time >= compare_start,
                UsageData.usage_time < start_date
            ).all()
            
            current_total = sum(d.total_electricity for d in current_data)
            compare_total = sum(d.total_electricity for d in compare_data)
            
            if compare_total > 0:
                change_rate = ((current_total - compare_total) / compare_total) * 100
            else:
                change_rate = 0
            
            comparison = {
                "current_period_total": round(current_total, 2),
                "compare_period_total": round(compare_total, 2),
                "difference": round(current_total - compare_total, 2),
                "change_rate": round(change_rate, 2),
                "trend": "增长" if change_rate > 0 else "下降" if change_rate < 0 else "持平"
            }
        
        # 3. 计算用电峰值时段
        peak_hours = AnalyzeServices._find_peak_hours([region_id], start_date, current_time)
        
        return {
            "success": True,
            "analysis_period": analysis_period,
            "region_info": {
                "region_id": region_id,
                "region_name": region.region_name,
                "meter_count": len(meters),
                "user_count": len(user_ids)
            },
            "trend_data": trend_data,
            "comparison": comparison,
            "peak_hours": peak_hours[:5] if peak_hours else [],  # 返回前5个高峰时段
            "summary": {
                "total_electricity": round(sum(d["total_electricity"] for d in trend_data), 2),
                "avg_electricity": round(sum(d["total_electricity"] for d in trend_data) / len(trend_data), 2) if trend_data else 0,
                "max_electricity": max((d["total_electricity"] for d in trend_data), default=0),
                "min_electricity": min((d["total_electricity"] for d in trend_data), default=0),
                "avg_per_meter": round(sum(d["total_electricity"] for d in trend_data) / len(meters), 2) if trend_data and meters else 0
            }
        }
    
    @staticmethod
    def region_statistics(region_id=None, start_date=None, end_date=None, usage_level=False):
        """
        区域用电统计（包含下级片区的递归汇总）
        :param region_id: 片区ID（可选，不传则统计所有片区）
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param usage_level: 是否生成用电量分级数据（用于热力图）
        :return: 统计结果
        """
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # 查询片区
        if region_id:
            regions = [Region.query.get(region_id)]
            if not regions[0]:
                raise BusinessException("片区不存在", 404)
        else:
            regions = Region.query.all()
        
        statistics = []
        
        for region in regions:
            # 获取该片区及所有子片区的ID列表
            all_region_ids = AnalyzeServices._get_all_sub_regions(region.id)
            
            # 获取这些片区的所有电表
            meters = Meter.query.filter(Meter.region_id.in_(all_region_ids)).all()
            if not meters:
                continue
            
            meter_ids = [m.id for m in meters]
            
            # 查询用电数据
            usage_data = UsageData.query.filter(
                UsageData.meter_id.in_(meter_ids),
                UsageData.usage_time >= start_date,
                UsageData.usage_time <= end_date
            ).all()
            
            total_electricity = sum(d.total_electricity for d in usage_data)
            avg_electricity = total_electricity / len(meters) if meters else 0
            
            # 确定用电等级（用于热力图）
            if usage_level:
                if avg_electricity < 100:
                    level = "低"
                elif avg_electricity < 300:
                    level = "中"
                elif avg_electricity < 500:
                    level = "高"
                else:
                    level = "很高"
            else:
                level = None
            
            statistics.append({
                "region_id": region.id,
                "region_name": region.region_name,
                "meter_count": len(meters),
                "total_electricity": round(total_electricity, 2),
                "avg_electricity": round(avg_electricity, 2),
                "usage_level": level
            })
        
        # 3. 筛选用电高峰时段（18-20点）
        peak_hours = AnalyzeServices._find_peak_hours(
            [stat["region_id"] for stat in statistics],
            start_date,
            end_date
        )
        
        return {
            "success": True,
            "time_range": {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d")
            },
            "region_statistics": statistics,
            "peak_hours": peak_hours,
            "summary": {
                "total_regions": len(statistics),
                "total_electricity": round(sum(s["total_electricity"] for s in statistics), 2),
                "avg_region_electricity": round(sum(s["total_electricity"] for s in statistics) / len(statistics), 2) if statistics else 0
            }
        }
    
    @staticmethod
    def _find_peak_hours(region_ids, start_date, end_date):
        """查找用电高峰时段"""
        # 获取所有相关电表
        meters = Meter.query.filter(Meter.region_id.in_(region_ids)).all()
        if not meters:
            return []
        
        meter_ids = [m.id for m in meters]
        
        # 查询IoT数据，按小时统计
        iot_data = IoTData.query.filter(
            IoTData.meter_id.in_(meter_ids),
            IoTData.collect_time >= start_date,
            IoTData.collect_time <= end_date
        ).all()
        
        # 按小时统计用电量
        hour_usage = {}
        for i in range(len(iot_data) - 1):
            current = iot_data[i]
            next_data = iot_data[i + 1]
            hour = current.collect_time.hour
            usage = next_data.electricity - current.electricity
            
            if hour not in hour_usage:
                hour_usage[hour] = []
            hour_usage[hour].append(usage)
        
        # 计算每个小时的平均用电量
        hour_avg = {}
        for hour, usages in hour_usage.items():
            hour_avg[hour] = sum(usages) / len(usages) if usages else 0
        
        # 找出用电量最高的时段
        sorted_hours = sorted(hour_avg.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {
                "hour": hour,
                "avg_usage": round(usage, 2),
                "is_peak": 18 <= hour < 21  # 标记18-20点为高峰时段
            }
            for hour, usage in sorted_hours[:10]  # 返回前10个小时
        ]
    
    @staticmethod
    def predict_peak_usage(region_id=None, predict_days=7):
        """
        用电高峰预测（包含下级片区）
        :param region_id: 片区ID（可选）
        :param predict_days: 预测天数（默认7天）
        :return: 预测结果
        """
        current_time = datetime.now()
        history_days = 90  # 使用最近3个月的数据进行预测
        start_date = current_time - timedelta(days=history_days)
        
        # 获取电表
        if region_id:
            # 获取该片区及所有子片区的ID列表
            all_region_ids = AnalyzeServices._get_all_sub_regions(region_id)
            meters = Meter.query.filter(Meter.region_id.in_(all_region_ids)).all()
            region = Region.query.get(region_id)
            region_name = region.region_name if region else "未知片区"
        else:
            meters = Meter.query.all()
            region_name = "全部片区"
        
        if not meters:
            raise BusinessException("没有找到电表数据", 404)
        
        meter_ids = [m.id for m in meters]
        
        # 1. 统计历史每日用电高峰
        daily_usage = UsageData.query.filter(
            UsageData.meter_id.in_(meter_ids),
            UsageData.usage_type == UsageType.DAY,
            UsageData.usage_time >= start_date
        ).all()
        
        # 按星期几分类统计
        weekday_usage = {i: [] for i in range(7)}  # 0=周一, 6=周日
        
        for record in daily_usage:
            weekday = record.usage_time.weekday()
            weekday_usage[weekday].append(record.total_electricity)
        
        # 计算每个星期几的平均用电量
        weekday_avg = {}
        for weekday, usages in weekday_usage.items():
            weekday_avg[weekday] = sum(usages) / len(usages) if usages else 0
        
        # 2. 查询IoT数据，统计每日的高峰时段
        iot_data = IoTData.query.filter(
            IoTData.meter_id.in_(meter_ids),
            IoTData.collect_time >= start_date
        ).order_by(IoTData.collect_time).all()
        
        # 按日期和小时统计
        daily_hourly_usage = {}
        for i in range(len(iot_data) - 1):
            current = iot_data[i]
            next_data = iot_data[i + 1]
            
            date_key = current.collect_time.date()
            hour = current.collect_time.hour
            usage = next_data.electricity - current.electricity
            
            if date_key not in daily_hourly_usage:
                daily_hourly_usage[date_key] = {}
            if hour not in daily_hourly_usage[date_key]:
                daily_hourly_usage[date_key][hour] = []
            daily_hourly_usage[date_key][hour].append(usage)
        
        # 统计每个小时的平均用电量
        hour_avg_usage = {h: [] for h in range(24)}
        for date, hourly in daily_hourly_usage.items():
            for hour, usages in hourly.items():
                avg = sum(usages) / len(usages) if usages else 0
                hour_avg_usage[hour].append(avg)
        
        # 计算每个小时的总体平均
        hour_overall_avg = {}
        for hour, usages in hour_avg_usage.items():
            hour_overall_avg[hour] = sum(usages) / len(usages) if usages else 0
        
        # 找出高峰时段（用电量最高的3个小时）
        peak_hours = sorted(hour_overall_avg.items(), key=lambda x: x[1], reverse=True)[:3]
        peak_hour_list = [h for h, _ in peak_hours]
        
        # 3. 生成未来7天的预测
        predictions = []
        for day_offset in range(predict_days):
            predict_date = current_time + timedelta(days=day_offset + 1)
            weekday = predict_date.weekday()
            
            # 预测当天的总用电量（基于历史同星期几的平均值）
            predicted_usage = weekday_avg.get(weekday, 0)
            
            # 预测高峰时段
            peak_periods = []
            for hour in peak_hour_list:
                peak_usage = hour_overall_avg.get(hour, 0)
                peak_periods.append({
                    "hour": hour,
                    "time_range": f"{hour:02d}:00-{(hour+1):02d}:00",
                    "predicted_usage": round(peak_usage, 2)
                })
            
            predictions.append({
                "date": predict_date.strftime("%Y-%m-%d"),
                "weekday": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][weekday],
                "predicted_total_usage": round(predicted_usage, 2),
                "peak_periods": peak_periods,
                "confidence": "高" if len(weekday_usage[weekday]) >= 10 else "中" if len(weekday_usage[weekday]) >= 5 else "低"
            })
        
        return {
            "success": True,
            "region_name": region_name,
            "predict_days": predict_days,
            "history_days": history_days,
            "predictions": predictions,
            "analysis_summary": {
                "data_points": len(daily_usage),
                "avg_daily_usage": round(sum(weekday_avg.values()) / len(weekday_avg), 2) if weekday_avg else 0,
                "typical_peak_hours": [f"{h:02d}:00-{(h+1):02d}:00" for h in peak_hour_list]
            }
        }
    
    @staticmethod
    def export_data(user_id, export_type="usage", region_id=None, start_date=None, end_date=None, format_type="csv"):
        """
        数据导出（包含下级片区的递归汇总）
        :param user_id: 导出用户ID
        :param export_type: 导出类型（usage/bill）
        :param region_id: 片区ID（可选）
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param format_type: 格式类型（csv/excel）
        :return: 导出的数据内容
        """
        # 1. 时间范围设置
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # 2. 片区管理员权限校验
        # 片区管理员只能导出其管辖的片区的数据
        user = User.query.get(user_id)
        if not user:
            raise BusinessException("用户不存在", 404)
        
        # 获取该用户管辖的所有片区（manager_id == user_id）
        managed_regions = Region.query.filter_by(manager_id=user_id).all()
        if not managed_regions:
            raise BusinessException("用户未管辖任何片区", 403)
        
        managed_region_ids = [r.id for r in managed_regions]
        
        # 如果指定了region_id，验证该片区是否在管辖范围内
        if region_id and region_id not in managed_region_ids:
            raise BusinessException("无权访问该片区的数据", 403)
        
        # 3. 导出数据
        # 如果不指定region_id，则使用第一个管辖片区
        if not region_id:
            region_id = managed_region_ids[0]
        
        # 获取该片区及所有子片区的ID列表
        all_region_ids = AnalyzeServices._get_all_sub_regions(region_id)
        
        if export_type == "usage":
            data = AnalyzeServices._export_usage_data(all_region_ids, start_date, end_date)
            headers = ["电表编号", "用户姓名", "片区", "日期", "总用电量(度)", "高峰用电量(度)", "低谷用电量(度)", "数据类型"]
        elif export_type == "bill":
            data = AnalyzeServices._export_bill_data(all_region_ids, start_date, end_date)
            headers = ["账单ID", "电表编号", "用户姓名", "片区", "账单月份", "总用电量(度)", "总金额(元)", "状态", "到期日", "支付时间"]
        else:
            raise BusinessException("不支持的导出类型", 400)
        
        # 4. 格式化数据
        if format_type == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(headers)
            writer.writerows(data)
            content = output.getvalue()
            output.close()
            
            return {
                "success": True,
                "format": "csv",
                "filename": f"{export_type}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv",
                "content": content,
                "record_count": len(data)
            }
        else:
            # Excel格式（返回数据，由前端或其他服务处理）
            return {
                "success": True,
                "format": "excel",
                "filename": f"{export_type}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx",
                "headers": headers,
                "data": data,
                "record_count": len(data)
            }
    
    @staticmethod
    def _export_usage_data(region_ids, start_date, end_date):
        """导出用电数据（支持多个片区）"""
        query = db.session.query(
            Meter.meter_code,
            User.real_name,
            Region.region_name,
            UsageData.usage_time,
            UsageData.total_electricity,
            UsageData.peak_electricity,
            UsageData.valley_electricity,
            UsageData.usage_type
        ).join(
            Meter, UsageData.meter_id == Meter.id
        ).join(
            User, Meter.user_id == User.id
        ).join(
            Region, Meter.region_id == Region.id
        ).filter(
            UsageData.usage_time >= start_date,
            UsageData.usage_time <= end_date
        )
        
        if region_ids:
            query = query.filter(Meter.region_id.in_(region_ids))
        
        results = query.all()
        
        data = []
        for row in results:
            data.append([
                row.meter_code,
                row.real_name or "未设置",
                row.region_name,
                row.usage_time.strftime("%Y-%m-%d"),
                round(row.total_electricity, 2),
                round(row.peak_electricity or 0, 2),
                round(row.valley_electricity or 0, 2),
                "日" if row.usage_type == UsageType.DAY else "月"
            ])
        
        return data
    
    @staticmethod
    def _export_bill_data(region_ids, start_date, end_date):
        """导出账单数据（支持多个片区）"""
        query = db.session.query(
            Bill.id,
            Meter.meter_code,
            User.real_name,
            Region.region_name,
            Bill.bill_month,
            Bill.total_electricity,
            Bill.total_amount,
            Bill.status,
            Bill.due_date,
            Bill.payment_time
        ).join(
            Meter, Bill.meter_id == Meter.id
        ).join(
            User, Bill.user_id == User.id
        ).join(
            Region, Meter.region_id == Region.id
        ).filter(
            Bill.bill_month >= start_date,
            Bill.bill_month <= end_date
        )
        
        if region_ids:
            query = query.filter(Meter.region_id.in_(region_ids))
        
        results = query.all()
        
        data = []
        for row in results:
            data.append([
                row.id,
                row.meter_code,
                row.real_name or "未设置",
                row.region_name,
                row.bill_month.strftime("%Y-%m"),
                round(row.total_electricity, 2),
                round(row.total_amount, 2),
                row.status.name,
                row.due_date.strftime("%Y-%m-%d"),
                row.payment_time.strftime("%Y-%m-%d %H:%M:%S") if row.payment_time else "未支付"
            ])
        
        return data

