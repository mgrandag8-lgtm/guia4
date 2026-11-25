from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from core.models import ModeloBase

# ---------------------------------------------------------------------------
# CONSTANTES
# ---------------------------------------------------------------------------
NOTA_MINIMA = Decimal("0")                  # La nota más baja posible
NOTA_MAXIMA = Decimal("100")                # La nota más alta posible
NOTA_MINIMA_APROBACION = Decimal("70")      # Con 70 o más (promedio) se aprueba

# Validadores reutilizables: se usan en n1, n2 y n3
VALIDADORES_NOTA = [
    MinValueValidator(NOTA_MINIMA),
    MaxValueValidator(NOTA_MAXIMA),
]


# ---------------------------------------------------------------------------
# CHOICES (listas de opciones fijas)
# ---------------------------------------------------------------------------
class Jornada(models.TextChoices):
    # NOMBRE = "valor que se guarda en la BD", "texto que ve el usuario"
    DIURNA = "diurna", "Diurna"
    NOCTURNA = "nocturna", "Nocturna"


class EstadoNota(models.TextChoices):
    APROBADO = "aprobado", "Aprobado"
    REPROBADO = "reprobado", "Reprobado"


# ---------------------------------------------------------------------------
# UNIVERSIDAD
# ---------------------------------------------------------------------------
class Universidad(ModeloBase):
    nombre = models.CharField(max_length=150, unique=True)  # unique: no se repite
    siglas = models.CharField(max_length=20)
    ciudad = models.CharField(max_length=100)
    # ImageField necesita la librería pillow (ya la tienes).
    # blank=True y null=True: el logo es opcional.
    logo = models.ImageField(upload_to="universidades/", blank=True, null=True)

    class Meta:
        verbose_name = "Universidad"
        verbose_name_plural = "Universidades"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.siglas})"


# ---------------------------------------------------------------------------
# FACULTAD
# ---------------------------------------------------------------------------
class Facultad(ModeloBase):
    # PROTECT: no deja borrar una universidad si tiene facultades
    universidad = models.ForeignKey(
        Universidad, on_delete=models.PROTECT, related_name="facultades"
    )
    nombre = models.CharField(max_length=150)
    decano = models.CharField(max_length=150, blank=True)  # opcional

    class Meta:
        verbose_name = "Facultad"
        verbose_name_plural = "Facultades"
        ordering = ["universidad__nombre", "nombre"]
        constraints = [
            # El nombre no se puede repetir dentro de la MISMA universidad
            models.UniqueConstraint(
                fields=["universidad", "nombre"],
                name="facultad_nombre_unico_por_universidad",
            )
        ]

    def __str__(self):
        return f"{self.nombre} - {self.universidad.siglas}"


# ---------------------------------------------------------------------------
# CARRERA
# ---------------------------------------------------------------------------
class Carrera(ModeloBase):
    facultad = models.ForeignKey(
        Facultad, on_delete=models.PROTECT, related_name="carreras"
    )
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=150)
    duracion_semestres = models.PositiveSmallIntegerField(default=8)

    class Meta:
        verbose_name = "Carrera"
        verbose_name_plural = "Carreras"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


# ---------------------------------------------------------------------------
# SEMESTRE
# ---------------------------------------------------------------------------
class Semestre(ModeloBase):
    # Solo se permiten números del 1 al 12
    numero = models.PositiveSmallIntegerField(
        unique=True,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
    )
    nombre = models.CharField(max_length=50)  # ej: "Primer semestre"

    class Meta:
        verbose_name = "Semestre"
        verbose_name_plural = "Semestres"
        ordering = ["numero"]

    def __str__(self):
        return self.nombre


