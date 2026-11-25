from django import forms
from django.db.models import Count
from django.forms import inlineformset_factory
from .models import (
    Carrera,
    Curso,
    EstadoNota,
    Estudiante,
    Facultad,
    Jornada,
    Matricula,
    Nota,
    Periodo,
    Seccion,
)


class EstudianteForm(forms.ModelForm):
    class Meta:
        model = Estudiante
        fields = [
            "cedula",
            "nombres",
            "apellidos",
            "email",
            "telefono",
            "fecha_nacimiento",
            "carrera",
            "foto",
        ]
        # Personalizamos cómo se dibujan los campos en HTML usando clases de Bootstrap 5
        widgets = {
            "cedula": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ej: 0912345678", "maxlength": "10"}
            ),
            "nombres": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ingrese los nombres"}
            ),
            "apellidos": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ingrese los apellidos"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "correo@ejemplo.com"}
            ),
            "telefono": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ej: 0991234567"}
            ),
            # format="%Y-%m-%d" es obligatorio para que el navegador cargue la fecha al editar
            "fecha_nacimiento": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"class": "form-control", "type": "date"},
            ),
            "carrera": forms.Select(attrs={"class": "form-select"}),
            "foto": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    # Validación personalizada para el campo cedula (Django ejecuta clean_<campo> automáticamente)
    def clean_cedula(self):
        cedula = self.cleaned_data.get("cedula", "").strip()
        # Verificamos que tenga solo números y que su longitud sea exactamente 10
        if not cedula.isdigit() or len(cedula) != 10:
            raise forms.ValidationError("La cédula debe contener exactamente 10 dígitos numéricos.")
        return cedula


class FiltroEstudianteForm(forms.Form):
    texto = forms.CharField(
        label="Buscar (Nombre o Cédula)",
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control form-control-sm", "placeholder": "Nombre, apellido o cédula..."}
        ),
    )
    carrera = forms.ModelChoiceField(
        label="Carrera",
        queryset=Carrera.objects.select_related("facultad").all(),
        required=False,
        empty_label="Todas las carreras",
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
    )
    facultad = forms.ModelChoiceField(
        label="Facultad",
        queryset=Facultad.objects.all(),
        required=False,
        empty_label="Todas las facultades",
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
    )
    nacido_desde = forms.DateField(
        label="Nacido desde",
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control form-control-sm", "type": "date"}),
    )
    nacido_hasta = forms.DateField(
        label="Nacido hasta",
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control form-control-sm", "type": "date"}),
    )

class SeccionChoiceField(forms.ModelChoiceField):
    """Muestra cada sección como: 'SOF-101 A · Nocturna · 2026-1 (12/30)'."""

    def label_from_instance(self, obj):
        inscritos = getattr(obj, "inscritos_count", None)
        if inscritos is None:
            inscritos = obj.matriculas.count()
        jornada = obj.get_jornada_display() if hasattr(obj, "get_jornada_display") else obj.jornada
        return f"{obj.curso.codigo} {obj.paralelo} · {jornada} · {obj.periodo.nombre} ({inscritos}/{obj.cupo})"


class MatriculaForm(forms.ModelForm):
    seccion = SeccionChoiceField(
        queryset=Seccion.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Sección",
    )

    class Meta:
        model = Matricula
        fields = ["estudiante", "seccion", "fecha"]
        widgets = {
            "estudiante": forms.Select(attrs={"class": "form-select"}),
            "fecha": forms.DateInput(attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["estudiante"].queryset = (
            Estudiante.objects.select_related("carrera")
            .order_by("apellidos", "nombres")
        )
        # Solo secciones del periodo activo, anotando el conteo de matriculados para evitar consultas N+1
        qs_secciones = (
            Seccion.objects.filter(periodo__activo=True)
            .select_related("curso", "periodo")
            .annotate(inscritos_count=Count("matriculas"))
            .order_by("curso__codigo", "paralelo")
        )
        # Si estamos editando una matrícula de un periodo anterior, incluimos su sección para no perderla
        if self.instance and self.instance.pk and self.instance.seccion_id:
            qs_secciones = (
                Seccion.objects.filter(pk=self.instance.seccion_id) | qs_secciones
            ).distinct().select_related("curso", "periodo").annotate(inscritos_count=Count("matriculas"))

        self.fields["seccion"].queryset = qs_secciones


NotaFormSet = inlineformset_factory(
    Matricula,
    Nota,
    fields=["n1", "n2", "n3"],
    extra=1,
    max_num=1,
    can_delete=False,
    widgets={
        "n1": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0", "max": "10"}),
        "n2": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0", "max": "10"}),
        "n3": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0", "max": "10"}),
    },
)


class FiltroMatriculaForm(forms.Form):
    texto = forms.CharField(
        required=False,
        label="Cédula o apellido",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Cédula o apellido del estudiante..."}),
    )
    periodo = forms.ModelChoiceField(
        queryset=Periodo.objects.all(),
        required=False,
        label="Periodo",
        empty_label="Todos los periodos",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    carrera = forms.ModelChoiceField(
        queryset=Carrera.objects.select_related("facultad").all(),
        required=False,
        label="Carrera",
        empty_label="Todas las carreras",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    curso = forms.ModelChoiceField(
        queryset=Curso.objects.all(),
        required=False,
        label="Curso",
        empty_label="Todos los cursos",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    jornada = forms.ChoiceField(
        required=False,
        label="Jornada",
        choices=[("", "Todas las jornadas")] + list(Jornada.choices),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    estado = forms.ChoiceField(
        required=False,
        label="Estado",
        choices=[("", "Todos los estados")] + list(EstadoNota.choices),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    promedio_desde = forms.DecimalField(
        required=False,
        label="Promedio desde",
        min_value=0,
        max_value=100,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "Ej. 70.00"}),
    )
    promedio_hasta = forms.DecimalField(
        required=False,
        label="Promedio hasta",
        min_value=0,
        max_value=100,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "Ej. 100.00"}),
    )