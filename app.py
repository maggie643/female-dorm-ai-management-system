import gradio as gr
import matplotlib.pyplot as plt
from workflow import submit_repair_request, get_all_orders, get_overdue, mark_complete, get_stats, get_staff_list, submit_rating, search_by_building_room

plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def submit_request(building, room, fault_desc):
    if not building or not room or not fault_desc:
        return "请填写完整的报修信息", None
    
    try:
        result = submit_repair_request(building, room, fault_desc)
    except Exception as e:
        return f"AI模型加载中，请稍后重试。错误信息：{str(e)[:100]}", None
    
    duplicate_warning = ""
    if result["duplicates"]:
        duplicate_warning = "\n\n⚠️ 检测到近期重复报修：\n"
        for dup in result["duplicates"]:
            dup_id, dup_no, dup_time, dup_status = dup
            duplicate_warning += f"  - 工单{dup_no} ({dup_status}) - {dup_time}\n"
    
    staff_info = ""
    if result["assigned_staff"]:
        staff_info = f"\n\n已分配维修人员：{result['assigned_staff']['staff_name']}"
    
    return f"""
工单创建成功！

工单编号：{result['order_no']}
故障分类：{result['fault_type']}
紧急等级：{result['priority_level']}
处理建议：{result['handling_suggestion']}
当前状态：{result['status']}{staff_info}{duplicate_warning}
""", result["order_no"]

def load_orders():
    orders = get_all_orders()
    if not orders:
        return []
    
    data = []
    for order in orders:
        id, order_no, building, room, fault_desc, fault_type, priority, status, submit_time, assigned_time, completed_time, staff_name, staff_phone = order
        data.append([id, order_no, building, room, fault_desc, fault_type, priority, status, submit_time, staff_name or "未分配"])
    
    return data

def load_overdue():
    orders = get_overdue()
    if not orders:
        return []
    
    data = []
    for order in orders:
        id, order_no, building, room, fault_desc, fault_type, priority, status, submit_time, estimated_time, staff_name = order
        data.append([id, order_no, building, room, fault_desc, fault_type, priority, status, submit_time, staff_name or "未分配"])
    
    return data

def search_orders(building, room):
    orders = search_by_building_room(building or None, room or None)
    if not orders:
        return []
    
    data = []
    for order in orders:
        id, order_no, building, room, fault_desc, fault_type, priority, status, submit_time, assigned_time, completed_time, staff_name, staff_phone = order
        data.append([id, order_no, building, room, fault_desc, fault_type, priority, status, submit_time, staff_name or "未分配"])
    
    return data

def complete_order(order_id):
    if order_id:
        mark_complete(int(order_id))
        return f"工单 {order_id} 已标记为完成", int(order_id)
    return "请输入要完成的工单ID", None

def submit_order_rating(order_id, rating, feedback):
    if not order_id:
        return "请先完成一个工单"
    submit_rating(order_id, rating, feedback)
    return f"感谢您的评价！评分：{rating}星，反馈：{feedback}"

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

