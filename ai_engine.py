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
        except ImportError:
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