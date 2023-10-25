from django.db import models

class Precio_kw(models.Model):
    precio = models.FloatField()
    fecha = models.DateField()
    hora = models.TimeField()
    duracion_m = models.IntegerField()