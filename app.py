import gradio as gr
import matplotlib.pyplot as plt
import csv
import io
from workflow import submit_repair_request, get_all_orders, get_overdue, mark_complete, get_stats, get_staff_list, submit_rating, search_by_building_room, get_school_list, ask_question, generate_report, register_school, get_school_settings, add_building_to_school, get_school_buildings, get_school_building_names, get_school_building_detail

plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def get_schools_for_dropdown():
    schools = get_school_list()
    return schools if schools else []

def submit_request(school, building, room, fault_desc):
    if not school or not building or not room or not fault_desc:
        return "请填写完整的报修信息", None, None
    
    try:
        result = submit_repair_request(school, building, room, fault_desc)
    except Exception as e:
        return f"AI模型加载中，请稍后重试。错误信息：{str(e)[:100]}", None, None
    
    duplicate_warning = ""
    if result["duplicates"]:
        duplicate_warning = "\n\n⚠️ 检测到近期重复报修：\n"
        for dup in result["duplicates"]:
            dup_id, dup_no, dup_time, dup_status = dup
            duplicate_warning += f"  - 工单{dup_no} ({dup_status}) - {dup_time}\n"
    
    staff_info = ""
    staff_phone = ""
    if result["assigned_staff"]:
        staff_info = f"\n\n已分配维修人员：{result['assigned_staff']['staff_name']}"
        staff_phone = f"\n联系电话：{result['assigned_staff']['staff_phone']}"
    
    priority_desc = {
        "P0": "🔴 紧急 - 立即处理",
        "P1": "🟠 重要 - 1小时内处理",
        "P2": "🟢 普通 - 2小时内处理"
    }
    
    student_feedback = f"""
📋 工单创建成功！

🏫 高校：{school}
📝 工单编号：{result['order_no']}
🔧 故障分类：{result['fault_type']}
🚨 紧急等级：{priority_desc.get(result['priority_level'], result['priority_level'])}
💡 处理建议：{result['handling_suggestion']}
📊 当前状态：{result['status']}{staff_info}{staff_phone}{duplicate_warning}
"""
    
    school_contact_info = ""
    if result["school_contact"]:
        contact_name, contact_phone, address = result["school_contact"]
        school_contact_info = f"""
📞 学校负责人：{contact_name}
📱 联系电话：{contact_phone}
📍 学校地址：{address}
"""
    
    return student_feedback, school_contact_info, result["order_no"]

def load_orders():
    orders = get_all_orders()
    if not orders:
        return []
    
    data = []
    for order in orders:
        id, order_no, school, building, room, fault_desc, fault_type, priority, status, submit_time, assigned_time, completed_time, staff_name, staff_phone = order
        priority_color = {"P0": "🔴", "P1": "🟠", "P2": "🟢"}.get(priority, "")
        data.append([id, order_no, school or "-", building, room, fault_desc, fault_type, f"{priority_color} {priority}", status, submit_time, staff_name or "未分配", staff_phone or "-"])
    
    return data

def load_overdue():
    orders = get_overdue()
    if not orders:
        return []
    
    data = []
    for order in orders:
        id, order_no, school, building, room, fault_desc, fault_type, priority, status, submit_time, estimated_time, staff_name = order
        priority_color = {"P0": "🔴", "P1": "🟠", "P2": "🟢"}.get(priority, "")
        data.append([id, order_no, school or "-", building, room, fault_desc, fault_type, f"{priority_color} {priority}", status, submit_time, staff_name or "未分配", "-"])
    
    return data

def search_orders(school, building, room):
    orders = search_by_building_room(school or None, building or None, room or None)
    if not orders:
        return []
    
    data = []
    for order in orders:
        id, order_no, school_val, building_val, room_val, fault_desc, fault_type, priority, status, submit_time, assigned_time, completed_time, staff_name, staff_phone = order
        priority_color = {"P0": "🔴", "P1": "🟠", "P2": "🟢"}.get(priority, "")
        data.append([id, order_no, school_val or "-", building_val, room_val, fault_desc, fault_type, f"{priority_color} {priority}", status, submit_time, staff_name or "未分配", staff_phone or "-"])
    
    return data

