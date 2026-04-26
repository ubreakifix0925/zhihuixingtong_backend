from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app import schemas, models
from app.database import get_db
from app.services.ai_client import ai_client
from app.services.question_bank_service import QuestionBankService
from app.services.mock_service import generate_mock_lesson_plan
from app.config import settings

router = APIRouter(prefix="/api/diagnosis", tags=["diagnosis"])

@router.get("/questions")
async def get_diagnosis_questions(
    grade: str, 
    subject: str, 
    hard: str, 
    count: int, 
    modules: List[str] = Query(...),   # 接收多个知识点
    db: Session = Depends(get_db)
    ):
    """获取诊断测试题"""
    service = QuestionBankService(db)
    questions = await service.get_or_generate_questions(
        grade=grade,
        subject=subject,
        modules=modules,
        hard=hard,
        required_count=count
    )
    #questions = await ai_client.generate_diagnosis_questions(grade, subject, point, hard, style)
    return {"questions": questions}

@router.post("/submit")
async def submit_diagnosis_answers(
    submission: schemas.DiagnosisAnswerSubmit,
    db: Session = Depends(get_db)
):
    # 1. 初始化服务
    qb_service = QuestionBankService(db)
    
    # 2. 统计模块得分
    modules_correct = {}
    modules_total = {}
    answer_details = []  # 用于存储答题明细

    for ans in submission.answers:
        # 获取题目（支持Mock模式或数据库查询）
        question = qb_service.get_question_by_id(ans.question_id)
        if not question:
            continue  # 或记录日志
        
        # 比对答案（选择题标准化大写）
        student_ans = ans.student_answer.strip().upper()
        standard_ans = question.answer.strip().upper()
        is_correct = (student_ans == standard_ans)
        
        # 统计该题关联的每个模块
        for mod in (question.modules or []):
            modules_total[mod] = modules_total.get(mod, 0) + 1
            if is_correct:
                modules_correct[mod] = modules_correct.get(mod, 0) + 1
        
        # 构建答题明细对象（暂不提交）
        answer_details.append({
            "question_id": question.id,
            "question_text": question.question,
            "question_type": question.question_type,
            "options": question.options,
            "standard_answer": question.answer,
            "student_answer": ans.student_answer,
            "is_correct": is_correct,
            "modules": question.modules
        })
    
    # 3. 计算得分率
    radar_data = {}
    weak_modules = []
    strong_modules = []
    for mod, total in modules_total.items():
        score = modules_correct.get(mod, 0) / total if total > 0 else 0
        radar_data[mod] = round(score, 2)
        if score < 0.6:
            weak_modules.append(mod)
        elif score >= 0.8:
            strong_modules.append(mod)
    
    # 4. 存储诊断结果主记录
    diagnosis_record = models.DiagnosisResult(
        student_id=submission.student_id,
        module_scores_json=radar_data,
        weak_points=",".join(weak_modules),
        strong_points=",".join(strong_modules)
    )
    db.add(diagnosis_record)
    db.flush()  # 获取主键ID到 diagnosis_record.id
    
    # 5. 存储答题明细
    for detail in answer_details:
        db.add(models.DiagnosisAnswerDetail(
            diagnosis_result_id=diagnosis_record.id,
            question_id=detail["question_id"],
            question_text=detail["question_text"],
            question_type=detail["question_type"],
            options=detail["options"],
            standard_answer=detail["standard_answer"],
            student_answer=detail["student_answer"],
            is_correct=detail["is_correct"],
            modules=detail["modules"]
        ))
    
    # 6. 调用AI生成诊断报告和教案（传递模块得分数据）
    ai_result = await ai_client.generate_diagnosis_report(
        student_id=submission.student_id,
        modules_scores={
            "radar_data": radar_data,
            "weak_modules": weak_modules,
            "strong_modules": strong_modules
        }
    )
    diagnosis_report = ai_result.get("diagnosis_report", {})
    lesson_plan_json = ai_result.get("lesson_plan", {})

    if ai_result is None:
        # AI 完全不可用且无 Mock 兜底时，构造内置报告
        diagnosis_report = {
            "diagnosis_summary": "AI 服务暂时不可用，请查看模块得分。",
            "radar_data": radar_data,
            "weak_modules": weak_modules,
            "strong_modules": strong_modules,
            "recommended_first_lesson": weak_modules[0] if weak_modules else "全部模块"
        }
        lesson_plan_json = generate_mock_lesson_plan(
            submission.student_id,
            {"recommended_first_lesson": diagnosis_report["recommended_first_lesson"]}
        )
    else:
        diagnosis_report = ai_result.get("diagnosis_report", {})
        lesson_plan_json = ai_result.get("lesson_plan", generate_mock_lesson_plan(submission.student_id, {}))
    
    # 7. 存储教案（版本1，资源未填充）
    plan_record = models.LessonPlan(
        student_id=submission.student_id,
        plan_json=lesson_plan_json,
        version=1,
        resource_enriched=False
    )
    db.add(plan_record)
    db.commit()
    db.refresh(plan_record)
    
    # 8. 返回结果
    return {
        "diagnosis_result_id": diagnosis_record.id,
        "diagnosis_report": diagnosis_report,
        "radar_data": radar_data,
        "lesson_plan": {
            "plan_id": plan_record.id,
            "version": plan_record.version,
            "plan_json": lesson_plan_json,
            "resource_enriched": False
        }
    }