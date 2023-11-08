

from datetime import date, datetime
from typing import Tuple

from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from dss import utils
from dss.chart import Chart, Dataset, Scale, Type
from dss.models import Consumo, Precio_venta, Produccion, Vecino


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
    # Si la petición contiene algún parametro get
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
        #return redirect("datos_vecino")
        
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
            raise(Http404)

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
                        data=str([h.kw_media_producidos * vecino.porcentaje for h in produccion]),
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
            ),
            Chart(
                canvas_id="Consumo Total",
                x_labels=str([i for i in range(24)]),
                datasets=[
                    Dataset(str(consumo_agregado)),
                    Dataset(
                        data=str([h.kw_media_producidos for h in produccion]),
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
