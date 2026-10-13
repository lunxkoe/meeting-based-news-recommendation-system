# app/api/routers/user.py
from fastapi import APIRouter, Request, Form, Depends, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from api.dependencies import get_user_service
from services.user_service import UserService

from core.templates import templates

router = APIRouter(prefix="/user", tags=["user"])

@router.get("/register")
async def register_ui(request: Request):
    return templates.TemplateResponse(request=request, name="register_user.html")

@router.post("/register")
async def register(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    service: UserService = Depends(get_user_service)
):
    await service.register_user(name, email, password)
    return RedirectResponse(url="/user/login", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/login")
async def login_ui(request: Request):
    return templates.TemplateResponse(request=request, name="login_user.html")

@router.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    service: UserService = Depends(get_user_service)
):
    user_data = await service.login_user(email, password)
    request.session["session_user"] = user_data
    return RedirectResponse(url="/meetings/read/all", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/user/login", status_code=status.HTTP_303_SEE_OTHER)