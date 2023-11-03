import json
from typing import Any
from django.http import HttpRequest, HttpResponse, JsonResponse
import datetime
import csv
from requests import get, Response

from dss.chart import *
from dss.models.precio_venta import Precio_venta
from .models import ConsumoDev, Precio_kw, Consumo, Vecino, Produccion
from django.shortcuts import render
from django.http import Http404


def index(request: HttpRequest) -> HttpResponse:
    vecinos = Vecino.objects.all()
    return render(request, "index.html", {"vecinos": vecinos})


def info_vecino(request: HttpRequest) -> HttpResponse:
    vecino_id = request.GET.get("vecino_id")

    # Intenta obtener el objeto Vecino correspondiente al vecino_id
    if (not (vecino_id and vecino_id.isnumeric())
        or not (
            vecino := Vecino.objects.get_or_create(id=int(vecino_id), defaults=None)[0]
    )):
        raise Http404("Vecino no encontrado")

    # Filtra los objetos Consumo y Produccion relacionados con el vecino
    consumo_vecino = Consumo.objects.filter(vecino=vecino)
    produccion_vecino = Produccion.objects.filter()

    consumo = consumo_vecino.filter(fecha=datetime.date(2023, 1, 3)).all()
    produccion = Produccion.objects.filter(
        fecha=datetime.date(2016, 3, 26)
    ).all()
    precio = Precio_venta.objects.filter(fecha=datetime.date(2023, 1, 3)).all()

    listaGanancia = [produccion[i].kw_media_producidos - consumo[i].kw_media_consumidos
                     for i in range(24)]

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
                canvas_id="prod_y_consumo_chart",
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
                canvas_id="precio",
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
                canvas_id="ganancia",
                x_labels=str([i for i in range(24)]),
                datasets=[
                    Dataset(str([g for g in listaGanancia])),
                    Dataset(
                        data=str(
                            [precio[i].precio * listaGanancia[i]/1000 for i in range(24)]),
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


def load_vecinos(request: HttpRequest) -> HttpResponse:
    return HttpResponse("")
    result = ConsumoDev.objects.filter(
        fecha__gte=datetime.date(2010, 10, 1), fecha__lt=datetime.date(2010, 11, 1)
    )
    print(result)
    for r in result:
        Consumo.objects.create(
            vecino=Vecino.objects.get(nombre="pepe"),
            kw_media_consumidos=r.kw_media_consumidos,
            fecha=datetime.date(2023, 1, r.fecha.day),
            hora=r.hora,
            duracion_m=60,
        )
    return HttpResponse(
        f"<html><body>It is now {datetime.datetime.now()}.</body></html>"
    )


def load_precios(request: HttpRequest) -> HttpResponse:
    res: Response = get("https://api.preciodelaluz.org/v1/prices/all?zone=PCB")
    print(res.text)
    a: dict[str, dict[str, Any]] = json.loads(res.text)

    a2 = Precio_kw.objects.filter(
        fecha=datetime.datetime.strptime(a["00-01"]["date"], "%d-%m-%Y")
    )
    if len(a2) == 0:
        print("vacío")
        for h, datos in a.items():
            new = Precio_kw.objects.create(
                precio=datos["price"] / 1000,
                fecha=datetime.datetime.strptime(datos["date"], "%d-%m-%Y"),
                hora=datetime.datetime.strptime(datos["hour"][:2], "%H"),
                duracion_m=60,
            )
            new.save()
    else:
        print(a2)

    # for h, datos in a.items():
    #     print(datos["price"])

    return HttpResponse(f"<html> {a} <html>")


def load_data(request: HttpRequest) -> HttpResponse:

    res = get("https://api.preciodelaluz.org/v1/prices/all?zone=PCB")
    print(res.text)

    # stext = [x for ]
    return HttpResponse(f"<html> {res.text} <html>")
    with open("datos consumo.csv") as csvfile:
        reader = csv.reader(csvfile, delimiter=";")
        for i, (date, time, consumo) in enumerate(reader):
            if i == 0:
                continue
            d = datetime.datetime.strptime(date, "%d/%m/%Y")
            t = datetime.datetime.strptime(time, "%H:%M:%S")
            # print(d, t, float(consumo.replace(",", ".")))
            new = ConsumoDev.objects.create(
                kw_media_consumidos=float(consumo.replace(",", ".")),
                fecha=d,
                hora=t,
                duracion_m=60,
            )

    return HttpResponse(html)

def test(request: HttpRequest)-> HttpResponse:
    res = get("https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real?start_date=2023-01-01T00:00&end_date=2023-01-31T23:59&time_trunc=hour")
    
    values = json.loads(res.text)["included"][0]["attributes"]["values"]
    for value in values:
        new = Precio_venta.objects.get_or_create(
            fecha=datetime.datetime.fromisoformat(value["datetime"]),
            hora=datetime.datetime.fromisoformat(value["datetime"]),
            defaults={
                "precio": value["value"]/1000,
                "duracion_m": 60,
            }
        )
        print(new)

    print(values)
    return HttpResponse()

    # new = Precio_kw.objects.create(
    #     precio=2,
    #     fecha=datetime.datetime.fromisoformat(),
    #     hora=,
    #     duracion_m=60,
    # )

    return JsonResponse(json.loads(res.text))