# ---------------------------------------------------------------------------
# PERIODO
# ---------------------------------------------------------------------------
class Periodo(ModeloBase):
    nombre = models.CharField(max_length=20, unique=True)  # ej: "2026-1"
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Periodo"
        verbose_name_plural = "Periodos"
        ordering = ["-fecha_inicio"]  # el signo "-" ordena del más nuevo al más antiguo

    def clean(self):
        # clean() valida reglas de negocio. Los formularios lo llaman automáticamente.
        super().clean()
        if self.fecha_inicio and self.fecha_fin and self.fecha_fin <= self.fecha_inicio:
            raise ValidationError(
                {"fecha_fin": "La fecha de fin debe ser posterior a la fecha de inicio."}
            )

    def __str__(self):
        return self.nombre


# ---------------------------------------------------------------------------
# CURSO (la materia)
# ---------------------------------------------------------------------------
class Curso(ModeloBase):
    # En el enunciado no indicaste on_delete: usé PROTECT para no perder cursos por accidente
    carrera = models.ForeignKey(
        Carrera, on_delete=models.PROTECT, related_name="cursos"
    )
    semestre = models.ForeignKey(
        Semestre, on_delete=models.PROTECT, related_name="cursos"
    )
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=150)
    creditos = models.PositiveSmallIntegerField(default=1)

    class Meta:
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"
        ordering = ["carrera__nombre", "semestre__numero", "nombre"]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


