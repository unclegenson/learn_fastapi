# session 0,1,2:

# from fastapi import FastAPI
# from pydantic import BaseModel
# app = FastAPI()

# @app.get('/home/{name}/{age}/')
# def home(name:str,age:int=0):
#     return {"Message":f"Greetings to {name} who is {age} years old."}

# @app.get('/users/me')
# def read_me():
#     return {"user_id":"the current user."}


# @app.get('/users/')
# def read_user(user_id:int = 0):
#     return {'user_id':user_id}  





##########################################################################
# session 3,4,5:

# from fastapi import FastAPI,Path,Query,status,HTTPException
# from pydantic import BaseModel


# class Item(BaseModel):
#     name : str
#     description : str | None = 'this is description'
#     price : float = Path(description='price should be more than 0',ge=0)
#     tax : float | None = 100

# class Person(BaseModel):
#     name : str
#     age : int
#     height : int
#     car : str

# class User(BaseModel):
#     username:str
#     phone:str
#     password:str

# class UserOut(BaseModel):
#     username:str
#     phone:str


# app = FastAPI()

# @app.post('/items/')
# async def createItem(item:Item):
#     return item

# @app.post('/persons/',status_code=status.HTTP_201_CREATED)
# async def createPerson(person:Person,job:str = Query(default='no job set',min_length=2,max_length=100)):
#     if (person.name == 'admin' or person.name == 'Admin'):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,detail='name cant be admin,Admin'
#         )
#     return {'person':person,'job':job}

# @app.post('/persons/login/',response_model=UserOut,status_code=201)
# async def loginUser(user:User):
#     return user



##########################################################################
# session 7:

# from fastapi import FastAPI ,Depends
# from typing import Annotated
# from sqlmodel import Field,Session,SQLModel,create_engine,select


# app = FastAPI()


# class User(SQLModel,table = True):
#     id: int = Field(primary_key=True)
#     username: str = Field(index=True)
#     email: str
#     phone_number: str
#     password: str 

# sql_file_name = 'mydb.sqlite3'
# sql_url = f'sqlite:///{sql_file_name}'
# connect_args = {'check_same_thread':False}
# engine = create_engine(sql_url,connect_args=connect_args)


# def create_db_and_tables():
#     SQLModel.metadata.create_all(engine)

# def get_session():
#     with Session(engine) as session:
#         yield session

# sessionDep = Annotated[Session,Depends(get_session)]

# @app.on_event('startup')
# def on_start_up():
#     create_db_and_tables()

# @app.post('/user/')
# async def create_new_user(user:User,session:sessionDep) -> dict:
#     session.add(user)
#     session.commit()
#     session.refresh(user)
#     return {'message':f'user {user.username} created'}



##########################################################################
# session 8:
from fastapi import FastAPI, HTTPException,Request
from sqlmodel import select
from models import User, UserIn, UserOut,UserUpdate
from db import create_db_and_tables, sessionDep,Hasher
import time
import datetime
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse


app = FastAPI()

@app.middleware('http')
async def add_time_header(request: Request,call_next):

    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    process_time = str(process_time)[0:5] + 's'
    response.headers['X-Process-Time'] = process_time

    return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    RATE_LIMIT_DURATION = datetime.timedelta(minutes=1)
    RATE_LIMIT_REQUESTS = 10

    def __init__(self, app):
        super().__init__(app)
        self.requests_count = {}  # {ip: (request_count, last_request)}

    async def dispatch(self, request, call_next):
        client_ip = request.client.host
        request_count, last_request = self.requests_count.get(client_ip, (0, datetime.datetime.min))
        elapesed_time = datetime.datetime.now() - last_request
        if (elapesed_time > self.RATE_LIMIT_DURATION):
            request_count = 1
        else: 
            if (request_count >= self.RATE_LIMIT_REQUESTS):
                return JSONResponse(status_code=400,content={'message':'rate limit exceed! try again later.'})
            request_count += 1

        self.requests_count[client_ip] = (request_count, datetime.datetime.now())
        response = await call_next(request)
        return response


app.add_middleware(RateLimitMiddleware)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.post("/users/", response_model=UserOut)
async def create_user(user: UserIn, session: sessionDep):

    similar_user = session.exec(select(User).where(User.email == user.email)).first()
    if (similar_user):
        raise HTTPException(status_code=400,detail='a user with this email is already existed!')
    
    similar_user = session.exec(select(User).where(User.username == user.username)).first()
    if (similar_user):
        raise HTTPException(status_code=400,detail='a user with this username is already existed!')
    
    db_user = User(**user.dict())  # Convert UserIn → User (table model)
    password_hashed = Hasher.hash_pass(user.password)
    db_user.password = password_hashed
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user  # Automatically converted to UserOut because of response_model


@app.get("/users/", response_model=list[UserOut])
async def get_users(session: sessionDep):
    users = session.exec(select(User)).all()
    return users


@app.get("/users/{user_id}", response_model=UserOut)
async def get_user(user_id: int, session: sessionDep):
    # user = session.exec(select(User).where(User.id == user_id)).first()
    user = session.get(User,user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.delete("/users/{user_id}")
async def delete_user(user_id: int, session: sessionDep):
    # user = session.exec(select(User).where(User.id == user_id)).first()
    user = session.get(User,user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    session.delete(user)
    session.commit()
    return {'message':'user deleted successfully'}

# 11 

@app.patch("/users/{user_id}")
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