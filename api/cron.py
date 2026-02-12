"""Vercel cron endpoints for scheduled bot jobs."""

import os

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse

from api._app import bot
from bot.utils.scheduler import initialize_tasks, send_random_task, send_week_results


app = FastAPI()


def _check_cron_auth(authorization: str | None) -> None:
    secret = os.getenv("CRON_SECRET")
    if not secret:
        return
    if authorization != f"Bearer {secret}":
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/send-task")
async def cron_send_task(authorization: str | None = Header(default=None)) -> JSONResponse:
    _check_cron_auth(authorization)
    initialize_tasks()
    await send_random_task(bot)
    return JSONResponse({"ok": True, "job": "send-task"})


@app.get("/week-end")
async def cron_week_end(authorization: str | None = Header(default=None)) -> JSONResponse:
    _check_cron_auth(authorization)
    await send_week_results(bot)
    return JSONResponse({"ok": True, "job": "week-end"})