# ---------------------------------------------------------------------------
# PROFESOR
# ---------------------------------------------------------------------------
class Profesor(ModeloBase):
    cedula = models.CharField(max_length=10, unique=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    email = models.EmailField()
    titulo = models.CharField(max_length=100)  # ej: "Ingeniero en Sistemas"

    class Meta:
        verbose_name = "Profesor"
        verbose_name_plural = "Profesores"
        ordering = ["apellidos", "nombres"]

    def __str__(self):
        return f"{self.apellidos} {self.nombres}"


# ---------------------------------------------------------------------------
# ESTUDIANTE
# ---------------------------------------------------------------------------
class Estudiante(ModeloBase):
    cedula = models.CharField(max_length=10, unique=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    email = models.EmailField()
    telefono = models.CharField(max_length=15, blank=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)  # opcional
    carrera = models.ForeignKey(
        Carrera, on_delete=models.PROTECT, related_name="estudiantes"
    )
    foto = models.ImageField(upload_to="estudiantes/", blank=True, null=True)

    class Meta:
        verbose_name = "Estudiante"
        verbose_name_plural = "Estudiantes"
        ordering = ["apellidos", "nombres"]

    @property
    def nombre_completo(self):
        # Propiedad: se usa como atributo, sin paréntesis (estudiante.nombre_completo)
        return f"{self.apellidos} {self.nombres}"

    def __str__(self):
        return f"{self.nombre_completo} ({self.cedula})"


# ---------------------------------------------------------------------------
# SECCION (la oferta de un curso en un periodo)
# ---------------------------------------------------------------------------
class Seccion(ModeloBase):
    curso = models.ForeignKey(
        Curso, on_delete=models.PROTECT, related_name="secciones"
    )
    periodo = models.ForeignKey(
        Periodo, on_delete=models.PROTECT, related_name="secciones"
    )
    profesor = models.ForeignKey(
        Profesor, on_delete=models.PROTECT, related_name="secciones"
    )
    paralelo = models.CharField(max_length=5, default="A")
    jornada = models.CharField(
        max_length=10, choices=Jornada.choices, default=Jornada.DIURNA
    )
    cupo = models.PositiveSmallIntegerField(default=30)

    # Relación muchos a muchos con Estudiante, pasando por la tabla Matricula.
    # "through" nos permite guardar datos extra (como la fecha) en la matrícula.
    estudiantes = models.ManyToManyField(
        Estudiante,
        through="Matricula",
        related_name="secciones",
    )

    class Meta:
        verbose_name = "Sección"
        verbose_name_plural = "Secciones"
        ordering = ["-periodo__fecha_inicio", "curso__nombre", "paralelo"]
        constraints = [
            # No puede haber dos secciones iguales del mismo curso,
            # periodo, paralelo y jornada
            models.UniqueConstraint(
                fields=["curso", "periodo", "paralelo", "jornada"],
                name="seccion_unica_curso_periodo_paralelo_jornada",
            )
        ]

    @property
    def inscritos(self):
        # Cantidad de estudiantes matriculados en esta sección
        return self.matriculas.count()

    def __str__(self):
        return (
            f"{self.curso.codigo} - Paralelo {self.paralelo} "
            f"({self.get_jornada_display()}) - {self.periodo.nombre}"
        )


# ---------------------------------------------------------------------------
# MATRICULA (une Estudiante con Seccion)
# ---------------------------------------------------------------------------
class Matricula(ModeloBase):
    estudiante = models.ForeignKey(
        Estudiante, on_delete=models.PROTECT, related_name="matriculas"
    )
    seccion = models.ForeignKey(
        Seccion, on_delete=models.PROTECT, related_name="matriculas"
    )
    # default=timezone.localdate (sin paréntesis): Django lo ejecuta al crear, así toma "hoy"
    fecha = models.DateField(default=timezone.localdate)

    class Meta:
        verbose_name = "Matrícula"
        verbose_name_plural = "Matrículas"
        ordering = ["-fecha", "estudiante__apellidos"]
        constraints = [
            # Un estudiante no se puede matricular dos veces en la misma sección
            models.UniqueConstraint(
                fields=["estudiante", "seccion"],
                name="matricula_unica_estudiante_seccion",
            )
        ]

    def clean(self):
        super().clean()
        # Solo validamos si ya se eligieron el estudiante y la sección
        if self.estudiante_id and self.seccion_id:
            # Regla 1: el curso debe ser de la carrera del estudiante
            if self.seccion.curso.carrera_id != self.estudiante.carrera_id:
                raise ValidationError(
                    "El curso de esta sección no pertenece a la carrera del estudiante."
                )

            # Regla 2: la sección debe tener cupo disponible.
            # exclude(pk=self.pk) evita contar esta misma matrícula al editarla.
            ocupados = self.seccion.matriculas.exclude(pk=self.pk).count()
            if ocupados >= self.seccion.cupo:
                raise ValidationError("La sección ya no tiene cupo disponible.")

    def __str__(self):
        return f"{self.estudiante.nombre_completo} → {self.seccion}"


# ---------------------------------------------------------------------------
# NOTA
# ---------------------------------------------------------------------------
class Nota(ModeloBase):
    # OneToOne: cada matrícula tiene UNA sola nota.
    # CASCADE: si se borra la matrícula, se borra su nota.
    matricula = models.OneToOneField(
        Matricula, on_delete=models.CASCADE, related_name="nota"
    )
    n1 = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0"), validators=VALIDADORES_NOTA
    )
    n2 = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0"), validators=VALIDADORES_NOTA
    )
    n3 = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0"), validators=VALIDADORES_NOTA
    )
    # editable=False: el usuario no los escribe, se calculan solos en save()
    promedio = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0"), editable=False
    )
    estado = models.CharField(
        max_length=10,
        choices=EstadoNota.choices,
        default=EstadoNota.REPROBADO,
        editable=False,
    )

    class Meta:
        verbose_name = "Nota"
        verbose_name_plural = "Notas"
        ordering = ["matricula__estudiante__apellidos", "matricula__estudiante__nombres"]

    def save(self, *args, **kwargs):
        # 1) Calculamos el promedio de las 3 notas y lo redondeamos a 2 decimales
        suma = Decimal(self.n1) + Decimal(self.n2) + Decimal(self.n3)
        self.promedio = (suma / Decimal("3")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # 2) Definimos el estado según el promedio
        if self.promedio >= NOTA_MINIMA_APROBACION:
            self.estado = EstadoNota.APROBADO
        else:
            self.estado = EstadoNota.REPROBADO

        # 3) Guardamos normalmente
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.matricula.estudiante.nombre_completo} - {self.promedio} ({self.get_estado_display()})"