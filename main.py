from fastapi import FastAPI

app = FastAPI()

@app.get('/home/{name}/{age}/')
def home(name:str,age:int=0):
    return {"Message":f"Greetings to {name} who is {age} years old."}

@app.get('/users/me')
def read_me():
    return {"user_id":"the current user."}


@app.get('/users/')
def read_user(user_id:int = 0):
    return {'user_id':user_id}