def get_my_orders(school, building, room):
    if not school and not building and not room:
        return []
    return search_orders(school, building, room)

def complete_order(order_id):
    if order_id:
        mark_complete(int(order_id))
        return f"工单 {order_id} 已标记为完成", int(order_id)
    return "请输入要完成的工单ID", None

def submit_order_rating(order_id, rating, feedback):
    if not order_id:
        return "请先完成一个工单", None
    submit_rating(order_id, rating, feedback)
    stars = "⭐" * rating + "☆" * (5 - rating)
    return f"感谢您的评价！\n\n评分：{stars}\n反馈：{feedback}", stars

def generate_stats():
    stats = get_stats()
    
    total = stats["total"]
    completed = stats["completed"]
    processing = stats["processing"]
    pending = stats["pending"]
    avg_rating = stats.get("avg_rating", 0)
    
    completion_rate = f"{completed/total*100:.1f}%" if total > 0 else "0%"
    
    summary = f"""
📊 工单统计概览

🏛️ 总工单数：{total}
✅ 已完成：{completed} ({completion_rate})
🔄 处理中：{processing}
⏳ 待分配：{pending}
⭐ 平均满意度：{'⭐' * int(avg_rating) if avg_rating > 0 else '-'} {avg_rating}分
"""
    
    if stats.get("school_stats") and stats["school_stats"]:
        summary += "\n🏫 高校报修统计：\n"
        for school_name, count in stats["school_stats"]:
            summary += f"   {school_name}: {count}单\n"
    
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    status_labels = ['已完成', '处理中', '待分配']
    status_values = [completed, processing, pending]
    colors = ['#4CAF50', '#2196F3', '#FF9800']
    axes[0].pie(status_values, labels=status_labels, autopct='%1.1f%%', startangle=90, colors=colors)
    axes[0].set_title('工单状态分布')
    
    if stats["priority_stats"]:
        priority_labels = [p[0] for p in stats["priority_stats"]]
        priority_values = [p[1] for p in stats["priority_stats"]]
        priority_colors = ['#F44336', '#FF9800', '#2196F3']
        axes[1].bar(priority_labels, priority_values, color=priority_colors)
        axes[1].set_title('紧急等级分布')
        axes[1].set_ylabel('工单数量')
    
    plt.tight_layout()
    
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    if stats["daily_stats"]:
        dates = [d[0] for d in stats["daily_stats"]][::-1]
        counts = [d[1] for d in stats["daily_stats"]][::-1]
        ax2.plot(dates, counts, marker='o', linestyle='-', color='#2196F3', linewidth=2)
        ax2.fill_between(dates, counts, alpha=0.3, color='#2196F3')
        ax2.set_title('近7日报修趋势')
        ax2.set_xlabel('日期')
        ax2.set_ylabel('报修数量')
        ax2.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    
    fig3, ax3 = plt.subplots(figsize=(10, 5))
    if stats["building_stats"]:
        buildings = [b[0] for b in stats["building_stats"]][:10]
        counts = [b[1] for b in stats["building_stats"]][:10]
        bars = ax3.barh(buildings, counts, color='#9C27B0')
        ax3.set_title('楼栋报修排行')
        ax3.set_xlabel('报修数量')
        ax3.set_ylabel('楼栋')
        for bar in bars:
            width = bar.get_width()
            ax3.text(width + 0.5, bar.get_y() + bar.get_height()/2, f'{int(width)}', va='center')
    
    plt.tight_layout()
    
    fig4, ax4 = plt.subplots(figsize=(10, 5))
    if stats["fault_type_stats"]:
        fault_types = [f[0] for f in stats["fault_type_stats"]]
        counts = [f[1] for f in stats["fault_type_stats"]]
        bars = ax4.bar(fault_types, counts, color='#FF5722')
        ax4.set_title('故障类型分布')
        ax4.set_xlabel('故障类型')
        ax4.set_ylabel('数量')
        ax4.tick_params(axis='x', rotation=45)
        for bar in bars:
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2, height + 0.5, f'{int(height)}', ha='center')
    
    plt.tight_layout()
    
    return summary, fig, fig2, fig3, fig4, stats

