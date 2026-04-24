import json
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Optional, List, Dict

def json_serializer(obj: Any) -> Any:
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    elif hasattr(obj, "__dict__"):
        return obj.__dict__
    else:
        raise TypeError(f"Type {type(obj)} not serializable")

def safe_json_dumps(data: Any, indent: Optional[int] = None, ensure_ascii: bool = False, **kwargs) -> str:
    return json.dumps(data, default=json_serializer, indent=indent, ensure_ascii=ensure_ascii, **kwargs)

def safe_json_loads(json_str: str) -> Any:
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON string: {e}")

def parse_json_field(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        return safe_json_loads(value)
    return value

# ---------- 新增：诊断题目解析 ----------
def parse_diagnosis_response(raw_response: dict) -> List[Dict[str, Any]]:
    """解析大模型返回的诊断题目原始JSON，转换为内部标准格式"""
    questions = []
    if "DiagnosisTest" in raw_response:
        for test_item in raw_response["DiagnosisTest"]:
            if "DiagnosisQuestion" in test_item:
                for q_item in test_item["DiagnosisQuestion"]:
                    q = parse_single_question(q_item)
                    if q:
                        questions.append(q)
    elif "questions" in raw_response:
        return raw_response["questions"]
    else:
        for item in raw_response:
            if isinstance(item, dict):
                q = parse_single_question(item)
                if q:
                    questions.append(item)
    return questions

def parse_single_question(q_raw: dict) -> Optional[Dict[str, Any]]:
    question_text = q_raw.get("question", "")
    q_type_raw = q_raw.get("type", "").strip()
    options_raw = q_raw.get("options", "")
    answer = q_raw.get("answer", "")
    
    # 标准化题型
    if "选择" in q_type_raw:
        q_type = "choice"
    elif "填空" in q_type_raw or "填写" in q_type_raw:
        q_type = "fill"
    else:
        q_type = "choice"
    
    options = None
    if q_type == "choice":
        if isinstance(options_raw, str):
            opt_lines = [line.strip() for line in options_raw.split("\n") if line.strip()]
            cleaned_opts = []
            for line in opt_lines:
                if len(line) > 2 and line[1] in ('.', '、', '．'):
                    cleaned_opts.append(line[2:].strip())
                else:
                    cleaned_opts.append(line)
            options = cleaned_opts
        elif isinstance(options_raw, list):
            options = options_raw

    # 确保 modules 字段存在
    modules = q_raw.get("modules", [])
    if not isinstance(modules, list):
        modules = []

    return {
        "modules": modules,
        "question": question_text,
        "type": q_type,
        "options": options,
        "answer": answer,
    }