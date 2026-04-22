from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import (
    students_router,
    diagnosis_router,
    lesson_plans_router,
    reports_router,
)
from app.config import settings

# 创建数据库表（首次运行时若不存在则创建）
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="智教星瞳 Backend",
    version="0.1.0",
    description="智教星瞳后端服务，提供学生管理、诊断、教案、报告等API",
)

# 配置CORS（开发阶段允许所有来源）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(students_router)
app.include_router(diagnosis_router)
app.include_router(lesson_plans_router)
app.include_router(reports_router)


@app.get("/")
def root():
    return {
        "message": "智教星瞳后端服务运行中",
        "version": "0.1.0",
        "mock_mode": settings.USE_MOCK_DATA,
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}