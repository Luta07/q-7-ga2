from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
import uuid
import time

app = FastAPI()

EMAIL = "24f3004361@ds.study.iitm.ac.in"
RATE_LIMIT = 14
WINDOW_SECONDS = 10

# Per-client rate limit storage
buckets = {}

# ----------------------------
# CORS Middleware
# ----------------------------
@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    origin = request.headers.get("Origin")

    # Handle preflight requests
    if request.method == "OPTIONS":
        response = Response(status_code=200)

        if origin:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
            response.headers["Access-Control-Allow-Credentials"] = "true"

        return response

    response = await call_next(request)

    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"

    return response

# ----------------------------
# Rate Limiting Middleware
# ----------------------------
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_id = request.headers.get("X-Client-Id")

    if client_id:
        now = time.time()

        bucket = buckets.setdefault(client_id, [])

        # Keep only timestamps within last 10 seconds
        bucket[:] = [t for t in bucket if now - t < WINDOW_SECONDS]

        if len(bucket) >= RATE_LIMIT:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"}
            )

        bucket.append(now)

    return await call_next(request)

# ----------------------------
# OPTIONS /ping
# ----------------------------
@app.options("/ping")
async def options_ping():
    return Response(status_code=200)

# ----------------------------
# GET /ping
# ----------------------------
@app.get("/ping")
async def ping(request: Request):
    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        request_id = str(uuid.uuid4())

    response = JSONResponse(
        content={
            "email": EMAIL,
            "request_id": request_id
        }
    )

    # Echo request id in response header
    response.headers["X-Request-ID"] = request_id

    return response

# ----------------------------
# Root endpoint
# ----------------------------
@app.get("/")
async def root():
    return {"status": "ok"}
