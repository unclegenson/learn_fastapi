from fastapi import Depends, HTTPException ,APIRouter
from sqlmodel import select
from jwt_auth import JWTBearer, sign_jwt
from models import LoginRequest, User, UserIn, UserOut, UserUpdate
from db import sessionDep,Hasher

router = APIRouter()


@router.post("/auth/login")
async def login(login_data: LoginRequest, session: sessionDep):
    user = session.exec(select(User).where(User.email == login_data.email)).first()
    
    if not user or not Hasher.verify_pass(login_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return sign_jwt(user.username)

@router.post("/users/", response_model=UserOut, dependencies=[Depends(JWTBearer())])
async def create_user(user: UserIn, session: sessionDep):
    similar_user = session.exec(select(User).where(User.email == user.email)).first()
    if similar_user:
        raise HTTPException(status_code=400, detail='A user with this email already exists!')
    
    similar_user = session.exec(select(User).where(User.username == user.username)).first()
    if similar_user:
        raise HTTPException(status_code=400, detail='A user with this username already exists!')
    
    db_user = User(
        username=user.username,
        email=user.email,
        phone_number=user.phone_number,
        password=Hasher.hash_pass(user.password)  
    )
    
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

@router.get("/users/", response_model=list[UserOut], dependencies=[Depends(JWTBearer())])
async def get_users(session: sessionDep):
    users = session.exec(select(User)).all()
    return users


@router.get("/users/{user_id}", response_model=UserOut, dependencies=[Depends(JWTBearer())])
async def get_user(user_id: int, session: sessionDep):
    # user = session.exec(select(User).where(User.id == user_id)).first()
    user = session.get(User,user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/users/{user_id}",dependencies=[Depends(JWTBearer())])
async def delete_user(user_id: int, session: sessionDep):
    # user = session.exec(select(User).where(User.id == user_id)).first()
    user = session.get(User,user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    session.delete(user)
    session.commit()
    return {'message':'user deleted successfully'}


@router.patch("/users/{user_id}",dependencies=[Depends(JWTBearer())])
async def update_user(user_id: int,user: UserUpdate, session: sessionDep):
    # user = session.exec(select(User).where(User.id == user_id)).first()
    want_to_update_user = session.get(User,user_id)
    if not want_to_update_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_data = user.model_dump(exclude_unset=True) # remove params that is set to None
    want_to_update_user.sqlmodel_update(user_data) # use for updating the past user 
    session.add(want_to_update_user)
    session.commit()
    session.refresh(want_to_update_user)
    return want_to_update_user

