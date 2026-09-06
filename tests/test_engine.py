from datetime import UTC, datetime, timedelta

import pytest

from tutor.curriculum import LESSONS, TOPICS, aggregate_status
from tutor.engine import LessonEngine
from tutor.llm import LLMError
from tutor.storage import Store


async def complete(engine, session):
    await engine.quiz(session)
    for _ in session["questions"]:
        engine.record_answer(session, "Ответ ученика")
    await engine.grade(session)


async def test_unknown_material_questions_and_pass(store, llm):
    engine = LessonEngine(store, llm)
    session = engine.start(engine.next_lesson())
    assert session["stage"] == "familiar"
    await engine.material(session)
    assert session["stage"] == "questions"
    await engine.answer(session, "Объясни ещё раз")
    assert store.session()["history"][0]["question"] == "Объясни ещё раз"
    await complete(engine, session)
    assert store.progress()["01.01"] == "passed"
    assert engine.next_lesson() == "01.02"
    assert store.db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] == 1


async def test_known_topic_skips_material(store, llm):
    engine = LessonEngine(store, llm)
    session = engine.start("01.01")
    await complete(engine, session)
    llm.material.assert_not_called()
    assert session["passed"]


@pytest.mark.parametrize("scores,passed", [([2, 2, 2, 1], True), ([2, 2, 1, 1], False), ([0] * 4, False)])
async def test_app_owns_threshold(store, llm, scores, passed):
    llm.grade.return_value["marks"] = [{"score": s, "feedback": "Объяснение"} for s in scores]
    engine = LessonEngine(store, llm)
    session = engine.start("01.01")
    await complete(engine, session)
    assert session["passed"] is passed
    assert store.progress()["01.01"] == ("passed" if passed else "failed")


async def test_restart_and_failed_grading_preserves_answers(tmp_path, llm):
    path = str(tmp_path / "state.sqlite3")
    first = Store(path)
    engine = LessonEngine(first, llm)
    session = engine.start("01.01")
    await engine.quiz(session)
    engine.record_answer(session, "Первый ответ")
    first.close()
    second = Store(path)
    engine = LessonEngine(second, llm)
    session = second.session()
    assert session["answers"] == ["Первый ответ"]
    for _ in range(3):
        engine.record_answer(session, "Ещё ответ")
    llm.grade.side_effect = LLMError("temporary")
    with pytest.raises(LLMError):
        await engine.grade(session)
    assert len(second.session()["answers"]) == 4
    assert second.session()["stage"] == "grading"
    assert second.progress() == {}
    llm.grade.side_effect = None
    await engine.grade(second.session())
    assert second.progress()["01.01"] == "passed"
    second.close()


async def test_repeat_preserves_previous_status_until_new_verdict(store, llm):
    engine = LessonEngine(store, llm)
    await complete(engine, engine.start("01.01"))
    repeated = engine.start("01.01")
    assert store.progress()["01.01"] == "passed"
    llm.grade.return_value["marks"] = [{"score": 0, "feedback": "Неверно"} for _ in range(4)]
    await complete(engine, repeated)
    assert store.progress()["01.01"] == "failed"
    assert store.db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] == 2


def test_postpone_does_not_mark_passed_and_manual_choice_works(store, llm):
    engine = LessonEngine(store, llm)
    session = engine.start("01.01")
    engine.postpone(session)
    assert store.session() is None
    assert store.progress() == {}
    assert engine.next_lesson() == "01.02"
    assert engine.next_lesson(datetime.now(UTC) + timedelta(days=2)) == "01.01"
    assert engine.start("01.01")["lesson_id"] == "01.01"


def test_curriculum_and_topic_status():
    assert len(TOPICS) == 30
    assert len(LESSONS) == sum(len(t.lessons) for t in TOPICS)
    assert all(l.scope and l.title for l in LESSONS.values())
    assert aggregate_status(["passed", "passed"]) == "passed"
    assert aggregate_status(["passed", "failed"]) == "failed"
    assert aggregate_status(["passed", "not_started"]) == "not_started"


async def test_generation_error_does_not_advance(store, llm):
    engine = LessonEngine(store, llm)
    session = engine.start("01.01")
    llm.material.side_effect = LLMError("temporary")
    with pytest.raises(LLMError):
        await engine.material(session)
    assert store.session()["stage"] == "familiar"
