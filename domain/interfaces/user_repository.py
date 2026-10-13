# app/domain/interfaces/user_repository.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class IUserRepository(ABC):
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """이메일로 사용자 정보를 조회합니다 (패스워드 미포함)."""
        pass

    @abstractmethod
    async def get_by_email_with_password(self, email: str) -> Optional[Dict[str, Any]]:
        """로그인 검증을 위해 패스워드가 포함된 사용자 정보를 조회합니다."""
        pass

    @abstractmethod
    async def create(self, user_data: Dict[str, Any]) -> None:
        """새로운 사용자를 생성합니다."""
        pass