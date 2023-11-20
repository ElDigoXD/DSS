"""
URL configuration for dss project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from dss.views.decisiones.aumento_participacion import aumento_participacion_vecino
from .views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('load_data/', load_data),
    path('load_vecinos/', load_vecinos),
    path('test/', test),
    path('', index, name='seleccionar_vecino'),
    path('datos/', info_vecino, name='datos_vecino'),
    path('orientacion_placas/', orientacion_placas, name="orientacion_placas"),
    path('orientacion_placas/<int:vecino_id>', orientacion_placas_vecino, name="orientacion_placas"),
    path('aumento_participacion/', aumento_participacion, name="aumento_participacion"),
    path('aumento_participacion/<int:vecino_id>', aumento_participacion_vecino, name="aumento_participacion"),
    path('baterias/', baterias, name="baterias"),
    path('test', bs_test, name="test")
]
