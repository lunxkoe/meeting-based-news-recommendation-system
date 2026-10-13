# app/core/templates.py
from fastapi.templating import Jinja2Templates
import os

# 프로젝트 루트의 "templates" 폴더를 바라보도록 설정
templates = Jinja2Templates(directory="templates")