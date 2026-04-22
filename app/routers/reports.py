from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app import schemas, models
from app.database import get_db
from app.services.mock_service import generate_mock_learning_report
from app.services.ai_client import ai_client
from app.config import settings

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/{student_id}/latest")
def get_latest_report(student_id: int, db: Session = Depends(get_db)):
    """获取指定学生的最新学习报告"""
    report = (
        db.query(models.LearningReport)
        .filter(models.LearningReport.student_id == student_id)
        .order_by(models.LearningReport.created_at.desc())
        .first()
    )
    if not report:
        # 返回模拟报告（不存入数据库）
        if settings.USE_MOCK_DATA:
            mock_report = generate_mock_learning_report(student_id, 1, [], [])
            return {"report_json": mock_report, "student_id": student_id}
        else:
            raise HTTPException(status_code=404, detail="No report found for this student")
    
    return {
        "report_id": report.id,
        "student_id": report.student_id,
        "lesson_id": report.lesson_id,
        "report_json": report.report_json,
        "created_at": report.created_at,
    }


@router.post("/class_records")
def create_class_record(
    record: schemas.ClassRecordCreate,
    db: Session = Depends(get_db)
):
    """创建课堂记录（用于实时数据上报）"""
    db_record = models.ClassRecord(
        student_id=record.student_id,
        lesson_id=record.lesson_id,
        focus_data_json=record.focus_data,
        answer_records_json=record.answer_records,
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return {"record_id": db_record.id, "status": "success"}


@router.post("/class_records")
def upload_class_record(
    report: schemas.ClassRecordReport,
    db: Session = Depends(get_db)
):
    """接收并存储课堂完整记录（专注度事件 + 答题记录）"""
    # 检查 student 和 lesson_plan 是否存在
    student = db.query(models.Student).filter(models.Student.id == report.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # 将 focus_events 转为 JSON 存储
    focus_data = [fe.dict() for fe in report.focus_events] if report.focus_events else []
    answer_data = [ar.dict() for ar in report.answer_records] if report.answer_records else []
    
    record = models.ClassRecord(
        student_id=report.student_id,
        lesson_id=int(report.lesson_id) if report.lesson_id.isdigit() else 0,
        focus_data_json=focus_data,
        answer_records_json=answer_data
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    
    return {
        "record_id": record.id,
        "status": "success",
        "message": "课堂记录已保存"
    }

@router.post("/real_time_adjustment")
async def get_real_time_adjustment(
    request: schemas.RealTimeAdjustmentRequest,
    db: Session = Depends(get_db)
):
    """
    实时调整决策接口
    客户端在上课过程中定时（如每30秒）或事件触发时调用，
    获取是否需要调整教学策略的指令。
    """
    # 构建 AI 输入上下文
    context = {
        "student_id": request.student_id,
        "lesson_id": request.lesson_id,
        "current_segment_id": request.current_segment_id,
        "focus_state": request.focus_state,
        "recent_answers": [ans.dict() for ans in request.recent_answers] if request.recent_answers else [],
        "active_questions_count": request.active_questions_count,
        "not_understand_count": request.not_understand_count
    }
    
    # 调用 AI 客户端获取调整决策
    adjustment = await ai_client.get_real_time_adjustment(context)
    
    # adjustment 格式示例：{"action": "insert", "params": {"content": "补充讲解..."}}
    return adjustment