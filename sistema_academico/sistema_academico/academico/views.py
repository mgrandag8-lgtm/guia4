from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import ProtectedError, Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)
from django.db import transaction
from .forms import (
    EstudianteForm,
    FiltroEstudianteForm,
    FiltroMatriculaForm,
    MatriculaForm,
    NotaFormSet,
)
from core.mixins import ComprobantePdfMixin, ExportarMixin, UsuarioRegistroMixin
from .forms import EstudianteForm, FiltroEstudianteForm
from .models import Estudiante, Matricula, Nota, Periodo, Seccion

# ==========================================
# VISTA PRINCIPAL (DASHBOARD)
# ==========================================

class InicioView(LoginRequiredMixin, TemplateView):
    template_name = "academico/inicio.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Buscamos el periodo que esté marcado como activo=True
        periodo_activo = Periodo.objects.filter(activo=True).first()
        total_notas = Nota.objects.count()
        aprobadas = Nota.objects.filter(estado="aprobado").count()

        context["periodo_activo"] = periodo_activo
        context["total_estudiantes"] = Estudiante.objects.count()
        context["total_secciones"] = (
            Seccion.objects.filter(periodo=periodo_activo).count() if periodo_activo else 0
        )
        context["total_matriculas"] = Matricula.objects.count()
        context["porcentaje_aprobados"] = (
            round((aprobadas / total_notas) * 100, 1) if total_notas > 0 else 0
        )
        return context


# ==========================================
# VISTAS CRUD: ESTUDIANTE
# ==========================================

class EstudianteListView(LoginRequiredMixin, ExportarMixin, ListView):
    model = Estudiante
    template_name = "academico/estudiante_lista.html"
    context_object_name = "estudiantes"
    paginate_by = 10

    # Configuración de reporte Excel
    titulo_reporte = "Listado de estudiantes"
    nombre_archivo = "estudiantes"

    # Configuración del componente reutilizable de filtros y columnas
    filtro_form_class = FiltroEstudianteForm
    campos_disponibles = [
        ("cedula", "Cédula"),
        ("apellidos", "Apellidos"),
        ("nombres", "Nombres"),
        ("email", "Correo"),
        ("telefono", "Teléfono"),
        ("fecha_nacimiento", "Nacimiento"),
        ("carrera__nombre", "Carrera"),
        ("carrera__facultad__nombre", "Facultad"),
    ]
    campos_por_defecto = [
        "cedula",
        "apellidos",
        "nombres",
        "email",
        "carrera__nombre",
    ]

    def get_queryset(self):
        # FiltroCamposMixin llama a super().get_queryset(), así que aquí preparamos la consulta base con JOINs
        return Estudiante.objects.select_related("carrera__facultad").all()

    def filtrar(self, queryset, datos):
        texto = datos.get("texto")
        carrera = datos.get("carrera")
        facultad = datos.get("facultad")
        nacido_desde = datos.get("nacido_desde")
        nacido_hasta = datos.get("nacido_hasta")

        # Búsqueda combinada con Q (OR) en nombres, apellidos o cédula
        if texto:
            queryset = queryset.filter(
                Q(nombres__icontains=texto)
                | Q(apellidos__icontains=texto)
                | Q(cedula__icontains=texto)
            )
        if carrera:
            queryset = queryset.filter(carrera=carrera)
        if facultad:
            queryset = queryset.filter(carrera__facultad=facultad)
        if nacido_desde:
            queryset = queryset.filter(fecha_nacimiento__gte=nacido_desde)
        if nacido_hasta:
            queryset = queryset.filter(fecha_nacimiento__lte=nacido_hasta)

        return queryset

class EstudianteCreateView(LoginRequiredMixin, UsuarioRegistroMixin, SuccessMessageMixin, CreateView):
    model = Estudiante
    form_class = EstudianteForm
    template_name = "academico/estudiante_form.html"
    success_url = reverse_lazy("academico:estudiante_lista")
    success_message = "Estudiante registrado correctamente."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Registrar Nuevo Estudiante"
        context["boton_texto"] = "Guardar Estudiante"
        return context


