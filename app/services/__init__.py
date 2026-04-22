"""
服务层包
提供 Mock 数据服务、AI 客户端等业务逻辑模块
"""

from app.services.mock_service import (
    generate_mock_diagnosis_questions,
    calculate_mock_diagnosis_result,
    generate_mock_lesson_plan,
    generate_mock_exercise_content,
    generate_mock_learning_report,
)

__all__ = [
    "generate_mock_diagnosis_questions",
    "calculate_mock_diagnosis_result",
    "generate_mock_lesson_plan",
    "generate_mock_exercise_content",
    "generate_mock_learning_report",
]