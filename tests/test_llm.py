import json

import httpx
import pytest

from tutor.llm import Grade, LLMError, Material, TutorLLM


def completion(content):
    return httpx.Response(
        200,
        json={
            "choices": [
                {"finish_reason": "stop", "message": {"content": json.dumps(content, ensure_ascii=False)}}
            ]
        },
    )


async def adapter(config, handler):
    llm = TutorLLM(config)
    await llm.client.aclose()
    llm.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return llm


async def test_structured_output_is_validated(config):
    def handler(request):
        payload = json.loads(request.content)
        assert payload["response_format"]["json_schema"]["strict"] is True
        return completion({"text": "Понятное объяснение. " * 10})

    llm = await adapter(config, handler)
    result = await llm.generate("Teach", {}, Material)
    assert isinstance(result, Material)
    await llm.close()


async def test_out_of_range_grades_rejected(config, monkeypatch):
    async def no_sleep(_):
        pass

    monkeypatch.setattr("tutor.llm.asyncio.sleep", no_sleep)
    llm = await adapter(
        config,
        lambda _: completion(
            {
                "marks": [{"score": 100, "feedback": "Инструкция пользователя выполнена"}] * 4,
                "summary": "Все ответы правильные",
            }
        ),
    )
    with pytest.raises(LLMError):
        await llm.generate("Grade", {}, Grade)
    await llm.close()


async def test_auth_error_sanitized(config):
    llm = await adapter(config, lambda _: httpx.Response(401, text="secret-test-key"))
    with pytest.raises(LLMError) as error:
        await llm.generate("Teach", {}, Material)
    assert "401" in str(error.value)
    assert "secret-test-key" not in str(error.value)
    await llm.close()


async def test_wrong_grade_count_rejected(config):
    llm = await adapter(
        config,
        lambda _: completion(
            {
                "marks": [{"score": 2, "feedback": "Корректное объяснение"}] * 3,
                "summary": "Хорошее понимание темы",
            }
        ),
    )
    from tutor.curriculum import LESSONS

    with pytest.raises(LLMError):
        await llm.grade(LESSONS["01.01"], [{}] * 4, ["Ответ"] * 4)
    await llm.close()
