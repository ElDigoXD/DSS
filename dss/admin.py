from django.contrib import admin

from .models import *

admin.site.register([Vecino, Produccion, Consumo, Precio_kw, ConsumoDev, Precio_venta])
