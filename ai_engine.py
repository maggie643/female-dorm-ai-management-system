import re
import os
from modelscope import snapshot_download

MODEL_ID = "qwen/Qwen-1_8B-Chat"
_model = None
_tokenizer = None
_use_rule_engine = False

def is_cpu_environment():
    try:
        import torch
        return not torch.cuda.is_available()
    except:
        return True

def load_model():
    global _model, _tokenizer, _use_rule_engine
    
    if _use_rule_engine:
        return None, None
    
    if _model is None:
        if is_cpu_environment():
            print("⚠️ CPU环境，使用规则引擎进行故障分类")
            _use_rule_engine = True
            return None, None
        
        try:
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
        except Exception as e:
            print(f"⚠️ 模型加载失败，使用规则引擎：{e}")
            _use_rule_engine = True
            return None, None
    
    return _model, _tokenizer

def rule_based_classify(fault_desc):
    fault_desc_lower = fault_desc.lower()
    
    fault_type_map = [
        ("空调", "空调故障"),
        ("冷气", "空调故障"),
        ("制冷", "空调故障"),
        ("制热", "空调故障"),
        ("热水器", "热水器故障"),
        ("热水", "热水器故障"),
        ("断电", "断电/跳闸"),
        ("跳闸", "断电/跳闸"),
        ("停电", "断电/跳闸"),
        ("漏电", "断电/跳闸"),
        ("漏水", "水管漏水"),
        ("水管", "水管漏水"),
        ("水龙头", "水管漏水"),
        ("下水", "水管漏水"),
        ("门锁", "门锁故障"),
        ("门", "门锁故障"),
        ("钥匙", "门锁故障"),
        ("插座", "插座损坏"),
        ("插头", "插座损坏"),
        ("电", "插座损坏"),
        ("堵塞", "卫生间堵塞"),
        ("马桶", "卫生间堵塞"),
        ("厕所", "卫生间堵塞"),
        ("下水道", "卫生间堵塞"),
        ("灯", "灯具损坏"),
        ("照明", "灯具损坏"),
        ("网络", "网络故障"),
        ("wifi", "网络故障"),
        ("网", "网络故障"),
        ("信号", "网络故障"),
    ]
    
    priority_rules = [
        (["断电", "跳闸", "漏电", "火灾", "燃烧", "煤气", "燃气", "爆炸", "中毒"], "P0"),
        (["漏水", "水管", "水龙头", "下水"], "P1"),
        (["空调", "冷气", "热水器", "热水"], "P1"),
        (["门锁", "门", "钥匙"], "P1"),
        (["灯", "照明", "插座", "插头"], "P2"),
        (["网络", "wifi", "网"], "P2"),
        (["堵塞", "马桶", "厕所"], "P2"),
    ]
    
    fault_type = "其他故障"
    for keyword, ft in fault_type_map:
        if keyword in fault_desc_lower:
            fault_type = ft
            break
    
    priority_level = "P2"
    for keywords, p in priority_rules:
        for kw in keywords:
            if kw in fault_desc_lower:
                priority_level = p
                break
        if priority_level != "P2":
            break
    
    suggestions = {
        "空调故障": "请检查遥控器电池和温度设置，如仍有问题请等待维修人员",
        "热水器故障": "请检查电源和水温设置，如仍有问题请等待维修人员",
        "断电/跳闸": "请检查电箱开关，切勿私拉乱接电线",
        "水管漏水": "请先用桶接水，关闭阀门，等待维修人员",
        "门锁故障": "请不要强行开锁，等待维修人员",
        "插座损坏": "请停止使用该插座，等待维修人员更换",
        "卫生间堵塞": "请使用马桶搋子尝试疏通，如无效请等待维修人员",
        "灯具损坏": "请使用备用灯具，等待维修人员更换",
        "网络故障": "请重启路由器，如仍有问题请联系网络中心",
        "其他故障": "请详细描述故障情况，等待维修人员处理",
    }
    
    return {
        "fault_type": fault_type,
        "priority_level": priority_level,
        "handling_suggestion": suggestions.get(fault_type, "请等待维修人员处理"),
        "raw_response": f"{fault_type}|{priority_level}",
        "rule_based": True
    }

