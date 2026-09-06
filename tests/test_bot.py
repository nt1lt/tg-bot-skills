from itertools import count
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError, TelegramRetryAfter
from aiogram.methods import DeleteMessage, SendMessage

from tutor.bot import TelegramTutor, chunks
from tutor.config import parse_schedule
from tutor.engine import LessonEngine
from tutor.storage import Store


def message(text, user=42, chat_type="private"):
    return SimpleNamespace(
        text=text, from_user=SimpleNamespace(id=user), chat=SimpleNamespace(id=user, type=chat_type)
    )


def app(config, store, llm):
    bot = AsyncMock()
    ids = count(1)
    bot.send_message.side_effect = lambda *args, **kwargs: SimpleNamespace(message_id=next(ids))
    return TelegramTutor(bot, config, store, LessonEngine(store, llm))


async def test_complete_telegram_flow(config, store, llm):
    tutor = app(config, store, llm)
    await tutor.message(message("/start"))
    await tutor.message(message("📚 Урок"))
    sid = store.session()["id"]
    await tutor.handle_callback(42, f"s:{sid}:material")
    await tutor.message(message("Почему это полезно?"))
    llm.answer.assert_awaited_once()
    await tutor.handle_callback(42, f"s:{sid}:quiz")
    for i in range(4):
        await tutor.message(message(f"Мой ответ {i}"))
    assert store.progress()["01.01"] == "passed"
    assert store.session()["stage"] == "result"
    await tutor.handle_callback(42, f"s:{sid}:next")
    assert store.session()["lesson_id"] == "01.02"


async def test_only_owner_in_private_chat(config, store, llm):
    tutor = app(config, store, llm)
    await tutor.message(message("/start", user=99))
    await tutor.message(message("/start", chat_type="group"))
    tutor.bot.send_message.assert_not_called()
    assert store.settings() is None


async def test_stale_buttons_do_not_modify_quiz(config, store, llm):
    tutor = app(config, store, llm)
    tutor.initialize(42)
    session = tutor.engine.start("01.01")
    await tutor.engine.quiz(session)
    prefix = f"s:{session['id']}:"
    await tutor.handle_callback(42, prefix + "unknown:0")
    await tutor.handle_callback(42, prefix + "unknown:0")
    await tutor.handle_callback(42, prefix + "quiz")
    assert store.session()["answers"] == ["Не знаю"]
    tutor.engine.start("02.01")
    await tutor.handle_callback(42, prefix + "later")
    assert store.session()["lesson_id"] == "02.01"


async def test_navigation_and_reminder_preserve_active_lesson(config, store, llm):
    tutor = app(config, store, llm)
    tutor.initialize(42)
    session = tutor.engine.start("01.01")
    await tutor.engine.quiz(session)
    tutor.engine.record_answer(session, "Первый ответ")
    await tutor.topics(42)
    await tutor.topic(42, 30, 1)
    await tutor.invitation(42)
    await tutor.handle_callback(42, "pick:30.07")
    assert store.session()["answers"] == ["Первый ответ"]
    await tutor.handle_callback(42, f"replace:{session['id']}:30.07")
    assert store.session()["lesson_id"] == "30.07"


async def test_schedule_does_not_become_quiz_answer(config, store, llm):
    tutor = app(config, store, llm)
    tutor.initialize(42)
    session = tutor.engine.start("01.01")
    await tutor.engine.quiz(session)
    await tutor.handle_callback(42, "schedule:edit")
    await tutor.message(message("Europe/Moscow 09:00,18:00"))
    assert store.settings()["times"] == ["09:00", "18:00"]
    assert store.session()["answers"] == []
    await tutor.message(message("/progress"))
    assert store.session()["answers"] == []


@pytest.mark.parametrize(
    "bad", ["Europe/Moscow 25:00", "No/Zone 10:00", "10:00", "Europe/Moscow 9:00", "Europe/Moscow "]
)
def test_invalid_schedule(bad):
    with pytest.raises(ValueError):
        parse_schedule(bad)


