#!/usr/bin/env python3
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.mock_service import (
    generate_mock_diagnosis_questions,
    calculate_mock_diagnosis_result,
    generate_mock_lesson_plan,
    generate_mock_resource_for_segment,
    generate_mock_exercise_content,
)

def generate_full_mock_response(student_id: int = 1):
    questions = generate_mock_diagnosis_questions("高中", "数学")
    mock_answers = [
        {"module": "函数", "question_id": 0, "answer": "7"},
        {"module": "函数", "question_id": 1, "answer": "B"},
        {"module": "几何", "question_id": 2, "answer": "B"},
        {"module": "几何", "question_id": 3, "answer": "πr²"},
        {"module": "代数", "question_id": 4, "answer": "4"},
    ]
    report = calculate_mock_diagnosis_result(mock_answers)
    lesson_plan_raw = generate_mock_lesson_plan(student_id, report)
    context = {"topic": lesson_plan_raw.get("topic", "二次函数")}
    enriched_plan = lesson_plan_raw.copy()
    for seg in enriched_plan.get("segments", []):
        resource = generate_mock_resource_for_segment(seg, context)
        seg["resource_type"] = resource["resource_type"]
        seg["resource_content"] = resource["resource_content"]
    exercise = generate_mock_exercise_content("二次函数", "中等")
    return {
        "student_id": student_id,
        "diagnosis_questions": questions,
        "mock_answers": mock_answers,
        "diagnosis_report": report,
        "lesson_plan_raw": lesson_plan_raw,
        "lesson_plan_enriched": enriched_plan,
        "exercise_content": exercise,
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="生成 Mock 数据")
    parser.add_argument("--output", type=str, help="输出 JSON 文件路径")
    parser.add_argument("--format", choices=["full", "questions", "plan"], default="full")
    args = parser.parse_args()
    data = generate_full_mock_response()
    if args.format == "questions":
        output = {"questions": data["diagnosis_questions"]}
    elif args.format == "plan":
        output = data["lesson_plan_enriched"]
    else:
        output = data
    json_str = json.dumps(output, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(json_str)
        print(f"Mock 数据已写入 {args.output}")
    else:
        print(json_str)