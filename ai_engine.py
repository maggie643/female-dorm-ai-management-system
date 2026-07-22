import re
import os
from modelscope import snapshot_download

MODEL_ID = "qwen/Qwen-1_8B-Chat"
_model = None
_tokenizer = None

def load_model():
    global _model, _tokenizer
    if _model is None:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        model_dir = snapshot_download(MODEL_ID)
        _tokenizer = AutoTokenizer.from_pretrained(model_dir)
        try:
            _model = AutoModelForCausalLM.from_pretrained(
                model_dir, device_map="auto", load_in_4bit=True
            )
        except Exception:
            try:
                _model = AutoModelForCausalLM.from_pretrained(
                    model_dir, device_map="auto", load_in_8bit=True
                )
            except Exception:
                _model = AutoModelForCausalLM.from_pretrained(
                    model_dir, device_map="auto"
                )
    return _model, _tokenizer

def judge_dorm_fault(building, room, fault_desc):
    model, tokenizer = load_model()
    
    prompt = f"""你是高校宿舍智能管理AI，根据报修信息判断故障类型与紧急等级（P0最高危，P2普通）
宿舍楼栋：{building}
宿舍房间：{room}
故障描述：{fault_desc}
输出格式：故障分类|紧急等级|处理建议
"""
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(**inputs, max_new_tokens=150)
    full_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    response_text = full_text[len(prompt):].strip()
    
    parts = response_text.split('|')
    if len(parts) >= 3:
        fault_type = parts[0].strip()
        priority_level = parts[1].strip()
        handling_suggestion = '|'.join(parts[2:]).strip()
    elif len(parts) == 2:
        fault_type = parts[0].strip()
        priority_level = parts[1].strip()
        handling_suggestion = ""
    else:
        fault_type = response_text.strip() if response_text else "其他故障"
        priority_level = "P2"
        handling_suggestion = ""
    
    priority_level = normalize_priority(priority_level)
    fault_type = normalize_fault_type(fault_type)
    
    return {
        "fault_type": fault_type,
        "priority_level": priority_level,
        "handling_suggestion": handling_suggestion,
        "raw_response": response_text
    }

def smart_qa(question, school_config=None):
    model, tokenizer = load_model()
    
    if school_config:
        knowledge_base = f"""
【宿舍管理规定】
1. 门禁时间：{school_config.get('dorm_access_time', '6:00-23:00')}
2. 用电规定：{school_config.get('electricity_rules', '禁止使用大功率电器')}（超过{school_config.get('max_power_watts', 800)}W）
3. 卫生检查：每周{school_config.get('hygiene_check_day', '周三')}{school_config.get('hygiene_check_time', '下午')}进行宿舍卫生检查
4. 访客登记：{school_config.get('visitor_rules', '访客需在宿管处登记')}
5. 报修流程：学生通过系统提交报修 → AI自动分类 → 派单维修 → 验收评价

【报修常见问题】
1. P0紧急报修：断电、漏水、火灾隐患等，30分钟内响应
2. P1重要报修：空调故障、热水器故障等，1小时内响应
3. P2普通报修：灯具损坏、网络故障等，2小时内响应

【安全须知】
1. 离开宿舍请关闭电源、锁好门窗
2. 禁止私拉乱接电线
3. 发现安全隐患请立即拨打紧急电话

【其他规定】
{school_config.get('other_rules', '')}
"""
    else:
        knowledge_base = """
【宿舍管理规定】
1. 门禁时间：周一至周五 6:00-23:00，周末 6:00-23:30
2. 用电规定：禁止使用大功率电器（超过800W），如电水壶、电磁炉等
3. 卫生检查：每周三下午进行宿舍卫生检查
4. 访客登记：访客需在宿管处登记身份证信息
5. 报修流程：学生通过系统提交报修 → AI自动分类 → 派单维修 → 验收评价

【报修常见问题】
1. P0紧急报修：断电、漏水、火灾隐患等，30分钟内响应
2. P1重要报修：空调故障、热水器故障等，1小时内响应
3. P2普通报修：灯具损坏、网络故障等，2小时内响应

【安全须知】
1. 离开宿舍请关闭电源、锁好门窗
2. 禁止私拉乱接电线
3. 发现安全隐患请立即拨打紧急电话
"""
    
    prompt = f"""你是高校宿舍智能运营助手，专门回答学生和运营人员的问题。

知识库：
{knowledge_base}

用户问题：{question}

请根据知识库内容，给出友好、专业的回答。如果问题超出知识库范围，请礼貌地说明。
"""
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(**inputs, max_new_tokens=300)
    full_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    response_text = full_text[len(prompt):].strip()
    return response_text

def generate_weekly_report(stats_data):
    model, tokenizer = load_model()
    
    stats_summary = f"""
工单统计：
- 总工单数：{stats_data.get('total', 0)}
- 已完成：{stats_data.get('completed', 0)}
- 处理中：{stats_data.get('processing', 0)}
- 待分配：{stats_data.get('pending', 0)}
- 平均满意度：{stats_data.get('avg_rating', 0)}分

故障类型分布：
{stats_data.get('fault_type_stats', [])}

紧急等级分布：
{stats_data.get('priority_stats', [])}

近7日报修趋势：
{stats_data.get('daily_stats', [])}

楼栋报修排行：
{stats_data.get('building_stats', [])}

高校报修统计：
{stats_data.get('school_stats', [])}
"""
    
    prompt = f"""你是高校宿舍运营数据分析师，请根据以下数据生成一份专业的运营周报。

数据统计：
{stats_summary}

请生成一份结构清晰、内容详实的运营周报，包含：
1. 本周工作概览
2. 关键指标分析
3. 问题与挑战
4. 改进建议
5. 下周工作计划

要求：语言专业但不晦涩，数据呈现直观，建议具有可操作性。
"""
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(**inputs, max_new_tokens=500)
    full_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    report_text = full_text[len(prompt):].strip()
    return report_text

def normalize_priority(priority):
    priority = priority.upper()
    if priority in ["P0", "最高危", "紧急", "高危"]:
        return "P0"
    elif priority in ["P1", "中等", "一般"]:
        return "P1"
    elif priority in ["P2", "普通", "低"]:
        return "P2"
    return "P2"

def normalize_fault_type(fault_type):
    type_map = {
        "空调": "空调故障",
        "热水器": "热水器故障",
        "断电": "断电/跳闸",
        "跳闸": "断电/跳闸",
        "漏水": "水管漏水",
        "水管": "水管漏水",
        "门锁": "门锁故障",
        "插座": "插座损坏",
        "堵塞": "卫生间堵塞",
        "卫生间": "卫生间堵塞",
        "灯具": "灯具损坏",
        "灯": "灯具损坏",
        "网络": "网络故障",
        "网": "网络故障"
    }
    
    for keyword, normalized in type_map.items():
        if keyword in fault_type:
            return normalized
    
    return fault_type