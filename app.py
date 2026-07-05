from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
import time

EMAIL = "24f3004361@ds.study.iitm.ac.in"

ALLOWED_ORIGIN = "https://app-11q3ur.example.com"
RATE_LIMIT = 14
WINDOW_SECONDS = 10

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        ALLOWED_ORIGIN,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

buckets = {}

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        request_id = request.headers.get("X-Request-ID")

        if not request_id:
            request_id = str(uuid.uuid4())

        request.state.request_id = request_id

        response = await call_next(request)

        response.headers["X-Request-ID"] = request_id

        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        client_id = request.headers.get("X-Client-Id")

        if client_id:
            now = time.time()

            bucket = buckets.setdefault(client_id, [])

            bucket[:] = [
                t for t in bucket
                if now - t < WINDOW_SECONDS
            ]

            if len(bucket) >= RATE_LIMIT:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded"}
                )

            bucket.append(now)

        return await call_next(request)

app.add_middleware(RequestContextMiddleware)
app.add_middleware(RateLimitMiddleware)

@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }
