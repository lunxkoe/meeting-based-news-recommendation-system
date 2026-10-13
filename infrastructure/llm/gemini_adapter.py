from typing import Tuple, List, Dict
from google import genai
import os
import json
from domain.interfaces.llm import ILLMClient
from domain.models import processes_schemas # 기존 스키마 재사용

class GeminiLLMAdapter(ILLMClient):
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model_name = 'gemini-2.5-flash-lite'

    async def generate_meeting_summary(self, content: str) -> Tuple[str, List[str]]:
        prompt = f"회의록: {content}"
        
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": processes_schemas.SummaryMeetingAndKeywordMeetingByLLM.model_json_schema(),
                },
            )
            data = processes_schemas.SummaryMeetingAndKeywordMeetingByLLM.model_validate_json(response.text)
            return data.summary_meeting, data.keyword_meeting_list
        except Exception as e:
            print(f"[Gemini Error] Meeting Summary Failed: {e}")
            raise

    async def generate_news_summary(self, news_content: str) -> str:
        prompt = f"다음 뉴스를 한국어로 3~4문장으로 요약해줘: {news_content}"
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": processes_schemas.SummaryNewsByLLM.model_json_schema(),
                },
            )
            data = processes_schemas.SummaryNewsByLLM.model_validate_json(response.text)
            return data.summary
        except Exception as e:
            print(f"[Gemini Error] News Summary Failed: {e}")
            return "요약 실패"
    