from datetime import date
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from dss.models.consumo import Consumo
from dss.models.precio_venta import Precio_venta
from dss.models.produccion import Produccion

from dss.models.vecino import Vecino


def baterias(request: HttpRequest) -> HttpResponse:
    vecino_id = None
    if not vecino_id:
        vecino_id = request.session.get("vecino_id")

    vecino = Vecino.objects.filter(id=vecino_id).first()

    if not vecino:
        raise Http404()

    consumo = list(Consumo.objects.filter(
        fecha__gte=date(2023, 1, 1),
        fecha__lt=date(2023, 2, 1),
        vecino_id=vecino_id
    ).order_by("fecha").all())

    produccion = list(Produccion.objects.filter(
        fecha__gte=date(2023, 1, 1),
        fecha__lt=date(2023, 2, 1),
    ).order_by("fecha", "hora").all())

    precio = list(Precio_venta.objects.filter(
        fecha__gte=date(2023, 1, 1),
        fecha__lt=date(2023, 2, 1),
    ).order_by("fecha", "hora").all())

    bateria = 0.0

    for (consumo, prod, precio) in map(lambda consumo, prod, precio: (consumo.kw_media_consumidos, prod.kw_media_producidos, precio.precio), consumo, produccion, precio):
        pass

    


    # Si hay excedente de produccion, se añade a la batería si cabe, si no se vende
    # Si falta produccion se coge de la batería, si la batería está vacía, se compra 

    


    return render(request, "decisiones/baterias.html")
