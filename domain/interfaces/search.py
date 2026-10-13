from abc import ABC, abstractmethod
from typing import List

class ISearchClient(ABC):
    @abstractmethod
    async def search_urls(self, keywords: List[str], count: int = 50) -> List[str]:
        """키워드 리스트로 관련 URL 검색"""
        pass