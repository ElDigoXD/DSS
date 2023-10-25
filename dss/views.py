
from django.http import HttpResponse
import datetime
import csv

from .models.consumo_dev import ConsumoDev


def load_data(request):
    now = datetime.datetime.now()
    html = "<html><body>It is now %s.</body></html>" % now

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