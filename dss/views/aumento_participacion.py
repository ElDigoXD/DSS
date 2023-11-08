from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def aumento_participacion(request: HttpRequest) -> HttpResponse:
    return render(request, "aumento_participacion.html")