def judge_dorm_fault(building, room, fault_desc):
    model, tokenizer = load_model()
    
    if _use_rule_engine:
        return rule_based_classify(fault_desc)
    
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
        "raw_response": response_text,
        "rule_based": False
    }

def rule_based_qa(question, school_config=None):
    question_lower = question.lower()
    
    if school_config:
        access_time = school_config.get('dorm_access_time', '6:00-23:00')
        power_watts = school_config.get('max_power_watts', 800)
        hygiene_day = school_config.get('hygiene_check_day', '周三')
        hygiene_time = school_config.get('hygiene_check_time', '下午')
        visitor_rules = school_config.get('visitor_rules', '访客需在宿管处登记')
    else:
        access_time = '周一至周五 6:00-23:00，周末 6:00-23:30'
        power_watts = 800
        hygiene_day = '周三'
        hygiene_time = '下午'
        visitor_rules = '访客需在宿管处登记'
    
    qa_rules = [
        (["门禁", "时间", "几点关门", "几点开门"], f"门禁时间：{access_time}"),
        (["用电", "功率", "电器", "多少瓦", "800"], f"用电规定：禁止使用大功率电器，最大功率限制为{power_watts}W"),
        (["卫生", "检查", "打扫"], f"卫生检查：每周{hygiene_day}{hygiene_time}进行宿舍卫生检查"),
        (["访客", "登记", "外人"], f"访客规定：{visitor_rules}"),
        (["报修", "流程", "怎么报修"], "报修流程：学生通过系统提交报修 → AI自动分类 → 派单维修 → 验收评价"),
        (["P0", "紧急"], "P0紧急报修：断电、漏水、火灾隐患等，30分钟内响应"),
        (["P1", "重要"], "P1重要报修：空调故障、热水器故障等，1小时内响应"),
        (["P2", "普通"], "P2普通报修：灯具损坏、网络故障等，2小时内响应"),
        (["安全", "须知", "注意事项"], "安全须知：1.离开宿舍请关闭电源、锁好门窗 2.禁止私拉乱接电线 3.发现安全隐患请立即拨打紧急电话"),
        (["你是谁", "什么", "介绍"], "我是高校宿舍智能运营助手，专门回答学生和运营人员的问题。"),
    ]
    
    for keywords, answer in qa_rules:
        for kw in keywords:
            if kw in question_lower:
                return answer
    
    if school_config:
        rules_text = f"""
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
        rules_text = """
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
    
    return f"您的问题已记录，以下是相关宿舍管理规定供参考：\n{rules_text}\n如需进一步帮助，请联系宿管。"

def smart_qa(question, school_config=None):
    model, tokenizer = load_model()
    
    if _use_rule_engine:
        return rule_based_qa(question, school_config)
    
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
    
    if _use_rule_engine:
        return rule_based_report(stats_data)
    
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

def rule_based_report(stats_data):
    total = stats_data.get('total', 0)
    completed = stats_data.get('completed', 0)
    processing = stats_data.get('processing', 0)
    pending = stats_data.get('pending', 0)
    avg_rating = stats_data.get('avg_rating', 0)
    
    completion_rate = (completed / total * 100) if total > 0 else 0
    
    report = f"""📊 高校宿舍运营周报

## 一、本周工作概览

- 📋 总工单数：{total}
- ✅ 已完成：{completed}（完成率：{completion_rate:.1f}%）
- 🔄 处理中：{processing}
- ⏳ 待分配：{pending}
- ⭐ 平均满意度：{avg_rating}分

## 二、关键指标分析

### 紧急等级分布
{stats_data.get('priority_stats', '暂无数据')}

### 故障类型分布
{stats_data.get('fault_type_stats', '暂无数据')}

### 近7日报修趋势
{stats_data.get('daily_stats', '暂无数据')}

### 楼栋报修排行
{stats_data.get('building_stats', '暂无数据')}

## 三、问题与挑战

1. 待分配工单数量：{pending}单，需及时处理
2. 完成率：{completion_rate:.1f}%，建议优化派单效率

## 四、改进建议

1. 优先处理P0紧急报修工单
2. 加强维修人员技能培训
3. 优化工单分配算法

## 五、下周工作计划

1. 完成所有待分配工单
2. 开展维修人员技能培训
3. 定期检查高风险宿舍设备

---
📌 本报告由系统自动生成
"""
    return report

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
