from datetime import UTC, datetime, timedelta
from uuid import uuid4

from tutor.curriculum import LESSONS
from tutor.storage import Store


class LessonEngine:
    def __init__(self, store: Store, llm):
        self.store = store
        self.llm = llm

    def next_lesson(self, now: datetime | None = None) -> str | None:
        now = now or datetime.now(UTC)
        progress, deferred = self.store.progress(), self.store.deferred()
        for lesson_id in LESSONS:
            if progress.get(lesson_id) == "passed":
                continue
            if lesson_id in deferred and datetime.fromisoformat(deferred[lesson_id]) > now:
                continue
            return lesson_id
        return None

    def start(self, lesson_id: str) -> dict:
        if lesson_id not in LESSONS:
            raise ValueError("Unknown lesson")
        session = {
            "id": uuid4().hex[:12],
            "lesson_id": lesson_id,
            "stage": "familiar",
            "material": "",
            "history": [],
            "questions": [],
            "answers": [],
        }
        self.store.save_session(session)
        return session

    async def material(self, session: dict):
        material = await self.llm.material(LESSONS[session["lesson_id"]])
        session["material"] = material["text"]
        session["stage"] = "questions"
        self.store.save_session(session)

    async def answer(self, session: dict, text: str) -> str:
        answer = await self.llm.answer(
            LESSONS[session["lesson_id"]], session["material"], session["history"], text
        )
        session["history"] = (session["history"] + [{"question": text, "answer": answer}])[-12:]
        self.store.save_session(session)
        return answer

    async def quiz(self, session: dict):
        quiz = await self.llm.quiz(LESSONS[session["lesson_id"]])
        session["questions"] = quiz["questions"]
        session["answers"] = []
        session["stage"] = "quiz"
        self.store.save_session(session)

    def record_answer(self, session: dict, text: str):
        if session["stage"] != "quiz" or len(session["answers"]) >= len(session["questions"]):
            raise ValueError("Not accepting answers")
        session["answers"].append(text)
        if len(session["answers"]) == len(session["questions"]):
            session["stage"] = "grading"
        self.store.save_session(session)

    async def grade(self, session: dict):
        if session["stage"] != "grading":
            raise ValueError("Quiz is not complete")
        result = await self.llm.grade(LESSONS[session["lesson_id"]], session["questions"], session["answers"])
        # Grade is also validated by the provider adapter. The application owns the threshold.
        score = sum(mark["score"] for mark in result["marks"])
        maximum = 2 * len(session["questions"])
        passed = score * 100 >= 80 * maximum
        session.update(stage="result", result=result, score=score, maximum=maximum, passed=passed)
        self.store.finish(session, passed)

    def postpone(self, session: dict):
        until = datetime.now(UTC) + timedelta(days=1)
        self.store.postpone(session["lesson_id"], until.isoformat())
