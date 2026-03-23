from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods


def chat(request):
    return render(request, "bot/chat.html")


@require_http_methods(["POST"])
def message(request):
    user_message = request.POST.get("message", "").strip()
    bot_response = user_message
    return render(request, "bot/partials/message.html", {
        "user_message": user_message,
        "bot_response": bot_response,
    })
