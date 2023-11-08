from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def orientacion_placas(request: HttpRequest) -> HttpResponse:
    return render(request, "orientacion_placas.html")