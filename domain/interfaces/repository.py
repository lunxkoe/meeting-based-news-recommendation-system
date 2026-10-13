# app/domain/interfaces/repository.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class IMeetingRepository(ABC):
    """
    회의록 데이터 저장소 인터페이스.
    MySQL을 쓰든 MSSQL을 쓰든 Service 계층은 이 인터페이스만 바라봅니다.
    """
    
    @abstractmethod
    async def save(self, meeting_data: Dict[str, Any]) -> int:
        """회의록 데이터를 저장하고 생성된 ID를 반환합니다."""
        pass

    @abstractmethod
    async def get_by_id(self, meeting_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """ID로 회의록을 조회합니다."""
        pass

    @abstractmethod
    async def get_all_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """사용자의 모든 회의록을 최신순으로 조회합니다."""
        pass

    @abstractmethod
    async def delete(self, meeting_id: int, user_id: int) -> None:
        """본인 소유의 회의록을 삭제합니다."""
        pass
    
    @abstractmethod
    async def clear_news_items(self, meeting_id: int, user_id: int) -> None:
        """뉴스 아이템을 초기화(NULL) 합니다."""
        pass