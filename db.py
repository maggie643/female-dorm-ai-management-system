import sqlite3
import os
import time

DB_PATH = "dorm_management.db"

def init_db():
    if os.path.exists(DB_PATH):
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE fault_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type_name TEXT NOT NULL UNIQUE,
            priority_level TEXT NOT NULL,
            handling_time_minutes INTEGER NOT NULL,
            skill_required TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE repair_staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            skills TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'available',
            current_order_id INTEGER
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE work_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_no TEXT NOT NULL UNIQUE,
            building TEXT NOT NULL,
            room TEXT NOT NULL,
            fault_desc TEXT NOT NULL,
            fault_type TEXT,
            priority_level TEXT,
            handling_suggestion TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            assigned_staff_id INTEGER,
            submit_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            assigned_time TIMESTAMP,
            completed_time TIMESTAMP,
            estimated_time TIMESTAMP,
            FOREIGN KEY (assigned_staff_id) REFERENCES repair_staff(id)
        )
    ''')
    
    default_fault_types = [
        ("空调故障", "P0", 30, "空调维修"),
        ("热水器故障", "P0", 60, "水电维修"),
        ("断电/跳闸", "P0", 15, "电气维修"),
        ("水管漏水", "P0", 30, "水电维修"),
        ("门锁故障", "P1", 60, "五金维修"),
        ("插座损坏", "P1", 30, "电气维修"),
        ("卫生间堵塞", "P1", 60, "管道维修"),
        ("灯具损坏", "P2", 120, "电气维修"),
        ("网络故障", "P2", 120, "网络维护"),
        ("其他故障", "P2", 240, "综合维修")
    ]
    cursor.executemany('INSERT INTO fault_types VALUES (NULL, ?, ?, ?, ?)', default_fault_types)
    
    default_staff = [
        ("张师傅", "13800138001", "空调维修,水电维修", "available", None),
        ("李师傅", "13800138002", "电气维修,五金维修", "available", None),
        ("王师傅", "13800138003", "管道维修,水电维修", "available", None),
        ("赵师傅", "13800138004", "网络维护,电气维修", "available", None),
        ("刘师傅", "13800138005", "综合维修,五金维修", "available", None)
    ]
    cursor.executemany('INSERT INTO repair_staff VALUES (NULL, ?, ?, ?, ?, ?)', default_staff)
    
    conn.commit()
    conn.close()

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def create_work_order(building, room, fault_desc, fault_type, priority_level, handling_suggestion):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    order_no = f"WO{int(time.time() * 1000)}{os.getpid()}"
    
    priority_map = {"P0": 30, "P1": 60, "P2": 120}
    handling_time = priority_map.get(priority_level, 120)
    
    cursor.execute('''
        INSERT INTO work_orders (order_no, building, room, fault_desc, fault_type, 
                                priority_level, handling_suggestion, estimated_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, DATETIME('now', ?))
    ''', (order_no, building, room, fault_desc, fault_type, priority_level, 
          handling_suggestion, f"+{handling_time} minutes"))
    
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return order_id, order_no

def assign_work_order(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT fault_type, priority_level FROM work_orders WHERE id = ?', (order_id,))
    order = cursor.fetchone()
    if not order:
        conn.close()
        return None
    
    fault_type, priority_level = order
    
    cursor.execute('SELECT skill_required FROM fault_types WHERE type_name = ?', (fault_type,))
    skill_row = cursor.fetchone()
    required_skill = skill_row[0] if skill_row else ""
    
    primary_skill = required_skill.split(",")[0] if required_skill else ""
    
    cursor.execute('''
        SELECT id, name, skills FROM repair_staff 
        WHERE status = 'available' AND skills LIKE ?
        ORDER BY CASE WHEN skills LIKE ? THEN 0 ELSE 1 END, id
        LIMIT 1
    ''', (f'%{primary_skill}%', f'%{required_skill}%'))
    
    staff = cursor.fetchone()
    
    if staff:
        staff_id, staff_name, _ = staff
        cursor.execute('UPDATE repair_staff SET status = "busy", current_order_id = ? WHERE id = ?', (order_id, staff_id))
        cursor.execute('UPDATE work_orders SET status = "processing", assigned_staff_id = ?, assigned_time = CURRENT_TIMESTAMP WHERE id = ?', (staff_id, order_id))
        conn.commit()
        result = {"staff_id": staff_id, "staff_name": staff_name}
    else:
        cursor.execute('''
            SELECT id, name FROM repair_staff 
            WHERE status = 'available' 
            ORDER BY id LIMIT 1
        ''')
        fallback_staff = cursor.fetchone()
        if fallback_staff:
            staff_id, staff_name = fallback_staff
            cursor.execute('UPDATE repair_staff SET status = "busy", current_order_id = ? WHERE id = ?', (order_id, staff_id))
            cursor.execute('UPDATE work_orders SET status = "processing", assigned_staff_id = ?, assigned_time = CURRENT_TIMESTAMP WHERE id = ?', (staff_id, order_id))
            conn.commit()
            result = {"staff_id": staff_id, "staff_name": staff_name}
        else:
            result = None
    
    conn.close()
    return result

def complete_work_order(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT assigned_staff_id FROM work_orders WHERE id = ?', (order_id,))
    staff_id = cursor.fetchone()
    
    if staff_id:
        cursor.execute('UPDATE repair_staff SET status = "available", current_order_id = NULL WHERE id = ?', (staff_id[0],))
        cursor.execute('UPDATE work_orders SET status = "completed", completed_time = CURRENT_TIMESTAMP WHERE id = ?', (order_id,))
        conn.commit()
    
    conn.close()

def get_work_orders(status=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if status:
        cursor.execute('''
            SELECT wo.id, wo.order_no, wo.building, wo.room, wo.fault_desc, wo.fault_type, 
                   wo.priority_level, wo.status, wo.submit_time, wo.assigned_time, wo.completed_time,
                   rs.name as staff_name, rs.phone as staff_phone
            FROM work_orders wo
            LEFT JOIN repair_staff rs ON wo.assigned_staff_id = rs.id
            WHERE wo.status = ?
            ORDER BY wo.submit_time DESC
        ''', (status,))
    else:
        cursor.execute('''
            SELECT wo.id, wo.order_no, wo.building, wo.room, wo.fault_desc, wo.fault_type, 
                   wo.priority_level, wo.status, wo.submit_time, wo.assigned_time, wo.completed_time,
                   rs.name as staff_name, rs.phone as staff_phone
            FROM work_orders wo
            LEFT JOIN repair_staff rs ON wo.assigned_staff_id = rs.id
            ORDER BY wo.submit_time DESC
        ''')
    
    orders = cursor.fetchall()
    conn.close()
    
    return orders

def get_pending_orders():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT wo.id, wo.order_no, wo.building, wo.room, wo.fault_desc, wo.fault_type, 
               wo.priority_level, wo.status, wo.submit_time, wo.estimated_time
        FROM work_orders wo
        WHERE wo.status = 'pending'
        ORDER BY CASE wo.priority_level WHEN 'P0' THEN 0 WHEN 'P1' THEN 1 ELSE 2 END, wo.submit_time
    ''')
    
    orders = cursor.fetchall()
    conn.close()
    
    return orders

