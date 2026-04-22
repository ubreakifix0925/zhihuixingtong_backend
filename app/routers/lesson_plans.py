from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any
from app import schemas, models
from app.database import get_db
from app.services.mock_service import generate_mock_lesson_plan
from app.services.ai_client import ai_client

router = APIRouter(prefix="/api/lesson_plans", tags=["lesson_plans"])

@router.get("/latest/{student_id}")
def get_latest_lesson_plan(student_id: int, db: Session = Depends(get_db)):
    plan = db.query(models.LessonPlan).filter(models.LessonPlan.student_id == student_id).order_by(models.LessonPlan.version.desc()).first()
    if not plan:
        mock_plan = generate_mock_lesson_plan(student_id, {"recommended_first_lesson": "二次函数"})
        return {"plan_id": 0, "version": 0, "plan_json": mock_plan}
    return {"plan_id": plan.id, "version": plan.version, "plan_json": plan.plan_json}

@router.post("/{plan_id}/update")
def update_lesson_plan(plan_id: int, new_plan_json: Dict[str, Any], db: Session = Depends(get_db)):
    old_plan = db.query(models.LessonPlan).filter(models.LessonPlan.id == plan_id).first()
    if not old_plan:
        raise HTTPException(status_code=404, detail="Lesson plan not found")
    new_plan = models.LessonPlan(student_id=old_plan.student_id, plan_json=new_plan_json, version=old_plan.version + 1)
    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)
    return {"plan_id": new_plan.id, "version": new_plan.version, "message": "Lesson plan updated successfully"}

@router.get("/{plan_id}")
def get_lesson_plan_by_id(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(models.LessonPlan).filter(models.LessonPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Lesson plan not found")
    return {"plan_id": plan.id, "student_id": plan.student_id, "version": plan.version, "plan_json": plan.plan_json, "created_at": plan.created_at}

@router.post("/{plan_id}/enrich")
async def enrich_lesson_plan_resources(plan_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    plan = db.query(models.LessonPlan).filter(models.LessonPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Lesson plan not found")
    if plan.resource_enriched:
        return {"status": "already_enriched", "plan_id": plan_id, "message": "Resources already generated"}

    async def _enrich_task():
        context = {"student_id": plan.student_id, "topic": plan.plan_json.get("topic", "")}
        enriched = await ai_client.enrich_lesson_plan_resources(plan.plan_json, context)
        plan.plan_json = enriched
        plan.resource_enriched = True
        db.commit()

    background_tasks.add_task(_enrich_task)
    return {"status": "processing", "plan_id": plan_id, "message": "Resource generation started in background"}

@router.get("/{plan_id}/status")
def get_enrich_status(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(models.LessonPlan).filter(models.LessonPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Lesson plan not found")
    return {"plan_id": plan_id, "resource_enriched": plan.resource_enriched, "version": plan.version}