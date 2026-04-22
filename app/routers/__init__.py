"""
路由模块包
统一导出所有子路由，便于 main.py 中集中注册
"""

from app.routers.students import router as students_router
from app.routers.diagnosis import router as diagnosis_router
from app.routers.lesson_plans import router as lesson_plans_router
from app.routers.reports import router as reports_router

__all__ = [
    "students_router",
    "diagnosis_router",
    "lesson_plans_router",
    "reports_router",
]