def load_staff():
    staff = get_staff_list()
    data = []
    for s in staff:
        id, name, phone, skills, status, current_order = s
        status_color = "🟢" if status == "available" else "🔴"
        data.append([id, name, phone, skills, f"{status_color} {status}", current_order or "-"])
    
    return data

def on_rating_change(rating):
    stars = "⭐" * rating + "☆" * (5 - rating)
    return stars

def export_orders_csv():
    orders = get_all_orders()
    if not orders:
        return None, "没有数据可导出"
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(["ID", "工单编号", "高校", "楼栋", "房间", "故障描述", "故障类型", "紧急等级", "状态", "提交时间", "分配时间", "完成时间", "处理人员", "联系电话"])
    
    for order in orders:
        id, order_no, school, building, room, fault_desc, fault_type, priority, status, submit_time, assigned_time, completed_time, staff_name, staff_phone = order
        writer.writerow([id, order_no, school or "-", building, room, fault_desc, fault_type, priority, status, submit_time, assigned_time or "-", completed_time or "-", staff_name or "-", staff_phone or "-"])
    
    output.seek(0)
    csv_data = output.getvalue()
    
    return gr.File(label="工单数据导出", value=csv_data, file_name="work_orders_export.csv"), "✅ 工单数据已导出，请下载CSV文件"

def chat_with_ai(question, school_name):
    if not question:
        return "请输入您的问题"
    
    try:
        school_config = get_school_settings(school_name) if school_name else None
        answer = ask_question(question, school_config)
        return answer
    except Exception as e:
        return f"AI助手暂不可用，请稍后重试。错误：{str(e)[:100]}"

def create_weekly_report():
    try:
        stats = get_stats()
        report = generate_report(stats)
        return report
    except Exception as e:
        return f"周报生成失败，请稍后重试。错误：{str(e)[:100]}"

def register_new_school(school_name, contact_name, contact_phone, address, dorm_access_time, 
                        electricity_rules, max_power_watts, hygiene_check_day, hygiene_check_time, 
                        visitor_rules, other_rules):
    if not school_name:
        return "请输入学校名称"
    
    try:
        register_school(school_name, contact_name, contact_phone, address,
                        dorm_access_time, electricity_rules, max_power_watts,
                        hygiene_check_day, hygiene_check_time, visitor_rules, other_rules)
        return f"✅ 学校「{school_name}」注册成功！"
    except Exception as e:
        return f"❌ 注册失败：{str(e)}"

def add_new_building(school_name, building_name, total_floors, rooms_per_floor, room_number_format):
    if not school_name or not building_name:
        return "请填写学校名称和楼栋名称"
    
    try:
        success = add_building_to_school(school_name, building_name, total_floors, rooms_per_floor, room_number_format)
        if success:
            return f"✅ 楼栋「{building_name}」添加成功！"
        else:
            return f"❌ 添加失败：学校「{school_name}」不存在，请先注册学校"
    except Exception as e:
        return f"❌ 添加失败：{str(e)}"

def load_buildings_for_school(school_name):
    if not school_name:
        return []
    return get_school_building_names(school_name)

def load_building_detail(school_name, building_name):
    if not school_name or not building_name:
        return ""
    
    info = get_school_building_detail(school_name, building_name)
    if info:
        total_floors, rooms_per_floor, room_format = info
        return f"""
🏢 楼栋信息

名称：{building_name}
总楼层：{total_floors}层
每层房间数：{rooms_per_floor}间
房间编号格式：{room_format}
总房间数：{total_floors * rooms_per_floor}间
"""
    return "未找到该楼栋信息"

