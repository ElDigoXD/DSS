
from django.http import HttpResponse
import datetime
import csv

from .models.produccion import Produccion

def load_data(request):
    now = datetime.datetime.now()
    html = "<html><body>It is now %s.</body></html>" % now

    with open("datos solar.csv") as csvfile:
        reader = csv.reader(csvfile, delimiter=";")
        for i, (field1, field2) in enumerate(reader):
            if i == 0:
                continue
            print(i, field1, field2)
            dt = datetime.datetime.strptime(field1, "%d/%m/%Y %H:%M")
            new = Produccion.objects.create(
                kw_media_producidos = float(field2),
                fecha = dt,
                hora = dt,
                duracion_m = 60
            )
            new.save()
            





    return HttpResponse(html)