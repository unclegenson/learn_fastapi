import time
import jwt 
from fastapi import HTTPException,Request
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials

JWT_SECRET = '2e9ed7c4942bbd4f1cc4cd5dd71490075f711fa5b5071dc145d755d5b6ce29e0'
JWT_ALGORITHM = 'HS256'

def token_response(token: str):
    return {'access_token':token}

def sign_jwt(identifier: str):
    payload = {'user_identifier': identifier, 'expires': time.time() + 21600 } # time in secs
    token = jwt.encode(payload,JWT_SECRET,algorithm=JWT_ALGORITHM)
    return token_response(token=token)

# In jwt_auth.py - More specific error handling
def decode_jwt(token: str):
    try:
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded_token if decoded_token['expires'] >= time.time() else None
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None
    
class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
    
    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        
        if credentials:
            print(f"Scheme received: {credentials.scheme}")  # Debug
            print(f"Credentials received: {credentials.credentials}")  # Debug
            
            if credentials.scheme.lower() != 'bearer':
                raise HTTPException(
                    status_code=403, 
                    detail='Invalid authentication scheme. Must be "Bearer"'
                )
            
            # Extract just the token part (in case it includes "Bearer ")
            token = credentials.credentials.strip()
            if token.lower().startswith('bearer '):
                token = token[7:].strip()  # Remove "Bearer " prefix if present
            
            print(f"Extracted token: {token}")  # Debug
            
            if not self.verify_token(token):
                raise HTTPException(status_code=403, detail='Invalid or expired token!')
            
            return token  # Return the clean token
        else:
            raise HTTPException(status_code=403, detail='Invalid authorization code!')
    
    def verify_token(self, jwt_token: str) -> bool:
        payload = decode_jwt(jwt_token)
        return payload is not None