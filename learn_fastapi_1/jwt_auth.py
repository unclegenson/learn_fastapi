import time
import jwt 
from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta

JWT_SECRET = '2e9ed7c4942bbd4f1cc4cd5dd71490075f711fa5b5071dc145d755d5b6ce29e0'
JWT_ALGORITHM = 'HS256'

# Token expiration times
ACCESS_TOKEN_EXPIRE_MINUTES = 360  # 6 hours in minutes
REFRESH_TOKEN_EXPIRE_DAYS = 30     # 30 days

# Store revoked tokens (in production, use Redis or database)
revoked_tokens = set()

def get_token_expiration():
    """Get expiration timestamps"""
    access_expires = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_expires = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return access_expires, refresh_expires

def token_response(access_token: str, refresh_token: str):
    access_expires, _ = get_token_expiration()
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'bearer',
        'expires_in': ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # in seconds
        'expires_at': access_expires.isoformat()  # Human readable expiration
    }

def sign_jwt(identifier: str, user_id: int):
    access_expires, refresh_expires = get_token_expiration()
    
    # Create access token
    access_token_payload = {
        'email': identifier, 
        'user_id': user_id, 
        'exp': access_expires,
        'type': 'access',
        'iat': datetime.utcnow()  # issued at
    }
    access_token = jwt.encode(access_token_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    # Create refresh token
    refresh_token_payload = {
        'user_id': user_id, 
        'email': identifier,
        'exp': refresh_expires,
        'type': 'refresh',
        'iat': datetime.utcnow()
    }
    refresh_token = jwt.encode(refresh_token_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return token_response(access_token=access_token, refresh_token=refresh_token)

def refresh_access_token(refresh_token: str):
    """Create new access token using refresh token"""
    try:
        if refresh_token in revoked_tokens:
            return None
            
        payload = jwt.decode(refresh_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        if payload.get('type') != 'refresh':
            return None
            
        # Create new access token with new expiration
        access_expires, _ = get_token_expiration()
        access_token_payload = {
            'email': payload.get('email', ''),
            'user_id': payload['user_id'], 
            'exp': access_expires,
            'type': 'access',
            'iat': datetime.utcnow()
        }
        access_token = jwt.encode(access_token_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        return access_token
        
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None

def decode_jwt(token: str):
    try:
        if token in revoked_tokens:
            return None
            
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded_token
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None

def get_token_remaining_time(token: str):
    """Get remaining time for a token in seconds"""
    payload = decode_jwt(token)
    if payload and 'exp' in payload:
        exp_timestamp = payload['exp']
        if isinstance(exp_timestamp, datetime):
            exp_timestamp = exp_timestamp.timestamp()
        remaining = exp_timestamp - time.time()
        return max(0, int(remaining))
    return 0

def is_token_expiring_soon(token: str, threshold_minutes: int = 5):
    """Check if token is expiring soon (for proactive refresh)"""
    remaining = get_token_remaining_time(token)
    return remaining <= (threshold_minutes * 60)

def revoke_token(token: str):
    """Revoke a token (add to blacklist)"""
    revoked_tokens.add(token)

class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
    
    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        
        if credentials:
            if credentials.scheme.lower() != 'bearer':
                raise HTTPException(
                    status_code=403, 
                    detail='Invalid authentication scheme. Must be "Bearer"'
                )
            
            # Extract just the token part (in case it includes "Bearer ")
            token = credentials.credentials.strip()
            if token.lower().startswith('bearer '):
                token = token[7:].strip()  # Remove "Bearer " prefix if present
            
            if not self.verify_token(token):
                raise HTTPException(status_code=403, detail='Invalid or expired token!')
            
            return token  # Return the clean token
        else:
            raise HTTPException(status_code=403, detail='Invalid authorization code!')
    
    def verify_token(self, jwt_token: str) -> bool:
        payload = decode_jwt(jwt_token)
        if payload is None or payload.get('type') != 'access':
            return False
        return True