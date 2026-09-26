import logging

from aiogram import Router, Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from app.core.config import settings
from sqlalchemy import select
from app.db.session import async_session_maker
from app.models.models import User

logger = logging.getLogger("movie_app.bot")

bot_router = Router()
bot = Bot(token=settings.bot_token)
dp = Dispatcher()

WEBAPP_URL = settings.webapp_url

@bot_router.message(CommandStart())
async def cmd_start(message: Message):
    tg_user = message.from_user
    if not tg_user:
        return

    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.id == tg_user.id))
        user = result.scalar_one_or_none()

        if not user:
            user = User(id=tg_user.id, first_name=tg_user.first_name, username=tg_user.username)
            session.add(user)
            await session.commit()
            logger.info("Зарегистрирован новый пользователь: %s (ID: %s)", tg_user.first_name, tg_user.id)
        else:
            user.first_name = tg_user.first_name
            user.username = tg_user.username
            await session.commit()

    keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎬 Открыть Movie App",
                web_app=WebAppInfo(url=WEBAPP_URL),
            )
        ]
    ]
)

    await message.answer(f"Привет, {tg_user.first_name}! \n\n"
                        "Я помогу тебе выбрать фильм на вечер и сохранить просмотренное в твой личный профиль. \n"
                        "Нажми на кнопку ниже, чтобы открыть Movie App и начать выбор фильма.", reply_markup=keyboard)
    
dp.include_router(bot_router)