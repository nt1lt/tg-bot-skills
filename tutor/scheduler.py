import asyncio
import logging
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter

from tutor.storage import Store

log = logging.getLogger(__name__)


def due_slots(settings: dict, now: datetime) -> list[str]:
    if settings.get("paused"):
        return []
    local = now.astimezone(ZoneInfo(settings["timezone"]))
    slots = []
    for time in settings["times"]:
        hour, minute = map(int, time.split(":"))
        scheduled = local.replace(hour=hour, minute=minute, second=0, microsecond=0)
        # No flood after downtime; a ten-minute grace period tolerates short restarts.
        delta = (local - scheduled).total_seconds()
        if 0 <= delta < 600:
            slots.append(f"{settings['timezone']}:{local.date()}:{time}")
    return slots


async def tick(store: Store, send, now: datetime | None = None):
    settings = store.settings()
    if not settings:
        return
    now = now or datetime.now(UTC)
    if settings.get("reminder_retry_at", 0) > now.timestamp():
        return
    for slot in due_slots(settings, now):
        if not store.claim_slot(slot):
            continue
        try:
            await send(settings["chat_id"])
        except TelegramForbiddenError:
            settings = store.settings()
            settings["paused"] = True
            store.save_settings(settings)
            log.warning("Reminders paused: bot blocked by owner")
            return
        except TelegramRetryAfter as exc:
            # Telegram definitely rejected the send, so allow a later tick to retry.
            store.release_slot(slot)
            settings = store.settings()
            settings["reminder_retry_at"] = now.timestamp() + exc.retry_after
            store.save_settings(settings)
            return
        except Exception as exc:  # noqa: BLE001 -- ambiguous delivery must retain the claimed slot
            # On ambiguous network failure, prefer avoiding duplicate invitations.
            log.warning("Invitation delivery failed (%s); slot retained", type(exc).__name__)


async def run_scheduler(store: Store, send):
    while True:
        try:
            await tick(store, send)
        except Exception as exc:  # noqa: BLE001 -- keep the background scheduler alive
            log.error("Scheduler tick failed (%s)", type(exc).__name__)
        await asyncio.sleep(30)