def test_valid_schedule_and_message_limits():
    assert parse_schedule("Europe/Moscow 19:00,10:00,10:00")[1] == ["10:00", "19:00"]
    assert all(len(c.encode("utf-16-le")) // 2 <= 4096 for c in chunks("🙂" * 10000))


async def test_callback_lengths(config, store, llm):
    tutor = app(config, store, llm)
    tutor.initialize(42)
    await tutor.topics(42, 5)
    await tutor.topic(42, 30, 1)
    for call in tutor.bot.send_message.await_args_list:
        markup = call.kwargs.get("reply_markup")
        if markup:
            assert all(len(b.callback_data.encode()) <= 64 for row in markup.inline_keyboard for b in row)


async def test_telegram_rate_limit_retries_same_chunk(config, store, llm, monkeypatch):
    tutor = app(config, store, llm)
    sleep = AsyncMock()
    monkeypatch.setattr("tutor.bot.asyncio.sleep", sleep)
    tutor.bot.send_message.side_effect = [
        TelegramRetryAfter(method=SendMessage(chat_id=42, text="x"), message="slow down", retry_after=2),
        SimpleNamespace(message_id=1),
    ]
    await tutor.send(42, "Текст урока")
    sleep.assert_awaited_once_with(2)
    assert tutor.bot.send_message.await_count == 2
    assert tutor.bot.send_message.await_args_list[0] == tutor.bot.send_message.await_args_list[1]


async def test_catalog_pages_replace_all_previous_chunks(config, store, llm):
    tutor = app(config, store, llm)
    await tutor.topics(42)
    first_page = store.service_messages(42)
    assert first_page
    await tutor.topics(42, 1)
    assert [call.args[1] for call in tutor.bot.delete_message.await_args_list] == first_page
    assert not set(first_page) & set(store.service_messages(42))
    await tutor.send(42, "Большое меню " * 1000)
    long_page = store.service_messages(42)
    assert len(long_page) > 1
    tutor.bot.delete_message.reset_mock()
    await tutor.topic(42, 30, 0)
    assert [call.args[1] for call in tutor.bot.delete_message.await_args_list] == long_page


async def test_lesson_history_survives_navigation_and_cleanup(config, store, llm):
    tutor = app(config, store, llm)
    tutor.initialize(42)
    await tutor.topics(42)
    menu_ids = set(store.service_messages(42))
    await tutor.lesson(42)
    assert store.service_messages(42) == []
    sid = store.session()["id"]
    await tutor.handle_callback(42, f"s:{sid}:material")
    await tutor.message(message("Уточните пример"))
    await tutor.handle_callback(42, f"s:{sid}:quiz")
    for _ in range(4):
        await tutor.message(message("Ответ"))
    assert store.session()["stage"] == "result"
    assert store.service_messages(42) == []
    sent_texts = {i: call.args[1] for i, call in enumerate(tutor.bot.send_message.await_args_list, 1)}
    expected_deleted = menu_ids | {
        i
        for i, text in sent_texts.items()
        if text in {"Готовлю объяснение…", "Готовлю тест…", "Все ответы сохранены. Проверяю тест…"}
    }
    await tutor.topics(42)
    await tutor.schedule(42)
    deleted = {call.args[1] for call in tutor.bot.delete_message.await_args_list}
    assert deleted & set(sent_texts) == expected_deleted


async def test_cleanup_survives_restart(config, tmp_path, llm):
    path = str(tmp_path / "messages.sqlite3")
    first = Store(path)
    tutor = app(config, first, llm)
    await tutor.topics(42)
    tracked = first.service_messages(42)
    first.close()
    second = Store(path)
    try:
        restarted = app(config, second, llm)
        restarted.bot.send_message.side_effect = lambda *a, **kw: SimpleNamespace(message_id=1000)
        await restarted.topics(42, 1)
        assert [call.args[1] for call in restarted.bot.delete_message.await_args_list] == tracked
        assert second.service_messages(42) == [1000]
    finally:
        second.close()


async def test_failed_send_keeps_old_menu_and_tracks_partial_screen(config, store, llm):
    tutor = app(config, store, llm)
    await tutor.send(42, "Текущее меню")
    tutor.bot.send_message.side_effect = [
        SimpleNamespace(message_id=2),
        TelegramNetworkError(method=SendMessage(chat_id=42, text="x"), message="network failure"),
    ]
    with pytest.raises(TelegramNetworkError):
        await tutor.send(42, "x" * 2000)
    tutor.bot.delete_message.assert_not_called()
    assert store.service_messages(42) == [1, 2]
    tutor.bot.send_message.side_effect = [SimpleNamespace(message_id=3)]
    await tutor.send(42, "Новое меню")
    assert store.service_messages(42) == [3]
    assert [call.args[1] for call in tutor.bot.delete_message.await_args_list] == [1, 2]


@pytest.mark.parametrize("temporary", [False, True])
async def test_cleanup_failure_does_not_break_new_screen(config, store, llm, temporary):
    tutor = app(config, store, llm)
    await tutor.send(42, "Старое меню")
    error = TelegramNetworkError if temporary else TelegramBadRequest
    tutor.bot.delete_message.side_effect = error(
        method=DeleteMessage(chat_id=42, message_id=1), message="Cannot delete"
    )
    await tutor.send(42, "Новое меню")
    assert store.service_messages(42) == ([1, 2] if temporary else [2])
