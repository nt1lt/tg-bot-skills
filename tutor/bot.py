import asyncio
import logging
from contextlib import suppress

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest, TelegramRetryAfter
from aiogram.types import (
    BotCommand,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)

from tutor.config import Config, parse_schedule
from tutor.curriculum import LESSONS, TOPICS, aggregate_status
from tutor.engine import LessonEngine
from tutor.llm import LLMError, TutorLLM
from tutor.scheduler import run_scheduler
from tutor.storage import Store

log = logging.getLogger(__name__)
STATUS = {"passed": "✅ Пройдена", "not_started": "⬜ Не пройдена", "failed": "❌ Провалено тестирование"}
MAIN = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📚 Урок"), KeyboardButton(text="🗂 Все темы")],
        [KeyboardButton(text="📊 Прогресс"), KeyboardButton(text="⏰ Расписание")],
    ],
    resize_keyboard=True,
)


def keyboard(rows: list[list[tuple[str, str]]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data=data) for label, data in row] for row in rows
        ]
    )


def chunks(text: str, limit: int = 3500) -> list[str]:
    # Telegram measures length in UTF-16 units; 1,750 codepoints are safe even for all-emoji output.
    limit = min(limit, 1750)
    result = []
    while len(text) > limit:
        cut = text.rfind("\n", 0, limit)
        if cut < limit // 2:
            cut = limit
        result.append(text[:cut])
        text = text[cut:].lstrip("\n")
    return result + ([text] if text else [])


