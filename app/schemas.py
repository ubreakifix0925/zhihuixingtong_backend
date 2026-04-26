from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from datetime import datetime

# ---------- 学生 ----------
class StudentCreate(BaseModel):
    nickname: str
    education: str
    subject: str

class StudentResponse(BaseModel):
    id: int
    nickname: str
    education: str
    subject: str
    created_at: datetime
    class Config:
        from_attributes = True

# ---------- 诊断 ----------
class DiagnosisAnswerSubmit(BaseModel):
    student_id: int
    answers: List[Dict[str, Any]]  # 每道题的答案结构

class DiagnosisReportResponse(BaseModel):
    student_id: int
    diagnosis_summary: str
    radar_data: Dict[str, float]   # 模块名->得分率(0~1)
    weak_modules: List[str]
    strong_modules: List[str]
    recommended_first_lesson: str

class DiagnosisQuestionsParams(BaseModel):
    grade: str
    subject: str
    modules: List[str]    # 知识点数组
    hard: str
    count: int = 10

class DiagnosisQuestionItem(BaseModel):                   # 主模块名
    modules: Optional[List[str]] = []   # 关联知识点标签
    question: str
    type: str
    options: Optional[List[str]] = None
    answer: str

# ---------- 提交诊断答案 ----------
class AnswerSubmitItem(BaseModel):
    question_id: int            # 题库题目ID
    student_answer: str         # 学生答案

class DiagnosisAnswerSubmit(BaseModel):
    student_id: int
    answers: List[AnswerSubmitItem]

# ---------- 教案 ----------
class LessonPlanResponse(BaseModel):
    plan_id: int
    version: int
    plan_json: Dict[str, Any]

# ---------- 课堂记录 ----------
class ClassRecordCreate(BaseModel):
    student_id: int
    lesson_id: int
    focus_data: Optional[List[Dict]] = None
    answer_records: Optional[List[Dict]] = None

class FocusEvent(BaseModel):
    timestamp: int          # 毫秒时间戳
    state: str              # "ATTENTIVE" / "DISTRACTED" / "AWAY"

class AnswerRecord(BaseModel):
    timestamp: int
    segment_id: str
    question: str
    student_answer: str
    standard_answer: str
    is_correct: bool

class ClassRecordReport(BaseModel):
    lesson_id: str          # 或 int，前端传什么就存什么
    student_id: int
    start_time: int
    end_time: int
    focus_events: Optional[List[FocusEvent]] = None
    answer_records: Optional[List[AnswerRecord]] = None

# ---------- 实时调整请求 ----------
class RealTimeAdjustmentRequest(BaseModel):
    student_id: int
    lesson_id: int
    current_segment_id: str
    focus_state: Optional[str] = None          # 当前专注状态
    recent_answers: Optional[List[AnswerRecord]] = None  # 最近几道答题记录
    active_questions_count: int = 0             # 主动提问次数
    not_understand_count: int = 0               # 点击“没听懂”次数

# ---------- 学习报告 ----------
class LearningReportResponse(BaseModel):
    report_id: int
    student_id: int
    lesson_id: int
    report_json: Dict[str, Any]
    created_at: datetime