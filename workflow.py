from db import create_work_order, assign_work_order, complete_work_order, \
    get_work_orders, get_pending_orders, get_overdue_orders, get_work_order_stats, get_repair_staff
from ai_engine import judge_dorm_fault

def submit_repair_request(building, room, fault_desc):
    ai_result = judge_dorm_fault(building, room, fault_desc)
    
    order_id, order_no = create_work_order(
        building=building,
        room=room,
        fault_desc=fault_desc,
        fault_type=ai_result["fault_type"],
        priority_level=ai_result["priority_level"],
        handling_suggestion=ai_result["handling_suggestion"]
    )
    
    assigned_staff = assign_work_order(order_id)
    
    return {
        "order_id": order_id,
        "order_no": order_no,
        "fault_type": ai_result["fault_type"],
        "priority_level": ai_result["priority_level"],
        "handling_suggestion": ai_result["handling_suggestion"],
        "assigned_staff": assigned_staff,
        "status": "processing" if assigned_staff else "pending"
    }

def get_all_orders():
    return get_work_orders()

def get_orders_by_status(status):
    return get_work_orders(status)

def get_pending():
    return get_pending_orders()

def get_overdue():
    return get_overdue_orders()

def mark_complete(order_id):
    complete_work_order(order_id)

def get_stats():
    return get_work_order_stats()

def get_staff_list():
    return get_repair_staff()