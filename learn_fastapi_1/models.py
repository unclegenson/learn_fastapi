from sqlmodel import SQLModel, Field,Relationship

class User(SQLModel, table=True):
    __tablename__ = "user"  
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True)
    email: str
    phone_number: str
    password: str

    posts: list['Post'] = Relationship(cascade_delete=True, back_populates='author')


# Used for input (no id, same fields except id)
class UserIn(SQLModel):
    username: str
    email: str
    phone_number: str
    password: str


# Used for output (no password)
class UserOut(SQLModel):
    id: int | None = None
    username: str
    email: str
    phone_number: str


# Used for update (patch)
class UserUpdate(SQLModel):
    id: int | None = None
    username: str | None = None
    email: str | None = None
    phone_number: str | None = None


class Post(SQLModel,table=True):
    __tablename__ = "post"  # Add this line
    id: int | None = Field(default=None, primary_key=True)
    title: str 
    description: str 

    user_id: int = Field(foreign_key='user.id',ondelete='CASCADE')  
    author: 'User' = Relationship(back_populates='posts')



class PostIn(SQLModel):
    title: str 
    description: str 
    user_id: int 

class PostOutWithAuthor(SQLModel):
    id: int 
    title: str 
    description: str 
    user_id: int 
    author: UserOut  # Include the full user object

# Used for update (patch)
class PostUpdate(SQLModel):
    id: int | None = None
    title: str | None = None
    description: str | None = None
    user_id: int | None = None

