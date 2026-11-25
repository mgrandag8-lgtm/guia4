from django.urls import path
from .views import (
    EstudianteCreateView,
    EstudianteDeleteView,
    EstudianteDetailView,
    EstudianteListView,
    EstudiantePdfView,
    EstudianteUpdateView,
    InicioView,
    MatriculaCreateView,
    MatriculaDeleteView,
    MatriculaDetailView,
    MatriculaListView,
    MatriculaPdfView,
    MatriculaUpdateView,
)

app_name = "academico"

urlpatterns = [
    path("", InicioView.as_view(), name="inicio"),
    # Estudiantes
    path("estudiantes/", EstudianteListView.as_view(), name="estudiante_lista"),
    path("estudiantes/nuevo/", EstudianteCreateView.as_view(), name="estudiante_crear"),
    path("estudiantes/<int:pk>/", EstudianteDetailView.as_view(), name="estudiante_detalle"),
    path("estudiantes/<int:pk>/pdf/", EstudiantePdfView.as_view(), name="estudiante_pdf"),
    path("estudiantes/<int:pk>/editar/", EstudianteUpdateView.as_view(), name="estudiante_editar"),
    path("estudiantes/<int:pk>/eliminar/", EstudianteDeleteView.as_view(), name="estudiante_eliminar"),
    # Matrículas
    path("matriculas/", MatriculaListView.as_view(), name="matricula_lista"),
    path("matriculas/nueva/", MatriculaCreateView.as_view(), name="matricula_crear"),
    path("matriculas/<int:pk>/", MatriculaDetailView.as_view(), name="matricula_detalle"),
    path("matriculas/<int:pk>/pdf/", MatriculaPdfView.as_view(), name="matricula_pdf"),
    path("matriculas/<int:pk>/editar/", MatriculaUpdateView.as_view(), name="matricula_editar"),
    path("matriculas/<int:pk>/eliminar/", MatriculaDeleteView.as_view(), name="matricula_eliminar"),
]