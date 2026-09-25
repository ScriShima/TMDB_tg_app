import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.bot.handlers import bot, dp
from app.services.tmdb import tmdb_service
from app.db.session import Base, engine
from app.models.models import User, UserMovie
from app.api.movies import router as movies_router
from app.api.user_movies import router as user_movies_router

async def start_bot():
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        print(f"Не удалось сбросить webhook, запускаю polling всё равно: {e}", flush=True)

    print("Бот успешно запущен, слушаю сообщения", flush=True)
    # uvicorn сам обрабатывает SIGINT/SIGTERM, поэтому сигналы aiogram отключаем
    await dp.start_polling(bot, handle_signals=False)

@asynccontextmanager
async def lifespan(app: FastAPI):

    polling_task = asyncio.create_task(start_bot())

    yield
    print("Остановка бота...", flush = True)
    polling_task.cancel()
    try:
        await polling_task
    except asyncio.CancelledError:
        pass
    await bot.session.close()
    await engine.dispose()
    print("База данных и бот успешно остановлены" flush = True)



app = FastAPI(title="Movie Mini App API",
            description="Backend API для Telegram Mini App с интеграцией TMDB",
            version="0.2.0",
            lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(movies_router)
app.include_router(user_movies_router)

@app.get("/health")
async def health_check():
    """Проверочный эндпоинт для проверки работоспособности API"""
    return {"status": "ok", "message": "API работает в штатном режиме"}
