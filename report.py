import csv
import json
from datetime import datetime
from db import get_work_orders, get_work_order_stats, get_repair_staff, get_schools

def export_work_orders_csv(file_path, school=None, status=None):
    orders = get_work_orders(status)
    
    with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow([
            "工单编号", "学校", "楼栋", "房间", "故障描述", "故障类型",
            "紧急等级", "状态", "处理人员", "处理人员电话",
            "提交时间", "分配时间", "完成时间"
        ])
        
        for order in orders:
            if school and school != order[2]:
                continue
            writer.writerow([
                order[1], order[2], order[3], order[4], order[5], order[6],
                order[7], order[8], order[12] or "", order[13] or "",
                order[9] or "", order[10] or "", order[11] or ""
            ])
    
    return file_path

def export_daily_report(file_path):
    stats = get_work_order_stats()
    
    report = {
        "report_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {
            "total_orders": stats["total"],
            "completed": stats["completed"],
            "processing": stats["processing"],
            "pending": stats["pending"],
            "completion_rate": round(stats["completed"] / stats["total"] * 100, 2) if stats["total"] > 0 else 0
        },
        "fault_type_distribution": dict(stats["fault_type_stats"]),
        "priority_distribution": dict(stats["priority_stats"]),
        "daily_trend": dict(stats["daily_stats"]),
        "building_stats": dict(stats["building_stats"]),
        "school_stats": dict(stats["school_stats"]),
        "avg_rating": stats["avg_rating"]
    }
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    return file_path, report

def generate_monthly_report(month=None):
    if not month:
        month = datetime.now().strftime("%Y-%m")
    
    orders = get_work_orders()
    filtered_orders = [o for o in orders if o[9] and month in o[9]]
    
    stats = {
        "month": month,
        "total_orders": len(filtered_orders),
        "completed_orders": len([o for o in filtered_orders if o[8] == "completed"]),
        "processing_orders": len([o for o in filtered_orders if o[8] == "processing"]),
        "pending_orders": len([o for o in filtered_orders if o[8] == "pending"]),
        "fault_type_distribution": {},
        "school_distribution": {}
    }
    
    for order in filtered_orders:
        fault_type = order[6]
        stats["fault_type_distribution"][fault_type] = stats["fault_type_distribution"].get(fault_type, 0) + 1
        
        school = order[2]
        stats["school_distribution"][school] = stats["school_distribution"].get(school, 0) + 1
    
    stats["completion_rate"] = round(stats["completed_orders"] / stats["total_orders"] * 100, 2) if stats["total_orders"] > 0 else 0
    
    return stats

def export_staff_report(file_path):
    staff = get_repair_staff()
    
    with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "姓名", "电话", "技能", "状态", "当前工单"])
        
        for s in staff:
            writer.writerow([
                s[0], s[1], s[2], s[3], s[4], s[5] or ""
            ])
    
    return file_path

def export_school_report(file_path):
    schools = get_schools()
    
    with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow([
            "学校名称", "负责人", "联系电话", "地址",
            "门禁时间", "用电规定", "最大功率",
            "卫生检查日", "卫生检查时间", "访客规定"
        ])
        
        for school in schools:
            writer.writerow([
                school[1], school[2], school[3], school[4],
                school[5] or "", school[6] or "", school[7] or "",
                school[8] or "", school[9] or "", school[10] or ""
            ])
    
    return file_path