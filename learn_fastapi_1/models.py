from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True)
    email: str
    phone_number: str
    password: str


# Used for input (no id, same fields except id)
class UserIn(SQLModel):
    username: str
    email: str
    phone_number: str
    password: str


# Used for output (no password)
class UserOut(SQLModel):
    id: int
    username: str
    email: str
    phone_number: str


# Used for update (patch)
class UserUpdate(SQLModel):
    id: int | None = None
    username: str | None = None
    email: str | None = None
    phone_number: str | None = None
