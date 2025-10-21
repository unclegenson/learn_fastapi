
from fastapi import FastAPI,Request
from db import create_db_and_tables
import time
import datetime
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from routes.users_routes import router as users_router
from routes.posts_routes import router as post_router


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

# Remove the @app.on_event("startup") completely


app = FastAPI(lifespan=event_lifespan)


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

app.include_router(users_router,tags=['users'])
app.include_router(post_router,tags=['posts'])