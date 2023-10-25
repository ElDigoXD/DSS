from django.db import models

class ConsumoDev(models.Model):
    kw_media_consumidos = models.FloatField()
    fecha = models.DateField()
    hora = models.TimeField()
    duracion_m = models.IntegerField()