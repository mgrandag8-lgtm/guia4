from django.contrib import admin

from .models import (
    Carrera,
    Curso,
    Estudiante,
    Facultad,
    Matricula,
    Nota,
    Periodo,
    Profesor,
    Seccion,
    Semestre,
    Universidad,
)


class BaseAdmin(admin.ModelAdmin):
    """
    Clase base para el panel administrativo.
    Muestra los campos de auditoría en solo lectura y asigna automáticamente el usuario logueado.
    """

    readonly_fields = ("user", "fecha_creacion", "fecha_modificacion")

    def save_model(self, request, obj, form, change):
        # Si es un registro nuevo (no tiene user asignado aún), guarda quién lo creó
        if not obj.user_id:
            obj.user = request.user
        super().save_model(request, obj, form, change)


# ==============================================================================
# INLINES (EDICIÓN DE MODELOS HIJOS DENTRO DEL PADRE)
# ==============================================================================
class NotaInline(admin.StackedInline):
    """Permite ingresar o editar las notas dentro del formulario de Matrícula."""

    model = Nota
    max_num = 1
    extra = 0
    readonly_fields = ("promedio", "estado", "user", "fecha_creacion", "fecha_modificacion")


# ==============================================================================
# REGISTRO DE LOS 11 MODELOS
# ==============================================================================
@admin.register(Universidad)
class UniversidadAdmin(BaseAdmin):
    list_display = ("siglas", "nombre", "ciudad", "fecha_creacion")
    search_fields = ("nombre", "siglas", "ciudad")
    list_filter = ("ciudad",)


@admin.register(Facultad)
class FacultadAdmin(BaseAdmin):
    list_display = ("nombre", "universidad", "decano")
    search_fields = ("nombre", "decano", "universidad__nombre", "universidad__siglas")
    list_filter = ("universidad",)


@admin.register(Carrera)
class CarreraAdmin(BaseAdmin):
    list_display = ("codigo", "nombre", "facultad", "duracion_semestres")
    search_fields = ("codigo", "nombre", "facultad__nombre")
    list_filter = ("facultad__universidad", "facultad", "duracion_semestres")


@admin.register(Semestre)
class SemestreAdmin(BaseAdmin):
    list_display = ("numero", "nombre")
    search_fields = ("nombre",)


@admin.register(Periodo)
class PeriodoAdmin(BaseAdmin):
    list_display = ("nombre", "fecha_inicio", "fecha_fin", "activo")
    search_fields = ("nombre",)
    list_filter = ("activo",)


@admin.register(Curso)
class CursoAdmin(BaseAdmin):
    list_display = ("codigo", "nombre", "carrera", "semestre", "creditos")
    search_fields = ("codigo", "nombre", "carrera__nombre")
    list_filter = ("carrera", "semestre", "creditos")


@admin.register(Profesor)
class ProfesorAdmin(BaseAdmin):
    list_display = ("cedula", "apellidos", "nombres", "titulo", "email")
    search_fields = ("cedula", "apellidos", "nombres", "email", "titulo")
    list_filter = ("titulo",)


@admin.register(Estudiante)
class EstudianteAdmin(BaseAdmin):
    list_display = ("cedula", "apellidos", "nombres", "carrera", "email", "telefono")
    search_fields = ("cedula", "apellidos", "nombres", "email")
    list_filter = ("carrera",)


@admin.register(Seccion)
class SeccionAdmin(BaseAdmin):
    list_display = ("curso", "periodo", "paralelo", "jornada", "profesor", "inscritos", "cupo")
    search_fields = ("curso__nombre", "curso__codigo", "profesor__apellidos", "paralelo")
    list_filter = ("periodo", "jornada", "curso__carrera")


@admin.register(Matricula)
class MatriculaAdmin(BaseAdmin):
    list_display = ("estudiante", "seccion", "fecha")
    search_fields = (
        "estudiante__cedula",
        "estudiante__apellidos",
        "estudiante__nombres",
        "seccion__curso__nombre",
    )
    list_filter = ("seccion__periodo", "seccion__jornada", "fecha")
    inlines = [NotaInline]

    def save_formset(self, request, form, formset, change):
        """Asigna también el usuario logueado cuando se crea una Nota desde el inline."""
        instances = formset.save(commit=False)
        for obj in instances:
            if hasattr(obj, "user") and not obj.user_id:
                obj.user = request.user
            obj.save()
        formset.save_m2m()


@admin.register(Nota)
class NotaAdmin(BaseAdmin):
    list_display = ("matricula", "n1", "n2", "n3", "promedio", "estado")
    search_fields = (
        "matricula__estudiante__cedula",
        "matricula__estudiante__apellidos",
        "matricula__seccion__curso__nombre",
    )
    list_filter = ("estado", "matricula__seccion__periodo")
    readonly_fields = ("promedio", "estado", "user", "fecha_creacion", "fecha_modificacion")