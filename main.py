# app/main.py
from fastapi import FastAPI, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

# [NEW] 모듈 임포트 경로
from core.database import Database
from api.routers import meetings, user
from utils import middleware, exc_handler 

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    db = Database.get_instance()
    db.connect()

    yield
    await db.close()

app = FastAPI(lifespan=lifespan)

app.add_middleware(middleware.MethodOverrideMiddleware)
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"), max_age=3600)

# [NEW] 라우터 등록
app.include_router(meetings.router)
app.include_router(user.router)

# 예외 핸들러
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
app.add_exception_handler(StarletteHTTPException, exc_handler.custom_http_exception_handler)
app.add_exception_handler(RequestValidationError, exc_handler.custom_request_validation_error_handler)

@app.get("/")
async def main_page():
    return RedirectResponse(url="/user/login", status_code=status.HTTP_307_TEMPORARY_REDIRECT)