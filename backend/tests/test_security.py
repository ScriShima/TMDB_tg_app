import hashlib
import hmac
import json
import time
import asyncio
from urllib.parse import urlencode

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.config import settings
from app.core.security import get_current_user, validate_telegram_data


def _sign(bot_token: str, fields: dict) -> str:
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    return hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()


def _init_data(bot_token: str, *, auth_date: int | None = None, user: dict | None = None) -> str:
    payload_user = user or {"id": 42, "first_name": "Ada", "username": "ada"}
    fields = {
        "auth_date": str(auth_date if auth_date is not None else int(time.time())),
        "query_id": "AAE",
        "user": json.dumps(payload_user, separators=(",", ":")),
    }
    fields["hash"] = _sign(bot_token, fields)
    return urlencode(fields)


def test_valid_init_data(monkeypatch):
    monkeypatch.setattr(settings, "bot_token", "123:token")
    user = validate_telegram_data(_init_data("123:token"))
    assert user.id == 42
    assert user.first_name == "Ada"
    assert user.username == "ada"


def test_bad_signature_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "bot_token", "123:token")
    raw = _init_data("other:token")
    with pytest.raises(HTTPException) as exc:
        validate_telegram_data(raw)
    assert exc.value.status_code == 401


def test_expired_init_data_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "bot_token", "123:token")
    raw = _init_data("123:token", auth_date=int(time.time()) - 90000)
    with pytest.raises(HTTPException) as exc:
        validate_telegram_data(raw)
    assert exc.value.status_code == 401


def test_dev_token_is_disabled_by_default(monkeypatch):
    monkeypatch.setattr(settings, "dev_auth_enabled", False)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="dev-test")
    with pytest.raises(HTTPException) as exc:
        asyncio.run(get_current_user(credentials))
    assert exc.value.status_code == 401


def test_dev_token_uses_configured_id(monkeypatch):
    monkeypatch.setattr(settings, "dev_auth_enabled", True)
    monkeypatch.setattr(settings, "dev_user_id", 7)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="dev-test")
    user = asyncio.run(get_current_user(credentials))
    assert user.id == 7
    assert user.first_name == "Dev"
