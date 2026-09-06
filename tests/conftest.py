from unittest.mock import AsyncMock

import pytest

from tutor.config import Config
from tutor.storage import Store


@pytest.fixture
def store():
    value = Store(":memory:")
    yield value
    value.close()


@pytest.fixture
def config():
    return Config(
        "123456:fake",
        42,
        "test-key",
        "https://llm.example/v1",
        "test-model",
        "schema",
        "Europe/Moscow",
        ["10:00", "14:00", "19:00"],
        ":memory:",
    )


@pytest.fixture
def llm():
    value = AsyncMock()
    value.material.return_value = {"text": "Учебный материал: " + "объяснение " * 20}
    value.answer.return_value = "Ответ с понятным примером."
    value.quiz.return_value = {
        "questions": [
            {"text": f"Объясните концепцию номер {i} на примере", "rubric": f"Эталон номер {i}: обоснование"}
            for i in range(4)
        ]
    }
    value.grade.return_value = {
        "marks": [{"score": 2, "feedback": "Верно: идея и применение объяснены"} for _ in range(4)],
        "summary": "Тема понята, переходите к практике.",
    }
    return value
