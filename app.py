import gradio as gr
from modelscope import snapshot_download, AutoModelForCausalLM, AutoTokenizer

# 拉取魔搭开源轻量大模型
model_id = "qwen/Qwen-1_8B-Chat"
model_dir = snapshot_download(model_id)
tokenizer = AutoTokenizer.from_pretrained(model_dir)
model = AutoModelForCausalLM.from_pretrained(
    model_dir, device_map="auto", load_in_4bit=True
)

# AI故障识别函数
def judge_dorm_fault(building, room, fault_desc):
    prompt = f"""你是高校宿舍智能管理AI，根据报修信息判断故障类型与紧急等级（P0最高危，P2普通）
宿舍楼栋：{building}
宿舍房间：{room}
故障描述：{fault_desc}
输出格式：故障分类|紧急等级|处理建议
"""
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(**inputs, max_new_tokens=150)
    res = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return res

# 搭建网页交互界面
with gr.Blocks(title="高校女生宿舍AI报修管理系统") as demo:
    gr.Markdown("# 高校女生宿舍智能报修AI管理平台")
    with gr.Row():
        dorm_build = gr.Textbox(label="宿舍楼栋", placeholder="女生A栋")
        dorm_room = gr.Textbox(label="宿舍房间号", placeholder="A0201")
    fault_text = gr.Textbox(label="故障详细描述", lines=3, placeholder="空调损坏/卫生间漏水/断电等")
    submit_btn = gr.Button("AI自动识别故障等级")
    result_out = gr.Textbox(label="AI识别结果")
    submit_btn.click(judge_dorm_fault, inputs=[dorm_build, dorm_room, fault_text], outputs=result_out)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0")
