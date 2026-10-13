from abc import ABC, abstractmethod
from typing import Tuple, List

class ILLMClient(ABC):

    @abstractmethod
    async def generate_meeting_summary(self, content: str) -> Tuple[str, List[str]]:
        """회의록 원문을 받아 요약문과 키워드 리스트를 반환"""
        pass

    @abstractmethod
    async def generate_news_summary(self, news_content: str) -> str:
        """뉴스 원문을 받아 요약문을 반환"""
        pass