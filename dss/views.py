
from django.http import HttpResponse
import datetime
import csv
from requests import get
from .models.consumo_dev import ConsumoDev


def load_data(request):
    now = datetime.datetime.now()
    html = "<html><body>It is now %s.</body></html>" % now

    # por cada vecino
    # añadir consumo relativo a su porcentaje
    # 1 mes

    res = get("https://api.preciodelaluz.org/v1/prices/all?zone=PCB")
    print(res.text)

    #stext = [x for ]
    return HttpResponse(f"<html> {text} <html>")
    with open("datos consumo.csv") as csvfile:
        reader = csv.reader(csvfile, delimiter=";")
        for i, (date, time, consumo) in enumerate(reader):
            if i == 0:
                continue
            d = datetime.datetime.strptime(date, "%d/%m/%Y")
            t = datetime.datetime.strptime(time, "%H:%M:%S")
            #print(d, t, float(consumo.replace(",", ".")))
            new = ConsumoDev.objects.create(
                kw_media_consumidos = float(consumo.replace(",", ".")),
                fecha = d,
                hora = t,
                duracion_m = 60
            )
            new.save()
            





    return HttpResponse(html)