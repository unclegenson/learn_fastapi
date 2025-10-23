from sqlmodel import SQLModel, Session, create_engine
from typing import Annotated
from fastapi import Depends
from passlib.context import CryptContext
from fastapi_mail import MessageSchema,ConnectionConfig,FastMail,MessageType

sqlite_file_name = "mydb.sqlite3"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

sessionDep = Annotated[Session, Depends(get_session)]

passwordContext = CryptContext(schemes=['sha256_crypt'])

class Hasher:
    @staticmethod
    def verify_pass(plain_pass: str, hashed_pass: str) -> bool:
        return passwordContext.verify(plain_pass, hashed_pass)

    @staticmethod
    def hash_pass(password: str) -> str:
        return passwordContext.hash(password)
    


# email_conf = ConnectionConfig(
#     MAIL_USERNAME='',
#     MAIL_PASSWORD='',
#     MAIL_FROM='',
#     MAIL_PORT=465,
#     MAIL_SERVER='smtp.gmail.com',
#     MAIL_STARTTLS=False,
#     MAIL_SSL_TLS=True,
#     USE_CREDENTIALS=True,
#     VALIDATE_CERTS=True
# )

# message_html = """<b> you regitered successfully :) </b>"""
# fm = FastMail(email_conf)

# async def send_email(email):
#     message = MessageSchema(subject='regiteration',recipients=[email],body=message_html,subtype=MessageType.html)
#     await fm.send_message(message=message)

