import json
from typing import Any
from django.http import HttpRequest, HttpResponse
import datetime
import csv
from requests import get, Response
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
    precio = Precio_kw.objects.filter(fecha=datetime.date(2023, 10, 27)).all()

    listaGanancia = [produccion[i].kw_media_producidos - consumo[i].kw_media_consumidos
                     for i in range(24)]

    context = {
        "vecino": vecino,
        "consumo": str([h.kw_media_consumidos for h in consumo]),
        "labels": str([i for i in range(24)]),
        "produccion": str([h.kw_media_producidos for h in produccion]),
        "precio": str([h.precio for h in precio]),
        "ganancia": str([g for g in listaGanancia]) 
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