class EstudianteUpdateView(LoginRequiredMixin, UsuarioRegistroMixin, SuccessMessageMixin, UpdateView):
    model = Estudiante
    form_class = EstudianteForm
    template_name = "academico/estudiante_form.html"
    success_url = reverse_lazy("academico:estudiante_lista")
    success_message = "Datos del estudiante actualizados correctamente."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = f"Editar Estudiante: {self.object.nombre_completo}"
        context["boton_texto"] = "Actualizar Cambios"
        return context


class EstudianteDetailView(LoginRequiredMixin, DetailView):
    model = Estudiante
    template_name = "academico/estudiante_detalle.html"
    context_object_name = "estudiante"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Traemos todas las matrículas del estudiante junto con su curso, periodo, profesor y nota
        context["matriculas"] = (
            self.object.matriculas.select_related(
                "seccion__curso", "seccion__periodo", "seccion__profesor", "nota"
            )
            .order_by("-seccion__periodo__nombre", "seccion__curso__nombre")
        )
        return context

class EstudiantePdfView(LoginRequiredMixin, ComprobantePdfMixin, DetailView):
    model = Estudiante
    context_object_name = "estudiante"
    template_pdf = "academico/pdf/estudiante_ficha.html"
    nombre_archivo = "ficha_estudiante"

    def get_queryset(self):
        # Cargamos carrera, facultad y universidad en una sola consulta SQL
        return Estudiante.objects.select_related("carrera__facultad__universidad")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Traemos las matrículas con su sección, periodo, curso y nota sin repetir consultas
        context["matriculas"] = (
            self.object.matriculas.select_related(
                "seccion__curso",
                "seccion__periodo",
                "nota",
            )
            .order_by("-seccion__periodo__nombre", "seccion__curso__nombre")
        )
        return context

class EstudianteDeleteView(LoginRequiredMixin, DeleteView):
    model = Estudiante
    template_name = "academico/estudiante_eliminar.html"
    context_object_name = "estudiante"
    success_url = reverse_lazy("academico:estudiante_lista")

    # Sobrescribimos form_valid para atrapar ProtectedError si tiene matrículas
    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Estudiante eliminado correctamente.")
            return response
        except ProtectedError:
            messages.error(self.request, "No se puede eliminar: tiene matrículas.")
            return redirect("academico:estudiante_lista")

# ==========================================
# VISTAS CRUD: MATRÍCULA Y NOTA (MAESTRO-DETALLE)
# ==========================================

class MatriculaNotaMixin:
    """
    Mixin maestro-detalle que gestiona MatriculaForm junto con NotaFormSet
    en la misma petición, validando y guardando ambos atómicamente.
    """

    model = Matricula
    form_class = MatriculaForm
    template_name = "academico/matricula_form.html"
    success_url = reverse_lazy("academico:matricula_lista")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "nota_formset" not in context:
            if self.request.POST:
                context["nota_formset"] = NotaFormSet(self.request.POST, instance=self.object)
            else:
                context["nota_formset"] = NotaFormSet(instance=self.object)
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        nota_formset = NotaFormSet(request.POST, instance=self.object)

        if form.is_valid() and nota_formset.is_valid():
            return self.form_valid(form, nota_formset)
        return self.form_invalid(form, nota_formset)

    def form_valid(self, form, nota_formset):
        with transaction.atomic():
            form.instance.user = self.request.user
            self.object = form.save()

            nota_formset.instance = self.object
            notas = nota_formset.save(commit=False)
            for nota in notas:
                nota.user = self.request.user
                nota.save()

        messages.success(self.request, self.success_message)
        return redirect(self.get_success_url())

    def form_invalid(self, form, nota_formset):
        return self.render_to_response(
            self.get_context_data(form=form, nota_formset=nota_formset)
        )


