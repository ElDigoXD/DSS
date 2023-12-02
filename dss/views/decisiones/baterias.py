from datetime import date
from functools import reduce

from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render

from dss.models.consumo import Consumo
from dss.models.precio_venta import Precio_venta
from dss.models.produccion import Produccion
from dss.models.vecino import Vecino

PORCENTAJE_PRECIO_COMPENSACION = 0.75


def simular(limite_batería_kw: float, porcentaje: float, consumo_db: list[Consumo], produccion_db: list[Produccion], precio_db: list[Precio_venta]):
    bateria = 0.0
    limite_batería = limite_batería_kw * 1000
    comprado_total = 0.0
    precio_comprado_total = 0.0

    vendido_total = 0.0
    precio_vendido_total = 0.0

    ahorrado_total = 0.0
    precio_ahorrado_total = 0.0

    autoconsumo_total = 0.0
    precio_autoconsumo_total = 0.0

    for (consumo, prod, precio) in map(
            lambda consumo, prod, precio: (consumo.kw_media_consumidos, prod.kw_media_producidos * porcentaje, precio.precio),
            consumo_db, produccion_db, precio_db):

        if prod > consumo:
            excedente = prod - consumo

            bateria_libre = limite_batería - bateria
            if excedente <= bateria_libre:
                bateria += excedente

            else:
                vendido = excedente - bateria_libre
                bateria = limite_batería

                vendido_total += vendido
                precio_vendido_total += vendido * precio * PORCENTAJE_PRECIO_COMPENSACION

            autoconsumo = consumo
            autoconsumo_total += autoconsumo
            precio_autoconsumo_total += autoconsumo * precio

        else:
            faltante = consumo - prod
            if faltante < bateria:
                bateria -= faltante

                ahorrado_total += faltante
                precio_ahorrado_total += faltante * precio

            else:
                comprado = faltante - bateria
                bateria = 0.0

                ahorrado_total += bateria
                precio_ahorrado_total += bateria * precio

                comprado_total += comprado
                precio_comprado_total += (comprado * precio)

            autoconsumo = prod
            autoconsumo_total += autoconsumo
            precio_autoconsumo_total += autoconsumo * precio

    consumido_total = reduce(lambda acc, x: x.kw_media_consumidos + acc, consumo_db, 0.0)
    precio_sin_ahorros = sum(list(map(lambda c, p: c.kw_media_consumidos * p.precio, consumo_db, precio_db)))

    print("ahorro  -", ahorrado_total / 1000, ":", precio_ahorrado_total / 1000)
    print("venta   -", vendido_total / 1000, ":", precio_vendido_total / 1000)
    print("compra  -", comprado_total / 1000, ":", precio_comprado_total / 1000)
    print("factura -", (precio_comprado_total - precio_vendido_total) / 1000)

    return {
        "kwh": (autoconsumo_total + ahorrado_total) / 1000,
        "porcentaje": (autoconsumo_total + ahorrado_total) / consumido_total * 100,
        "dinero_ahorrado": (precio_sin_ahorros - precio_comprado_total) / 1000,
        "dinero_excedente": precio_vendido_total / 1000,
    }


def baterias(request: HttpRequest) -> HttpResponse:
    vecino_id = 1
    if not vecino_id:
        vecino_id = request.session.get("vecino_id")

    vecino = Vecino.objects.filter(id=vecino_id).first()

    if not vecino:
        raise Http404()

    consumo_db = list(Consumo.objects.filter(
        fecha__gte=date(2023, 1, 1),
        fecha__lt=date(2023, 2, 1),
        vecino_id=vecino_id
    ).order_by("fecha", "hora").all())

    produccion_db = list(Produccion.objects.filter(
        fecha__gte=date(2023, 1, 1),
        fecha__lt=date(2023, 2, 1),
    ).order_by("fecha", "hora").all())

    precio_db = list(Precio_venta.objects.filter(
        fecha__gte=date(2023, 1, 1),
        fecha__lt=date(2023, 2, 1),
    ).order_by("fecha", "hora").all())
    # Si hay excedente de produccion, se añade a la batería si cabe, si no se vende
    # Si falta produccion se coge de la batería, si la batería está vacía, se compra 

    consumido_total = reduce(lambda acc, x: x.kw_media_consumidos + acc, consumo_db, 0.0) / 1000
    precio_sin_ahorros = sum(list(map(lambda c, p: c.kw_media_consumidos * p.precio, consumo_db, precio_db))) / 1000

    context = {
        "acordeon": [{
            "semana": "Mes",
            "total": {
                "kwh": consumido_total,
                "precio": precio_sin_ahorros,
            },
            "actual": simular(0.0, vecino.porcentaje, consumo_db, produccion_db, precio_db),
            "aumentado_5": simular(5.0, vecino.porcentaje, consumo_db, produccion_db, precio_db),
            "aumentado_10": simular(10.0, vecino.porcentaje, consumo_db, produccion_db, precio_db),
            "aumentado_15": simular(15.0, vecino.porcentaje, consumo_db, produccion_db, precio_db),
            "aumentado_20": simular(20.0, vecino.porcentaje, consumo_db, produccion_db, precio_db),
        }]
    }

    return render(request, "decisiones/baterias.html", context)
