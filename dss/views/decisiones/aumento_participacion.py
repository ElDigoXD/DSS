from datetime import date
from functools import reduce
from itertools import groupby
from typing import Any

from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render

from dss.chart import *
from dss.models.consumo import Consumo
from dss.models.precio_venta import Precio_venta
from dss.models.produccion import Produccion
from dss.models.vecino import Vecino

PORCENTAJES_AUMENTO =[0.05, 0.1, 0.15, 0.2]
PORCENTAJE_PRECIO_COMPENSACION = 0.75


def aumento_participacion(request: HttpRequest) -> HttpResponse:
    return aumento_participacion_vecino(request, None)


def obtener_semana(semana: int, consumo: list[Consumo], produccion: list[Produccion], precio_kw: list[Precio_venta],
                   porcentaje: float) -> dict[str, Any]:
    slice_semana = slice(7 * 24 * (semana - 1), 7 * 24 * semana) if semana != 0 else slice(-1)

    consumo_diario = consumo[slice_semana]
    consumo_agregado = [reduce(lambda acc, x: acc + x.kw_media_consumidos, v, 0.0)
                        for _, v in groupby(sorted(consumo_diario, key=lambda x: x.hora.hour), lambda x: x.hora.hour)]

    produccion_normal = [reduce(lambda acc, x: acc + x.kw_media_producidos * porcentaje, v, 0.0)
                         for _, v in
                         groupby(sorted(produccion[slice_semana], key=lambda x: x.hora.hour), lambda x: x.hora.hour)]

    def aplicar_porcentaje(x: Produccion, porcentaje: float) -> float:
        return x.kw_media_producidos * porcentaje

    produccion_diaria = list(map(lambda x: aplicar_porcentaje(x, porcentaje), produccion[slice_semana]))
    produccion_aumentada_diaria_5 = list(
        map(lambda x: aplicar_porcentaje(x, porcentaje + PORCENTAJES_AUMENTO[0]), produccion[slice_semana]))
    produccion_aumentada_diaria_10 = list(
        map(lambda x: aplicar_porcentaje(x, porcentaje + PORCENTAJES_AUMENTO[1]), produccion[slice_semana]))
    produccion_aumentada_diaria_15 = list(
        map(lambda x: aplicar_porcentaje(x, porcentaje + PORCENTAJES_AUMENTO[2]), produccion[slice_semana]))
    produccion_aumentada_diaria_20 = list(
        map(lambda x: aplicar_porcentaje(x, porcentaje + PORCENTAJES_AUMENTO[3]), produccion[slice_semana]))
    
    ahorro_normal_diario = list(map(lambda p, c: min(p, c.kw_media_consumidos),
                                    produccion_diaria, consumo_diario))

    ahorro_aumentado_diario_5 = list(map(lambda p, c: min(p, c.kw_media_consumidos), produccion_aumentada_diaria_5, consumo_diario))
    ahorro_aumentado_diario_10 = list(map(lambda p, c: min(p, c.kw_media_consumidos), produccion_aumentada_diaria_10, consumo_diario))
    ahorro_aumentado_diario_15 = list(map(lambda p, c: min(p, c.kw_media_consumidos), produccion_aumentada_diaria_15, consumo_diario))
    ahorro_aumentado_diario_20 = list(map(lambda p, c: min(p, c.kw_media_consumidos), produccion_aumentada_diaria_20, consumo_diario))

    ahorro_normal = sum(ahorro_normal_diario)
    ahorro_aumentado_5 = sum(ahorro_aumentado_diario_5)
    ahorro_aumentado_10 = sum(ahorro_aumentado_diario_10)
    ahorro_aumentado_15 = sum(ahorro_aumentado_diario_15)
    ahorro_aumentado_20 = sum(ahorro_aumentado_diario_20)

    def calcular_precio_energía_ahorrada(ahorro_diario: list[float], precio_kw_diario: list[Precio_venta]) -> list[float]:
        return list(map(lambda a, p: a * p.precio, ahorro_diario, precio_kw_diario))

    precio_kw_diario = precio_kw[slice_semana]
    precio_energia_ahorrada_total = sum(list(map(lambda c, p: c.kw_media_consumidos * p.precio, consumo_diario, precio_kw_diario))) / 1000
    precio_energia_ahorrada_normal = sum(calcular_precio_energía_ahorrada(ahorro_normal_diario, precio_kw_diario)) / 1000
    precio_energia_ahorrada_aumentado_5 = sum(calcular_precio_energía_ahorrada(ahorro_aumentado_diario_5, precio_kw_diario)) / 1000
    precio_energia_ahorrada_aumentado_10 = sum(calcular_precio_energía_ahorrada(ahorro_aumentado_diario_10, precio_kw_diario)) / 1000
    precio_energia_ahorrada_aumentado_15 = sum(calcular_precio_energía_ahorrada(ahorro_aumentado_diario_15, precio_kw_diario)) / 1000
    precio_energia_ahorrada_aumentado_20 = sum(calcular_precio_energía_ahorrada(ahorro_aumentado_diario_20, precio_kw_diario)) / 1000

    excedente_diario = map(lambda p, c: max(0.0, p - c.kw_media_consumidos), produccion_diaria, consumo_diario)
    excedente_consumo_diario_5 = map(lambda p, c: max(0.0, p - c.kw_media_consumidos), produccion_aumentada_diaria_5, consumo_diario)
    excedente_consumo_diario_10 = map(lambda p, c: max(0.0, p - c.kw_media_consumidos), produccion_aumentada_diaria_10, consumo_diario)
    excedente_consumo_diario_15 = map(lambda p, c: max(0.0, p - c.kw_media_consumidos), produccion_aumentada_diaria_15, consumo_diario)
    excedente_consumo_diario_20 = map(lambda p, c: max(0.0, p - c.kw_media_consumidos), produccion_aumentada_diaria_20, consumo_diario)

    precio_excedente_diario = map(lambda e, p: e * p.precio * PORCENTAJE_PRECIO_COMPENSACION/1000, excedente_diario, precio_kw_diario)
    precio_excedente_aumentado_diario_5 = map(lambda e, p: e * p.precio * PORCENTAJE_PRECIO_COMPENSACION/1000, excedente_consumo_diario_5, precio_kw_diario)
    precio_excedente_aumentado_diario_10 = map(lambda e, p: e * p.precio * PORCENTAJE_PRECIO_COMPENSACION/1000, excedente_consumo_diario_10, precio_kw_diario)
    precio_excedente_aumentado_diario_15 = map(lambda e, p: e * p.precio * PORCENTAJE_PRECIO_COMPENSACION/1000, excedente_consumo_diario_15, precio_kw_diario)
    precio_excedente_aumentado_diario_20 = map(lambda e, p: e * p.precio * PORCENTAJE_PRECIO_COMPENSACION/1000, excedente_consumo_diario_20, precio_kw_diario)


    produccion_total = reduce(lambda acc, x: x.kw_media_consumidos + acc, consumo_diario, 0.0)

    return {
        "semana": "Mes",
        "totales": {"total": produccion_total / 1000, 
                    "normal": ahorro_normal / 1000,
                    "aumentado_5": ahorro_aumentado_5 / 1000,
                    "aumentado_10": ahorro_aumentado_10 / 1000,
                    "aumentado_15": ahorro_aumentado_15 / 1000,
                    "aumentado_20": ahorro_aumentado_20 / 1000,
                    
                    },
        "porcentajes": [
            ahorro_normal / produccion_total * 100, 
            ahorro_aumentado_5 / produccion_total * 100,
            ahorro_aumentado_10 / produccion_total * 100,
            ahorro_aumentado_15 / produccion_total * 100,
            ahorro_aumentado_20 / produccion_total * 100,
            ],
        "precios": [
            precio_energia_ahorrada_total, 
            precio_energia_ahorrada_normal, 
            precio_energia_ahorrada_aumentado_5,
            precio_energia_ahorrada_aumentado_10,
            precio_energia_ahorrada_aumentado_15,
            precio_energia_ahorrada_aumentado_20,
            ],
        "devolucion_excedente": [
            sum(precio_excedente_diario), 
            sum(precio_excedente_aumentado_diario_5),
            sum(precio_excedente_aumentado_diario_10),
            sum(precio_excedente_aumentado_diario_15),
            sum(precio_excedente_aumentado_diario_20),
            ],
        "chart": Chart(
            str(semana),
            str([i for i in range(24)]),
            [
                # Dataset(str([c for c in ahorro_normal]), label="Ahorro normal", background_color="rgba(0, 168, 232, 0.5)"),
                # Dataset(str([p for p in ahorro_mañana]), label="Ahorro mañana", background_color="rgba(242, 100, 25, 1)"),
                # Dataset(str([p for p in ahorro_tarde]), label="Ahorro tarde", background_color="rgba(246, 174, 45, 1)"),
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

    dic = obtener_semana(0, list(consumo), list(produccion), list(precio), vecino.porcentaje)

    acordeon.append(
        dic
    )

    context = {
        "kw_contratados": vecino.porcentaje * 42,
        "acordeon": acordeon
    }
    return render(request, "decisiones/aumento_participacion.html", context=context)
