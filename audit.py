import json
from db import add_audit_log, get_audit_logs, get_audit_stats

def log_order_action(operator_role, operator_name, action, order_no, order_data=None):
    target_data = json.dumps(order_data) if order_data else None
    add_audit_log(
        operator_role=operator_role,
        operator_name=operator_name,
        action=action,
        target_type="work_order",
        target_data=target_data
    )

def log_school_action(operator_role, operator_name, action, school_name):
    add_audit_log(
        operator_role=operator_role,
        operator_name=operator_name,
        action=action,
        target_type="school",
        target_data=school_name
    )

def log_staff_action(operator_role, operator_name, action, staff_name):
    add_audit_log(
        operator_role=operator_role,
        operator_name=operator_name,
        action=action,
        target_type="staff",
        target_data=staff_name
    )

def log_ai_call(operator_role, operator_name, prompt, response):
    target_data = json.dumps({"prompt": prompt[:100], "response": response[:100]})
    add_audit_log(
        operator_role=operator_role,
        operator_name=operator_name,
        action="AI调用",
        target_type="ai_service",
        target_data=target_data
    )

def get_audit_records(operator_role=None, action=None, target_type=None, start_date=None, end_date=None):
    logs = get_audit_logs(operator_role, action, target_type, start_date, end_date)
    return [
        {
            "id": l[0],
            "operator_role": l[1],
            "operator_name": l[2],
            "action": l[3],
            "target_type": l[4],
            "target_id": l[5],
            "target_data": l[6],
            "timestamp": l[7],
            "ip_address": l[8]
        }
        for l in logs
    ]

def get_audit_summary():
    return get_audit_stats()