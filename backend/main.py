import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.bot.handlers import bot, dp
from app.services.tmdb import tmdb_service
from app.db.session import Base, engine
from app.models.models import User, UserMovie

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("База данных успешно создана")

    polling_task = asyncio.create_task(dp.start_polling(bot))
    print("Бот успешно запущен")
    yield
    print("Остановка бота...")
    polling_task.cancel()
    try:
        await polling_task
    except asyncio.CancelledError:
        pass
    await bot.session.close()
    await engine.dispose()
    print("База данных и бот успешно остановлены")



app = FastAPI(title="Movie Mini App API",
            description="Backend API для Telegram Mini App с интеграцией TMDB",
            version="0.1.0",
            lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Проверочный эндпоинт для проверки работоспособности API"""
    return {"status": "ok", "message": "API работает в штатном режиме"}

@app.get("/api/movies/test")
async def test_tmdb():
    """Тестовый эндпоинт для проверки интеграции с TMDB"""
    data = await tmdb_service.get_popular_movies()
    return {
        "status": "success",
        "total_results": data.get("total_results"),
        "first_movie": data.get("results", [{}])[0].get("title"),
    }

