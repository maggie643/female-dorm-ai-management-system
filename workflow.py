from db import create_work_order, assign_work_order, complete_work_order, \
    get_work_orders, get_pending_orders, get_overdue_orders, get_work_order_stats, get_repair_staff, \
    add_order_rating, check_duplicate_repair, search_orders, get_schools, get_school_contact, \
    add_school, get_school_by_name, get_school_config, add_building, get_buildings_by_school, \
    get_building_names_by_school, get_building_info
from ai_engine import judge_dorm_fault, smart_qa, generate_weekly_report

def submit_repair_request(school, building, room, fault_desc):
    ai_result = judge_dorm_fault(building, room, fault_desc)
    
    duplicates = check_duplicate_repair(building, room, ai_result["fault_type"])
    
    order_id, order_no = create_work_order(
        school=school,
        building=building,
        room=room,
        fault_desc=fault_desc,
        fault_type=ai_result["fault_type"],
        priority_level=ai_result["priority_level"],
        handling_suggestion=ai_result["handling_suggestion"]
    )
    
    assigned_staff = assign_work_order(order_id)
    
    school_contact = get_school_contact(school) if school else None
    
    return {
        "order_id": order_id,
        "order_no": order_no,
        "fault_type": ai_result["fault_type"],
        "priority_level": ai_result["priority_level"],
        "handling_suggestion": ai_result["handling_suggestion"],
        "assigned_staff": assigned_staff,
        "status": "processing" if assigned_staff else "pending",
        "duplicates": duplicates,
        "school_contact": school_contact
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

def submit_rating(order_id, rating, feedback):
    add_order_rating(order_id, rating, feedback)

def get_stats():
    return get_work_order_stats()

def get_staff_list():
    return get_repair_staff()

def get_school_list():
    return get_schools()

def search_by_building_room(school=None, building=None, room=None):
    return search_orders(school, building, room)

def ask_question(question, school_config=None):
    return smart_qa(question, school_config)

def generate_report(stats_data):
    return generate_weekly_report(stats_data)

def register_school(school_name, contact_name="", contact_phone="", address="",
                    dorm_access_time="", electricity_rules="", max_power_watts=800,
                    hygiene_check_day="周三", hygiene_check_time="下午", visitor_rules="", other_rules=""):
    school_id = add_school(school_name, contact_name, contact_phone, address,
                           dorm_access_time, electricity_rules, max_power_watts,
                           hygiene_check_day, hygiene_check_time, visitor_rules, other_rules)
    return school_id

def get_school_info(school_name):
    return get_school_by_name(school_name)

def get_school_settings(school_name):
    return get_school_config(school_name)

def add_building_to_school(school_name, building_name, total_floors, rooms_per_floor, room_number_format):
    school = get_school_by_name(school_name)
    if school:
        school_id = school[0]
        add_building(school_id, building_name, total_floors, rooms_per_floor, room_number_format)
        return True
    return False

def get_school_buildings(school_name):
    return get_buildings_by_school(school_name)

def get_school_building_names(school_name):
    return get_building_names_by_school(school_name)

def get_school_building_detail(school_name, building_name):
    return get_building_info(school_name, building_name)