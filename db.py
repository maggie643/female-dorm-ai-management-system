import sqlite3
import os
import time

DB_PATH = "dorm_management.db"

def init_db():
    if os.path.exists(DB_PATH):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('ALTER TABLE work_orders ADD COLUMN rating INTEGER')
        except:
            pass
        try:
            cursor.execute('ALTER TABLE work_orders ADD COLUMN feedback TEXT')
        except:
            pass
        try:
            cursor.execute('ALTER TABLE work_orders ADD COLUMN school TEXT')
        except:
            pass
        try:
            cursor.execute('ALTER TABLE schools ADD COLUMN dorm_access_time TEXT')
        except:
            pass
        try:
            cursor.execute('ALTER TABLE schools ADD COLUMN electricity_rules TEXT')
        except:
            pass
        try:
            cursor.execute('ALTER TABLE schools ADD COLUMN max_power_watts INTEGER')
        except:
            pass
        try:
            cursor.execute('ALTER TABLE schools ADD COLUMN hygiene_check_day TEXT')
        except:
            pass
        try:
            cursor.execute('ALTER TABLE schools ADD COLUMN hygiene_check_time TEXT')
        except:
            pass
        try:
            cursor.execute('ALTER TABLE schools ADD COLUMN visitor_rules TEXT')
        except:
            pass
        try:
            cursor.execute('ALTER TABLE schools ADD COLUMN other_rules TEXT')
        except:
            pass
        try:
            cursor.execute('''
                CREATE TABLE buildings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    school_id INTEGER,
                    building_name TEXT NOT NULL,
                    total_floors INTEGER,
                    rooms_per_floor INTEGER,
                    room_number_format TEXT,
                    FOREIGN KEY (school_id) REFERENCES schools(id)
                )
            ''')
        except:
            pass
        try:
            cursor.execute('''
                CREATE TABLE notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recipient_role TEXT NOT NULL,
                    recipient_id INTEGER,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    order_no TEXT,
                    status TEXT NOT NULL DEFAULT 'unread',
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (order_no) REFERENCES work_orders(order_no)
                )
            ''')
        except:
            pass
        try:
            cursor.execute('''
                CREATE TABLE audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operator_role TEXT NOT NULL,
                    operator_name TEXT,
                    action TEXT NOT NULL,
                    target_type TEXT,
                    target_id INTEGER,
                    target_data TEXT,
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT
                )
            ''')
        except:
            pass
        conn.commit()
        conn.close()
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE schools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_name TEXT NOT NULL UNIQUE,
            contact_name TEXT,
            contact_phone TEXT,
            address TEXT,
            dorm_access_time TEXT,
            electricity_rules TEXT,
            max_power_watts INTEGER,
            hygiene_check_day TEXT,
            hygiene_check_time TEXT,
            visitor_rules TEXT,
            other_rules TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE buildings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER,
            building_name TEXT NOT NULL,
            total_floors INTEGER,
            rooms_per_floor INTEGER,
            room_number_format TEXT,
            FOREIGN KEY (school_id) REFERENCES schools(id)
        )
    ''')
    
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
            school TEXT,
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
            rating INTEGER,
            feedback TEXT,
            FOREIGN KEY (assigned_staff_id) REFERENCES repair_staff(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient_role TEXT NOT NULL,
            recipient_id INTEGER,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            order_no TEXT,
            status TEXT NOT NULL DEFAULT 'unread',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_no) REFERENCES work_orders(order_no)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operator_role TEXT NOT NULL,
            operator_name TEXT,
            action TEXT NOT NULL,
            target_type TEXT,
            target_id INTEGER,
            target_data TEXT,
            timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT
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
    
    default_schools = [
        ("北京大学", "王主任", "13900139001", "北京市海淀区颐和园路5号", 
         "周一至周五 6:00-23:00，周末 6:00-23:30", "禁止使用大功率电器", 800, 
         "周三", "下午", "访客需在宿管处登记身份证信息", ""),
        ("清华大学", "李主任", "13900139002", "北京市海淀区清华园1号",
         "周一至周五 6:00-23:00，周末 6:00-23:30", "禁止使用大功率电器", 800,
         "周四", "下午", "访客需在宿管处登记", ""),
        ("复旦大学", "张主任", "13900139003", "上海市杨浦区邯郸路220号",
         "周一至周五 6:00-23:00，周末 6:00-23:30", "禁止使用大功率电器", 800,
         "周三", "上午", "访客需登记", ""),
        ("上海交通大学", "刘主任", "13900139004", "上海市闵行区东川路800号",
         "周一至周五 6:00-23:00，周末 6:00-23:30", "禁止使用大功率电器", 800,
         "周二", "下午", "访客需登记", ""),
        ("浙江大学", "陈主任", "13900139005", "杭州市西湖区余杭塘路866号",
         "周一至周五 6:00-23:00，周末 6:00-23:30", "禁止使用大功率电器", 800,
         "周三", "下午", "访客需登记", ""),
        ("南京大学", "赵主任", "13900139006", "南京市鼓楼区汉口路22号",
         "周一至周五 6:00-23:00，周末 6:00-23:30", "禁止使用大功率电器", 800,
         "周四", "下午", "访客需登记", ""),
        ("武汉大学", "周主任", "13900139007", "武汉市武昌区珞珈山16号",
         "周一至周五 6:00-23:00，周末 6:00-23:30", "禁止使用大功率电器", 800,
         "周五", "下午", "访客需登记", ""),
        ("四川大学", "吴主任", "13900139008", "成都市武侯区一环路南一段24号",
         "周一至周五 6:00-23:00，周末 6:00-23:30", "禁止使用大功率电器", 800,
         "周三", "上午", "访客需登记", ""),
        ("中山大学", "徐主任", "13900139009", "广州市海珠区新港西路135号",
         "周一至周五 6:00-23:00，周末 6:00-23:30", "禁止使用大功率电器", 800,
         "周二", "下午", "访客需登记", ""),
        ("西安交通大学", "孙主任", "13900139010", "西安市碑林区咸宁西路28号",
         "周一至周五 6:00-23:00，周末 6:00-23:30", "禁止使用大功率电器", 800,
         "周四", "下午", "访客需登记", ""),
        ("香港大学", "陈教授", "852-28592111", "香港薄扶林道",
         "周一至周五 7:00-22:30，周末 7:00-23:00", "禁止使用超过1000W电器", 1000,
         "周二", "下午", "访客需出示有效证件", ""),
        ("香港中文大学", "王教授", "852-39437777", "香港沙田",
         "周一至周五 7:00-22:30，周末 7:00-23:00", "禁止使用超过1000W电器", 1000,
         "周三", "下午", "访客需出示有效证件", ""),
        ("香港科技大学", "李教授", "852-23586000", "香港清水湾",
         "周一至周五 7:00-22:30，周末 7:00-23:00", "禁止使用超过1000W电器", 1000,
         "周四", "下午", "访客需出示有效证件", ""),
        ("香港理工大学", "张教授", "852-27666666", "香港红磡",
         "周一至周五 7:00-22:30，周末 7:00-23:00", "禁止使用超过1000W电器", 1000,
         "周五", "下午", "访客需出示有效证件", ""),
        ("澳门大学", "刘教授", "+853-88228888", "澳门氹仔",
         "周一至周五 6:30-23:00，周末 6:30-23:30", "禁止使用大功率电器", 800,
         "周五", "下午", "访客需提前预约", ""),
        ("澳门科技大学", "赵教授", "+853-88972888", "澳门氹仔",
         "周一至周五 6:30-23:00，周末 6:30-23:30", "禁止使用大功率电器", 800,
         "周三", "下午", "访客需提前预约", ""),
        ("澳门理工大学", "孙教授", "+853-28567866", "澳门高美士街",
         "周一至周五 6:30-23:00，周末 6:30-23:30", "禁止使用大功率电器", 800,
         "周四", "下午", "访客需提前预约", "")
    ]
    cursor.executemany('''
        INSERT INTO schools VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', default_schools)
    
    cursor.execute('SELECT id FROM schools WHERE school_name = "北京大学"')
    pk_id = cursor.fetchone()[0]
    default_buildings_pk = [
        (pk_id, "A栋", 6, 20, "A0101-A0620"),
        (pk_id, "B栋", 6, 20, "B0101-B0620"),
        (pk_id, "C栋", 8, 24, "C0101-C0824"),
        (pk_id, "D栋", 6, 20, "D0101-D0620"),
        (pk_id, "E栋", 8, 24, "E0101-E0824")
    ]
    cursor.executemany('INSERT INTO buildings VALUES (NULL, ?, ?, ?, ?, ?)', default_buildings_pk)
    
    cursor.execute('SELECT id FROM schools WHERE school_name = "清华大学"')
    qh_id = cursor.fetchone()[0]
    default_buildings_qh = [
        (qh_id, "紫荆1号楼", 12, 24, "Z10101-Z11224"),
        (qh_id, "紫荆2号楼", 12, 24, "Z20101-Z21224"),
        (qh_id, "紫荆3号楼", 12, 24, "Z30101-Z31224"),
        (qh_id, "紫荆4号楼", 12, 24, "Z40101-Z41224"),
        (qh_id, "紫荆5号楼", 12, 24, "Z50101-Z51224")
    ]
    cursor.executemany('INSERT INTO buildings VALUES (NULL, ?, ?, ?, ?, ?)', default_buildings_qh)
    
    cursor.execute('SELECT id FROM schools WHERE school_name = "复旦大学"')
    fd_id = cursor.fetchone()[0]
    default_buildings_fd = [
        (fd_id, "东区1号楼", 6, 20, "E10101-E10620"),
        (fd_id, "东区2号楼", 6, 20, "E20101-E20620"),
        (fd_id, "西区1号楼", 8, 24, "W10101-W10824"),
        (fd_id, "西区2号楼", 8, 24, "W20101-W20824")
    ]
    cursor.executemany('INSERT INTO buildings VALUES (NULL, ?, ?, ?, ?, ?)', default_buildings_fd)
    
    cursor.execute('SELECT id FROM schools WHERE school_name = "上海交通大学"')
    sjtu_id = cursor.fetchone()[0]
    default_buildings_sjtu = [
        (sjtu_id, "东1号楼", 6, 20, "D10101-D10620"),
        (sjtu_id, "东2号楼", 6, 20, "D20101-D20620"),
        (sjtu_id, "西1号楼", 8, 24, "X10101-X10824"),
        (sjtu_id, "西2号楼", 8, 24, "X20101-X20824")
    ]
    cursor.executemany('INSERT INTO buildings VALUES (NULL, ?, ?, ?, ?, ?)', default_buildings_sjtu)
    
    cursor.execute('SELECT id FROM schools WHERE school_name = "浙江大学"')
    zju_id = cursor.fetchone()[0]
    default_buildings_zju = [
        (zju_id, "紫金港1号楼", 10, 24, "ZJ10101-ZJ11024"),
        (zju_id, "紫金港2号楼", 10, 24, "ZJ20101-ZJ21024"),
        (zju_id, "玉泉1号楼", 6, 20, "YQ10101-YQ10620"),
        (zju_id, "玉泉2号楼", 6, 20, "YQ20101-YQ20620")
    ]
    cursor.executemany('INSERT INTO buildings VALUES (NULL, ?, ?, ?, ?, ?)', default_buildings_zju)
    
    cursor.execute('SELECT id FROM schools WHERE school_name = "香港大学"')
    hku_id = cursor.fetchone()[0]
    default_buildings_hku = [
        (hku_id, "莫理斯堂", 8, 16, "M101-M816"),
        (hku_id, "圣约翰堂", 8, 16, "SJ101-SJ816"),
        (hku_id, "利玛窦堂", 6, 12, "RM101-RM612"),
        (hku_id, "何东夫人堂", 6, 12, "HD101-HD612")
    ]
    cursor.executemany('INSERT INTO buildings VALUES (NULL, ?, ?, ?, ?, ?)', default_buildings_hku)
    
    cursor.execute('SELECT id FROM schools WHERE school_name = "香港中文大学"')
    cuhk_id = cursor.fetchone()[0]
    default_buildings_cuhk = [
        (cuhk_id, "和声书院", 10, 20, "HS101-HS1020"),
        (cuhk_id, "逸夫书院", 10, 20, "YF101-YF1020"),
        (cuhk_id, "崇基学院", 8, 18, "CK101-CK818"),
        (cuhk_id, "新亚书院", 8, 18, "XY101-XY818")
    ]
    cursor.executemany('INSERT INTO buildings VALUES (NULL, ?, ?, ?, ?, ?)', default_buildings_cuhk)
    
    cursor.execute('SELECT id FROM schools WHERE school_name = "澳门大学"')
    umac_id = cursor.fetchone()[0]
    default_buildings_umac = [
        (umac_id, "东亚楼", 8, 16, "EA101-EA816"),
        (umac_id, "横琴楼", 10, 20, "HQ101-HQ1020"),
        (umac_id, "友谊楼", 8, 16, "YY101-YY816"),
        (umac_id, "思源楼", 6, 12, "SY101-SY612")
    ]
    cursor.executemany('INSERT INTO buildings VALUES (NULL, ?, ?, ?, ?, ?)', default_buildings_umac)
    
    default_orders = [
        ("WO202607010001", "北京大学", "A栋", "A0201", "空调不制冷，室内温度很高", "空调故障", "P0", "建议立即安排空调维修师傅上门检查", "completed", 1, "2026-07-01 08:30:00", "2026-07-01 08:45:00", "2026-07-01 10:30:00", "2026-07-01 09:30:00", 5, "维修及时，师傅技术很好"),
        ("WO202607010002", "北京大学", "A栋", "A0305", "卫生间漏水严重", "水管漏水", "P0", "建议立即安排水电维修师傅处理", "completed", 3, "2026-07-01 09:00:00", "2026-07-01 09:15:00", "2026-07-01 11:00:00", "2026-07-01 11:00:00", 4, "维修效果不错"),
        ("WO202607010003", "北京大学", "B栋", "B0512", "宿舍断电了", "断电/跳闸", "P0", "建议检查配电箱和电路", "processing", 2, "2026-07-01 10:00:00", "2026-07-01 10:10:00", None, "2026-07-01 11:10:00", None, None),
        ("WO202607010004", "清华大学", "紫荆1号楼", "Z10203", "热水器不加热", "热水器故障", "P0", "建议安排维修师傅检查热水器", "completed", 1, "2026-07-01 11:00:00", "2026-07-01 11:15:00", "2026-07-01 13:00:00", "2026-07-01 12:00:00", 5, "师傅很专业"),
        ("WO202607010005", "清华大学", "紫荆2号楼", "Z20315", "门锁坏了，打不开", "门锁故障", "P1", "建议安排五金维修师傅更换锁芯", "processing", 2, "2026-07-01 12:00:00", "2026-07-01 12:30:00", None, "2026-07-01 13:30:00", None, None),
        ("WO202607010006", "复旦大学", "东区1号楼", "E10308", "灯具不亮", "灯具损坏", "P2", "建议更换灯泡", "completed", 2, "2026-07-01 14:00:00", "2026-07-01 14:30:00", "2026-07-01 15:30:00", "2026-07-01 16:30:00", 3, "还行"),
        ("WO202607020001", "北京大学", "C栋", "C0418", "网络无法连接", "网络故障", "P2", "建议检查网络设备", "pending", None, "2026-07-02 08:00:00", None, None, "2026-07-02 10:00:00", None, None),
        ("WO202607020002", "上海交通大学", "东1号楼", "D10205", "插座没电", "插座损坏", "P1", "建议更换插座", "processing", 2, "2026-07-02 09:00:00", "2026-07-02 09:30:00", None, "2026-07-02 10:30:00", None, None),
        ("WO202607020003", "浙江大学", "紫金港1号楼", "ZJ10512", "卫生间堵塞", "卫生间堵塞", "P1", "建议安排管道维修", "completed", 3, "2026-07-02 10:00:00", "2026-07-02 10:30:00", "2026-07-02 12:00:00", "2026-07-02 12:00:00", 4, "维修干净"),
        ("WO202607020004", "香港大学", "莫理斯堂", "M305", "空调漏水", "空调故障", "P0", "建议立即检查空调", "completed", 1, "2026-07-02 11:00:00", "2026-07-02 11:15:00", "2026-07-02 13:00:00", "2026-07-02 12:00:00", 5, "非常满意"),
        ("WO202607020005", "香港中文大学", "和声书院", "HS512", "断电跳闸", "断电/跳闸", "P0", "建议检查电路", "processing", 2, "2026-07-02 12:00:00", "2026-07-02 12:10:00", None, "2026-07-02 13:10:00", None, None),
        ("WO202607020006", "澳门大学", "东亚楼", "EA408", "热水器故障", "热水器故障", "P0", "建议维修热水器", "pending", None, "2026-07-02 13:00:00", None, None, "2026-07-02 15:00:00", None, None),
        ("WO202607030001", "北京大学", "D栋", "D0115", "门锁生锈", "门锁故障", "P2", "建议更换门锁", "pending", None, "2026-07-03 08:30:00", None, None, "2026-07-03 10:30:00", None, None),
        ("WO202607030002", "清华大学", "紫荆3号楼", "Z30618", "网络不稳定", "网络故障", "P2", "建议检查路由器", "processing", 4, "2026-07-03 09:00:00", "2026-07-03 09:30:00", None, "2026-07-03 11:30:00", None, None),
        ("WO202607030003", "南京大学", "1号楼", "10203", "空调异响", "空调故障", "P1", "建议检查空调风扇", "completed", 1, "2026-07-03 10:00:00", "2026-07-03 10:30:00", "2026-07-03 12:00:00", "2026-07-03 11:00:00", 4, "异响消失"),
        ("WO202607030004", "武汉大学", "桂园1号楼", "GY10305", "水管老化漏水", "水管漏水", "P0", "建议更换水管", "completed", 3, "2026-07-03 11:00:00", "2026-07-03 11:15:00", "2026-07-03 13:30:00", "2026-07-03 13:30:00", 5, "维修彻底"),
        ("WO202607030005", "四川大学", "望江楼1号楼", "WJ10412", "灯具闪烁", "灯具损坏", "P2", "建议更换灯管", "pending", None, "2026-07-03 14:00:00", None, None, "2026-07-03 16:00:00", None, None),
        ("WO202607030006", "中山大学", "东校区1号楼", "DX10208", "插座松动", "插座损坏", "P1", "建议紧固或更换插座", "processing", 2, "2026-07-03 15:00:00", "2026-07-03 15:30:00", None, "2026-07-03 17:30:00", None, None),
        ("WO202607040001", "西安交通大学", "兴庆1号楼", "XQ10515", "热水器漏水", "热水器故障", "P0", "建议立即维修", "processing", 1, "2026-07-04 08:00:00", "2026-07-04 08:15:00", None, "2026-07-04 09:15:00", None, None),
        ("WO202607040002", "香港科技大学", "学生宿舍1号", "ST10305", "空调不启动", "空调故障", "P0", "建议检查电源和遥控器", "completed", 1, "2026-07-04 09:00:00", "2026-07-04 09:15:00", "2026-07-04 11:00:00", "2026-07-04 10:00:00", 5, "快速修复"),
        ("WO202607040003", "香港理工大学", "红磡宿舍", "HK0212", "卫生间下水道堵塞", "卫生间堵塞", "P1", "建议通下水道", "completed", 3, "2026-07-04 10:00:00", "2026-07-04 10:30:00", "2026-07-04 12:00:00", "2026-07-04 12:00:00", 4, "效果好"),
        ("WO202607040004", "澳门科技大学", "研究生宿舍", "YS0308", "网络断线", "网络故障", "P2", "建议联系网络中心", "pending", None, "2026-07-04 11:00:00", None, None, "2026-07-04 13:00:00", None, None),
        ("WO202607040005", "澳门理工大学", "校本部宿舍", "XB0215", "空调制冷效果差", "空调故障", "P1", "建议清洗空调滤网", "processing", 1, "2026-07-04 14:00:00", "2026-07-04 14:30:00", None, "2026-07-04 16:30:00", None, None),
        ("WO202607050001", "北京大学", "E栋", "E0620", "走廊灯不亮", "灯具损坏", "P2", "建议更换灯泡", "completed", 2, "2026-07-05 08:00:00", "2026-07-05 08:30:00", "2026-07-05 09:30:00", "2026-07-05 10:30:00", 3, "正常"),
        ("WO202607050002", "清华大学", "紫荆4号楼", "Z40412", "门禁系统故障", "其他故障", "P1", "建议联系门禁管理部门", "pending", None, "2026-07-05 09:00:00", None, None, "2026-07-05 11:00:00", None, None),
        ("WO202607050003", "复旦大学", "西区1号楼", "W10508", "热水器温度不够", "热水器故障", "P1", "建议调节温度或维修", "processing", 1, "2026-07-05 10:00:00", "2026-07-05 10:30:00", None, "2026-07-05 12:30:00", None, None),
        ("WO202607060001", "上海交通大学", "西1号楼", "X20315", "墙面渗水", "其他故障", "P1", "建议检查外墙防水", "pending", None, "2026-07-06 08:00:00", None, None, "2026-07-06 10:00:00", None, None),
        ("WO202607060002", "浙江大学", "玉泉1号楼", "YQ10205", "空调遥控器失灵", "空调故障", "P2", "建议更换遥控器电池", "completed", 1, "2026-07-06 09:00:00", "2026-07-06 09:30:00", "2026-07-06 10:00:00", "2026-07-06 11:00:00", 5, "简单解决"),
        ("WO202607070001", "北京大学", "A栋", "A0108", "门锁反锁", "门锁故障", "P0", "建议立即上门开锁", "completed", 2, "2026-07-07 08:00:00", "2026-07-07 08:10:00", "2026-07-07 08:45:00", "2026-07-07 09:10:00", 5, "非常及时"),
        ("WO202607070002", "香港大学", "圣约翰堂", "SJ203", "厨房下水道堵塞", "卫生间堵塞", "P1", "建议通下水道", "processing", 3, "2026-07-07 09:00:00", "2026-07-07 09:30:00", None, "2026-07-07 11:30:00", None, None)
    ]
    cursor.executemany('''
        INSERT INTO work_orders (order_no, school, building, room, fault_desc, fault_type, 
                                priority_level, handling_suggestion, status, assigned_staff_id, 
                                submit_time, assigned_time, completed_time, estimated_time, rating, feedback)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', default_orders)
    
    conn.commit()
    conn.close()

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def add_school(school_name, contact_name="", contact_phone="", address="", 
               dorm_access_time="", electricity_rules="", max_power_watts=800,
               hygiene_check_day="周三", hygiene_check_time="下午", visitor_rules="", other_rules=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO schools 
        (school_name, contact_name, contact_phone, address, dorm_access_time, 
         electricity_rules, max_power_watts, hygiene_check_day, hygiene_check_time, 
         visitor_rules, other_rules)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (school_name, contact_name, contact_phone, address, dorm_access_time, 
          electricity_rules, max_power_watts, hygiene_check_day, hygiene_check_time, 
          visitor_rules, other_rules))
    
    school_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return school_id

def get_school_by_name(school_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM schools WHERE school_name = ?', (school_name,))
    result = cursor.fetchone()
    conn.close()
    return result

def get_school_config(school_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT dorm_access_time, electricity_rules, max_power_watts, 
               hygiene_check_day, hygiene_check_time, visitor_rules, other_rules
        FROM schools WHERE school_name = ?
    ''', (school_name,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return {
            "dorm_access_time": result[0] or "6:00-23:00",
            "electricity_rules": result[1] or "禁止使用大功率电器",
            "max_power_watts": result[2] or 800,
            "hygiene_check_day": result[3] or "周三",
            "hygiene_check_time": result[4] or "下午",
            "visitor_rules": result[5] or "访客需在宿管处登记",
            "other_rules": result[6] or ""
        }
    return None

def get_schools():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT school_name FROM schools ORDER BY school_name')
    schools = [s[0] for s in cursor.fetchall()]
    conn.close()
    return schools

def get_school_contact(school_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT contact_name, contact_phone, address FROM schools WHERE school_name = ?', (school_name,))
    result = cursor.fetchone()
    conn.close()
    return result

def add_building(school_id, building_name, total_floors, rooms_per_floor, room_number_format):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO buildings (school_id, building_name, total_floors, rooms_per_floor, room_number_format)
        VALUES (?, ?, ?, ?, ?)
    ''', (school_id, building_name, total_floors, rooms_per_floor, room_number_format))
    
    conn.commit()
    conn.close()

def get_buildings_by_school(school_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT b.building_name, b.total_floors, b.rooms_per_floor, b.room_number_format
        FROM buildings b
        JOIN schools s ON b.school_id = s.id
        WHERE s.school_name = ?
        ORDER BY b.building_name
    ''', (school_name,))
    
    buildings = cursor.fetchall()
    conn.close()
    return buildings

def get_building_names_by_school(school_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT b.building_name
        FROM buildings b
        JOIN schools s ON b.school_id = s.id
        WHERE s.school_name = ?
        ORDER BY b.building_name
    ''', (school_name,))
    
    names = [b[0] for b in cursor.fetchall()]
    conn.close()
    return names

def get_building_info(school_name, building_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT b.total_floors, b.rooms_per_floor, b.room_number_format
        FROM buildings b
        JOIN schools s ON b.school_id = s.id
        WHERE s.school_name = ? AND b.building_name = ?
    ''', (school_name, building_name))
    
    result = cursor.fetchone()
    conn.close()
    return result

def create_work_order(school, building, room, fault_desc, fault_type, priority_level, handling_suggestion):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    order_no = f"WO{int(time.time() * 1000)}{os.getpid()}"
    
    priority_map = {"P0": 30, "P1": 60, "P2": 120}
    handling_time = priority_map.get(priority_level, 120)
    
    cursor.execute('''
        INSERT INTO work_orders (order_no, school, building, room, fault_desc, fault_type, 
                                priority_level, handling_suggestion, estimated_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, DATETIME('now', ?))
    ''', (order_no, school, building, room, fault_desc, fault_type, priority_level, 
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
        SELECT id, name, skills, phone FROM repair_staff 
        WHERE status = 'available' AND skills LIKE ?
        ORDER BY CASE WHEN skills LIKE ? THEN 0 ELSE 1 END, id
        LIMIT 1
    ''', (f'%{primary_skill}%', f'%{required_skill}%'))
    
    staff = cursor.fetchone()
    
    if staff:
        staff_id, staff_name, staff_skills, staff_phone = staff
        cursor.execute('UPDATE repair_staff SET status = "busy", current_order_id = ? WHERE id = ?', (order_id, staff_id))
        cursor.execute('UPDATE work_orders SET status = "processing", assigned_staff_id = ?, assigned_time = CURRENT_TIMESTAMP WHERE id = ?', (staff_id, order_id))
        conn.commit()
        result = {"staff_id": staff_id, "staff_name": staff_name, "staff_phone": staff_phone}
    else:
        cursor.execute('''
            SELECT id, name, phone FROM repair_staff 
            WHERE status = 'available' 
            ORDER BY id LIMIT 1
        ''')
        fallback_staff = cursor.fetchone()
        if fallback_staff:
            staff_id, staff_name, staff_phone = fallback_staff
            cursor.execute('UPDATE repair_staff SET status = "busy", current_order_id = ? WHERE id = ?', (order_id, staff_id))
            cursor.execute('UPDATE work_orders SET status = "processing", assigned_staff_id = ?, assigned_time = CURRENT_TIMESTAMP WHERE id = ?', (staff_id, order_id))
            conn.commit()
            result = {"staff_id": staff_id, "staff_name": staff_name, "staff_phone": staff_phone}
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

def add_order_rating(order_id, rating, feedback):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('UPDATE work_orders SET rating = ?, feedback = ? WHERE id = ?', (rating, feedback, order_id))
    conn.commit()
    conn.close()

def check_duplicate_repair(building, room, fault_type):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, order_no, submit_time, status 
        FROM work_orders 
        WHERE building = ? AND room = ? AND fault_type = ? 
        AND submit_time > DATETIME('now', '-7 days')
        ORDER BY submit_time DESC
        LIMIT 3
    ''', (building, room, fault_type))
    
    duplicates = cursor.fetchall()
    conn.close()
    
    return duplicates

def search_orders(school=None, building=None, room=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = '''
        SELECT wo.id, wo.order_no, wo.school, wo.building, wo.room, wo.fault_desc, wo.fault_type, 
               wo.priority_level, wo.status, wo.submit_time, wo.assigned_time, wo.completed_time,
               rs.name as staff_name, rs.phone as staff_phone
        FROM work_orders wo
        LEFT JOIN repair_staff rs ON wo.assigned_staff_id = rs.id
        WHERE 1=1
    '''
    params = []
    
    if school:
        query += ' AND wo.school LIKE ?'
        params.append(f'%{school}%')
    if building:
        query += ' AND wo.building LIKE ?'
        params.append(f'%{building}%')
    if room:
        query += ' AND wo.room LIKE ?'
        params.append(f'%{room}%')
    
    query += ' ORDER BY wo.submit_time DESC'
    
    cursor.execute(query, params)
    orders = cursor.fetchall()
    conn.close()
    
    return orders

def get_work_orders(status=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if status:
        cursor.execute('''
            SELECT wo.id, wo.order_no, wo.school, wo.building, wo.room, wo.fault_desc, wo.fault_type, 
                   wo.priority_level, wo.status, wo.submit_time, wo.assigned_time, wo.completed_time,
                   rs.name as staff_name, rs.phone as staff_phone
            FROM work_orders wo
            LEFT JOIN repair_staff rs ON wo.assigned_staff_id = rs.id
            WHERE wo.status = ?
            ORDER BY wo.submit_time DESC
        ''', (status,))
    else:
        cursor.execute('''
            SELECT wo.id, wo.order_no, wo.school, wo.building, wo.room, wo.fault_desc, wo.fault_type, 
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
        SELECT wo.id, wo.order_no, wo.school, wo.building, wo.room, wo.fault_desc, wo.fault_type, 
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
        SELECT wo.id, wo.order_no, wo.school, wo.building, wo.room, wo.fault_desc, wo.fault_type, 
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
    
    cursor.execute('''
        SELECT wo.school, COUNT(*) as count
        FROM work_orders wo
        GROUP BY wo.school
        ORDER BY count DESC
    ''')
    school_stats = cursor.fetchall()
    
    avg_rating = 0
    cursor.execute('SELECT AVG(rating) FROM work_orders WHERE rating IS NOT NULL')
    rating_result = cursor.fetchone()
    if rating_result[0]:
        avg_rating = round(rating_result[0], 1)
    
    conn.close()
    
    return {
        "total": total,
        "completed": completed,
        "processing": processing,
        "pending": pending,
        "fault_type_stats": fault_type_stats,
        "priority_stats": priority_stats,
        "daily_stats": daily_stats,
        "building_stats": building_stats,
        "school_stats": school_stats,
        "avg_rating": avg_rating
    }

def get_repair_staff():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, name, phone, skills, status, current_order_id FROM repair_staff')
    staff = cursor.fetchall()
    
    conn.close()
    return staff

def add_notification(recipient_role, title, content, order_no=None, recipient_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO notifications (recipient_role, recipient_id, title, content, order_no)
        VALUES (?, ?, ?, ?, ?)
    ''', (recipient_role, recipient_id, title, content, order_no))
    
    conn.commit()
    conn.close()

def get_notifications(recipient_role, recipient_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = 'SELECT id, title, content, order_no, status, created_at FROM notifications WHERE recipient_role = ?'
    params = [recipient_role]
    
    if recipient_id is not None:
        query += ' AND recipient_id = ?'
        params.append(recipient_id)
    
    query += ' ORDER BY created_at DESC'
    
    cursor.execute(query, params)
    notifications = cursor.fetchall()
    
    conn.close()
    return notifications

def mark_notification_read(notification_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('UPDATE notifications SET status = "read" WHERE id = ?', (notification_id,))
    conn.commit()
    conn.close()

def get_unread_count(recipient_role, recipient_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = 'SELECT COUNT(*) FROM notifications WHERE recipient_role = ? AND status = "unread"'
    params = [recipient_role]
    
    if recipient_id is not None:
        query += ' AND recipient_id = ?'
        params.append(recipient_id)
    
    cursor.execute(query, params)
    count = cursor.fetchone()[0]
    
    conn.close()
    return count

def add_audit_log(operator_role, operator_name, action, target_type=None, target_id=None, target_data=None, ip_address=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO audit_logs (operator_role, operator_name, action, target_type, target_id, target_data, ip_address)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (operator_role, operator_name, action, target_type, target_id, target_data, ip_address))
    
    conn.commit()
    conn.close()

def get_audit_logs(operator_role=None, action=None, target_type=None, start_date=None, end_date=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = 'SELECT id, operator_role, operator_name, action, target_type, target_id, target_data, timestamp, ip_address FROM audit_logs WHERE 1=1'
    params = []
    
    if operator_role:
        query += ' AND operator_role = ?'
        params.append(operator_role)
    if action:
        query += ' AND action LIKE ?'
        params.append(f'%{action}%')
    if target_type:
        query += ' AND target_type = ?'
        params.append(target_type)
    if start_date:
        query += ' AND timestamp >= ?'
        params.append(f'{start_date} 00:00:00')
    if end_date:
        query += ' AND timestamp <= ?'
        params.append(f'{end_date} 23:59:59')
    
    query += ' ORDER BY timestamp DESC'
    
    cursor.execute(query, params)
    logs = cursor.fetchall()
    
    conn.close()
    return logs

def get_audit_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM audit_logs')
    total = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT operator_role, COUNT(*) as count
        FROM audit_logs
        GROUP BY operator_role
    ''')
    role_stats = cursor.fetchall()
    
    cursor.execute('''
        SELECT action, COUNT(*) as count
        FROM audit_logs
        GROUP BY action
        ORDER BY count DESC
        LIMIT 10
    ''')
    action_stats = cursor.fetchall()
    
    cursor.execute('''
        SELECT strftime('%Y-%m-%d', timestamp) as date, COUNT(*) as count
        FROM audit_logs
        GROUP BY date
        ORDER BY date DESC
        LIMIT 7
    ''')
    daily_stats = cursor.fetchall()
    
    conn.close()
    
    return {
        "total": total,
        "role_stats": role_stats,
        "action_stats": action_stats,
        "daily_stats": daily_stats
    }

init_db()