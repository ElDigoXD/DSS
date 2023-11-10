from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def aumento_participacion(request: HttpRequest) -> HttpResponse:
    return render(request, "decisiones/aumento_participacion.html")