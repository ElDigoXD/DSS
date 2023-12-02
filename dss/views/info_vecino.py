from datetime import datetime
from typing import Tuple

from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from dss import utils
from dss.chart import Chart, Dataset, Scale, Type
from dss.models import Consumo, Precio_venta, Produccion, Vecino
from dss.utils import float_round


def vecino_fecha_GET(vecino_id_str: str | None, fecha_str: str | None) -> Tuple[Vecino | None, datetime | None]:
    vecino = None
    fecha = None

    if fecha_str:
        if not (fecha := utils.try_strptime(fecha_str, "%Y-%m-%d")):
            return (None, None)

    if vecino_id_str:
        vecino_id = utils.try_int(vecino_id_str)
        vecino = Vecino.objects.filter(id=vecino_id).first()

    return (vecino, fecha)


def info_vecino(request: HttpRequest) -> HttpResponse:
    # Si la petición contiene algún parámetro get
    vecino_id_str = request.GET.get("vecino_id")
    fecha_str = request.GET.get("fecha")

    if vecino_id_str or fecha_str:
        vecino, fecha = vecino_fecha_GET(vecino_id_str, fecha_str)

        if not fecha:
            raise Http404("Fecha invalida")
        if not vecino:
            raise Http404("Vecino no encontrado")

        # Guarda los parametros en la sesión, así podremos 
        # navegar a páginas sin tener que pasar parámetros en la url
        request.session["vecino_id"] = vecino.pk
        request.session["fecha"] = datetime.strftime(fecha, "%Y-%m-%d")

        # Descomentar para "limpiar" los parametros de la url, 
        # si cambiamos de GET a POST no debería hacer falta
        # return redirect("datos_vecino")

    else:
        vecino_id = request.session.get("vecino_id")
        fecha_str = request.session.get("fecha")
        print(request.session.__dict__)
        if not (vecino_id and fecha_str):
            # Redirecciona a la página de seleccionar el vecino para
            # poder realizar la primera consulta get.
            return redirect("seleccionar_vecino")

        fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
        vecino = Vecino.objects.filter(id=vecino_id).first()
        if not vecino:
            raise (Http404)

    # Filtra los objetos Consumo y Produccion relacionados con el vecino
    consumo_vecino = Consumo.objects.filter(vecino=vecino)
    consumo_total = Consumo.objects.filter(fecha=fecha.date()).all()

    consumo_agregado = [0.0] * 24

    for i in range(24):
        for h in consumo_total:
            if h.hora.hour == i:
                consumo_agregado[i] = consumo_agregado[i] + h.kw_media_consumidos

    consumo = consumo_vecino.filter(fecha=fecha.date()).all()
    produccion = Produccion.objects.filter(fecha=fecha.date()).all()
    precio = Precio_venta.objects.filter(fecha=fecha.date()).all()

    if len(produccion) != 24 or len(consumo) != 24:
        raise Http404(f"Error: len(produccion): {len(produccion)} or len(consumo): {len(consumo)}")
        raise Http404(f"La fecha no está en el sistema")

    lista_ahorro = [(produccion[i].kw_media_producidos * vecino.porcentaje) - consumo[i].kw_media_consumidos for i in range(24)]
    context = {
        "vecino": vecino,
        "charts": [
            Chart(
                name="Produccion y consumo",
                canvas_id="Produccion_y_consumo",
                legend=True,
                x_labels=str([i for i in range(24)]),
                datasets=[
                    Dataset(
                        label="kW consumidos",
                        data=str([h.kw_media_consumidos for h in consumo])),
                    Dataset(
                        label="kW producidos",
                        data=str([h.kw_media_producidos * vecino.porcentaje for h in produccion]),
                        background_color="rgba(0,255,0,0.5)",
                        border_color="rgba(0,255,0,0.1)"
                    )
                ],
                scales=[Scale()]
            ),
            Chart(
                name="Precio kWh",
                canvas_id="Precio_kWh",
                legend=True,
                x_labels=str([i for i in range(24)]),
                datasets=[
                    Dataset(
                        label="€/kWh",
                        data=str([float_round(h.precio) for h in precio]),
                        background_color="rgba(0,255,255,0.5)",
                        border_color="rgba(0,255,255,0.1)"
                    )
                ],
                scales=[Scale()],
            ),
            Chart(
                name="Ahorro por autoconsumo",
                canvas_id="Ahorro",
                legend=True,
                type=Type.BAR,
                x_labels=str([i for i in range(24)]),
                datasets=[
                    Dataset(
                        label="kW autoconsumidos",
                        data=str([float_round(g/1000) for g in lista_ahorro])),
                    Dataset(
                        label="€ ahorrados",
                        data=str([float_round(precio[i].precio * lista_ahorro[i] / 1000) for i in range(24)]),
                        y_axis_id="y2",
                        background_color="rgba(255,0,0,0.5)")
                ],
                scales=[Scale("y", "left"), Scale("y2", "right")]
            ),
            Chart(
                name="Consumo de toda la comunidad",
                canvas_id="Consumo_Total",
                legend=True,
                x_labels=str([i for i in range(24)]),
                datasets=[
                    Dataset(
                        label="Consumo total",
                        data=str([float_round(c/1000) for c in consumo_agregado])),
                    Dataset(
                        label="Producción total",
                        data=str([float_round(h.kw_media_producidos/1000) for h in produccion]),
                        background_color="rgba(0,255,0,0.5)",
                        border_color="rgba(0,255,0,0.1)"
                    )
                ],
                scales=[Scale()]
            )
        ]
    }

    return render(
        request,
        "datos.html",
        context=context
    )
