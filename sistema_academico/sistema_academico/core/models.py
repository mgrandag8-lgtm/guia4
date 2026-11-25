from django.conf import settings
from django.db import models


class ModeloBase(models.Model):
    """
    Modelo abstracto: NO crea una tabla propia.
    Todos los modelos del sistema heredan de este para tener
    los mismos 3 campos de auditoría (quién y cuándo).
    """

    # Usuario que registró el dato.
    # Uso settings.AUTH_USER_MODEL (es el modelo User de Django) porque es la forma recomendada.
    # SET_NULL: si se borra el usuario, el registro NO se borra, solo queda sin usuario.
    # editable=False: no aparece en los formularios; lo llenaremos desde las vistas.
    # related_name con %(app_label)s y %(class)s: Django los reemplaza por la app y el modelo,
    # así no se repite el nombre entre modelos (ej: academico_curso_registrados).
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False,
        related_name="%(app_label)s_%(class)s_registrados",
    )

    # Se llena sola UNA vez, cuando se crea el registro
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    # Se actualiza sola CADA vez que se guarda el registro
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True  # Importante: así Django no crea una tabla para ModeloBase