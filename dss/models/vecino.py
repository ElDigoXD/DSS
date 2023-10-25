from django.db import models

class Vecino(models.Model):
    nombre = models.CharField(max_length=50)
    porcentaje = models.FloatField()