import csv
import json
from datetime import date, datetime
from typing import Any

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from requests import Response, get

from dss.models import Consumo, ConsumoDev, Precio_kw, Precio_venta, Vecino, Produccion
from .decisiones.aumento_participacion import aumento_participacion
from .decisiones.baterias import baterias
from .decisiones.orientacion_placas import orientacion_placas, orientacion_placas_vecino
from .info_vecino import info_vecino


def bs_test(request: HttpRequest) -> HttpResponse:
    return HttpResponse("")
    result = Produccion.objects.filter(
        fecha__gte=date(2023, 1, 1), fecha__lt=date(2023, 2, 1)
    )
    for r in result:
        r.kw_media_producidos = r.kw_media_producidos / 10
        r.save()
    return HttpResponse(
        f"<html><body>It is now {datetime.now()}.</body></html>"
    )


def index(request: HttpRequest) -> HttpResponse:
    vecinos = Vecino.objects.all()
    return render(request, "index.html", {"vecinos": vecinos})


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
        fecha=datetime.strptime(a["00-01"]["date"], "%d-%m-%Y")
    )
    if len(a2) == 0:
        print("vacío")
        for h, datos in a.items():
            new = Precio_kw.objects.create(
                precio=datos["price"] / 1000,
                fecha=datetime.strptime(datos["date"], "%d-%m-%Y"),
                hora=datetime.strptime(datos["hour"][:2], "%H"),
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
            d = datetime.strptime(date, "%d/%m/%Y")
            t = datetime.strptime(time, "%H:%M:%S")
            # print(d, t, float(consumo.replace(",", ".")))
            new = ConsumoDev.objects.create(
                kw_media_consumidos=float(consumo.replace(",", ".")),
                fecha=d,
                hora=t,
                duracion_m=60,
            )

    return HttpResponse(html)


def test(request: HttpRequest) -> HttpResponse:
    res = get(
        "https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real?start_date=2023-01-01T00:00&end_date=2023-01-31T23:59&time_trunc=hour")

    values = json.loads(res.text)["included"][0]["attributes"]["values"]
    for value in values:
        new = Precio_venta.objects.get_or_create(
            fecha=datetime.fromisoformat(value["datetime"]),
            hora=datetime.fromisoformat(value["datetime"]),
            defaults={
                "precio": value["value"] / 1000,
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
