# app/services/meeting_service.py
from typing import List, Optional
from fastapi import HTTPException, status

from domain.interfaces.repository import IMeetingRepository
from domain.interfaces.llm import ILLMClient

class MeetingService:
    def __init__(
        self, 
        repository: IMeetingRepository, 
        llm_client: ILLMClient,
        celery_task = None  # 순환 참조 방지를 위해 런타임에 주입하거나 래퍼 사용
    ):
        self.repository = repository
        self.llm_client = llm_client
        self.celery_task = celery_task

    async def create_meeting(self, user_id: int, title: str, original_text: str) -> int:
        # 1. LLM 요약 수행
        try:
            summary, keywords = await self.llm_client.generate_meeting_summary(original_text)
        except Exception as e:
            # 로그 처리 필요
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
                detail=f"회의록 분석 실패: {e}"
            )

        # 2. 데이터 저장 준비
        meeting_data = {
            "user_id": user_id,
            "title": title,
            "original_meeting": original_text,
            "summary_meeting": summary,
            "keywords": keywords
        }

        # 3. Repository를 통해 DB 저장
        try:
            meeting_id = await self.repository.save(meeting_data)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="DB 저장 실패"
            )

        # 4. Celery 태스크 호출 (뉴스 분석)
        if self.celery_task:
            try:
                self.celery_task.delay(
                    meeting_id=meeting_id,
                    user_id=user_id,
                    summary_meeting=summary,
                    keyword_meeting_list=keywords
                )
            except Exception as e:
                print(f"Celery Task 호출 실패: {e}")
                # 태스크 실패가 회의록 생성 실패는 아니므로 에러는 넘김
        
        return meeting_id

    async def get_all_meetings(self, user_id: int) -> List[dict]:
        return await self.repository.get_all_by_user(user_id)

    async def get_meeting_detail(self, meeting_id: int, user_id: int) -> dict:
        meeting = await self.repository.get_by_id(meeting_id, user_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="회의록을 찾을 수 없습니다.")
        return meeting

    async def delete_meeting(self, meeting_id: int, user_id: int):
        # 삭제 쿼리에 user_id 조건을 걸어 본인 회의록만 삭제
        await self.repository.delete(meeting_id, user_id)

    async def retry_news_analysis(self, meeting_id: int, user_id: int):
        """뉴스 분석 재시도 비즈니스 로직"""
        
        # 1. 회의록 조회 및 권한 확인
        meeting = await self.repository.get_by_id(meeting_id, user_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="회의록을 찾을 수 없습니다.")
        
        # 2. 필수 데이터(요약/키워드) 확인
        if not meeting.get('summary_meeting') or not meeting.get('keywords'):
             raise HTTPException(status_code=400, detail="요약본이나 키워드가 없어 분석할 수 없습니다.")

        # 3. 기존 뉴스 데이터 초기화 (Repository에 메서드 필요)
        await self.repository.clear_news_items(meeting_id, user_id)
        
        # 4. Celery 태스크 재호출
        if self.celery_task:
            self.celery_task.delay(
                meeting_id=meeting_id,
                user_id=user_id,
                summary_meeting=meeting['summary_meeting'],
                keyword_meeting_list=meeting['keywords']
            )
        else:
            raise HTTPException(status_code=500, detail="백그라운드 작업을 실행할 수 없습니다.")