from django.db import models

class Vecino(models.Model):
    nombre = models.CharField(max_length=50)
    porcentaje = models.FloatField()

    def __str__(self) -> str:
        return f"{self.nombre} | {self.porcentaje*100}%"