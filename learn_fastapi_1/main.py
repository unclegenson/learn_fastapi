
from fastapi import FastAPI,Request
from db import create_db_and_tables
import time
import datetime
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from jwt_auth import get_token_remaining_time, is_token_expiring_soon

from routes.users_routes import router as users_router
from routes.posts_routes import router as post_router
from routes.auth_routes import router as auth_router




@asynccontextmanager
async def event_lifespan(app):
    print('server starts at', datetime.datetime.now())
    # Do startup tasks here
    create_db_and_tables()  # Move it here
    
    with open('server_time_log','a') as log:
        log.write(f'server starts at {datetime.datetime.now()}\n')
    
    yield  # The app runs here
    
    # Do shutdown tasks here
    with open('server_time_log','a') as log:
        log.write(f'server shut downs at {datetime.datetime.now()}\n')


app = FastAPI(lifespan=event_lifespan)

@app.middleware('http')
async def token_expiration_middleware(request: Request, call_next):
    response = await call_next(request)
    
    # Check if this is an authenticated request
    auth_header = request.headers.get('authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header[7:]
        remaining = get_token_remaining_time(token)
        
        # Add headers to inform client about token status
        response.headers['X-Token-Expires-In'] = str(remaining)
        response.headers['X-Token-Expiring-Soon'] = str(is_token_expiring_soon(token))
    
    return response

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
        current_time = datetime.datetime.now()
        
        # Get or initialize request data
        if client_ip in self.requests_count:
            request_count, last_request = self.requests_count[client_ip]
            elapsed_time = current_time - last_request
            
            # Reset counter if time window has passed
            if elapsed_time > self.RATE_LIMIT_DURATION:
                request_count = 0
            else:
                # Check rate limit
                if request_count >= self.RATE_LIMIT_REQUESTS:
                    return JSONResponse(
                        status_code=429,  
                        content={'message': 'Rate limit exceeded! Try again later.'}
                    )
        else:
            request_count = 0
        
        request_count += 1
        self.requests_count[client_ip] = (request_count, current_time)
        
        response = await call_next(request)
        return response

app.add_middleware(RateLimitMiddleware)

app.include_router(auth_router,tags=['auth'])
app.include_router(users_router,tags=['users'])
app.include_router(post_router,tags=['posts'])

@app.get("/")
async def root():
    return {"message": "Welcome to the API"}


# access: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImFkbWluQGdtYWlsLmNvbSIsInVzZXJfaWQiOjEsImV4cCI6MTc2MTIzODIyMi45ODE0NzE4LCJ0eXBlIjoiYWNjZXNzIn0.WQltjEIycpk9j0GAuqqaVIaVLsMxlaH9-_GIHB6SEQk
# refresh: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGdtYWlsLmNvbSIsImV4cCI6MTc2MzgwODYyMi45ODE1NjMzLCJ0eXBlIjoicmVmcmVzaCJ9.QkJ32u-e7O4CtzxQcnQvjvqRC9CzuWyPNp1kaJD_d8U

