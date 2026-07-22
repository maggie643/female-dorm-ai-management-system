import json
from db import add_notification, get_notifications, mark_notification_read, get_unread_count

def send_order_notification(order_no, status, school, building, room, staff_name=None, staff_phone=None):
    if status == "pending":
        add_notification(
            recipient_role="admin",
            title=f"新工单待处理",
            content=f"学校：{school}\n楼栋：{building}\n房间：{room}\n工单编号：{order_no}\n请及时分配维修人员",
            order_no=order_no
        )
        add_notification(
            recipient_role="staff",
            title=f"新报修工单",
            content=f"学校：{school}\n楼栋：{building}\n房间：{room}\n工单编号：{order_no}",
            order_no=order_no
        )
    elif status == "processing":
        add_notification(
            recipient_role="student",
            title=f"工单已分配",
            content=f"您的报修工单已分配给维修人员\n工单编号：{order_no}\n学校：{school}\n楼栋：{building}\n房间：{room}\n维修人员：{staff_name}\n联系电话：{staff_phone}",
            order_no=order_no
        )
        add_notification(
            recipient_role="admin",
            title=f"工单已分配",
            content=f"工单 {order_no} 已分配给 {staff_name}",
            order_no=order_no
        )
    elif status == "completed":
        add_notification(
            recipient_role="student",
            title=f"工单已完成",
            content=f"您的报修工单已完成\n工单编号：{order_no}\n学校：{school}\n楼栋：{building}\n房间：{room}\n请评价服务质量",
            order_no=order_no
        )
        add_notification(
            recipient_role="admin",
            title=f"工单已完成",
            content=f"工单 {order_no} 已完成",
            order_no=order_no
        )

def send_alert_notification(order_no, alert_type, school, building, room):
    if alert_type == "timeout":
        add_notification(
            recipient_role="admin",
            title=f"⚠️ 工单超时预警",
            content=f"工单 {order_no} 即将超时\n学校：{school}\n楼栋：{building}\n房间：{room}\n请尽快处理",
            order_no=order_no
        )

def get_role_notifications(role):
    notifications = get_notifications(role)
    return [
        {
            "id": n[0],
            "title": n[1],
            "content": n[2],
            "order_no": n[3],
            "status": n[4],
            "created_at": n[5]
        }
        for n in notifications
    ]

def get_unread_notifications_count(role):
    return get_unread_count(role)

def mark_all_read(role):
    notifications = get_notifications(role)
    for n in notifications:
        if n[4] == "unread":
            mark_notification_read(n[0])