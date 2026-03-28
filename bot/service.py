import json
import logging
import zoneinfo
from datetime import datetime

from django.conf import settings
from pydantic_ai import Agent
from pydantic_ai.messages import ModelRequest, ModelResponse, ToolCallPart
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from bot.models import Inteligence

logger = logging.getLogger(__name__)

model = OpenAIChatModel(
    "gpt-5.4", provider=OpenAIProvider(api_key=settings.OPEN_AI_KEY)
)

agent = Agent(
    model,
    system_prompt="""Você é um agente pessoal para escrita e consulta de informações."
    Você tem acesso ao modelo:
    class Inteligence(models.Model):
        content = models.JSONField()
        instructions = models.TextField()
    O campo content é onde tem todos os dados salvos.
    O campo instructions explica a estrutura do json que está no campo content.
    Caso o usuário adicione ou remove um tipo de informação, você deve atualizar
    o campo instructions com a nova estrutura do json, além de alterar o json do campo content.
    A resposta final deve ser no formato HTML""",
)

history = None


@agent.tool_plain
def _current_time():
    tz = zoneinfo.ZoneInfo("America/Sao_Paulo")
    return datetime.now(tz)


@agent.tool_plain(docstring_format="google", require_parameter_descriptions=True)
def _update_inteligence(instructions: str, content: dict):
    """Replace the entire inteligence record with new instructions and content. Use _update_content_by_key for partial updates.

    Args:
        instructions: description of the JSON structure stored in content
        content: the JSON data to store
    """
    obj = Inteligence.objects.first()
    if obj is None:
        Inteligence.objects.create(instructions=instructions, content=content)
    else:
        obj.instructions = instructions
        obj.content = content
        obj.save()
    return "ok"


@agent.tool_plain(docstring_format="google", require_parameter_descriptions=True)
def _update_content_by_key(
    key: str, value: dict | list | str | int | float | bool | None
):
    """Update a single top-level key in the content JSON without affecting other keys.

    Args:
        key: the top-level key to create or update
        value: the value to set for the key
    """
    obj = Inteligence.objects.first()
    if obj is None:
        Inteligence.objects.create(instructions="", content={key: value})
    else:
        if obj.content is None:
            obj.content = {}
        obj.content[key] = value
        obj.save()
    return "ok"


@agent.tool_plain(docstring_format="google", require_parameter_descriptions=True)
def _delete_content_key(key: str):
    """Remove a top-level key from the content JSON.

    Args:
        key: the top-level key to remove
    """
    obj = Inteligence.objects.first()
    if obj is None or obj.content is None:
        return "key not found"
    if key not in obj.content:
        return "key not found"
    del obj.content[key]
    obj.save()
    return "ok"


@agent.tool_plain
def _read_instructions():
    """Read the instructions that describe the JSON structure stored in content."""
    obj = Inteligence.objects.first()
    if obj is None:
        return None
    return obj.instructions


@agent.tool_plain(docstring_format="google", require_parameter_descriptions=True)
def _read_content_by_key(key: str):
    """Read a specific top-level key from the content JSON.

    Args:
        key: the top-level key to read from the content JSON
    """
    obj = Inteligence.objects.first()
    if obj is None or obj.content is None:
        return None
    return obj.content.get(key)


@agent.tool_plain
def _list_content_keys():
    """List all top-level keys in the content JSON."""
    obj = Inteligence.objects.first()
    if obj is None or obj.content is None:
        return []
    return list(obj.content.keys())


@agent.tool_plain(docstring_format="google", require_parameter_descriptions=True)
def _search_content(query: str):
    """Search for a text within the content JSON values. Returns all top-level keys whose serialized values contain the query (case-insensitive).

    Args:
        query: text to search for within the JSON values
    """
    obj = Inteligence.objects.first()
    if obj is None or obj.content is None:
        return {}
    query_lower = query.lower()
    results = {}
    for key, value in obj.content.items():
        serialized = json.dumps(value, ensure_ascii=False).lower()
        if query_lower in serialized:
            results[key] = value
    return results


def _trim_history(messages, max_messages=20):
    if len(messages) <= max_messages:
        return messages
    trimmed = messages[-max_messages:]
    # Garantir que o histórico comece com um ModelRequest (mensagem do usuário),
    # nunca com um ModelResponse (que pode conter tool_calls órfãos)
    while trimmed and not isinstance(trimmed[0], ModelRequest):
        trimmed.pop(0)
    return trimmed


def _log_result(result):
    tool_calls = []
    for message in result.new_messages():
        if isinstance(message, ModelResponse):
            for part in message.parts:
                if isinstance(part, ToolCallPart):
                    tool_calls.append(
                        f"{part.tool_name}({json.dumps(part.args_as_dict(), ensure_ascii=False)})"
                    )
    if tool_calls:
        logger.info("Tools chamadas: %s", ", ".join(tool_calls))

    usage = result.usage()
    logger.info(
        "Tokens — input: %d, output: %d, total: %d",
        usage.input_tokens,
        usage.output_tokens,
        usage.total_tokens,
    )


def send_message(text):
    global history

    if history is None:
        result = agent.run_sync(
            "Puxe todos os dados do banco de dados, para você ter esse contexto",
            message_history=history,
        )
        history = result.all_messages()
        _log_result(result)

    result = agent.run_sync(text, message_history=history)
    history = _trim_history(result.all_messages(), max_messages=20)
    _log_result(result)

    return result.output
