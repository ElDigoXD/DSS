from ast import Tuple
from datetime import date, datetime, timedelta
from functools import reduce
from itertools import groupby
from pprint import pprint
from typing import Any
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render

from dss.models.consumo import Consumo
from dss.models.produccion import Produccion
from dss.models.vecino import Vecino
from dss.models.precio_venta import Precio_venta

from dss.chart import *

PORCENTAJE_AUMENTO = 0.05


def aumento_participacion(request: HttpRequest) -> HttpResponse:
    return aumento_participacion_vecino(request, None)


def obtener_semana(semana: int, consumo: list[Consumo], produccion: list[Produccion], precio_kw: list[Precio_venta], porcentaje: float) -> dict[str, Any]:
    slice_semana = slice(7*24*(semana-1), 7*24*semana) if semana != 0 else slice(-1)

    consumo_diario = consumo[slice_semana]
    consumo_agregado = [reduce(lambda acc, x: acc + x.kw_media_consumidos, v, 0.0)
                        for _, v in groupby(sorted(consumo_diario, key=lambda x: x.hora.hour), lambda x: x.hora.hour)]

    produccion_diaria = produccion[slice_semana]
    produccion_normal = [reduce(lambda acc, x: acc + x.kw_media_producidos * porcentaje, v, 0.0)
                         for _, v in groupby(sorted(produccion_diaria, key=lambda x: x.hora.hour), lambda x: x.hora.hour)]

    def aplicar_porcentaje(x:Produccion, porcentaje: float) -> float:
        return x.kw_media_producidos * porcentaje
        


    produccion_diaria = list(map(lambda x: aplicar_porcentaje(x, porcentaje), produccion[slice_semana]))
    produccion_aumentada_diaria = list(map(lambda x: aplicar_porcentaje(x, porcentaje + PORCENTAJE_AUMENTO), produccion[slice_semana]))

    pprint(list(zip(produccion_diaria, produccion_aumentada_diaria)))
    ahorro_normal_diario = list(map(lambda p, c: min(p, c.kw_media_consumidos),
                                     produccion_diaria, consumo_diario))
    
    ahorro_aumentado_diario = list(map(lambda p, c: min(p, c.kw_media_consumidos), 
                                    produccion_aumentada_diaria, consumo_diario))

    ahorro_normal = sum(ahorro_normal_diario)
    ahorro_aumentado = sum(ahorro_aumentado_diario)

    precio_kw_diario = precio_kw[slice_semana]
    precio_energia_total = sum(list(map(lambda c, p: c.kw_media_consumidos * p.precio, consumo_diario, precio_kw_diario)))/1000
    precio_energia_normal = sum(list(map(lambda a, p: a * p.precio, ahorro_normal_diario, precio_kw_diario)))/1000
    precio_energia_aumentado = sum(list(map(lambda a, p: a * p.precio, ahorro_aumentado_diario, precio_kw_diario)))/1000

    produccion_total = reduce(lambda acc, x: x.kw_media_consumidos + acc, consumo_diario, 0.0)
    
    return {
                "semana": semana,
                "totales": {"total": produccion_total/1000, "normal": ahorro_normal/1000, "aumentado": ahorro_aumentado/1000},
                "porcentajes": [ahorro_normal/produccion_total*100, ahorro_aumentado/produccion_total*100],
                "precios": [precio_energia_total, precio_energia_normal, precio_energia_aumentado],
                "chart": Chart(
                    str(semana),
                    str([i for i in range(24)]),
                    [
                        #Dataset(str([c for c in ahorro_normal]), label="Ahorro normal", background_color="rgba(0, 168, 232, 0.5)"),
                        #Dataset(str([p for p in ahorro_mañana]), label="Ahorro mañana", background_color="rgba(242, 100, 25, 1)"),
                        #Dataset(str([p for p in ahorro_tarde]), label="Ahorro tarde", background_color="rgba(246, 174, 45, 1)"),
                    ],
                    [Scale()],
                    Type.BAR,
                    legend=True
                )
            }


def aumento_participacion_vecino(request: HttpRequest, vecino_id) -> HttpResponse:
    if not vecino_id:
        vecino_id = request.session.get("vecino_id")

    vecino = Vecino.objects.filter(id=vecino_id).first()

    if not vecino:
        raise Http404()

    consumo = Consumo.objects.filter(
        fecha__gte=date(2023, 1, 1),
        fecha__lt=date(2023, 2, 1),
        vecino_id=vecino_id
    ).order_by("fecha").all()

    produccion = Produccion.objects.filter(
        fecha__gte=date(2023, 1, 1),
        fecha__lt=date(2023, 2, 1),
    ).order_by("fecha", "hora").all()

    precio = Precio_venta.objects.filter(
        fecha__gte=date(2023, 1, 1),
        fecha__lt=date(2023, 2, 1),
    ).order_by("fecha", "hora").all()

    acordeon = []

    for i, semana in enumerate(["Mes", "Primera semana", "Segunda semana", "Tercera semana", "Cuarta semana"]):
        dic = obtener_semana(i, list(consumo), list(produccion), list(precio), vecino.porcentaje)

        acordeon.append(
            dic
        )

    context = {
        "acordeon": acordeon
    }
    return render(request, "decisiones/aumento_participacion.html", context=context)
