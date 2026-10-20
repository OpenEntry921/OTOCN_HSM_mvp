import asyncio
import hmac
import json
import os
import time
from collections import defaultdict, deque
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.background import BackgroundTask
from webdemo.core import Engine, USERS, ASSETS, SCENARIOS

STATIC = Path(__file__).parent / "static"


def create_app(directory=None):
    engine = Engine(directory or os.getenv("DEMO_STATE_DIR", ".demo-state"))
    app = FastAPI(title="OT-OCN 실행 통제 데모")
    app.state.engine = engine
    attempts = defaultdict(deque)
    access_key = os.getenv("DEMO_ACCESS_KEY")

    @app.middleware("http")
    async def protect(request, call_next):
        # For public deployment set a shared demo password; HTTP Basic works for SSE too.
        if access_key:
            import base64

            try:
                raw = base64.b64decode(
                    request.headers.get("authorization", "").split(" ", 1)[1]
                ).decode()
                valid = hmac.compare_digest(raw.split(":", 1)[1], access_key)
            except (IndexError, ValueError, UnicodeError):
                valid = False
            if not valid:
                return JSONResponse(
                    {"detail": "데모 접근 인증 필요"},
                    401,
                    headers={"WWW-Authenticate": 'Basic realm="OT-OCN demo"'},
                )
        if request.method == "POST":
            if request.headers.get("sec-fetch-site") == "cross-site":
                return JSONResponse({"detail": "교차 사이트 요청 차단"}, 403)
            peer = request.client.host if request.client else "local"
            q = attempts[peer]
            now = time.monotonic()
            while q and q[0] < now - 60:
                q.popleft()
            if len(q) >= 30:
                return JSONResponse({"detail": "분당 30회 제한"}, 429)
            q.append(now)
            if int(request.headers.get("content-length", "0")) > 8192:
                return JSONResponse({"detail": "요청 크기 초과"}, 413)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'"
        )
        return response

    @app.get("/")
    def index():
        return FileResponse(STATIC / "index.html")

    app.mount("/static", StaticFiles(directory=STATIC), name="static")

    @app.get("/api/config")
    def config():
        return {"users": USERS, "assets": ASSETS, "scenarios": SCENARIOS}

    @app.post("/api/runs", status_code=202)
    async def run(request: Request):
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 8192:
                raise HTTPException(413, "요청 크기 초과")
        try:
            data = json.loads(body)
            rid, tx = engine.create(data)
        except (ValueError, TypeError):
            raise HTTPException(
                422,
                "입력값을 확인하세요. 필수 문자열·양수 수량·자산별 소수점 제한을 준수해야 합니다.",
            )
        return JSONResponse(
            {"request_id": rid},
            status_code=202,
            background=BackgroundTask(engine.process, rid, tx, data["scenario"]),
        )

    @app.get("/api/runs")
    def history():
        with engine.store.connect() as db:
            return [
                dict(r)
                for r in db.execute(
                    "SELECT id,created,result FROM runs ORDER BY created DESC LIMIT 50"
                )
            ]

    @app.get("/api/runs/{rid}")
    def detail(rid: str):
        data = engine.get(rid)
        if data is None:
            raise HTTPException(404, "실행 기록 없음")
        return data

    @app.get("/api/runs/{rid}/download")
    def download(rid: str):
        return JSONResponse(
            detail(rid),
            headers={
                "Content-Disposition": 'attachment; filename="execution-audit.json"'
            },
        )

    @app.get("/api/runs/{rid}/events")
    async def events(rid: str, request: Request, after: int = 0):
        if engine.get(rid) is None:
            raise HTTPException(404, "실행 기록 없음")
        try:
            cursor = max(after, int(request.headers.get("last-event-id", "0")))
        except ValueError:
            raise HTTPException(400, "잘못된 이벤트 순번")

        async def stream():
            nonlocal cursor
            while not await request.is_disconnected():
                for event in engine.store.events(rid, cursor):
                    cursor = event["seq"]
                    yield f"id: {cursor}\nevent: stage\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
                data = engine.get(rid)
                if data["result"] is not None:
                    # Completion may have committed after the first events read.
                    for event in engine.store.events(rid, cursor):
                        cursor = event["seq"]
                        yield f"id: {cursor}\nevent: stage\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
                    yield f"event: complete\ndata: {json.dumps(data['result'], ensure_ascii=False)}\n\n"
                    break
                yield ": heartbeat\n\n"
                await asyncio.sleep(0.2)

        return StreamingResponse(
            stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    return app


app = create_app()
