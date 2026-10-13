# app/infrastructure/db/meeting_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Optional, Dict, Any
import json

from domain.interfaces.repository import IMeetingRepository

class MySQLMeetingRepository(IMeetingRepository):

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, meeting_data: Dict[str, Any]) -> int:
        query = text('''
            INSERT INTO meetings(
                user_id, title, created_dt,
                original_meeting, summary_meeting, keywords
            )
            VALUES(
                :user_id, :title, now(),
                :original_meeting, :summary_meeting, :keywords
            )
        ''')
        
        # JSON 직렬화 처리
        keywords_json = json.dumps(meeting_data["keywords"], ensure_ascii=False) if meeting_data["keywords"] else None
        
        result = await self.session.execute(query, {
            "user_id": meeting_data["user_id"],
            "title": meeting_data["title"],
            "original_meeting": meeting_data["original_meeting"],
            "summary_meeting": meeting_data["summary_meeting"],
            "keywords": keywords_json
        })
        await self.session.commit()
        return result.lastrowid

    async def get_by_id(self, meeting_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        query = text('SELECT * FROM meetings WHERE user_id = :user_id AND id = :id')
        result = await self.session.execute(query, {"user_id": user_id, "id": meeting_id})
        row = result.fetchone()
        
        if row:
            # RowMapping을 dict로 변환
            data = row._asdict()
            # JSON 필드 파싱 (DB에서 문자열로 왔을 경우)
            if isinstance(data.get('keywords'), str):
                data['keywords'] = json.loads(data['keywords'])
            if isinstance(data.get('news_items'), str):
                data['news_items'] = json.loads(data['news_items'])
            return data
        return None

    async def get_all_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        query = text('''
            SELECT id, title, created_dt 
            FROM meetings
            WHERE user_id = :user_id
            ORDER BY created_dt DESC
        ''')
        result = await self.session.execute(query, {"user_id": user_id})
        rows = result.fetchall()
        return [row._asdict() for row in rows]

    async def delete(self, meeting_id: int, user_id: int) -> None:
        query = text('DELETE FROM meetings WHERE id = :id AND user_id = :user_id')
        await self.session.execute(query, {"id": meeting_id, "user_id": user_id})
        await self.session.commit()

    async def clear_news_items(self, meeting_id: int, user_id: int) -> None:
        query = text('UPDATE meetings SET news_items = NULL WHERE id = :id AND user_id = :user_id')
        await self.session.execute(query, {"id": meeting_id, "user_id": user_id})
        await self.session.commit()