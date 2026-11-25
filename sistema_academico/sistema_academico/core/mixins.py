from datetime import date, datetime
from django.utils import timezone
from .utils import exportar_excel, render_pdf, valor_campo


class UsuarioRegistroMixin:
    """Mixin reutilizable que asigna al usuario autenticado antes de guardar un registro."""

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class FiltroCamposMixin:
    """
    Mixin reutilizable para vistas ListView que agrega:
    - Formulario de filtros por GET.
    - Selección dinámica y segura de columnas a mostrar.
    - Cadena de consulta limpia (sin 'page' ni 'exportar') para paginación y exportación.
    """

    filtro_form_class = None
    campos_disponibles = []  # Lista de tuplas: [("ruta", "Título"), ...]
    campos_por_defecto = []  # Lista de rutas: ["ruta1", "ruta2", ...]

    def filtrar(self, queryset, datos):
        """Cada vista sobrescribe este método para aplicar sus filtros con datos (cleaned_data)."""
        return queryset

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filtro_form = None

        if self.filtro_form_class:
            self.filtro_form = self.filtro_form_class(self.request.GET or None)
            if self.filtro_form.is_valid():
                queryset = self.filtrar(queryset, self.filtro_form.cleaned_data)

        return queryset

    def get_campos_seleccionados(self):
        """
        Lee ?campos=... de la URL, filtra dejando SOLO las rutas permitidas en
        campos_disponibles (seguridad) y si no hay ninguna usa campos_por_defecto.
        """
        permitidos = {ruta for ruta, _ in self.campos_disponibles}
        elegidos = [
            c for c in self.request.GET.getlist("campos") if c in permitidos
        ]
        if elegidos:
            return elegidos
        if self.campos_por_defecto:
            return list(self.campos_por_defecto)
        return [ruta for ruta, _ in self.campos_disponibles]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        etiquetas = dict(self.campos_disponibles)
        seleccionados = self.get_campos_seleccionados()

        encabezados = [etiquetas[ruta] for ruta in seleccionados]

        objetos = context.get(self.context_object_name) or context.get("object_list") or []
        filas = [
            (obj, [valor_campo(obj, ruta) for ruta in seleccionados])
            for obj in objetos
        ]

        params = self.request.GET.copy()
        params.pop("page", None)
        params.pop("exportar", None)

        context["filtro_form"] = getattr(self, "filtro_form", None)
        context["campos_disponibles"] = self.campos_disponibles
        context["campos_seleccionados"] = seleccionados
        context["encabezados"] = encabezados
        context["filas"] = filas
        context["consulta"] = params.urlencode()
        return context


class ExportarMixin(FiltroCamposMixin):
    """
    Extiende FiltroCamposMixin para exportar el listado filtrado completo (sin paginar)
    a Excel o PDF, respetando exactamente las columnas elegidas por el usuario.
    """

    titulo_reporte = "Reporte"
    nombre_archivo = "reporte"
    template_pdf = "core/pdf/listado.html"

    def filtros_aplicados(self):
        """
        Devuelve una lista legible como ['Carrera: Ingeniería de Software', ...]
        usando las etiquetas (labels) de los campos activos en self.filtro_form.
        """
        resultado = []
        form = getattr(self, "filtro_form", None)
        if not form or not form.is_valid():
            return resultado

        for nombre, valor in form.cleaned_data.items():
            if valor in (None, "", [], ()):
                continue

            campo = form.fields.get(nombre)
            etiqueta = campo.label if (campo and campo.label) else nombre.replace("_", " ").capitalize()

            if hasattr(campo, "choices") and not hasattr(campo, "queryset"):
                opciones = dict(campo.choices)
                valor_texto = opciones.get(valor, valor)
            elif isinstance(valor, datetime):
                valor_texto = valor.strftime("%d/%m/%Y %H:%M")
            elif isinstance(valor, date):
                valor_texto = valor.strftime("%d/%m/%Y")
            else:
                valor_texto = str(valor)

            resultado.append(f"{etiqueta}: {valor_texto}")

        return resultado

    def _datos_exportacion(self):
        """Prepara queryset completo (sin paginar), encabezados y filas con valor_campo."""
        queryset = self.get_queryset()
        etiquetas = dict(self.campos_disponibles)
        seleccionados = self.get_campos_seleccionados()

        encabezados = [etiquetas[ruta] for ruta in seleccionados]
        filas = [
            [valor_campo(obj, ruta) for ruta in seleccionados]
            for obj in queryset
        ]
        return encabezados, filas

    def get(self, request, *args, **kwargs):
        formato = request.GET.get("exportar")

        if formato == "excel":
            encabezados, filas = self._datos_exportacion()
            return exportar_excel(
                self.titulo_reporte,
                encabezados,
                filas,
                self.nombre_archivo,
            )

        if formato == "pdf":
            encabezados, filas = self._datos_exportacion()
            usuario = request.user.get_full_name() or request.user.username
            contexto = {
                "titulo": self.titulo_reporte,
                "fecha_generacion": timezone.localtime(),
                "usuario": usuario,
                "total_registros": len(filas),
                "filtros_aplicados": self.filtros_aplicados(),
                "encabezados": encabezados,
                "filas": filas,
            }
            return render_pdf(
                self.template_pdf,
                contexto,
                self.nombre_archivo,
                descargar=False,
            )

        return super().get(request, *args, **kwargs)


class ComprobantePdfMixin:
    """
    Mixin reutilizable para vistas DetailView que renderiza un registro individual
    directamente como PDF usando render_pdf().
    El archivo descargado/mostrado se nombra '<nombre_archivo>-<pk>.pdf'.
    """

    template_pdf = None
    nombre_archivo = "comprobante"
    descargar_pdf = False

    def render_to_response(self, context, **response_kwargs):
        usuario = self.request.user.get_full_name() or self.request.user.username
        context["fecha_generacion"] = timezone.localtime()
        context["usuario"] = usuario

        archivo = f"{self.nombre_archivo}-{self.object.pk}"
        return render_pdf(
            self.template_pdf,
            context,
            archivo,
            descargar=self.descargar_pdf,
        )