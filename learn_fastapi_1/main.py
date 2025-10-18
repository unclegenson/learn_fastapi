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

from fastapi import FastAPI ,Depends
from typing import Annotated
from sqlmodel import Field,Session,SQLModel,create_engine,select


app = FastAPI()


class User(SQLModel,table = True):
    id: int = Field(primary_key=True)
    username: str = Field(index=True)
    email: str
    phone_number: str
    password: str 

sql_file_name = 'mydb.sqlite3'
sql_url = f'sqlite:///{sql_file_name}'
connect_args = {'check_same_thread':False}
engine = create_engine(sql_url,connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

sessionDep = Annotated[Session,Depends(get_session)]

@app.on_event('startup')
def on_start_up():
    create_db_and_tables()

@app.post('/user/')
async def create_new_user(user:User,session:sessionDep) -> dict:
    session.add(user)
    session.commit()
    session.refresh(user)
    return {'message':f'user {user.username} created'}