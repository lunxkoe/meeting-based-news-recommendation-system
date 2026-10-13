from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

# [수정 1] api.dependencies에서 서비스와 "유저 인증 함수"를 가져옵니다.
# (기존의 from services import user_svc 삭제)
from api.dependencies import get_meeting_service, get_current_user_required
from services.meeting_service import MeetingService

from core.templates import templates

router = APIRouter(prefix="/meetings", tags=["meetings"])

# 1. 회의록 생성 페이지 (GET)
@router.get("/create")
async def create_meeting_ui(
    request: Request,
    # [수정 2] user_svc 대신 get_current_user_required 사용
    session_user = Depends(get_current_user_required)
):
    return templates.TemplateResponse(
        request=request,
        name="create_meeting.html",
        context={"session_user": session_user}
    )

# 2. 회의록 생성 요청 (POST)
@router.post("/create")
async def create_meeting(
    request: Request,
    title: str = Form(...),
    original_meeting: str = Form(...),
    service: MeetingService = Depends(get_meeting_service),
    # [수정 3] user_svc 대신 get_current_user_required 사용
    session_user = Depends(get_current_user_required)
):
    await service.create_meeting(
        user_id=session_user["id"],
        title=title,
        original_text=original_meeting
    )
    
    return RedirectResponse(
        url="/meetings/read/all",
        status_code=status.HTTP_303_SEE_OTHER
    )

# 3. 회의록 목록 조회 (GET)
@router.get("/read/all")
async def get_all_meetings_ui(
    request: Request,
    service: MeetingService = Depends(get_meeting_service),
    session_user = Depends(get_current_user_required)
):
    all_meetings = await service.get_all_meetings(user_id=session_user["id"])
    
    return templates.TemplateResponse(
        request=request,
        name="main_meeting.html",
        context={
            "all_meetings": all_meetings,
            "session_user": session_user
        }
    )

# 4. 회의록 상세 조회 (GET)
@router.get("/read/{id}")
async def get_by_id_meeting_ui(
    request: Request,
    id: int,
    service: MeetingService = Depends(get_meeting_service),
    session_user = Depends(get_current_user_required)
):
    meeting = await service.get_meeting_detail(meeting_id=id, user_id=session_user["id"])
    
    return templates.TemplateResponse(
        request=request,
        name="read_meeting.html",
        context={
            "meeting": meeting,
            "session_user": session_user
        }
    )

# 5. 회의록 삭제 (DELETE)
@router.delete("/delete/{id}")
async def delete_meeting(
    request: Request,
    id: int,
    service: MeetingService = Depends(get_meeting_service),
    session_user = Depends(get_current_user_required)
):
    await service.delete_meeting(meeting_id=id, user_id=session_user["id"])

    return RedirectResponse(
        url="/meetings/read/all",
        status_code=status.HTTP_303_SEE_OTHER
    )

@router.post("/retry-news/{id}")
async def retry_news_analysis(
    id: int,
    service: MeetingService = Depends(get_meeting_service),
    session_user = Depends(get_current_user_required)
):
    await service.retry_news_analysis(meeting_id=id, user_id=session_user["id"])

    # 비동기 요청이므로 202 Accepted 또는 JSON 응답 반환
    return JSONResponse(
        content={"status": "retry_started", "meeting_id": id},
        status_code=status.HTTP_202_ACCEPTED
    )