from django.db import models
from .vecino import Vecino

class Consumo(models.Model):
    vecino = models.ForeignKey(Vecino, on_delete=models.CASCADE)
    kw_media_consumidos = models.FloatField()
    fecha = models.DateField()
    hora = models.TimeField()
    duracion_m = models.IntegerField()