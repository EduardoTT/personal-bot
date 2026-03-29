import logging

from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from bot.service import send_message

logger = logging.getLogger(__name__)


def chat(request):
    return render(request, "bot/chat.html")


@require_http_methods(["POST"])
def message(request):
    history = request.session.get("history", [])
    user_message = request.POST.get("message", "").strip()
    try:
        bot_response, updated_history = send_message(user_message, history)
        request.session["history"] = updated_history
    except Exception:
        logger.exception("Erro ao processar mensagem")
        return HttpResponse(status=500)
    return render(
        request,
        "bot/partials/message.html",
        {
            "bot_response": bot_response,
        },
    )
