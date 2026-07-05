from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
import uuid
import time

app = FastAPI()

EMAIL = "24f3004361@ds.study.iitm.ac.in"
RATE_LIMIT = 14
WINDOW_SECONDS = 10

buckets = {}

@app.middleware("http")
async def rate_limit(request: Request, call_next):
    client_id = request.headers.get("X-Client-Id")

    if client_id:
        now = time.time()

        bucket = buckets.setdefault(client_id, [])
        bucket[:] = [t for t in bucket if now - t < WINDOW_SECONDS]

        if len(bucket) >= RATE_LIMIT:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"}
            )

        bucket.append(now)

    return await call_next(request)

@app.options("/ping")
async def options_ping():
    response = Response(status_code=200)
    response.headers["Access-Control-Allow-Origin"] = "https://app-11q3ur.example.com"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

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

    # Explicitly set header on the final response object
    response.headers["X-Request-ID"] = request_id

    origin = request.headers.get("Origin")

    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"

    return response

@app.get("/")
async def root():
    return {"status": "ok"}
