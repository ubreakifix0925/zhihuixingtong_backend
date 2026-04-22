import json
import httpx
import re
from typing import Dict, List, Any, Optional
from app.config import settings
from app.services.mock_service import (
    generate_mock_diagnosis_questions,
    calculate_mock_diagnosis_result,
    generate_mock_lesson_plan,
    generate_mock_resource_for_segment,
)
from app.utils.json_utils import parse_diagnosis_response

class AIClient:
    """vivo 九问平台 API 客户端"""

    def __init__(self):
        self.base_url = settings.JIUWEN_API_BASE_URL.rstrip("/")
        self.api_key = settings.JIUWEN_API_KEY
        self.timeout = settings.AI_REQUEST_TIMEOUT
        self.use_mock = settings.USE_MOCK_DATA

    def _get_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    async def _call_jiuwen_chat(
        self, query: str, inputs: Dict[str, Any], user: str = "system",
        conversation_id: Optional[str] = None, response_mode: str = "blocking"
    ) -> Dict[str, Any]:
        if self.use_mock:
            return None
        url = f"{self.base_url}/chat-messages"
        payload = {"query": query, "inputs": inputs, "user": user, "response_mode": response_mode}
        if conversation_id:
            payload["conversation_id"] = conversation_id
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            return response.json()

    def _extract_json_from_answer(self, answer: str) -> Dict[str, Any]:
        if not answer:
            return {}
        answer = answer.strip()
        try:
            return json.loads(answer)
        except json.JSONDecodeError:
            pass
        json_match = re.search(r"```json\s*([\s\S]*?)\s*```", answer)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass
        start = answer.find("{")
        end = answer.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(answer[start:end+1])
            except:
                pass
        return {}

    async def generate_diagnosis_questions(
            self, 
            grade: str, 
            subject: str, 
            modules: List[str], 
            hard: str, 
            count: int = 5
    ) -> List[Dict[str, Any]]:
        if self.use_mock:
            return generate_mock_diagnosis_questions(grade, subject)
        modules_str = "、".join(modules)
        query = f""
        inputs = {
            "subject": subject, 
            "grade": grade, 
            "modules": json.dumps(modules, ensure_ascii=False), 
            "hard": hard, 
            "test_num": str(count)
        }
        resp = await self._call_jiuwen_chat(query, inputs, user=f"student_{hash(subject)}")
        if not resp:
            raise Exception("Failed to call AI service")
        raw_json = self._extract_json_from_answer(resp.get("answer", ""))
        return parse_diagnosis_response(raw_json)

    async def generate_diagnosis_report(self, student_id: int, answers: List[Dict[str, Any]]) -> Dict[str, Any]:
        if self.use_mock:
            report = calculate_mock_diagnosis_result(answers)
            plan = generate_mock_lesson_plan(student_id, report)
            return {"diagnosis_report": report, "lesson_plan": plan}
        answers_json = json.dumps(answers, ensure_ascii=False)
        query = f"学生诊断答题结果如下：\n{answers_json}\n请根据答题情况生成诊断报告和个性化教案。输出格式必须为严格的 JSON：{{\"diagnosis_report\": {{\"diagnosis_summary\": \"...\", \"radar_data\": {{...}}, \"weak_modules\": [...], \"strong_modules\": [...], \"recommended_first_lesson\": \"...\"}}, \"lesson_plan\": {{...}}}}"
        inputs = {"student_id": str(student_id), "answers": answers_json}
        resp = await self._call_jiuwen_chat(query, inputs, user=f"student_{student_id}")
        if not resp:
            raise Exception("Failed to call AI service")
        return self._extract_json_from_answer(resp.get("answer", ""))

    async def generate_resource_for_segment(self, segment: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        if self.use_mock:
            return generate_mock_resource_for_segment(segment, context)
        seg_json = json.dumps(segment, ensure_ascii=False)
        ctx_json = json.dumps(context, ensure_ascii=False)
        query = f"教学环节信息：{seg_json}\n上下文：{ctx_json}\n请生成该环节所需的教学资源。输出格式：{{\"resource_type\": \"ppt|blackboard|video|textbook\", \"resource_content\": \"...\"}}"
        resp = await self._call_jiuwen_chat(query, {"segment": seg_json, "context": ctx_json}, user="teacher")
        if not resp:
            raise Exception("Failed to call AI service")
        return self._extract_json_from_answer(resp.get("answer", ""))

    async def enrich_lesson_plan_resources(self, plan_json: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        enriched_plan = plan_json.copy()
        for seg in enriched_plan.get("segments", []):
            resource = await self.generate_resource_for_segment(seg, context)
            seg["resource_type"] = resource.get("resource_type", "ppt")
            seg["resource_content"] = resource.get("resource_content", "")
        return enriched_plan

    async def get_real_time_adjustment(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """实时调整决策"""
        #if self.use_mock:
        if 1:
            # Mock 模式下，根据专注状态简单返回
            focus = context.get("focus_state", "ATTENTIVE")
            if focus == "DISTRACTED" or focus == "AWAY":
                return {"action": "insert", "params": {"tts_text": "请注意听讲哦", "resource_type": "ppt", "resource_content": "# 提醒\n请集中注意力"}}
            return {"action": "none"}

        # 真实调用九问智能体
        ctx_json = json.dumps(context, ensure_ascii=False)
        query = f"当前课堂实时数据：{ctx_json}\n请给出教学调整决策。输出格式：{{\"action\": \"none|insert|switch_resource|add_question|slow_down\", \"params\": {{...}}}}"
        inputs = {"context": ctx_json}
        resp = await self._call_jiuwen_chat(query, inputs, user=f"student_{context.get('student_id')}")
        if not resp:
            return {"action": "none"}
        return self._extract_json_from_answer(resp.get("answer", ""))

    async def generate_learning_report(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        if self.use_mock:
            from app.services.mock_service import generate_mock_learning_report
            return generate_mock_learning_report(session_data.get("student_id", 1), session_data.get("lesson_id", 1), session_data.get("focus_data", []), session_data.get("answer_records", []))
        data_json = json.dumps(session_data, ensure_ascii=False)
        query = f"课堂记录数据：{data_json}\n请生成学习报告。输出格式：{{...}}"
        resp = await self._call_jiuwen_chat(query, {"session_data": data_json}, user=f"student_{session_data.get('student_id')}")
        if not resp:
            raise Exception("Failed to call AI service")
        return self._extract_json_from_answer(resp.get("answer", ""))

    async def generate_exercise_content(self, point: str, level: str = "中等") -> Dict[str, Any]:
        if self.use_mock:
            from app.services.mock_service import generate_mock_exercise_content
            return generate_mock_exercise_content(point, level)
        query = f"知识点：{point}，难度：{level}。请生成配套习题课内容（含例题和练习题）。输出格式：{{...}}"
        resp = await self._call_jiuwen_chat(query, {"point": point, "level": level}, user="teacher")
        if not resp:
            raise Exception("Failed to call AI service")
        return self._extract_json_from_answer(resp.get("answer", ""))

ai_client = AIClient()