from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
import time

EMAIL = "24f3004361@ds.study.iitm.ac.in"

RATE_LIMIT = 14
WINDOW_SECONDS = 10

app = FastAPI()

# -----------------------------
# CORS Middleware
# -----------------------------
@app.middleware("http")
async def cors_middleware(request: Request, call_next):

    origin = request.headers.get("origin")

    if request.method == "OPTIONS":
        response = JSONResponse({"ok": True})

        if origin:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
            response.headers["Access-Control-Allow-Credentials"] = "true"

        return response

    response = await call_next(request)

    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"

    return response

# -----------------------------
# Rate Limiter
# -----------------------------
buckets = {}

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

# -----------------------------
# Request Context Middleware
# -----------------------------
class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        request_id = request.headers.get("X-Request-ID")

        if not request_id:
            request_id = str(uuid.uuid4())

        request.state.request_id = request_id

        response = await call_next(request)

        response.headers["X-Request-ID"] = request_id

        return response

app.add_middleware(RequestContextMiddleware)
app.add_middleware(RateLimitMiddleware)

# -----------------------------
# Ping Endpoint
# -----------------------------
@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }

@app.options("/ping")
async def ping_options():
    return {"ok": True}

@app.get("/")
async def root():
    return {"status": "ok"}
