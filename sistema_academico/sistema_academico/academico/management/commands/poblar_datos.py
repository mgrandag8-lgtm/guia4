from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from academico.models import (
    Carrera,
    Curso,
    Estudiante,
    Facultad,
    Jornada,
    Matricula,
    Nota,
    Periodo,
    Profesor,
    Seccion,
    Semestre,
    Universidad,
)

User = get_user_model()


class Command(BaseCommand):
    help = "Puebla la base de datos con datos académicos de prueba sin duplicarlos."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Iniciando carga de datos de prueba..."))

        # Buscamos un superusuario para asignarlo como creador de los registros (si existe)
        usuario_admin = User.objects.filter(is_superuser=True).first()

        # 1. UNIVERSIDADES (2)
        u1, _ = Universidad.objects.get_or_create(
            nombre="Universidad Estatal de Milagro",
            defaults={"siglas": "UNEMI", "ciudad": "Milagro", "user": usuario_admin},
        )
        u2, _ = Universidad.objects.get_or_create(
            nombre="Universidad de Guayaquil",
            defaults={"siglas": "UG", "ciudad": "Guayaquil", "user": usuario_admin},
        )

        # 2. FACULTADES (3)
        f1, _ = Facultad.objects.get_or_create(
            universidad=u1,
            nombre="Facultad de Ciencias e Ingeniería",
            defaults={"decano": "Ing. Roberto Mendoza, MSc.", "user": usuario_admin},
        )
        f2, _ = Facultad.objects.get_or_create(
            universidad=u1,
            nombre="Facultad de Ciencias Sociales, Educación Comercial y Derecho",
            defaults={"decano": "Econ. Gabriela Torres, PhD.", "user": usuario_admin},
        )
        f3, _ = Facultad.objects.get_or_create(
            universidad=u2,
            nombre="Facultad de Ciencias Matemáticas y Físicas",
            defaults={"decano": "Ing. Carlos Zambrano, MSc.", "user": usuario_admin},
        )

        # 3. CARRERAS (3)
        c_soft, _ = Carrera.objects.get_or_create(
            codigo="SOFT-01",
            defaults={
                "facultad": f1,
                "nombre": "Ingeniería de Software",
                "duracion_semestres": 8,
                "user": usuario_admin,
            },
        )
        c_adm, _ = Carrera.objects.get_or_create(
            codigo="ADM-02",
            defaults={
                "facultad": f2,
                "nombre": "Administración de Empresas",
                "duracion_semestres": 8,
                "user": usuario_admin,
            },
        )
        c_sis, _ = Carrera.objects.get_or_create(
            codigo="SIS-03",
            defaults={
                "facultad": f3,
                "nombre": "Ingeniería en Sistemas Computacionales",
                "duracion_semestres": 9,
                "user": usuario_admin,
            },
        )

        # 4. SEMESTRES (2)
        sem1, _ = Semestre.objects.get_or_create(
            numero=1,
            defaults={"nombre": "Primero", "user": usuario_admin},
        )
        sem2, _ = Semestre.objects.get_or_create(
            numero=2,
            defaults={"nombre": "Segundo", "user": usuario_admin},
        )

        # 5. PERÍODO ACTIVO (1)
        periodo, _ = Periodo.objects.get_or_create(
            nombre="2026-2",
            defaults={
                "fecha_inicio": date(2026, 10, 1),
                "fecha_fin": date(2027, 2, 28),
                "activo": True,
                "user": usuario_admin,
            },
        )

        # 6. CURSOS (6: 2 por cada carrera)
        cursos_data = [
            ("SW-101", "Fundamentos de Programación", c_soft, sem1, 4),
            ("SW-201", "Desarrollo Web con Django", c_soft, sem2, 4),
            ("AD-101", "Contabilidad General", c_adm, sem1, 3),
            ("AD-201", "Gestión del Talento Humano", c_adm, sem2, 3),
            ("SI-101", "Arquitectura de Computadores", c_sis, sem1, 4),
            ("SI-201", "Bases de Datos Relacionales", c_sis, sem2, 4),
        ]
        cursos = {}
        for codigo, nombre, carrera, semestre, creditos in cursos_data:
            curso, _ = Curso.objects.get_or_create(
                codigo=codigo,
                defaults={
                    "nombre": nombre,
                    "carrera": carrera,
                    "semestre": semestre,
                    "creditos": creditos,
                    "user": usuario_admin,
                },
            )
            cursos[codigo] = curso

        # 7. PROFESORES (3)
        profesores_data = [
            ("0911111111", "Andrés", "Salazar", "asalazar@institucion.edu.ec", "Magíster en Ingeniería de Software"),
            ("0922222222", "Valeria", "Cedeño", "vcedeno@institucion.edu.ec", "Doctora en Administración"),
            ("0933333333", "Fernando", "Paredes", "fparedes@institucion.edu.ec", "Magíster en Ciencias de la Computación"),
        ]
        profesores = []
        for cedula, nombres, apellidos, email, titulo in profesores_data:
            prof, _ = Profesor.objects.get_or_create(
                cedula=cedula,
                defaults={
                    "nombres": nombres,
                    "apellidos": apellidos,
                    "email": email,
                    "titulo": titulo,
                    "user": usuario_admin,
                },
            )
            profesores.append(prof)

        # 8. SECCIONES (4: diurnas y nocturnas)
        sec1, _ = Seccion.objects.get_or_create(
            curso=cursos["SW-101"],
            periodo=periodo,
            paralelo="A",
            jornada=Jornada.DIURNA,
            defaults={"profesor": profesores[0], "cupo": 30, "user": usuario_admin},
        )
        sec2, _ = Seccion.objects.get_or_create(
            curso=cursos["SW-201"],
            periodo=periodo,
            paralelo="B",
            jornada=Jornada.NOCTURNA,
            defaults={"profesor": profesores[0], "cupo": 30, "user": usuario_admin},
        )
        sec3, _ = Seccion.objects.get_or_create(
            curso=cursos["AD-101"],
            periodo=periodo,
            paralelo="A",
            jornada=Jornada.DIURNA,
            defaults={"profesor": profesores[1], "cupo": 30, "user": usuario_admin},
        )
        sec4, _ = Seccion.objects.get_or_create(
            curso=cursos["SI-201"],
            periodo=periodo,
            paralelo="A",
            jornada=Jornada.NOCTURNA,
            defaults={"profesor": profesores[2], "cupo": 30, "user": usuario_admin},
        )

        # 9. ESTUDIANTES (15: 6 en Software, 5 en Administración, 4 en Sistemas)
        estudiantes_data = [
            # Carrera: Ingeniería de Software (índices 0 al 5)
            ("0950000001", "Camila", "Vera", "cvera@estudiantes.edu.ec", "0991000001", c_soft),
            ("0950000002", "Mateo", "Morán", "mmoran@estudiantes.edu.ec", "0991000002", c_soft),
            ("0950000003", "Sofía", "Alvarado", "salvarado@estudiantes.edu.ec", "0991000003", c_soft),
            ("0950000004", "Diego", "Castro", "dcastro@estudiantes.edu.ec", "0991000004", c_soft),
            ("0950000005", "Lucía", "Reyes", "lreyes@estudiantes.edu.ec", "0991000005", c_soft),
            ("0950000006", "Sebastián", "Ortiz", "sortiz@estudiantes.edu.ec", "0991000006", c_soft),
            # Carrera: Administración de Empresas (índices 6 al 10)
            ("0950000007", "Daniela", "Vargas", "dvargas@estudiantes.edu.ec", "0991000007", c_adm),
            ("0950000008", "Javier", "Peña", "jpena@estudiantes.edu.ec", "0991000008", c_adm),
            ("0950000009", "Paula", "Molina", "pmolina@estudiantes.edu.ec", "0991000009", c_adm),
            ("0950000010", "Kevin", "Silva", "ksilva@estudiantes.edu.ec", "0991000010", c_adm),
            ("0950000011", "Natalia", "Ríos", "nrios@estudiantes.edu.ec", "0991000011", c_adm),
            # Carrera: Ingeniería en Sistemas (índices 11 al 14)
            ("0950000012", "Andrés", "Lozano", "alozano@estudiantes.edu.ec", "0991000012", c_sis),
            ("0950000013", "Elena", "Bravo", "ebravo@estudiantes.edu.ec", "0991000013", c_sis),
            ("0950000014", "Martín", "Guerrero", "mguerrero@estudiantes.edu.ec", "0991000014", c_sis),
            ("0950000015", "Carolina", "Suárez", "csuarez@estudiantes.edu.ec", "0991000015", c_sis),
        ]
        estudiantes = []
        for cedula, nombres, apellidos, email, telefono, carrera in estudiantes_data:
            est, _ = Estudiante.objects.get_or_create(
                cedula=cedula,
                defaults={
                    "nombres": nombres,
                    "apellidos": apellidos,
                    "email": email,
                    "telefono": telefono,
                    "carrera": carrera,
                    "user": usuario_admin,
                },
            )
            estudiantes.append(est)

        # 10. MATRÍCULAS (25) Y NOTAS VARIADAS (respetando carrera del estudiante = carrera del curso)
        # Lista de tuplas: (indice_estudiante, seccion, n1, n2, n3)
        matriculas_notas_data = [
            # 6 matrículas en sec1 (SW-101 Diurna) -> Estudiantes de Software (0..5)
            (0, sec1, "85.00", "90.00", "88.00"),  # Aprobado
            (1, sec1, "70.00", "72.00", "68.00"),  # Aprobado (70.00 exacto)
            (2, sec1, "55.00", "60.00", "58.00"),  # Reprobado
            (3, sec1, "92.00", "95.00", "94.00"),  # Aprobado
            (4, sec1, "64.00", "65.00", "66.00"),  # Reprobado
            (5, sec1, "78.00", "80.00", "82.00"),  # Aprobado
            # 6 matrículas en sec2 (SW-201 Nocturna) -> Mismos estudiantes de Software (0..5)
            (0, sec2, "88.00", "84.00", "90.00"),  # Aprobado
            (1, sec2, "60.00", "62.00", "65.00"),  # Reprobado
            (2, sec2, "75.00", "70.00", "74.00"),  # Aprobado
            (3, sec2, "96.00", "91.00", "93.00"),  # Aprobado
            (4, sec2, "71.00", "73.00", "72.00"),  # Aprobado
            (5, sec2, "45.00", "50.00", "55.00"),  # Reprobado
            # 5 matrículas en sec3 (AD-101 Diurna) -> Estudiantes de Administración (6..10)
            (6, sec3, "82.00", "85.00", "80.00"),   # Aprobado
            (7, sec3, "68.00", "69.00", "67.00"),   # Reprobado
            (8, sec3, "90.00", "88.00", "92.00"),   # Aprobado
            (9, sec3, "74.00", "76.00", "75.00"),   # Aprobado
            (10, sec3, "50.00", "58.00", "62.00"),  # Reprobado
            # 4 matrículas en sec4 (SI-201 Nocturna) -> Estudiantes de Sistemas (11..14)
            (11, sec4, "81.00", "79.00", "85.00"),  # Aprobado
            (12, sec4, "65.00", "68.00", "64.00"),  # Reprobado
            (13, sec4, "89.00", "92.00", "90.00"),  # Aprobado
            (14, sec4, "73.00", "71.00", "75.00"),  # Aprobado
            # 4 matrículas adicionales en sec1/sec2 con otro paralelo para completar las 25
            # Creamos una sección extra paralela de SW-201 Diurna para 4 estudiantes de Software
        ]

        sec5, _ = Seccion.objects.get_or_create(
            curso=cursos["SW-201"],
            periodo=periodo,
            paralelo="A",
            jornada=Jornada.DIURNA,
            defaults={"profesor": profesores[2], "cupo": 30, "user": usuario_admin},
        )
        matriculas_notas_data.extend([
            (0, sec5, "91.00", "89.00", "93.00"),  # Aprobado (Matrícula 22)
            (1, sec5, "72.00", "74.00", "70.00"),  # Aprobado (Matrícula 23)
            (2, sec5, "59.00", "61.00", "60.00"),  # Reprobado (Matrícula 24)
            (3, sec5, "84.00", "86.00", "85.00"),  # Aprobado (Matrícula 25)
        ])

        creadas = 0
        for idx_est, seccion, n1, n2, n3 in matriculas_notas_data:
            estudiante = estudiantes[idx_est]
            matricula, created = Matricula.objects.get_or_create(
                estudiante=estudiante,
                seccion=seccion,
                defaults={"user": usuario_admin},
            )
            if created:
                creadas += 1

            Nota.objects.get_or_create(
                matricula=matricula,
                defaults={
                    "n1": Decimal(n1),
                    "n2": Decimal(n2),
                    "n3": Decimal(n3),
                    "user": usuario_admin,
                },
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"¡Carga completada! Se registraron {creadas} matrículas nuevas "
                f"(Total en BD: {Matricula.objects.count()} matrículas y {Nota.objects.count()} notas)."
            )
        )