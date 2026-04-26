import json
from typing import Dict, List, Any
from app.utils.json_utils import parse_diagnosis_response

# 模拟大模型返回的原始诊断题目结构
MOCK_DIAGNOSIS_RAW_RESPONSE = {
    "DiagnosisTest": [
        {"DiagnosisQuestion": [{"module": "函数", "question": "函数f(x)=2x+1，求f(3)", "type": "填空", "options": "", "answer": "7"}]},
        {"DiagnosisQuestion": [{"module": "函数", "question": "二次函数y=x²-4x+3的对称轴是？", "type": "选择", "options": "A. x=1\nB. x=2\nC. x=3\nD. x=4", "answer": "B"}]},
        {"DiagnosisQuestion": [{"module": "几何", "question": "勾股定理适用于什么三角形？", "type": "选择", "options": "A. 锐角三角形\nB. 直角三角形\nC. 钝角三角形\nD. 任意三角形", "answer": "B"}]},
        {"DiagnosisQuestion": [{"module": "几何", "question": "圆的面积公式是？", "type": "填空", "options": "", "answer": "πr²"}]},
        {"DiagnosisQuestion": [{"module": "代数", "question": "方程2x+5=13的解是？", "type": "填空", "options": "", "answer": "4"}]},
    ]
}

def generate_mock_report_from_scores(student_id: int, modules_scores: Dict[str, Any]) -> Dict[str, Any]:
    radar_data = modules_scores.get("radar_data", {})
    weak_modules = modules_scores.get("weak_modules", [])
    strong_modules = modules_scores.get("strong_modules", [])
    weak_str = "、".join(weak_modules) if weak_modules else "无"
    strong_str = "、".join(strong_modules) if strong_modules else "无"
    diagnosis_summary = f"诊断结果：薄弱模块 - {weak_str}；优势模块 - {strong_str}。建议针对薄弱模块进行强化学习。"
    return {
        "diagnosis_summary": diagnosis_summary,
        "radar_data": radar_data,
        "weak_modules": weak_modules,
        "strong_modules": strong_modules,
        "recommended_first_lesson": weak_modules[0] if weak_modules else "综合复习"
    }
def generate_mock_diagnosis_questions(education: str, subject: str) -> List[Dict]:
    """返回诊断题目Mock数据（已解析为标准格式）"""
    return parse_diagnosis_response(MOCK_DIAGNOSIS_RAW_RESPONSE)

def calculate_mock_diagnosis_result(answers: List[Dict]) -> Dict:
    """模拟判分，生成诊断报告"""
    radar_data = {"函数": 0.5, "几何": 1.0, "代数": 1.0}
    weak_modules = ["函数"]
    strong_modules = ["几何", "代数"]
    summary = "学生在函数部分表现薄弱，特别是二次函数性质掌握不牢；几何和代数基础扎实。"
    return {
        "diagnosis_summary": summary,
        "radar_data": radar_data,
        "weak_modules": weak_modules,
        "strong_modules": strong_modules,
        "recommended_first_lesson": "二次函数图像与性质"
    }

def generate_mock_lesson_plan(student_id: int, diagnosis: Dict) -> Dict:
    """生成模拟教案JSON（未填充资源）"""
    return {
        "student_id": student_id,
        "topic": diagnosis.get("recommended_first_lesson", "二次函数"),
        "segments": [
            {"segment_id": "seg1", "type": "lecture", "resource_type": "ppt", "resource_content": "", "tts_text": "同学们好，今天我们来学习二次函数。二次函数的一般形式是y等于a x平方加b x加c，其中a不等于零。", "duration": 45},
            {"segment_id": "seg2", "type": "lecture", "resource_type": "blackboard", "resource_content": "", "tts_text": "二次函数的对称轴公式是x等于负的2a分之b。", "duration": 30},
            {"segment_id": "seg3", "type": "example", "resource_type": "ppt", "resource_content": "", "tts_text": "我们来看一道例题，求二次函数y等于x平方减4x加3的对称轴和顶点坐标。", "duration": 60, "question_node": {"question": "该函数的对称轴是多少？", "answer": "x=2", "hint": "用公式x=-b/(2a)"}}
        ]
    }

def generate_mock_resource_for_segment(segment: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
    """根据 segment 类型生成模拟教学资源"""
    seg_type = segment.get("type", "lecture")
    topic = context.get("topic", "二次函数") if context else "二次函数"
    if seg_type == "lecture":
        return {"resource_type": "ppt", "resource_content": f"# {topic}\n\n## 知识点讲解\n\n- 定义与性质\n- 公式推导\n- 典型例题引入"}
    elif seg_type == "example":
        return {"resource_type": "blackboard", "resource_content": f"【例题】已知 {topic} 相关条件，求解下列问题：\n\n解：\n步骤1：...\n步骤2：...\n故答案为：..."}
    elif seg_type == "question":
        return {"resource_type": "ppt", "resource_content": f"# 课堂提问\n\n{segment.get('question_node', {}).get('question', '请回答')}"}
    else:
        return {"resource_type": "textbook", "resource_content": f"教材内容：{topic} 章节核心概念。"}

def generate_mock_exercise_content(point: str, level: str = "中等") -> Dict[str, Any]:
    """生成习题课 Mock 内容"""
    return {
        "point": point,
        "level": level,
        "examples": [{"type": "example", "question": f"关于{point}的典型例题", "explanation": "详细讲解步骤...", "resource_content": f"# 例题\n{point} 综合应用", "tts_text": f"我们来看一道关于{point}的例题"}],
        "exercises": [{"type": "exercise", "question": f"{point} 练习题（{level}难度）", "answer": "参考答案", "hint": "解题提示"}]
    }

def generate_mock_learning_report(student_id: int, lesson_id: int, focus_data: List, answer_records: List) -> Dict:
    """生成模拟学习报告"""
    return {
        "student_id": student_id,
        "lesson_id": lesson_id,
        "focus_score": 85,
        "correct_rate": 0.75,
        "knowledge_mastery": {"函数": 0.6, "几何": 0.9},
        "weak_points": ["二次函数顶点式转换"],
        "suggestions": "建议多练习配方和顶点式转换题目。",
        "next_lesson_preview": "二次函数应用题"
    }