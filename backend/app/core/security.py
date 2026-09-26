import hmac
import hashlib
import json
import time
from urllib.parse import parse_qsl
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from app.core.config import settings

class TelegramUser(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None
    is_premium: Optional[bool] = None

def validate_telegram_data(init_data: str) -> TelegramUser:
    """Проверяет валидность строки initdata"""
    if not init_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Отсутствуют данные авторизации",
        )

    try:
        parsed_data = dict(parse_qsl(init_data, keep_blank_values=True))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Некорректный формат данных авторизации",
        )

    received_hash = parsed_data.pop("hash", None)
    if not received_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Отсутствует хэш авторизации",
        )

    try:
        auth_date = int(parsed_data.get("auth_date", "0"))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Некорректное поле auth_date",
        )
    if int(time.time()) - auth_date > 86400:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Сессия Telegram WebApp просрочена",
        )

    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed_data.items())
    )

    secret_key = hmac.new(
        b"WebAppData",
        settings.bot_token.encode(),
        hashlib.sha256,
    ).digest()
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительная подпись данных",
        )

    user_raw = parsed_data.get("user")
    if not user_raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Поле user отсутствует в init_data",
        )

    user_dict = json.loads(user_raw)
    return TelegramUser(**user_dict)


_bearer = HTTPBearer(
    auto_error=False,
    description="Заголовок Authorization: Telegram initData. Префикс Bearer подставится сам.",
)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> TelegramUser:
    """Зависимость FastAPI для получения текущего пользователя"""
    token = credentials.credentials.strip() if credentials else ""
    if settings.dev_auth_enabled and token == "dev-test":
        return TelegramUser(
            id=settings.dev_user_id,
            first_name="Dev",
            username="dev",
        )
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется заголовок Authorization",
        )

    return validate_telegram_data(token)