总工单数：{total}
已完成：{completed} ({completion_rate})
处理中：{processing}
待分配：{pending}
平均满意度：{'⭐' * int(avg_rating) if avg_rating > 0 else '-'} {avg_rating}分
"""
    
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
    
    return summary, fig, fig2, fig3, fig4

def load_staff():
    staff = get_staff_list()
    data = []
    for s in staff:
        id, name, phone, skills, status, current_order = s
        data.append([id, name, phone, skills, status, current_order or "-"])
    
    return data

def update_visibility(role):
    admin_visible = role == "管理员"
    staff_visible = role in ["管理员", "宿管"]
    student_visible = role == "学生"
    
    return (
        gr.update(visible=admin_visible),  
        gr.update(visible=staff_visible),  
        gr.update(visible=True),          
        gr.update(visible=student_visible),
        gr.update(visible=admin_visible),  
        gr.update(visible=admin_visible),  
        gr.update(visible=admin_visible)   
    )

with gr.Blocks(title="高校宿舍AI报修管理系统") as demo:
    gr.Markdown("# 🏠 高校宿舍智能报修AI管理平台")
    
    with gr.Row():
        role_dropdown = gr.Dropdown(["管理员", "宿管", "学生"], label="角色选择", value="管理员")
    
    with gr.Tabs():
        with gr.TabItem("📝 报修提交"):
            gr.Markdown("## 提交报修申请")
            with gr.Row():
                dorm_build = gr.Textbox(label="宿舍楼栋", placeholder="A栋")
                dorm_room = gr.Textbox(label="宿舍房间号", placeholder="A0201")
            fault_text = gr.Textbox(label="故障详细描述", lines=4, placeholder="空调不制冷/卫生间漏水/插座没电等")
            submit_btn = gr.Button("AI智能识别并提交", variant="primary")
            result_out = gr.Textbox(label="提交结果", lines=8, interactive=False)
            submit_btn.click(submit_request, inputs=[dorm_build, dorm_room, fault_text], outputs=[result_out])
        
        with gr.TabItem("📋 工单管理"):
            gr.Markdown("## 工单列表")
            
            with gr.Row():
                search_build = gr.Textbox(label="搜索楼栋", placeholder="输入楼栋名称")
                search_room = gr.Textbox(label="搜索房间", placeholder="输入房间号")
                search_btn = gr.Button("搜索")
            
            with gr.Row():
                refresh_btn = gr.Button("刷新列表")
                overdue_btn = gr.Button("查看超时工单")
            
            orders_df = gr.Dataframe(headers=["ID", "工单编号", "楼栋", "房间", "故障描述", "故障类型", "紧急等级", "状态", "提交时间", "处理人员"], 
                                     interactive=False)
            
            gr.Markdown("## 完成工单")
            with gr.Row():
                order_id_input = gr.Textbox(label="工单ID", placeholder="输入要完成的工单ID")
                complete_btn = gr.Button("标记完成")
            complete_result = gr.Textbox(label="操作结果")
            
            gr.Markdown("## 服务评价")
            with gr.Row():
                rating_input = gr.Slider(1, 5, label="满意度评分", step=1, value=5)
                feedback_input = gr.Textbox(label="评价内容", placeholder="请输入您的评价")
                rating_btn = gr.Button("提交评价")
            rating_result = gr.Textbox(label="评价结果")
            
            refresh_btn.click(load_orders, outputs=orders_df)
            overdue_btn.click(load_overdue, outputs=orders_df)
            search_btn.click(search_orders, inputs=[search_build, search_room], outputs=orders_df)
            complete_btn.click(complete_order, inputs=[order_id_input], outputs=[complete_result])
            rating_btn.click(submit_order_rating, inputs=[order_id_input, rating_input, feedback_input], outputs=rating_result)
            
            gr.Markdown("## 维修人员状态")
            staff_df = gr.Dataframe(headers=["ID", "姓名", "电话", "技能", "状态", "当前工单"], 
                                    interactive=False)
            refresh_btn.click(load_staff, outputs=staff_df)
        
        with gr.TabItem("📊 数据分析"):
            gr.Markdown("## 数据统计分析")
            refresh_stats_btn = gr.Button("刷新统计数据")
            
            stats_text = gr.Textbox(label="统计概览", lines=10, interactive=False)
            
            gr.Markdown("### 工单分布")
            pie_img = gr.Plot(label="状态分布")
            
            gr.Markdown("### 报修趋势")
            trend_img = gr.Plot(label="近7日趋势")
            
            gr.Markdown("### 楼栋排行")
            building_img = gr.Plot(label="楼栋报修排行")
            
            gr.Markdown("### 故障类型")
            fault_img = gr.Plot(label="故障类型分布")
            
            refresh_stats_btn.click(generate_stats, outputs=[stats_text, pie_img, trend_img, building_img, fault_img])

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