class TelegramTutor:
    def __init__(self, bot: Bot, config: Config, store: Store, engine: LessonEngine):
        self.bot, self.config, self.store, self.engine = bot, config, store, engine
        self.lock = asyncio.Lock()
        self.output_lock = asyncio.Lock()

    async def send(self, chat: int, text: str, markup=None, *, preserve: bool = False):
        """Replace service screens, but keep the complete lesson conversation.

        Send the new screen first so a failed send does not remove the current controls.
        Track each chunk immediately so partial sends can be cleaned up on the next action.
        The output lock also serializes invitations with foreground replies.
        """
        async with self.output_lock:
            previous = self.store.service_messages(chat)
            parts = chunks(text)
            for i, part in enumerate(parts):
                try:
                    sent = await self.bot.send_message(
                        chat, part, reply_markup=markup if i == len(parts) - 1 else None
                    )
                except TelegramRetryAfter as exc:
                    # Retry only an explicitly rejected send, never an ambiguous timeout.
                    await asyncio.sleep(exc.retry_after)
                    sent = await self.bot.send_message(
                        chat, part, reply_markup=markup if i == len(parts) - 1 else None
                    )
                if not preserve:
                    self.store.track_service_message(chat, sent.message_id)
            await self.clear_service_messages(chat, previous)

    async def clear_service_messages(self, chat: int, message_ids: list[int]):
        for message_id in message_ids:
            try:
                await self.bot.delete_message(chat, message_id)
            except TelegramBadRequest:
                # Already deleted or too old for Telegram to allow deletion.
                pass
            except TelegramAPIError as exc:
                # Keep the ID for a later cleanup; the current screen remains usable.
                log.warning("Service message cleanup deferred (%s)", type(exc).__name__)
                continue
            self.store.forget_service_message(chat, message_id)

    def authorized(self, user: int, chat: int, chat_type: str) -> bool:
        return user == self.config.owner_id and chat == user and chat_type == "private"

    def initialize(self, chat: int):
        if not self.store.settings():
            self.store.save_settings(
                {
                    "chat_id": chat,
                    "timezone": self.config.timezone,
                    "times": self.config.times,
                    "paused": False,
                    "editing_schedule": False,
                }
            )

    async def message(self, message: Message):
        if not message.from_user or not self.authorized(
            message.from_user.id, message.chat.id, message.chat.type
        ):
            return
        if self.lock.locked():
            await self.send(
                message.chat.id, "Ещё обрабатываю предыдущий запрос. Отправьте сообщение после ответа."
            )
            return
        async with self.lock:
            try:
                await self.handle_message(message)
            except LLMError as exc:
                await self.show_error(message.chat.id, str(exc))
            except Exception as exc:  # noqa: BLE001 -- isolate updates; never log secret-bearing API errors
                log.error("Message handling failed (%s)", type(exc).__name__)
                await self.send(
                    message.chat.id, "Не удалось завершить действие. Откройте /lesson для продолжения.", MAIN
                )

    async def callback(self, query: CallbackQuery):
        if not query.message or not self.authorized(
            query.from_user.id, query.message.chat.id, query.message.chat.type
        ):
            await query.answer("Это личный бот.")
            return
        if self.lock.locked():
            await query.answer("Обрабатываю предыдущий запрос…")
            return
        await query.answer()
        async with self.lock:
            try:
                self.initialize(query.message.chat.id)
                # Adopt clicked navigation screens sent before message tracking was introduced.
                # Never adopt s:* buttons: those can belong to retained lesson content.
                data = query.data or ""
                if data.startswith(("topics:", "topic:", "pick:", "replace:", "schedule:")) or data in {
                    "lesson",
                    "invite",
                }:
                    self.store.track_service_message(query.message.chat.id, query.message.message_id)
                await self.handle_callback(query.message.chat.id, query.data or "")
            except LLMError as exc:
                await self.show_error(query.message.chat.id, str(exc))
            except Exception as exc:  # noqa: BLE001 -- isolate updates; never log secret-bearing API errors
                log.error("Callback handling failed (%s)", type(exc).__name__)
                await self.send(
                    query.message.chat.id, "Не удалось завершить действие. Откройте /lesson.", MAIN
                )

    async def show_error(self, chat: int, error: str):
        session = self.store.session()
        markup = self.actions(session) if session else MAIN
        await self.send(chat, error + "\nПрогресс сохранён. Повторите действие кнопкой ниже.", markup)

    def actions(self, session: dict):
        prefix = f"s:{session['id']}:"
        stage = session["stage"]
        if stage == "familiar":
            rows = [[("Не знаю — объясни", prefix + "material")], [("Знаю — сразу тест", prefix + "quiz")]]
        elif stage == "questions":
            rows = [[("Вопросов нет — к тесту", prefix + "quiz")]]
        elif stage == "quiz":
            rows = [[("Не знаю ответ", prefix + f"unknown:{len(session['answers'])}")]]
        elif stage == "grading":
            rows = [[("Повторить проверку", prefix + "grade")]]
        else:
            rows = [
                [("Разобрать заново", prefix + "retry"), ("Повторить тест", prefix + "retest")],
                [("Следующий урок", prefix + "next")],
            ]
        rows.append([("Отложить на завтра", prefix + "later")])
        return keyboard(rows)

    async def show_session(self, chat: int, session: dict):
        lesson = LESSONS[session["lesson_id"]]
        title = f"{lesson.id} · {lesson.title}\n\n"
        if session["stage"] == "familiar":
            text = title + "Знакома ли вам эта тема?\n\n" + lesson.scope
        elif session["stage"] == "questions":
            text = (
                title
                + session["material"]
                + "\n\nЗадавайте вопросы текстом. Когда будете готовы, нажмите «К тесту»."
            )
        elif session["stage"] == "quiz":
            index = len(session["answers"])
            text = (
                title
                + f"Вопрос {index + 1} из {len(session['questions'])}\n\n"
                + session["questions"][index]["text"]
            )
            text += "\n\nОтветьте одним сообщением. Разбор будет после всего теста."
        elif session["stage"] == "grading":
            text = title + "Все ответы сохранены. Осталось проверить тест."
        else:
            result = session["result"]
            text = title + ("✅ Тема пройдена!" if session["passed"] else "❌ Тестирование не пройдено.")
            text += f"\nБаллы: {session['score']}/{session['maximum']}. Порог — 80%.\n"
            for i, mark in enumerate(result["marks"], 1):
                text += f"\n{i}. {mark['score']}/2 — {mark['feedback']}\n"
            text += "\n" + result["summary"]
        await self.send(chat, text, self.actions(session), preserve=session["stage"] != "grading")

    async def lesson(self, chat: int):
        session = self.store.session()
        if session:
            await self.show_session(chat, session)
            return
        lesson_id = self.engine.next_lesson()
        if lesson_id:
            await self.show_session(chat, self.engine.start(lesson_id))
        else:
            await self.send(
                chat,
                "Все доступные уроки пройдены или отложены до завтра. "
                "В «Все темы» можно выбрать любой урок вручную.",
                MAIN,
            )

    async def topics(self, chat: int, page: int = 0):
        page = max(0, min(page, (len(TOPICS) - 1) // 5))
        progress = self.store.progress()
        rows, lines = (
            [],
            [
                f"Учебный план · страница {page + 1}/{(len(TOPICS) + 4) // 5}",
                "Раздел засчитывается после теста; тема — когда пройдены все её разделы.",
            ],
        )
        for topic in TOPICS[page * 5 : page * 5 + 5]:
            states = [progress.get(item.id, "not_started") for item in topic.lessons]
            status = aggregate_status(states)
            done = states.count("passed")
            lines.append(
                f"\n{topic.stage}\n{topic.id}. {topic.title} — {STATUS[status]} ({done}/{len(states)})"
            )
            rows.append([(f"{topic.id}. {topic.title}", f"topic:{topic.id}:0")])
        navigation = []
        if page > 0:
            navigation.append(("← Назад", f"topics:{page - 1}"))
        if (page + 1) * 5 < len(TOPICS):
            navigation.append(("Далее →", f"topics:{page + 1}"))
        if navigation:
            rows.append(navigation)
        await self.send(chat, "\n".join(lines), keyboard(rows))

    async def topic(self, chat: int, topic_id: int, page: int):
        if not 1 <= topic_id <= len(TOPICS):
            return
        topic = TOPICS[topic_id - 1]
        page = max(0, min(page, (len(topic.lessons) - 1) // 6))
        progress = self.store.progress()
        rows, lines = [], [topic.stage + "\n" + topic.title]
        for lesson in topic.lessons[page * 6 : page * 6 + 6]:
            status = progress.get(lesson.id, "not_started")
            lines.append(f"\n{lesson.id}. {lesson.title}\n{STATUS[status]}")
            rows.append([(f"{STATUS[status].split()[0]} {lesson.title}", "pick:" + lesson.id)])
        nav = []
        if page:
            nav.append(("←", f"topic:{topic_id}:{page - 1}"))
        if (page + 1) * 6 < len(topic.lessons):
            nav.append(("→", f"topic:{topic_id}:{page + 1}"))
        if nav:
            rows.append(nav)
        rows.append([("Все темы", f"topics:{(topic_id - 1) // 5}")])
        await self.send(chat, "\n".join(lines), keyboard(rows))

    async def schedule(self, chat: int):
        settings = self.store.settings()
        state = "пауза" if settings["paused"] else "включены"
        await self.send(
            chat,
            f"Приглашения: {state}\nЧасовой пояс: {settings['timezone']}\n"
            f"Время: {', '.join(settings['times'])}",
            keyboard(
                [
                    [("Изменить время", "schedule:edit")],
                    [
                        (
                            "Включить" if settings["paused"] else "Пауза",
                            "schedule:on" if settings["paused"] else "schedule:off",
                        )
                    ],
                ]
            ),
        )

    async def handle_message(self, message: Message):
        chat, text = message.chat.id, (message.text or "").strip()
        if not text:
            await self.send(chat, "Пока поддерживаю текстовые сообщения и кнопки.")
            return
        self.initialize(chat)
        command = text.split()[0].split("@")[0]
        settings = self.store.settings()
        if command in {"/start", "/help"}:
            settings["editing_schedule"] = False
            self.store.save_settings(settings)
            await self.send(
                chat,
                "Я помогу пройти путь до middle+/senior ML Engineer.\n\n"
                "Урок: знакомство с темой → объяснение и вопросы → 3–5 открытых вопросов → разбор. "
                "Каждый ответ оценивается от 0 до 2; для прохождения нужно 80%. "
                "Короткие уроки дополняйте практикой: они проверяют понимание, а не заменяют рабочий опыт.\n\n"
                "/lesson — начать или продолжить\n/topics — весь план\n/progress — результаты\n"
                "/schedule — расписание\n/cancel — отменить ввод расписания\n\n"
                "Приглашения приходят, пока бот запущен. Время можно изменить кнопкой «Расписание».",
                MAIN,
            )
            return
        if command == "/cancel":
            settings["editing_schedule"] = False
            self.store.save_settings(settings)
            await self.send(chat, "Ввод расписания отменён. Урок сохранён.", MAIN)
            return
        navigation = {"/lesson", "/topics", "/progress", "/schedule"}
        if command in navigation or text in {"📚 Урок", "🗂 Все темы", "📊 Прогресс", "⏰ Расписание"}:
            settings["editing_schedule"] = False
            self.store.save_settings(settings)
            if command == "/lesson" or text == "📚 Урок":
                await self.lesson(chat)
            elif command == "/topics" or text == "🗂 Все темы":
                await self.topics(chat)
            elif command == "/progress" or text == "📊 Прогресс":
                progress = self.store.progress()
                passed = sum(s == "passed" for s in progress.values())
                failed = sum(s == "failed" for s in progress.values())
                await self.send(
                    chat,
                    f"Всего разделов: {len(LESSONS)}\n✅ Пройдена: {passed}\n"
                    f"❌ Провалено тестирование: {failed}\n⬜ Не пройдена: {len(LESSONS) - passed - failed}\n\n"
                    "Статус отражает последнюю завершённую попытку. Повторение доступно в «Все темы».",
                    MAIN,
                )
            else:
                if command == "/schedule" and " " in text:
                    await self.save_schedule(chat, text.split(maxsplit=1)[1])
                else:
                    await self.schedule(chat)
            return
        if text.startswith("/"):
            await self.send(chat, "Неизвестная команда. Список: /help", MAIN)
            return
        if settings.get("editing_schedule"):
            await self.save_schedule(chat, text)
            return
        if len(text) > 6000:
            await self.send(chat, "Сократите сообщение до 6000 символов.")
            return
        session = self.store.session()
        if not session:
            await self.send(chat, "Нажмите «Урок» или выберите раздел в «Все темы».", MAIN)
        elif session["stage"] == "questions":
            await self.bot.send_chat_action(chat, "typing")
            answer = await self.engine.answer(session, text)
            await self.send(chat, answer, self.actions(session), preserve=True)
        elif session["stage"] == "quiz":
            self.engine.record_answer(session, text)
            await self.after_answer(chat, session)
        else:
            await self.send(chat, "Выберите действие кнопкой ниже.", self.actions(session))

    async def save_schedule(self, chat: int, text: str):
        try:
            timezone, times = parse_schedule(text)
        except ValueError as exc:
            await self.send(chat, str(exc))
            return
        settings = self.store.settings()
        settings.update(timezone=timezone, times=times, editing_schedule=False)
        self.store.save_settings(settings)
        await self.schedule(chat)

    async def after_answer(self, chat: int, session: dict):
        if session["stage"] == "grading":
            await self.send(chat, "Все ответы сохранены. Проверяю тест…")
            await self.engine.grade(session)
        await self.show_session(chat, session)

    async def handle_callback(self, chat: int, data: str):
        parts = data.split(":")
        if parts[0] == "topics" and len(parts) == 2:
            await self.topics(chat, int(parts[1]))
        elif parts[0] == "topic" and len(parts) == 3:
            await self.topic(chat, int(parts[1]), int(parts[2]))
        elif data in {"lesson", "invite"}:
            settings = self.store.settings()
            settings["editing_schedule"] = False
            self.store.save_settings(settings)
            session = self.store.session()
            if data == "invite" and session and session["stage"] == "result":
                self.store.save_session(None)
            await self.lesson(chat)
        elif parts[0] == "pick" and len(parts) == 2 and parts[1] in LESSONS:
            settings = self.store.settings()
            settings["editing_schedule"] = False
            self.store.save_settings(settings)
            session = self.store.session()
            if session and session["stage"] != "result":
                await self.send(
                    chat,
                    "Есть незаконченный урок. Начать выбранный раздел заново? "
                    "Ответы текущего незавершённого теста будут сброшены; результаты завершённых тестов сохранятся.",
                    keyboard(
                        [
                            [("Начать выбранный", f"replace:{session['id']}:{parts[1]}")],
                            [("Продолжить текущий", "lesson")],
                        ]
                    ),
                )
            else:
                await self.show_session(chat, self.engine.start(parts[1]))
        elif parts[0] == "replace" and len(parts) == 3 and parts[2] in LESSONS:
            session = self.store.session()
            if session and session["id"] == parts[1]:
                await self.show_session(chat, self.engine.start(parts[2]))
            else:
                await self.stale(chat)
        elif data.startswith("schedule:"):
            settings = self.store.settings()
            if data == "schedule:edit":
                settings["editing_schedule"] = True
                self.store.save_settings(settings)
                await self.send(
                    chat,
                    "Напишите часовой пояс и время, например:\n"
                    "Europe/Moscow 10:00,14:00,19:00\n\nОтмена: /cancel",
                )
            elif data in {"schedule:on", "schedule:off"}:
                settings.update(paused=data == "schedule:off", editing_schedule=False)
                self.store.save_settings(settings)
                await self.schedule(chat)
        elif parts[0] == "s" and len(parts) in {3, 4}:
            session = self.store.session()
            if not session or session["id"] != parts[1]:
                await self.stale(chat)
                return
            settings = self.store.settings()
            settings["editing_schedule"] = False
            self.store.save_settings(settings)
            action, stage = parts[2], session["stage"]
            if action == "later":
                self.engine.postpone(session)
                await self.send(
                    chat,
                    "Отложено на 24 часа. Можно начать другой урок или вернуться через «Все темы».",
                    MAIN,
                )
                return
            if action == "material" and stage == "familiar":
                await self.send(chat, "Готовлю объяснение…")
                await self.engine.material(session)
            elif action == "quiz" and stage in {"familiar", "questions"}:
                await self.send(chat, "Готовлю тест…")
                await self.engine.quiz(session)
            elif action == "unknown" and stage == "quiz" and len(parts) == 4:
                if parts[3] != str(len(session["answers"])):
                    await self.stale(chat)
                    return
                self.engine.record_answer(session, "Не знаю")
                await self.after_answer(chat, session)
                return
            elif action == "grade" and stage == "grading":
                await self.send(chat, "Проверяю ответы…")
                await self.engine.grade(session)
            elif action in {"retry", "retest"} and stage == "result":
                session = self.engine.start(session["lesson_id"])
                if action == "retry":
                    await self.engine.material(session)
                else:
                    await self.engine.quiz(session)
            elif action == "next" and stage == "result":
                if not session["passed"]:
                    self.engine.postpone(session)
                else:
                    self.store.save_session(None)
                await self.lesson(chat)
                return
            else:
                await self.stale(chat)
                return
            await self.show_session(chat, session)

    async def stale(self, chat: int):
        await self.send(
            chat, "Эта кнопка относится к прошлому шагу. Откройте /lesson для актуального состояния."
        )

    async def invitation(self, chat: int):
        session = self.store.session()
        if session and session["stage"] != "result":
            title = LESSONS[session["lesson_id"]].title
            text = f"Время для ML 📚\nПродолжим урок «{title}»?"
        else:
            lesson_id = self.engine.next_lesson()
            if not lesson_id:
                return
            text = f"Время для ML 📚\nПредлагаю урок «{LESSONS[lesson_id].title}». Начнём?"
        # Invitation never replaces an ongoing lesson. Selection happens only after a click.
        await self.send(chat, text, keyboard([[("Начать / продолжить", "invite")]]))


async def run():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    # HTTP request logs can include bot tokens in URLs.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    config = Config.load()
    store = Store(config.database)
    llm = TutorLLM(config)
    bot = Bot(config.token)
    app = TelegramTutor(bot, config, store, LessonEngine(store, llm))
    dispatcher = Dispatcher()
    dispatcher.message.register(app.message)

    dispatcher.callback_query.register(app.callback)
    task = None
    try:
        await bot.set_my_commands(
            [
                BotCommand(command=command, description=description)
                for command, description in [
                    ("start", "Начать"),
                    ("lesson", "Урок"),
                    ("topics", "Все темы"),
                    ("progress", "Прогресс"),
                    ("schedule", "Расписание"),
                    ("help", "Помощь"),
                ]
            ]
        )
        task = asyncio.create_task(run_scheduler(store, app.invitation))
        await dispatcher.start_polling(
            bot, allowed_updates=["message", "callback_query"], close_bot_session=False
        )
    finally:
        if task:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
        await bot.session.close()
        await llm.close()
        store.close()
