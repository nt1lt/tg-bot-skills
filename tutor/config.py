import os
import re
from dataclasses import dataclass
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dotenv import load_dotenv


def parse_schedule(value: str) -> tuple[str, list[str]]:
    parts = value.strip().split(maxsplit=1)
    if len(parts) != 2:
        raise ValueError("Формат: Europe/Moscow 10:00,14:00,19:00")
    timezone, raw = parts
    try:
        ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError("Неизвестный часовой пояс. Пример: Europe/Moscow") from exc
    times = sorted({t.strip() for t in raw.split(",")})
    if not 1 <= len(times) <= 6 or any(not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", t) for t in times):
        raise ValueError("Укажите от 1 до 6 времён в формате ЧЧ:ММ через запятую.")
    return timezone, times


@dataclass(frozen=True)
class Config:
    token: str
    owner_id: int
    api_key: str
    base_url: str
    model: str
    json_mode: str
    timezone: str
    times: list[str]
    database: str

    @classmethod
    def load(cls) -> "Config":
        load_dotenv()
        required = ("TELEGRAM_BOT_TOKEN", "TELEGRAM_OWNER_ID", "LLM_API_KEY", "LLM_MODEL")
        missing = [key for key in required if not os.getenv(key, "").strip()]
        if missing:
            raise ValueError("Заполните .env: " + ", ".join(missing))
        owner_id = int(os.environ["TELEGRAM_OWNER_ID"])
        if owner_id <= 0:
            raise ValueError("TELEGRAM_OWNER_ID должен быть положительным числом")
        timezone, times = parse_schedule(
            os.getenv("TIMEZONE", "Europe/Moscow") + " " + os.getenv("LESSON_TIMES", "10:00,14:00,19:00")
        )
        mode = os.getenv("LLM_JSON_MODE", "schema")
        if mode not in {"schema", "json", "prompt"}:
            raise ValueError("LLM_JSON_MODE: schema, json или prompt")
        return cls(
            os.environ["TELEGRAM_BOT_TOKEN"],
            owner_id,
            os.environ["LLM_API_KEY"],
            os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
            os.environ["LLM_MODEL"],
            mode,
            timezone,
            times,
            os.getenv("DATABASE_PATH", "data/tutor.sqlite3"),
        )
