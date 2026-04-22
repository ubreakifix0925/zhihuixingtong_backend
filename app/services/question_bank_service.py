"""
本地题库服务
负责从数据库筛选题目，并在不足时调用 AI 生成补充
"""

import random
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app import models
from app.services.ai_client import ai_client


class QuestionBankService:
    def __init__(self, db: Session):
        self.db = db

    def query_questions(
        self,
        grade: str,
        subject: str,
        modules: Optional[List[str]] = None,
        hard: Optional[str] = None,
        limit: int = 10
    ) -> List[models.QuestionBank]:
        """从本地题库筛选题目，支持多知识点（至少匹配一个）"""
        filters = [
            models.QuestionBank.grade == grade,
            models.QuestionBank.subject == subject,
        ]
        if hard:
            filters.append(models.QuestionBank.hard == hard)

        query = self.db.query(models.QuestionBank).filter(and_(*filters))
        # 先获取较多题目，再按知识点过滤
        candidates = query.order_by(func.random()).limit(limit * 3).all()

        if not modules:
            return candidates[:limit]

        # 筛选 modules 字段与传入数组有交集的题目
        result = []
        for q in candidates:
            q_modules = q.modules or []
            if any(m in q_modules for m in modules):
                result.append(q)
                if len(result) >= limit:
                    break
        return result

    def save_questions(self, questions: List[Dict[str, Any]], tags: Dict[str, Any]):
        """批量保存题目到本地题库"""
        saved_count = 0
        for q in questions:
            existing = self.db.query(models.QuestionBank).filter(
                models.QuestionBank.question == q["question"]
            ).first()
            if existing:
                continue
            db_q = models.QuestionBank(
                grade=tags["grade"],
                subject=tags["subject"],
                modules=tags.get("modules", []),
                hard=tags.get("hard", ""),
                module=q.get("module", ""),
                question=q["question"],
                question_type=q["type"],
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
        modules: List[str],
        hard: str,
        required_count: int = 10
    ) -> List[Dict[str, Any]]:
        """
        核心方法：优先从本地获取，不足时调用 AI 生成并入库
        返回格式：List[DiagnosisQuestionItem]
        """
        # 1. 从本地查询
        local_questions = self.query_questions(
            grade, subject, modules, hard, required_count
        )
        local_list = []
        for q in local_questions:
            local_list.append({
                "module": q.module,
                "modules": q.modules or [],
                "question": q.question,
                "type": q.question_type,
                "options": q.options,
                "answer": q.answer
            })

        # 2. 若本地题目足够，直接返回
        if len(local_list) >= required_count:
            return local_list[:required_count]

        # 3. 不足部分，调用 AI 生成
        shortage = required_count - len(local_list)
        ai_questions_raw = await ai_client.generate_diagnosis_questions(
            grade=grade,
            subject=subject,
            modules=modules,
            hard=hard,
            count=shortage
        )
        ai_questions = ai_questions_raw[:shortage]

        # 4. 将 AI 生成的题目存入本地题库
        tags = {
            "grade": grade,
            "subject": subject,
            "modules": modules,
            "hard": hard
        }
        self.save_questions(ai_questions, tags)

        # 5. 合并结果
        result = local_list + ai_questions
        return result