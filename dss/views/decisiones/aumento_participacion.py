from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from dss.models.vecino import Vecino
from dss.models.produccion import Produccion

from datetime import date
from dss.chart import *


def aumento_participacion(request: HttpRequest) -> HttpResponse:
    return aumento_participacion_vecino(request, None)

def aumento_participacion_vecino(request: HttpRequest, vecino_id) -> HttpResponse:
    if not vecino_id:
        vecino_id = request.session.get("vecino_id")

    vecino = Vecino.objects.filter(id=vecino_id).first()

    porcentaje_actual = vecino.porcentaje

    produccion_semana = Produccion.objects.filter( 
        fecha__gte=date(2023,1,1), 
        fecha__lte=date(2023,1,7),
    ).all()

    produccion_semana_actual = [0.0]*24
    for i in range(24):
        for h in produccion_semana:
            if h.hora.hour == i:
                produccion_semana_actual[i] = produccion_semana_actual[i] + h.kw_media_producidos * vecino.porcentaje

    porcentaje_aumento = vecino.porcentaje + 0.10
    produccion_semana_aumento = [0.0]*24
    for i in range(24):
        for h in produccion_semana:
            if h.hora.hour == i:
                produccion_semana_aumento[i] = produccion_semana_aumento[i] + h.kw_media_producidos * porcentaje_aumento

    context = {
        "vecino":vecino,
        "porcentaje_actual": porcentaje_actual*100,
        "porcentaje_aumento": porcentaje_aumento*100,
        "chart": Chart(
            "Aumento Produccion",
            str([i for i in range(24)]),
            [
                Dataset(str([pa for pa in produccion_semana_actual]), background_color="rgba(0,255,0,0.75)"),
                Dataset(str([pau for pau in produccion_semana_aumento]), background_color="rgba(255,0,0,0.5)"),
            ],
            [Scale()]
        )
    }

    return render(request, "decisiones/aumento_participacion.html", context=context)