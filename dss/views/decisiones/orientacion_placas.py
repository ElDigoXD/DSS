from datetime import date, datetime, timedelta
from functools import reduce
from itertools import groupby

from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render

from dss.chart import *
from dss.models.consumo import Consumo
from dss.models.precio_venta import Precio_venta
from dss.models.produccion import Produccion
from dss.models.vecino import Vecino
from dss.utils import float_round

EFICIENCIA_ROTACION = 0.95


def orientacion_placas(request: HttpRequest) -> HttpResponse:
    return orientacion_placas_vecino(request, None)


def obtener_semana(semana: int, consumo: list[Consumo], produccion: list[Produccion], precio_kw: list[Precio_venta],
                   porcentaje: float) -> tuple[
    list[float], list[float], list[float], list[float], list[float], list[float], list[
        float], float, float, float, float]:
    slice_semana = slice(7 * 24 * (semana - 1), 7 * 24 * semana) if semana != 0 else slice(-1)

    consumo_diario = consumo[slice_semana]
    consumo_agregado = [reduce(lambda acc, x: acc + x.kw_media_consumidos, v, 0.0)
                        for _, v in groupby(sorted(consumo_diario, key=lambda x: x.hora.hour), lambda x: x.hora.hour)]

    produccion_diaria = produccion[slice_semana]
    produccion_normal = [reduce(lambda acc, x: acc + x.kw_media_producidos * porcentaje, v, 0.0)
                         for _, v in
                         groupby(sorted(produccion_diaria, key=lambda x: x.hora.hour), lambda x: x.hora.hour)]

    produccion_time = [(datetime.combine(p.fecha, p.hora), p.kw_media_producidos * porcentaje) for p in
                       produccion_diaria]

    produccion_mañana_diario = [(datetime - timedelta(hours=1), kw) for datetime, kw in produccion_time]
    popped = produccion_mañana_diario.pop(0)
    produccion_mañana = [reduce(lambda acc, x: acc + x[1], v, 0.0)
                         for _, v in
                         groupby(sorted(produccion_mañana_diario, key=lambda x: x[0].hour), lambda x: x[0].hour)]

    produccion_tarde_diario = [(datetime + timedelta(hours=1), kw) for datetime, kw in produccion_time]
    produccion_tarde_diario.insert(0, (popped[0] + timedelta(hours=1), 0.0))
    produccion_tarde = [reduce(lambda acc, x: acc + x[1], v, 0.0)
                        for _, v in groupby(sorted(produccion_tarde_diario, key=lambda x: x[0].hour), lambda x: x[0].hour)]

    ahorro_normal_diario = list(map(lambda p, c: (p.hora.hour, min(p.kw_media_producidos * porcentaje, c.kw_media_consumidos)),
                                    produccion_diaria, consumo_diario))

    def calcular_ahorro_diario(producción_diaria: list[tuple[datetime, float]], consumo_diario: list[consumo]) -> list[tuple[datetime, float]]:
        return list(map(lambda p, c: (p[0].hour, min(p[1] * EFICIENCIA_ROTACION, c.kw_media_consumidos)),
                        producción_diaria, consumo_diario))

    ahorro_mañana_diario = calcular_ahorro_diario(produccion_mañana_diario, consumo_diario)
    ahorro_tarde_diario = calcular_ahorro_diario(produccion_tarde_diario, consumo_diario)

    def agrupar_ahorro_por_horas(ahorro_diario: list[tuple[datetime, float]]):
        return [reduce(lambda acc, x: acc + x[1], v, 0.0)
                for _, v in groupby(sorted(ahorro_diario, key=lambda x: x[0]), lambda x: x[0])]

    ahorro_normal = agrupar_ahorro_por_horas(ahorro_normal_diario)
    ahorro_mañana = agrupar_ahorro_por_horas(ahorro_mañana_diario)
    ahorro_tarde = agrupar_ahorro_por_horas(ahorro_tarde_diario)

    def calcular_precio_energía_ahorrada(ahorro_diario: list[tuple[datetime, float]], precio_kw_diario: list[Precio_venta]) -> list[float]:
        return list(map(lambda a, p: a[1] * p.precio, ahorro_diario, precio_kw_diario))

    precio_kw_diario = precio_kw[slice_semana]
    precio_energia_total = sum(list(map(lambda c, p: c.kw_media_consumidos * p.precio, consumo_diario, precio_kw_diario))) / 1000
    precio_energia_normal = sum(calcular_precio_energía_ahorrada(ahorro_normal_diario, precio_kw_diario)) / 1000
    precio_energia_mañana = sum(calcular_precio_energía_ahorrada(ahorro_mañana_diario, precio_kw_diario)) / 1000
    precio_energia_tarde = sum(calcular_precio_energía_ahorrada(ahorro_tarde_diario, precio_kw_diario)) / 1000

    return (consumo_agregado,
            produccion_normal, produccion_mañana, produccion_tarde,
            ahorro_normal, ahorro_mañana, ahorro_tarde,
            precio_energia_total, precio_energia_normal, precio_energia_mañana, precio_energia_tarde)


def orientacion_placas_vecino(request: HttpRequest, vecino_id) -> HttpResponse:
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
        (consumo_agregado,
         produccion_normal, produccion_mañana, produccion_tarde,
         ahorro_normal, ahorro_mañana, ahorro_tarde,
         precio_total, precio_normal, precio_mañana, precio_tarde) = obtener_semana(i, list(consumo), list(produccion),
                                                                                    list(precio), vecino.porcentaje)

        diferencias = [sum(ahorro_normal) / sum(consumo_agregado) * 100,
                       sum(ahorro_mañana) / sum(consumo_agregado) * 100,
                       sum(ahorro_tarde) / sum(consumo_agregado) * 100]
        totales = {"total": sum(consumo_agregado) / 1000, "normal": sum(ahorro_normal) / 1000,
                   "mañana": sum(ahorro_mañana) / 1000, "tarde": sum(ahorro_tarde) / 1000}

        acordeon.append(
            {
                "semana": semana,
                "totales": totales,
                "porcentajes": diferencias,
                "precios": [precio_total, precio_normal, precio_mañana, precio_tarde],
                "chart": Chart(
                    semana,
                    str([i for i in range(24)]),
                    [
                        Dataset(
                            label="Ahorro normal (kW)",
                            data=str([float_round(a / 1000) for a in ahorro_normal]),
                            background_color="rgba(0, 168, 232, 0.5)"),
                        Dataset(
                            label="Ahorro mañana (kW)",
                            data=str([float_round(a / 1000) for a in ahorro_mañana]),
                            background_color="rgba(242, 100, 25, 1)"),
                        Dataset(
                            label="Ahorro tarde (kW)",
                            data=str([float_round(a / 1000) for a in ahorro_tarde]),
                            background_color="rgba(246, 174, 45, 1)"),
                    ],
                    [Scale()],
                    Type.BAR,
                    legend=True
                )
            },
        )

    context = {
        "acordeon": acordeon
    }
    return render(request, "decisiones/orientacion_placas.html", context=context)
