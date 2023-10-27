from django.db import models

class ConsumoDev(models.Model):
    kw_media_consumidos = models.FloatField()
    fecha = models.DateField()
    hora = models.TimeField()
    duracion_m = models.IntegerField()

    def __str__(self) -> str:
        return f"{self.fecha} {self.hora} | {self.kw_media_consumidos}"
