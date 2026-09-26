import asyncio
import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.bot.handlers import bot, dp
from app.core.config import settings
from app.db.session import engine
from app.api.movies import router as movies_router
from app.api.user_movies import router as user_movies_router
from app.services.tmdb import tmdb_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("movie_app")

async def start_bot():
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception as exc:
        logger.warning("Не удалось сбросить webhook, запускаю polling всё равно: %s", exc)

    logger.info("Бот успешно запущен, слушаю сообщения")
    while True:
        try:
            # uvicorn сам обрабатывает SIGINT/SIGTERM, поэтому сигналы aiogram отключаем
            await dp.start_polling(bot, handle_signals=False, close_bot_session=False)
            return
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Polling упал, перезапуск через 5 секунд")
            await asyncio.sleep(5)

@asynccontextmanager
async def lifespan(app: FastAPI):
    tmdb_service.start()
    polling_task = asyncio.create_task(start_bot())

    yield
    logger.info("Остановка бота...")
    polling_task.cancel()
    try:
        await polling_task
    except asyncio.CancelledError:
        pass
    await bot.session.close()
    await tmdb_service.close()
    await engine.dispose()
    logger.info("База данных и бот успешно остановлены")


app = FastAPI(
    title="Movie Mini App API",
    description="Backend API для Telegram Mini App с интеграцией TMDB",
    version="0.4.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(httpx.HTTPStatusError)
async def http_status_error_handler(request: Request, exc: httpx.HTTPStatusError):
    logger.error("Ошибка TMDB API: %s - %s", exc.response.status_code, exc.request.url)
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": "Сервис подбора фильмов временно недоступен"},
    )

@app.exception_handler(httpx.RequestError)
async def http_request_error_handler(request: Request, exc: httpx.RequestError):
    logger.error("Сетевой сбой при запросе к TMDB: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        content={"detail": "Превышено время ожидания ответа от каталога"},
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        raise exc
    logger.exception("Непредвиденная ошибка при обработке %s", request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Внутренняя ошибка сервера"},
    )

app.include_router(movies_router)
app.include_router(user_movies_router)

@app.get("/health")
async def health_check():
    """Проверка API и соединения с базой"""
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception:
        logger.exception("База данных недоступна")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "error", "message": "База данных недоступна"},
        )
    return {"status": "ok", "message": "API работает в штатном режиме"}
