from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def baterias(request: HttpRequest) -> HttpResponse:
    return render(request, "decisiones/baterias.html")