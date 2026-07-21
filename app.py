import gradio as gr
import matplotlib.pyplot as plt
import io
import base64
from workflow import submit_repair_request, get_all_orders, get_overdue, mark_complete, get_stats, get_staff_list

plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def submit_request(building, room, fault_desc):
    if not building or not room or not fault_desc:
        return "请填写完整的报修信息"
    
    result = submit_repair_request(building, room, fault_desc)
    
    staff_info = ""
    if result["assigned_staff"]:
        staff_info = f"\n\n已分配维修人员：{result['assigned_staff']['staff_name']}"
    
    return f"""
工单创建成功！

工单编号：{result['order_no']}
故障分类：{result['fault_type']}
紧急等级：{result['priority_level']}
处理建议：{result['handling_suggestion']}
当前状态：{result['status']}{staff_info}
"""

def load_orders():
    orders = get_all_orders()
    if not orders:
        return gr.Dataframe.update(value=[[]], headers=["ID", "工单编号", "楼栋", "房间", "故障描述", "故障类型", "紧急等级", "状态", "提交时间", "处理人员"])
    
    data = []
    for order in orders:
        id, order_no, building, room, fault_desc, fault_type, priority, status, submit_time, assigned_time, completed_time, staff_name, staff_phone = order
        data.append([id, order_no, building, room, fault_desc, fault_type, priority, status, submit_time, staff_name or "未分配"])
    
    return gr.Dataframe.update(value=data, headers=["ID", "工单编号", "楼栋", "房间", "故障描述", "故障类型", "紧急等级", "状态", "提交时间", "处理人员"])

def load_overdue():
    orders = get_overdue()
    if not orders:
        return gr.Dataframe.update(value=[[]], headers=["ID", "工单编号", "楼栋", "房间", "故障描述", "故障类型", "紧急等级", "状态", "提交时间", "处理人员"])
    
    data = []
    for order in orders:
        id, order_no, building, room, fault_desc, fault_type, priority, status, submit_time, estimated_time, staff_name = order
        data.append([id, order_no, building, room, fault_desc, fault_type, priority, status, submit_time, staff_name or "未分配"])
    
    return gr.Dataframe.update(value=data, headers=["ID", "工单编号", "楼栋", "房间", "故障描述", "故障类型", "紧急等级", "状态", "提交时间", "处理人员"])

def complete_order(order_id):
    if order_id:
        mark_complete(int(order_id))
        return f"工单 {order_id} 已标记为完成"
    return "请输入要完成的工单ID"

def generate_stats():
    stats = get_stats()
    
    total = stats["total"]
    completed = stats["completed"]
    processing = stats["processing"]
    pending = stats["pending"]
    
    completion_rate = f"{completed/total*100:.1f}%" if total > 0 else "0%"
    summary = f"""
📊 工单统计概览

总工单数：{total}
已完成：{completed} ({completion_rate})
处理中：{processing}
待分配：{pending}
"""
    
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    status_labels = ['已完成', '处理中', '待分配']
    status_values = [completed, processing, pending]
    axes[0].pie(status_values, labels=status_labels, autopct='%1.1f%%', startangle=90)
    axes[0].set_title('工单状态分布')
    
    if stats["priority_stats"]:
        priority_labels = [p[0] for p in stats["priority_stats"]]
        priority_values = [p[1] for p in stats["priority_stats"]]
        axes[1].bar(priority_labels, priority_values, color=['red', 'orange', 'blue'])
        axes[1].set_title('紧急等级分布')
        axes[1].set_ylabel('工单数量')
    
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode()
    plt.close()
    
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    if stats["daily_stats"]:
        dates = [d[0] for d in stats["daily_stats"]][::-1]
        counts = [d[1] for d in stats["daily_stats"]][::-1]
        ax2.plot(dates, counts, marker='o', linestyle='-')
        ax2.set_title('近7日报修趋势')
        ax2.set_xlabel('日期')
        ax2.set_ylabel('报修数量')
        ax2.tick_params(axis='x', rotation=45)
    
    buf2 = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf2, format='png')
    buf2.seek(0)
    trend_img_str = base64.b64encode(buf2.read()).decode()
    plt.close()
    
    return summary, f"data:image/png;base64,{img_str}", f"data:image/png;base64,{trend_img_str}"

def load_staff():
    staff = get_staff_list()
    data = []
    for s in staff:
        id, name, phone, skills, status, current_order = s
        data.append([id, name, phone, skills, status, current_order or "-"])
    
    return gr.Dataframe.update(value=data, headers=["ID", "姓名", "电话", "技能", "状态", "当前工单"])

with gr.Blocks(title="高校宿舍AI报修管理系统") as demo:
    gr.Markdown("# 🏠 高校宿舍智能报修AI管理平台")
    
    with gr.Tabs():
        with gr.TabItem("📝 报修提交"):
            gr.Markdown("## 提交报修申请")
            with gr.Row():
                dorm_build = gr.Textbox(label="宿舍楼栋", placeholder="A栋")
                dorm_room = gr.Textbox(label="宿舍房间号", placeholder="A0201")
            fault_text = gr.Textbox(label="故障详细描述", lines=4, placeholder="空调不制冷/卫生间漏水/插座没电等")
            submit_btn = gr.Button("AI智能识别并提交", variant="primary")
            result_out = gr.Textbox(label="提交结果", lines=8, interactive=False)
            submit_btn.click(submit_request, inputs=[dorm_build, dorm_room, fault_text], outputs=result_out)
        
        with gr.TabItem("📋 工单管理"):
            gr.Markdown("## 工单列表")
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
            
            refresh_btn.click(load_orders, outputs=orders_df)
            overdue_btn.click(load_overdue, outputs=orders_df)
            complete_btn.click(complete_order, inputs=[order_id_input], outputs=complete_result)
            
            gr.Markdown("## 维修人员状态")
            staff_df = gr.Dataframe(headers=["ID", "姓名", "电话", "技能", "状态", "当前工单"], 
                                    interactive=False)
            refresh_btn.click(load_staff, outputs=staff_df)
        
        with gr.TabItem("📊 数据分析"):
            gr.Markdown("## 数据统计分析")
            refresh_stats_btn = gr.Button("刷新统计数据")
            
            stats_text = gr.Textbox(label="统计概览", lines=10, interactive=False)
            
            gr.Markdown("### 工单分布")
            pie_img = gr.Image(label="状态分布")
            
            gr.Markdown("### 报修趋势")
            trend_img = gr.Image(label="近7日趋势")
            
            refresh_stats_btn.click(generate_stats, outputs=[stats_text, pie_img, trend_img])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7900)