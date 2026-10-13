# app/services/user_service.py
from fastapi import HTTPException, status
from passlib.context import CryptContext
from domain.interfaces.user_repository import IUserRepository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    def __init__(self, repository: IUserRepository):
        self.repository = repository

    async def register_user(self, name: str, email: str, password: str):
        # 1. 중복 확인
        existing_user = await self.repository.get_by_email(email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="해당 이메일은 이미 등록되어 있습니다."
            )
        
        # 2. 비밀번호 해싱 및 저장
        hashed_password = pwd_context.hash(password)
        await self.repository.create({
            "name": name,
            "email": email,
            "hashed_password": hashed_password
        })

    async def login_user(self, email: str, password: str) -> dict:
        # 1. 사용자 조회 (비밀번호 포함)
        user = await self.repository.get_by_email_with_password(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="등록되지 않은 사용자입니다."
            )
        
        # 2. 비밀번호 검증
        if not pwd_context.verify(password, user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="비밀번호를 확인해주세요."
            )
        
        # 3. 세션에 저장할 정보 반환 (비밀번호 제외)
        return {"id": user["id"], "name": user["name"], "email": user["email"]}