def update_role_visibility(role):
    if role == "学生":
        return [
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=False)
        ]
    elif role == "宿管":
        return [
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=False)
        ]
    else:
        return [
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=True)
        ]

with gr.Blocks(title="高校宿舍AI运营管理系统") as demo:
    gr.Markdown("# 🤖 高校宿舍AI运营管理平台")
    gr.Markdown("### AI + 运营 / 「运营人，造自己的工具」")
    
    with gr.Row():
        role_dropdown = gr.Dropdown(["管理员", "宿管", "学生"], label="角色选择", value="管理员")
    
    with gr.Tabs() as tabs:
        with gr.TabItem("📝 报修提交") as tab_repair:
            gr.Markdown("## 提交报修申请")
            
            school_input = gr.Textbox(label="🏫 学校名称", placeholder="请输入学校名称，如：北京大学", value="")
            building_dropdown = gr.Dropdown([], label="🏢 宿舍楼栋")
            building_detail = gr.Textbox(label="楼栋详情", interactive=False)
            
            def on_school_change(school):
                buildings = load_buildings_for_school(school)
                if buildings:
                    return gr.update(choices=buildings, value=buildings[0]), ""
                return gr.update(choices=[], value=""), ""
            
            school_input.change(on_school_change, inputs=[school_input], outputs=[building_dropdown, building_detail])
            
            def on_building_change(school, building):
                return load_building_detail(school, building)
            
            building_dropdown.change(on_building_change, inputs=[school_input, building_dropdown], outputs=[building_detail])
            
            gr.Markdown("### 🚨 紧急等级说明")
            gr.Markdown("""
| 等级 | 标识 | 说明 | 处理时限 |
|------|------|------|----------|
| P0 | 🔴 | 紧急 | 30分钟内 |
| P1 | 🟠 | 重要 | 60分钟内 |
| P2 | 🟢 | 普通 | 120分钟内 |
""")
            
            with gr.Row():
                dorm_build_input = gr.Textbox(label="自定义楼栋（如未找到）", placeholder="A栋")
                dorm_room = gr.Textbox(label="宿舍房间号", placeholder="A0201")
            fault_text = gr.Textbox(label="故障详细描述", lines=4, placeholder="空调不制冷/卫生间漏水/插座没电等")
            submit_btn = gr.Button("AI智能识别并提交", variant="primary")
            
            gr.Markdown("### 📤 学生端反馈")
            student_result = gr.Textbox(label="报修结果", lines=10, interactive=False)
            
            gr.Markdown("### 📞 老师端反馈")
            teacher_result = gr.Textbox(label="学校联系人信息", lines=5, interactive=False)
            
            gr.Markdown("### 🔍 我的报修记录")
            with gr.Row():
                my_build = gr.Textbox(label="搜索楼栋", placeholder="输入楼栋")
                my_room = gr.Textbox(label="搜索房间", placeholder="输入房间号")
                my_search_btn = gr.Button("查询我的报修")
            my_orders_df = gr.Dataframe(headers=["ID", "工单编号", "高校", "楼栋", "房间", "故障描述", "故障类型", "紧急等级", "状态", "提交时间", "处理人员", "联系电话"], 
                                       interactive=False)
            
            def submit_with_school(building_dropdown_val, building_input_val, room, fault_desc):
                building = building_dropdown_val if building_dropdown_val else building_input_val
                return submit_request(school_input.value, building, room, fault_desc)
            
            submit_btn.click(submit_request, inputs=[school_input, building_dropdown, dorm_room, fault_text], 
                            outputs=[student_result, teacher_result])
            my_search_btn.click(get_my_orders, inputs=[school_input, my_build, my_room], outputs=my_orders_df)
        
        with gr.TabItem("📋 工单管理") as tab_management:
            gr.Markdown("## 工单列表")
            
            with gr.Row():
                search_school = gr.Textbox(label="搜索高校", placeholder="输入高校名称")
                search_build = gr.Textbox(label="搜索楼栋", placeholder="输入楼栋名称")
                search_room = gr.Textbox(label="搜索房间", placeholder="输入房间号")
                search_btn = gr.Button("搜索")
            
            with gr.Row():
                refresh_btn = gr.Button("刷新列表")
                overdue_btn = gr.Button("查看超时工单")
                export_btn = gr.Button("导出CSV")
            
            orders_df = gr.Dataframe(headers=["ID", "工单编号", "高校", "楼栋", "房间", "故障描述", "故障类型", "紧急等级", "状态", "提交时间", "处理人员", "联系电话"], 
                                     interactive=False)
            
            export_file = gr.File(label="导出文件", visible=False)
            export_result = gr.Textbox(label="导出结果", interactive=False)
            
            gr.Markdown("## 完成工单")
            with gr.Row():
                order_id_input = gr.Textbox(label="工单ID", placeholder="输入要完成的工单ID")
                complete_btn = gr.Button("标记完成")
            complete_result = gr.Textbox(label="操作结果")
            
            gr.Markdown("## ⭐ 服务评价")
            with gr.Row():
                rating_display = gr.Textbox(label="当前评分", value="⭐⭐⭐⭐⭐", interactive=False)
                rating_input = gr.Slider(1, 5, label="满意度评分", step=1, value=5)
            feedback_input = gr.Textbox(label="评价内容", placeholder="请输入您的评价")
            rating_btn = gr.Button("提交评价")
            rating_result = gr.Textbox(label="评价结果")
            
            rating_input.change(on_rating_change, inputs=[rating_input], outputs=[rating_display])
            refresh_btn.click(load_orders, outputs=orders_df)
            overdue_btn.click(load_overdue, outputs=orders_df)
            search_btn.click(search_orders, inputs=[search_school, search_build, search_room], outputs=orders_df)
            complete_btn.click(complete_order, inputs=[order_id_input], outputs=[complete_result])
            rating_btn.click(submit_order_rating, inputs=[order_id_input, rating_input, feedback_input], outputs=[rating_result])
            export_btn.click(export_orders_csv, outputs=[export_file, export_result])
            
            gr.Markdown("## 维修人员状态")
            staff_df = gr.Dataframe(headers=["ID", "姓名", "电话", "技能", "状态", "当前工单"], 
                                    interactive=False)
            refresh_btn.click(load_staff, outputs=staff_df)
        
        with gr.TabItem("📊 数据分析") as tab_analysis:
            gr.Markdown("## 数据统计分析")
            refresh_stats_btn = gr.Button("刷新统计数据")
            
            stats_text = gr.Textbox(label="统计概览", lines=12, interactive=False)
            
            gr.Markdown("### 工单分布")
            pie_img = gr.Plot(label="状态分布")
            
            gr.Markdown("### 报修趋势")
            trend_img = gr.Plot(label="近7日趋势")
            
            gr.Markdown("### 楼栋排行")
            building_img = gr.Plot(label="楼栋报修排行")
            
            gr.Markdown("### 故障类型")
            fault_img = gr.Plot(label="故障类型分布")
            
            refresh_stats_btn.click(generate_stats, outputs=[stats_text, pie_img, trend_img, building_img, fault_img])
        
        with gr.TabItem("🤖 AI智能助手") as tab_ai:
            gr.Markdown("## AI智能问答助手")
            gr.Markdown("💡 可以问关于宿舍管理规定、报修流程、安全须知等问题")
            
            ai_school_input = gr.Textbox(label="🏫 当前学校", placeholder="请输入学校名称以获取该校的管理规定", value="")
            chat_history = gr.Chatbot(height=400)
            chat_input = gr.Textbox(label="输入问题", placeholder="门禁时间是什么时候？/ 大功率电器有哪些？/ 报修流程是怎样的？")
            chat_btn = gr.Button("发送", variant="primary")
            
            def chat_with_history(message, history):
                answer = chat_with_ai(message, ai_school_input.value)
                history.append((message, answer))
                return "", history
            
            chat_btn.click(chat_with_history, inputs=[chat_input, chat_history], outputs=[chat_input, chat_history])
            
            gr.Markdown("## 📈 运营周报生成")
            gr.Markdown("一键生成专业的运营周报，包含工作概览、关键指标、改进建议等")
            
            report_btn = gr.Button("生成周报", variant="secondary")
            report_output = gr.Textbox(label="运营周报", lines=20, interactive=False)
            
            report_btn.click(create_weekly_report, outputs=report_output)
        
        with gr.TabItem("📊 运营仪表盘") as tab_dashboard:
            gr.Markdown("## 🎯 运营数据驾驶舱")
            refresh_dashboard_btn = gr.Button("刷新数据")
            
            with gr.Row():
                with gr.Column():
                    total_orders = gr.Number(label="🏛️ 总工单数", value=0)
                with gr.Column():
                    completed_rate = gr.Number(label="✅ 完成率(%)", value=0)
                with gr.Column():
                    avg_rating = gr.Number(label="⭐ 平均满意度", value=0)
                with gr.Column():
                    pending_count = gr.Number(label="⏳ 待分配", value=0)
            
            with gr.Row():
                with gr.Column():
                    fig_pie = gr.Plot(label="状态分布")
                with gr.Column():
                    fig_bar = gr.Plot(label="紧急等级")
            
            with gr.Row():
                fig_trend = gr.Plot(label="近7日趋势")
            
            with gr.Row():
                fig_building = gr.Plot(label="楼栋排行")
            
            def update_dashboard():
                stats = get_stats()
                total = stats["total"]
                completed = stats["completed"]
                processing = stats["processing"]
                pending = stats["pending"]
                avg_rating_val = stats.get("avg_rating", 0)
                completion_rate_val = (completed/total*100) if total > 0 else 0
                
                fig1, axes = plt.subplots(figsize=(6, 6))
                status_labels = ['已完成', '处理中', '待分配']
                status_values = [completed, processing, pending]
                colors = ['#4CAF50', '#2196F3', '#FF9800']
                axes.pie(status_values, labels=status_labels, autopct='%1.1f%%', startangle=90, colors=colors)
                axes.set_title('工单状态分布')
                plt.tight_layout()
                
                fig2, ax2 = plt.subplots(figsize=(6, 6))
                if stats["priority_stats"]:
                    priority_labels = [p[0] for p in stats["priority_stats"]]
                    priority_values = [p[1] for p in stats["priority_stats"]]
                    priority_colors = ['#F44336', '#FF9800', '#2196F3']
                    ax2.bar(priority_labels, priority_values, color=priority_colors)
                    ax2.set_title('紧急等级分布')
                    ax2.set_ylabel('工单数量')
                plt.tight_layout()
                
                fig3, ax3 = plt.subplots(figsize=(10, 4))
                if stats["daily_stats"]:
                    dates = [d[0] for d in stats["daily_stats"]][::-1]
                    counts = [d[1] for d in stats["daily_stats"]][::-1]
                    ax3.plot(dates, counts, marker='o', linestyle='-', color='#2196F3', linewidth=2)
                    ax3.fill_between(dates, counts, alpha=0.3, color='#2196F3')
                    ax3.set_title('近7日报修趋势')
                    ax3.set_xlabel('日期')
                    ax3.set_ylabel('报修数量')
                    ax3.tick_params(axis='x', rotation=45)
                plt.tight_layout()
                
                fig4, ax4 = plt.subplots(figsize=(10, 4))
                if stats["building_stats"]:
                    buildings = [b[0] for b in stats["building_stats"]][:8]
                    counts = [b[1] for b in stats["building_stats"]][:8]
                    bars = ax4.barh(buildings, counts, color='#9C27B0')
                    ax4.set_title('楼栋报修排行')
                    ax4.set_xlabel('报修数量')
                    ax4.set_ylabel('楼栋')
                    for bar in bars:
                        width = bar.get_width()
                        ax4.text(width + 0.5, bar.get_y() + bar.get_height()/2, f'{int(width)}', va='center')
                plt.tight_layout()
                
                return total, round(completion_rate_val, 1), avg_rating_val, pending, fig1, fig2, fig3, fig4
            
            refresh_dashboard_btn.click(update_dashboard, outputs=[total_orders, completed_rate, avg_rating, pending_count, fig_pie, fig_bar, fig_trend, fig_building])
        
        with gr.TabItem("🏫 学校管理") as tab_school:
            gr.Markdown("## 学校注册")
            gr.Markdown("管理员可以注册新学校并配置宿舍管理规定")
            
            with gr.Row():
                reg_school_name = gr.Textbox(label="学校名称", placeholder="请输入学校名称")
                reg_contact_name = gr.Textbox(label="负责人姓名", placeholder="负责人姓名")
                reg_contact_phone = gr.Textbox(label="联系电话", placeholder="联系电话")
            
            with gr.Row():
                reg_address = gr.Textbox(label="学校地址", placeholder="学校地址")
            
            gr.Markdown("### 宿舍管理规定")
            
            with gr.Row():
                reg_dorm_access = gr.Textbox(label="门禁时间", placeholder="如：周一至周五 6:00-23:00，周末 6:00-23:30", value="周一至周五 6:00-23:00，周末 6:00-23:30")
                reg_electricity = gr.Textbox(label="用电规定", placeholder="如：禁止使用大功率电器", value="禁止使用大功率电器")
            
            with gr.Row():
                reg_max_power = gr.Number(label="最大功率限制(W)", value=800)
                reg_hygiene_day = gr.Textbox(label="卫生检查日期", placeholder="如：周三", value="周三")
                reg_hygiene_time = gr.Textbox(label="卫生检查时间", placeholder="如：下午", value="下午")
            
            with gr.Row():
                reg_visitor = gr.Textbox(label="访客规定", placeholder="如：访客需在宿管处登记身份证信息", value="访客需在宿管处登记身份证信息")
                reg_other = gr.Textbox(label="其他规定", placeholder="其他管理规定")
            
            reg_result = gr.Textbox(label="注册结果", interactive=False)
            reg_btn = gr.Button("注册学校", variant="primary")
            
            reg_btn.click(register_new_school, inputs=[reg_school_name, reg_contact_name, reg_contact_phone, reg_address,
                                                      reg_dorm_access, reg_electricity, reg_max_power,
                                                      reg_hygiene_day, reg_hygiene_time, reg_visitor, reg_other],
                         outputs=[reg_result])
            
            gr.Markdown("---")
            gr.Markdown("## 添加楼栋")
            gr.Markdown("为已注册的学校添加宿舍楼栋")
            
            with gr.Row():
                add_school_name = gr.Textbox(label="学校名称", placeholder="请输入已注册的学校名称")
                add_building_name = gr.Textbox(label="楼栋名称", placeholder="如：A栋")
            
            with gr.Row():
                add_total_floors = gr.Number(label="总楼层数", value=6)
                add_rooms_per_floor = gr.Number(label="每层房间数", value=20)
                add_room_format = gr.Textbox(label="房间编号格式", placeholder="如：A0101-A0620", value="A0101-A0620")
            
            add_result = gr.Textbox(label="添加结果", interactive=False)
            add_btn = gr.Button("添加楼栋", variant="secondary")
            
            add_btn.click(add_new_building, inputs=[add_school_name, add_building_name, add_total_floors, 
                                                   add_rooms_per_floor, add_room_format],
                         outputs=[add_result])
    
    role_dropdown.change(update_role_visibility, inputs=[role_dropdown], outputs=[tab_repair, tab_management, tab_analysis, tab_ai, tab_dashboard, tab_school])

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0", 
        server_port=7860,
        theme=gr.themes.Soft(
            primary_hue="blue",
            secondary_hue="teal",
            neutral_hue="slate",
        )
    )