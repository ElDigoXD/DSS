from datetime import date
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from dss.models.consumo import Consumo
from dss.models.produccion import Produccion
from dss.models.vecino import Vecino

from dss.chart import *


def calcular_diferencia(produccion, consumo):
    diferencia = [min(produccion[i], consumo[i]) for i in range(24)]
    diferencia = sum(diferencia)
    diferencia = diferencia / sum(consumo)
    return diferencia


def orientacion_placas(request: HttpRequest) -> HttpResponse:
    return orientacion_placas_vecino(request, None)


def orientacion_placas_vecino(request: HttpRequest, vecino_id) -> HttpResponse:
    if not vecino_id:
        vecino_id = request.session.get("vecino_id")

    vecino = Vecino.objects.filter(id=vecino_id).first()
    consumo_semana = Consumo.objects.filter(
        fecha__gte=date(2023, 1, 1),
        fecha__lte=date(2023, 1, 7),
        vecino_id=vecino_id
    ).all()

    produccion_semana = Produccion.objects.filter(
        fecha__gte=date(2023, 1, 1),
        fecha__lte=date(2023, 1, 7),
    ).all()

    consumo_agregado = [0.0]*24
    for i in range(24):
        for h in consumo_semana:
            if h.hora.hour == i:
                consumo_agregado[i] = consumo_agregado[i] + h.kw_media_consumidos

    produccion_agregada = [0.0]*24
    for i in range(24):
        for h in produccion_semana:
            if h.hora.hour == i:
                produccion_agregada[i] = produccion_agregada[i] + h.kw_media_producidos * vecino.porcentaje

    produccion_mañana = produccion_agregada.copy()
    produccion_mañana.pop(0)
    produccion_mañana.insert(23, 0)
    produccion_mañana = [i * 0.95 for i in produccion_mañana]
    produccion_tarde = produccion_agregada.copy()
    produccion_tarde.insert(0, 0)
    produccion_tarde = [i * 0.95 for i in produccion_tarde]

    diferencias = [calcular_diferencia(p, consumo_agregado)*100 for p in [produccion_agregada, produccion_mañana, produccion_tarde]]
    context = {
        "acordeon": [
            {
                "semana": "Mes",
                "porcentajes": diferencias,
                "chart": Chart(
                    "m",
                    str([i for i in range(24)]),
                    [
                        Dataset(str([c for c in consumo_agregado]), background_color="rgba(0,0,255,0.5)"),
                        Dataset(str([p for p in produccion_mañana]), background_color="rgba(0,255,0,1)"),
                        Dataset(str([p for p in produccion_agregada]), background_color="rgba(255,0,0,1)"),
                        Dataset(str([p for p in produccion_tarde]), background_color="rgba(255,255,0,1)"),
                    ],
                    [Scale()]
                )
            },
            {
                "semana": "Primera semana",
                "porcentajes": diferencias,
                "chart": Chart(
                    "a",
                    str([i for i in range(24)]),
                    [
                        Dataset(str([c for c in consumo_agregado]), background_color="rgba(0,0,255,0.5)"),
                        Dataset(str([p for p in produccion_mañana]), background_color="rgba(0,255,0,1)"),
                        Dataset(str([p for p in produccion_agregada]), background_color="rgba(255,0,0,1)"),
                        Dataset(str([p for p in produccion_tarde]), background_color="rgba(255,255,0,1)"),
                    ],
                    [Scale()]
                )
            },
            {
                "semana": "Segunda semana",
                "porcentajes": diferencias,
                "chart": Chart(
                    "b",
                    str([i for i in range(24)]),
                    [
                        Dataset(str([c for c in consumo_agregado]), background_color="rgba(0,0,255,0.5)"),
                        Dataset(str([p for p in produccion_mañana]), background_color="rgba(0,255,0,1)"),
                        Dataset(str([p for p in produccion_agregada]), background_color="rgba(255,0,0,1)"),
                        Dataset(str([p for p in produccion_tarde]), background_color="rgba(255,255,0,1)"),
                    ],
                    [Scale()]
                )
            },
            {
                "semana": "Tercera semana",
                "porcentajes": diferencias,
                "chart": Chart(
                    "c",
                    str([i for i in range(24)]),
                    [
                        Dataset(str([c for c in consumo_agregado]), background_color="rgba(0,0,255,0.5)"),
                        Dataset(str([p for p in produccion_mañana]), background_color="rgba(0,255,0,1)"),
                        Dataset(str([p for p in produccion_agregada]), background_color="rgba(255,0,0,1)"),
                        Dataset(str([p for p in produccion_tarde]), background_color="rgba(255,255,0,1)"),
                    ],
                    [Scale()]
                )
            },
            {
                "semana": "Cuarta semana",
                "porcentajes": diferencias,
                "chart": Chart(
                    "d",
                    str([i for i in range(24)]),
                    [
                        Dataset(str([c for c in consumo_agregado]), background_color="rgba(0,0,255,0.5)"),
                        Dataset(str([p for p in produccion_mañana]), background_color="rgba(0,255,0,1)"),
                        Dataset(str([p for p in produccion_agregada]), background_color="rgba(255,0,0,1)"),
                        Dataset(str([p for p in produccion_tarde]), background_color="rgba(255,255,0,1)"),
                    ],
                    [Scale()]
                )
            },
        ]
    }
    return render(request, "decisiones/orientacion_placas.html", context=context)
