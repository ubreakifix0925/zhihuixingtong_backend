from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import schemas, models
from app.database import get_db
from app.services.ai_client import ai_client
from app.services.question_bank_service import QuestionBankService
from app.config import settings

router = APIRouter(prefix="/api/diagnosis", tags=["diagnosis"])

@router.get("/questions")
async def get_diagnosis_questions(
    grade: str, 
    subject: str, 
    point: str, 
    hard: str, 
    count: int, 
    db: Session = Depends(get_db)
    ):
    """获取诊断测试题"""
    service = QuestionBankService(db)
    questions = await service.get_or_generate_questions(
        grade=grade,
        subject=subject,
        point=point,
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
    """提交诊断答案，生成报告与初始教案"""
    ai_result = await ai_client.generate_diagnosis_report(submission.student_id, submission.answers)
    diagnosis_report = ai_result["diagnosis_report"]
    lesson_plan_json = ai_result["lesson_plan"]
    # 存储诊断结果
    diagnosis_record = models.DiagnosisResult(
        student_id=submission.student_id,
        module_scores_json=diagnosis_report.get("radar_data", {}),
        weak_points=",".join(diagnosis_report.get("weak_modules", [])),
        strong_points=",".join(diagnosis_report.get("strong_modules", []))
    )
    db.add(diagnosis_record)
    # 存储教案（版本1，资源未填充）
    plan_record = models.LessonPlan(
        student_id=submission.student_id,
        plan_json=lesson_plan_json,
        version=1,
        resource_enriched=False
    )
    db.add(plan_record)
    db.commit()
    db.refresh(plan_record)
    return {
        "diagnosis_report": diagnosis_report,
        "lesson_plan": {
            "plan_id": plan_record.id,
            "version": plan_record.version,
            "plan_json": lesson_plan_json,
            "resource_enriched": False
        }
    }