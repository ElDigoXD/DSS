from datetime import date

from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render

from dss.models.consumo import Consumo
from dss.models.precio_venta import Precio_venta
from dss.models.produccion import Produccion
from dss.models.vecino import Vecino

PORCENTAJE_PRECIO_COMPENSACION = 0.75


def baterias(request: HttpRequest) -> HttpResponse:
    vecino_id = None
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

    porcentaje = vecino.porcentaje
    bateria = 0.0
    # Todo: comprobar si funciona poniendo el limite a 0
    # Todo: limite dinámico
    limite_batería = 10_000

    comprado_total = 0.0
    precio_comprado_total = 0.0

    vendido_total = 0.0
    precio_vendido_total = 0.0

    ahorrado_total = 0.0
    precio_ahorrado_total = 0.0

    for (consumo, prod, precio) in map(
            lambda consumo, prod, precio: (consumo.kw_media_consumidos, prod.kw_media_producidos * porcentaje, precio.precio),
            consumo_db, produccion_db, precio_db):

        if prod > consumo:
            excedente = prod - consumo
            bateria_libre = limite_batería - bateria
            if excedente <= bateria_libre:
                bateria = bateria + excedente

            else:
                vendido = excedente - bateria_libre
                bateria = limite_batería

                vendido_total = vendido_total + vendido
                precio_vendido_total = precio_vendido_total + (vendido * precio * PORCENTAJE_PRECIO_COMPENSACION)

        else:
            faltante = consumo - prod
            if faltante < bateria:
                bateria = bateria - faltante

                ahorrado_total = ahorrado_total + faltante
                precio_ahorrado_total = precio_ahorrado_total + (faltante * precio)

            else:
                comprado = faltante - bateria
                bateria = 0.0

                ahorrado_total = ahorrado_total + bateria
                precio_ahorrado_total = precio_ahorrado_total + (bateria * precio)

                comprado_total = comprado_total + comprado
                precio_comprado_total = precio_comprado_total + (comprado * precio)

    print("ahorro  -", ahorrado_total / 1000, ":", precio_ahorrado_total / 1000)
    print("venta   -", vendido_total / 1000, ":", precio_vendido_total / 1000)
    print("compra  -", comprado_total / 1000, ":", precio_comprado_total / 1000)
    print("factura -", (precio_comprado_total - precio_vendido_total) / 1000)

    # Si hay excedente de produccion, se añade a la batería si cabe, si no se vende
    # Si falta produccion se coge de la batería, si la batería está vacía, se compra 

    context = {
        "acordeon": [{

        }]
    }

    return render(request, "decisiones/baterias.html", context)
