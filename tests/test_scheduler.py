from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram.methods import SendMessage

from tutor.scheduler import due_slots, tick
from tutor.storage import Store

NOW = datetime(2026, 9, 6, 7, 0, tzinfo=UTC)


def settings():
    return {"chat_id": 42, "timezone": "Europe/Moscow", "times": ["10:00", "14:00", "19:00"], "paused": False}


async def test_invitation_once_even_after_restart(tmp_path):
    path = str(tmp_path / "state.sqlite3")
    first = Store(path)
    first.save_settings(settings())
    send = AsyncMock()
    await tick(first, send, NOW)
    first.close()
    second = Store(path)
    await tick(second, send, NOW + timedelta(minutes=1))
    send.assert_awaited_once_with(42)
    second.close()


def test_timezone_and_no_downtime_flood():
    assert len(due_slots(settings(), NOW)) == 1
    assert due_slots(settings(), NOW - timedelta(seconds=1)) == []
    assert due_slots(settings(), NOW + timedelta(minutes=10)) == []
    assert due_slots({**settings(), "paused": True}, NOW) == []


async def test_never_contacts_owner_before_start(store):
    send = AsyncMock()
    await tick(store, send, NOW)
    send.assert_not_called()


async def test_blocked_bot_pauses_reminders(store):
    store.save_settings(settings())
    send = AsyncMock(
        side_effect=TelegramForbiddenError(method=SendMessage(chat_id=42, text="x"), message="blocked")
    )
    await tick(store, send, NOW)
    assert store.settings()["paused"]


async def test_rate_limit_is_respected(store):
    store.save_settings(settings())
    send = AsyncMock(
        side_effect=TelegramRetryAfter(
            method=SendMessage(chat_id=42, text="x"), message="rate limited", retry_after=120
        )
    )
    await tick(store, send, NOW)
    await tick(store, send, NOW + timedelta(seconds=30))
    assert send.await_count == 1
    send.side_effect = None
    await tick(store, send, NOW + timedelta(seconds=120))
    assert send.await_count == 2


async def test_ambiguous_failure_does_not_duplicate(store):
    store.save_settings(settings())
    send = AsyncMock(side_effect=TimeoutError())
    await tick(store, send, NOW)
    await tick(store, send, NOW + timedelta(minutes=1))
    assert send.await_count == 1


async def test_dst_repeated_hour_has_one_invitation(store):
    store.save_settings({**settings(), "timezone": "America/New_York", "times": ["01:30"]})
    send = AsyncMock()
    await tick(store, send, datetime(2026, 11, 1, 5, 30, tzinfo=UTC))
    await tick(store, send, datetime(2026, 11, 1, 6, 30, tzinfo=UTC))
    assert send.await_count == 1
