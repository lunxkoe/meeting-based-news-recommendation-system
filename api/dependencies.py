# app/api/dependencies.py
from fastapi import Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import os
from typing import Optional

# Core 모듈 임포트
from core.database import get_db_conn

# Infrastructure (Repository & Adapter) 임포트
from infrastructure.db.meeting_repository import MySQLMeetingRepository
from infrastructure.db.user_repository import MySQLUserRepository
from infrastructure.llm.gemini_adapter import GeminiLLMAdapter

# Service 임포트
from services.meeting_service import MeetingService
from services.user_service import UserService

# =========================================================
# 1. Database & Repository Dependencies
# =========================================================

# Meeting Repository 주입
async def get_meeting_repository(session: AsyncSession = Depends(get_db_conn)) -> MySQLMeetingRepository:
    return MySQLMeetingRepository(session)

# User Repository 주입
async def get_user_repository(session: AsyncSession = Depends(get_db_conn)) -> MySQLUserRepository:
    return MySQLUserRepository(session)


# =========================================================
# 2. Infrastructure Adapters Dependencies
# =========================================================

# LLM Adapter 주입 (Gemini)
def get_llm_client() -> GeminiLLMAdapter:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        # 실제 운영 환경에서는 로그를 남기고 서버 시작을 막거나 예외 처리
        raise ValueError("GEMINI_API_KEY environment variable is not set.")
    return GeminiLLMAdapter(api_key)


# =========================================================
# 3. Service Layer Dependencies (조립)
# =========================================================

# Meeting Service 주입 (Repository + LLM Adapter + Celery Task)
def get_meeting_service(
    repository: MySQLMeetingRepository = Depends(get_meeting_repository),
    llm_client: GeminiLLMAdapter = Depends(get_llm_client)
) -> MeetingService:
    # Celery Task는 런타임에 가져오거나(순환참조 방지), None으로 처리
    try:
        from celery_worker import process_news_task
    except ImportError:
        process_news_task = None
        
    return MeetingService(
        repository=repository,
        llm_client=llm_client,
        celery_task=process_news_task
    )

# User Service 주입 (Repository)
def get_user_service(
    repository: MySQLUserRepository = Depends(get_user_repository)
) -> UserService:
    return UserService(repository)


# =========================================================
# 4. Authentication & Session Helpers
# =========================================================

def get_current_user(request: Request) -> Optional[dict]:
    """세션에서 현재 로그인한 사용자 정보를 가져옵니다 (없으면 None)."""
    return request.session.get("session_user")

def get_current_user_required(request: Request) -> dict:
    """로그인이 필수인 엔드포인트에서 사용합니다."""
    user = request.session.get("session_user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="로그인이 필요한 서비스입니다."
        )
    return user