def get_overdue_orders():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT wo.id, wo.order_no, wo.building, wo.room, wo.fault_desc, wo.fault_type, 
               wo.priority_level, wo.status, wo.submit_time, wo.estimated_time,
               rs.name as staff_name
        FROM work_orders wo
        LEFT JOIN repair_staff rs ON wo.assigned_staff_id = rs.id
        WHERE wo.status IN ('pending', 'processing') AND wo.estimated_time < CURRENT_TIMESTAMP
        ORDER BY wo.priority_level, wo.estimated_time
    ''')
    
    orders = cursor.fetchall()
    conn.close()
    
    return orders

def get_work_order_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM work_orders')
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM work_orders WHERE status = "completed"')
    completed = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM work_orders WHERE status = "processing"')
    processing = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM work_orders WHERE status = "pending"')
    pending = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT wo.fault_type, COUNT(*) as count
        FROM work_orders wo
        GROUP BY wo.fault_type
        ORDER BY count DESC
    ''')
    fault_type_stats = cursor.fetchall()
    
    cursor.execute('''
        SELECT wo.priority_level, COUNT(*) as count
        FROM work_orders wo
        GROUP BY wo.priority_level
        ORDER BY wo.priority_level
    ''')
    priority_stats = cursor.fetchall()
    
    cursor.execute('''
        SELECT strftime('%Y-%m-%d', wo.submit_time) as date, COUNT(*) as count
        FROM work_orders wo
        GROUP BY date
        ORDER BY date DESC
        LIMIT 7
    ''')
    daily_stats = cursor.fetchall()
    
    cursor.execute('''
        SELECT wo.building, COUNT(*) as count
        FROM work_orders wo
        GROUP BY wo.building
        ORDER BY count DESC
    ''')
    building_stats = cursor.fetchall()
    
    conn.close()
    
    return {
        "total": total,
        "completed": completed,
        "processing": processing,
        "pending": pending,
        "fault_type_stats": fault_type_stats,
        "priority_stats": priority_stats,
        "daily_stats": daily_stats,
        "building_stats": building_stats
    }

def get_repair_staff():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, name, phone, skills, status, current_order_id FROM repair_staff')
    staff = cursor.fetchall()
    
    conn.close()
    return staff

init_db()