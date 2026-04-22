from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Boolean
from sqlalchemy.sql import func
from app.database import Base

class Student(Base):
    __tablename__ = "student"
    id = Column(Integer, primary_key=True, index=True)
    nickname = Column(String(50), nullable=False)
    education = Column(String(20), nullable=False)
    subject = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class QuestionBank(Base):
    __tablename__ = "question_bank"
    id = Column(Integer, primary_key=True, index=True)
    # 题目标签（用于筛选）
    grade = Column(String(20), nullable=False, index=True)      # 大学/高中/初中/小学
    subject = Column(String(20), nullable=False, index=True)    # 数学/语文/无机化学等
    modules = Column(JSON, nullable=True)  # 知识点
    hard = Column(String(10), nullable=True, index=True)  # 简单/中等/困难
    # 题目内容
    module = Column(String(50), nullable=False)      # 模块名称（如“古诗词”）
    question = Column(Text, nullable=False)          # 题干
    type = Column(String(10), nullable=False)  # choice / fill
    options = Column(JSON, nullable=True)            # 选项列表
    answer = Column(String(255), nullable=False)     # 标准答案
    # 元数据
    source = Column(String(20), default="ai")        # ai / manual
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DiagnosisResult(Base):
    __tablename__ = "diagnosis_result"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student.id"), nullable=False)
    module_scores_json = Column(JSON, nullable=False)
    weak_points = Column(Text, nullable=True)
    strong_points = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class LessonPlan(Base):
    __tablename__ = "lesson_plan"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student.id"), nullable=False)
    plan_json = Column(JSON, nullable=False)
    version = Column(Integer, default=1)
    resource_enriched = Column(Boolean, default=False)   # 新增：资源是否已生成
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ClassRecord(Base):
    __tablename__ = "class_record"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student.id"), nullable=False)
    lesson_id = Column(Integer, nullable=False)
    focus_data_json = Column(JSON, nullable=True)
    answer_records_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class LearningReport(Base):
    __tablename__ = "learning_report"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student.id"), nullable=False)
    lesson_id = Column(Integer, nullable=False)
    report_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())