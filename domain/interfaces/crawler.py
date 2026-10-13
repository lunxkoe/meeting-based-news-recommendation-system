from abc import ABC, abstractmethod
from typing import Dict, Optional, List

class ICrawlerClient(ABC):
    @abstractmethod
    async def crawl_urls(self, urls: List[str]) -> List[Dict[str, Optional[str]]]:
        """URL 리스트를 받아 제목, 원문을 추출"""
        pass