"""
本地题库服务
负责从数据库筛选题目，并在不足时调用 AI 生成补充
"""

import random
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func   # 新增 func 导入
from app import models
from app.services.ai_client import ai_client
from app.utils.json_utils import parse_diagnosis_response
import json


class QuestionBankService:
    def __init__(self, db: Session):
        self.db = db

    def query_questions(
        self,
        grade: str,
        subject: str,
        point: Optional[str] = None,
        hard: Optional[str] = None,
        limit: int = 10
    ) -> List[models.QuestionBank]:
        """从本地题库筛选题目"""
        filters = [
            models.QuestionBank.grade == grade,
            models.QuestionBank.subject == subject,
        ]
        if point:
            filters.append(models.QuestionBank.point == point)
        if hard:
            filters.append(models.QuestionBank.hard == hard)

        query = self.db.query(models.QuestionBank).filter(and_(*filters))
        # 随机排序，避免每次返回相同题目
        questions = query.order_by(func.random()).limit(limit).all()
        return questions

    def save_questions(self, questions: List[Dict[str, Any]], tags: Dict[str, str]):
        """批量保存题目到本地题库"""
        saved_count = 0
        for q in questions:
            # 检查是否已存在完全相同的题目（避免重复）
            existing = self.db.query(models.QuestionBank).filter(
                models.QuestionBank.question == q["question"]
            ).first()
            if existing:
                continue
            db_q = models.QuestionBank(
                grade=tags["grade"],
                subject=tags["subject"],
                point=tags.get("point", ""),
                hard=tags.get("hard", ""),
                module=q["module"],
                question=q["question"],
                type=q["type"],
                options=q.get("options"),
                answer=q["answer"],
                source="ai"
            )
            self.db.add(db_q)
            saved_count += 1
        self.db.commit()
        return saved_count

    async def get_or_generate_questions(
        self,
        grade: str,
        subject: str,
        point: str,
        hard: str,
        required_count: int = 10
    ) -> List[Dict[str, Any]]:
        """
        核心方法：优先从本地获取，不足时调用 AI 生成并入库
        返回格式与前端要求一致：List[DiagnosisQuestion]
        """
        # 1. 从本地查询
        local_questions = self.query_questions(
            grade, subject, point, hard, required_count
        )
        local_list = [
            {
                "module": q.module,
                "question": q.question,
                "type": q.type,
                "options": q.options,
                "answer": q.answer
            }
            for q in local_questions
        ]

        # 2. 若本地题目足够，直接返回
        if len(local_list) >= required_count:
            return local_list[:required_count]

        # 3. 不足部分，调用 AI 生成
        shortage = required_count - len(local_list)
        ai_questions_raw = await ai_client.generate_diagnosis_questions(
            grade, subject, point, hard
        )
        # 如果 AI 返回题目过多，只取需要的数量
        ai_questions = ai_questions_raw[:shortage]

        # 4. 将 AI 生成的题目存入本地题库
        tags = {
            "grade": grade,
            "subject": subject,
            "point": point,
            "hard": hard
        }
        self.save_questions(ai_questions, tags)

        # 5. 合并本地 + AI 生成的结果
        result = local_list + ai_questions
        return result