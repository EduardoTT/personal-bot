import zoneinfo
from datetime import datetime

from django.conf import settings
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from bot.models import Record, Tag

agent = Agent(
    OpenAIChatModel(
        "gpt-5-nano", provider=OpenAIProvider(api_key=settings.OPEN_AI_KEY)
    ),
    instructions="Você é um agente pessoal, para acesso rápido à informações. "
    "Você deve buscar informações nos registros (Records), chamando as tools. "
    "Você pode buscar diretamente pelos records. "
    "Caso nenhuma informação seja pertinente, você pode responder com o seu próprio "
    "conhecimento. Ou então dizer que não sabe. "
    "Caso você entenda que o usuário deseja salvar alguma informação, ou que está "
    "informando algo que queira buscar depois, você deve salvar como um Record. "
    "Geralmente quando o usuário pede para criar algo, ele também deseja salvar. "
    "Você também pode editar um Record, caso o usuário esteja atualizando alguma informação. "
    "Sempre informe o usuário de alterações ou criações. "
    "Não peça para o usuário informar tags, isso é algo interno do sistema. Contudo, ele "
    "pode proativamente informar. Considere que também é seu trabalho manter os registros "
    "arrumados, ou seja, cada registro com um tema único e sem duplicações. "
    "O texto retornado deve ser no formato HTML.",
)

history = None


@agent.tool_plain(docstring_format="google", require_parameter_descriptions=True)
def _save_record(tags: list[str], text: str):
    """Create a record and add tags to it.

    Args:
        tags: list of tags to help fetching the most appropriate records later
        text: the text of the record
    """
    existing_tags = Tag.objects.filter(name__in=tags)
    existing_names = set(existing_tags.values_list("name", flat=True))

    new_tags = [Tag(name=tag) for tag in tags if tag not in existing_names]
    Tag.objects.bulk_create(new_tags, ignore_conflicts=True)

    record = Record.objects.create(text=text)

    tag_objs = Tag.objects.filter(name__in=tags)
    record.tags.add(*tag_objs)


@agent.tool_plain
def _fetch_all_records():
    """Fetch all existing records"""
    return list(Record.objects.all().values("id", "text"))


@agent.tool_plain
def _fetch_all_tags():
    """Fetch all existing tags"""
    return list(Tag.objects.all().values("id", "name"))


@agent.tool_plain(docstring_format="google", require_parameter_descriptions=True)
def _fetch_records_containing_text(text: str):
    """Fetch records that contains (like) some text

    Args:
        text: the argument for 'like / contains' search
    """
    return list(Record.objects.filter(text__icontains=text).values("id", "text"))


@agent.tool_plain(docstring_format="google", require_parameter_descriptions=True)
def _get_records_by_tag(tags: list[str]):
    """Fetch all records by its tags

    Args:
        tags: list of tags
    """
    return list(Record.objects.filter(tags__name__in=tags).values("id", "text"))


@agent.tool_plain(docstring_format="google", require_parameter_descriptions=True)
def _update_record(id: int, new_text: str):
    """Update record with new text

    Args:
        id: id of record in db
        new_text: new text to override current text
    """
    return Record.objects.filter(id=id).update(text=new_text)


@agent.tool_plain(docstring_format="google", require_parameter_descriptions=True)
def _delete_record(id: int):
    """Delete record by id

    Args:
        id: id of the record in db
    """
    return Record.objects.filter(id=id).delete()


@agent.tool_plain
def _current_time():
    tz = zoneinfo.ZoneInfo("America/Sao_Paulo")
    return datetime.now(tz)


def send_message(text):
    global history
    result = agent.run_sync(text, message_history=history)
    history = result.all_messages()[-20:]
    return result.output