# Reemplaza MatriculaListView por esta versión:
class MatriculaListView(LoginRequiredMixin, ExportarMixin, ListView):
    model = Matricula
    template_name = "academico/matricula_lista.html"
    context_object_name = "matriculas"
    paginate_by = 10

    titulo_reporte = "Reporte de matrículas y notas"
    nombre_archivo = "matriculas"

    filtro_form_class = FiltroMatriculaForm
    campos_disponibles = [
        ("estudiante__cedula", "Cédula"),
        ("estudiante", "Estudiante"),
        ("seccion__curso__nombre", "Curso"),
        ("seccion__paralelo", "Paralelo"),
        ("seccion__jornada", "Jornada"),
        ("seccion__periodo__nombre", "Periodo"),
        ("seccion__profesor", "Profesor"),
        ("nota__n1", "N1"),
        ("nota__n2", "N2"),
        ("nota__n3", "N3"),
        ("nota__promedio", "Promedio"),
        ("nota__estado", "Estado"),
        ("fecha", "Fecha"),
    ]
    campos_por_defecto = [
        "estudiante__cedula",
        "estudiante",
        "seccion__curso__nombre",
        "seccion__jornada",
        "nota__promedio",
        "nota__estado",
    ]

    def get_queryset(self):
        return (
            Matricula.objects.select_related(
                "estudiante__carrera",
                "seccion__curso__carrera",
                "seccion__periodo",
                "seccion__profesor",
                "nota",
            )
            .order_by("-fecha", "estudiante__apellidos")
        )

    def filtrar(self, queryset, datos):
        texto = datos.get("texto")
        periodo = datos.get("periodo")
        carrera = datos.get("carrera")
        curso = datos.get("curso")
        jornada = datos.get("jornada")
        estado = datos.get("estado")
        promedio_desde = datos.get("promedio_desde")
        promedio_hasta = datos.get("promedio_hasta")

        if texto:
            queryset = queryset.filter(
                Q(estudiante__cedula__icontains=texto)
                | Q(estudiante__apellidos__icontains=texto)
            )
        if periodo:
            queryset = queryset.filter(seccion__periodo=periodo)
        if carrera:
            queryset = queryset.filter(seccion__curso__carrera=carrera)
        if curso:
            queryset = queryset.filter(seccion__curso=curso)
        if jornada:
            queryset = queryset.filter(seccion__jornada=jornada)
        if estado:
            queryset = queryset.filter(nota__estado=estado)
        if promedio_desde is not None:
            queryset = queryset.filter(nota__promedio__gte=promedio_desde)
        if promedio_hasta is not None:
            queryset = queryset.filter(nota__promedio__lte=promedio_hasta)

        return queryset


# Agrega esta vista debajo de MatriculaDetailView:
class MatriculaPdfView(LoginRequiredMixin, ComprobantePdfMixin, DetailView):
    model = Matricula
    context_object_name = "matricula"
    template_pdf = "academico/pdf/matricula_comprobante.html"
    nombre_archivo = "matricula"

    def get_queryset(self):
        return Matricula.objects.select_related(
            "estudiante__carrera__facultad__universidad",
            "seccion__curso",
            "seccion__periodo",
            "seccion__profesor",
            "nota",
        )


class MatriculaCreateView(LoginRequiredMixin, MatriculaNotaMixin, CreateView):
    success_message = "Matrícula y notas registradas correctamente."

    def post(self, request, *args, **kwargs):
        self.object = None
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = "Registrar Nueva Matrícula"
        context["boton_texto"] = "Guardar Matrícula y Notas"
        return context


class MatriculaUpdateView(LoginRequiredMixin, MatriculaNotaMixin, UpdateView):
    success_message = "Matrícula y notas actualizadas correctamente."

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = f"Editar Matrícula: {self.object.estudiante}"
        context["boton_texto"] = "Actualizar Matrícula y Notas"
        return context


class MatriculaDetailView(LoginRequiredMixin, DetailView):
    model = Matricula
    template_name = "academico/matricula_detalle.html"
    context_object_name = "matricula"

    def get_queryset(self):
        return Matricula.objects.select_related(
            "estudiante__carrera__facultad",
            "seccion__curso",
            "seccion__periodo",
            "seccion__profesor",
            "nota",
        )


class MatriculaDeleteView(LoginRequiredMixin, DeleteView):
    model = Matricula
    template_name = "academico/matricula_eliminar.html"
    context_object_name = "matricula"
    success_url = reverse_lazy("academico:matricula_lista")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Matrícula eliminada correctamente.")
        return response