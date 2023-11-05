

from datetime import date

from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render

from dss import utils
from dss.chart import Chart, Dataset, Scale, Type
from dss.models import Consumo, Precio_venta, Produccion, Vecino


def info_vecino(request: HttpRequest) -> HttpResponse:
    vecino_id = request.GET.get("vecino_id")
    fecha = request.GET.get("fecha")

    if not (fecha
            and (fecha := utils.try_strptime(fecha, "%Y-%m-%d"))):

        raise Http404("Fecha invalida")

    # Intenta obtener el objeto Vecino correspondiente al vecino_id
    if not (vecino_id
            and (vecino_id := utils.try_int(vecino_id))
            and (vecino := Vecino.objects.filter(id=vecino_id).first())):

        raise Http404("Vecino no encontrado")

    # Filtra los objetos Consumo y Produccion relacionados con el vecino
    consumo_vecino = Consumo.objects.filter(vecino=vecino)

    consumo = consumo_vecino.filter(fecha=fecha.date()).all()
    produccion = Produccion.objects.filter(fecha=date(2016, 3, 26)).all()
    precio = Precio_venta.objects.filter(fecha=fecha.date()).all()

    if len(produccion) or len(consumo) != 24:
        raise Http404(f"Error: len(produccion): {len(produccion)} or len(consumo): {len(consumo)}")
        raise Http404(f"La fecha no está en el sistema")
        
    listaGanancia = [produccion[i].kw_media_producidos - consumo[i].kw_media_consumidos for i in range(24)]

    context = {
        "vecino": vecino,
        "consumo": str([h.kw_media_consumidos for h in consumo]),
        "labels": str([i for i in range(24)]),
        "produccion": str([h.kw_media_producidos for h in produccion]),
        "precio": str([h.precio for h in precio]),
        "ganancia": str([g for g in listaGanancia]),
        "charts": [
            # Chart(
            #     canvas_id="test",
            #     x_labels="[1,2,3,4]",
            #     datasets=[Dataset("[3,2,1,4]"), Dataset("[2,2,2,3]", "y2")],
            #     scales=[Scale("y", "left"), Scale("y2", "right", "")]
            # ),
            Chart(
                canvas_id="Produccion y consumo",
                x_labels=str([i for i in range(24)]),
                datasets=[
                    Dataset(str([h.kw_media_consumidos for h in consumo])),
                    Dataset(
                        data=str([h.kw_media_producidos for h in produccion]),
                        background_color="rgba(0,255,0,0.5)",
                        border_color="rgba(0,255,0,0.1)"
                    )
                ],
                scales=[Scale()]
            ),
            Chart(
                canvas_id="Precio KWh",
                x_labels=str([i for i in range(24)]),
                datasets=[
                    Dataset(
                        data=str([h.precio for h in precio]),
                        background_color="rgba(0,255,255,0.5)",
                        border_color="rgba(0,255,255,0.1)"
                    )
                ],
                scales=[Scale()],
            ),
            Chart(
                type=Type.BAR,
                canvas_id="Ganancia",
                x_labels=str([i for i in range(24)]),
                datasets=[
                    Dataset(str([g for g in listaGanancia])),
                    Dataset(
                        data=str([precio[i].precio * listaGanancia[i]/1000 for i in range(24)]),
                        y_axis_id="y2",
                        background_color="rgba(255,0,0,0.5)")
                ],
                scales=[Scale("y", "left"), Scale("y2", "right")]
            )
        ]
    }

    return render(
        request,
        "datos.html",
        context=context
    )
