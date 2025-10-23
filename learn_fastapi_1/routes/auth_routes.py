from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import select
from jwt_auth import JWTBearer, sign_jwt, refresh_access_token, decode_jwt, revoke_token, get_token_remaining_time, is_token_expiring_soon
from models import LoginRequest, User
from db import sessionDep, Hasher

router = APIRouter()

@router.post("/auth/login")
async def login(login_data: LoginRequest, session: sessionDep):
    user = session.exec(select(User).where(User.email == login_data.email)).first()
    
    if not user or not Hasher.verify_pass(login_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return sign_jwt(user.email, user.id)

@router.post("/auth/refresh")
async def refresh_token(refresh_token: str):
    new_access_token = refresh_access_token(refresh_token)
    
    if not new_access_token:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    
    return {
        'access_token': new_access_token,
        'token_type': 'bearer',
        'expires_in': 21600  # 6 hours in seconds
    }

@router.post("/auth/logout", dependencies=[Depends(JWTBearer())])
async def logout(token: str = Depends(JWTBearer())):
    # Add the current access token to revoked list
    revoke_token(token)
    
    return {"message": "Successfully logged out"}

@router.get("/auth/token-info", dependencies=[Depends(JWTBearer())])
async def get_token_info(token: str = Depends(JWTBearer())):
    """Get information about the current token"""
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    remaining_time = get_token_remaining_time(token)
    expiring_soon = is_token_expiring_soon(token)
    
    return {
        "user_id": payload.get("user_id"),
        "email": payload.get("email"),
        "token_type": payload.get("type"),
        "remaining_time_seconds": remaining_time,
        "expiring_soon": expiring_soon,
        "expires_in_minutes": remaining_time // 60,
        "human_readable_expiry": f"Token expires in {remaining_time // 60} minutes and {remaining_time % 60} seconds"
    }
