import os
from datetime import date, datetime
from io import BytesIO

from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from xhtml2pdf import pisa


def valor_campo(objeto, ruta):
    """
    Lee el valor de un atributo siguiendo una ruta separada por '__'
    (ej. 'carrera__facultad__nombre').
    Si el campo tiene choices, devuelve su texto legible (get_<campo>_display).
    Si en el camino algún objeto es None o no existe, devuelve ''.
    """
    actual = objeto
    for parte in ruta.split("__"):
        if actual is None:
            return ""

        metodo_display = getattr(actual, f"get_{parte}_display", None)
        if callable(metodo_display):
            actual = metodo_display()
        else:
            try:
                actual = getattr(actual, parte)
            except AttributeError:
                return ""

    if actual is None:
        return ""
    if isinstance(actual, datetime):
        return actual.strftime("%d/%m/%Y %H:%M")
    if isinstance(actual, date):
        return actual.strftime("%d/%m/%Y")
    return actual


def exportar_excel(titulo, encabezados, filas, nombre_archivo):
    """
    Genera y devuelve un HttpResponse con un archivo Excel (.xlsx):
    - Fila 1: Título en negrita.
    - Fila 3: Encabezados con fondo verde (#0C4B33) y letra blanca en negrita.
    - Fila 4 en adelante: Datos.
    - Paneles congelados en A4 y ajuste automático de ancho (máx. 50).
    """
    libro = Workbook()
    hoja = libro.active
    hoja.title = "Reporte"

    hoja["A1"] = titulo
    hoja["A1"].font = Font(bold=True, size=14)

    relleno_encabezado = PatternFill(start_color="0C4B33", end_color="0C4B33", fill_type="solid")
    fuente_encabezado = Font(bold=True, color="FFFFFF")

    for col_idx, texto_encabezado in enumerate(encabezados, start=1):
        celda = hoja.cell(row=3, column=col_idx, value=texto_encabezado)
        celda.fill = relleno_encabezado
        celda.font = fuente_encabezado
        celda.alignment = Alignment(horizontal="center", vertical="center")

    for fila_idx, fila_datos in enumerate(filas, start=4):
        for col_idx, valor in enumerate(fila_datos, start=1):
            val_limpio = valor if isinstance(valor, (int, float, bool)) else str(valor)
            hoja.cell(row=fila_idx, column=col_idx, value=val_limpio)

    hoja.freeze_panes = "A4"

    for col_idx, texto_encabezado in enumerate(encabezados, start=1):
        letra_col = get_column_letter(col_idx)
        longitud_max = len(str(texto_encabezado))

        for fila_datos in filas:
            if col_idx - 1 < len(fila_datos):
                largo_celda = len(str(fila_datos[col_idx - 1]))
                if largo_celda > longitud_max:
                    longitud_max = largo_celda

        hoja.column_dimensions[letra_col].width = min(max(longitud_max + 4, 12), 50)

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{nombre_archivo}.xlsx"'
    libro.save(response)
    return response


def link_callback(uri, rel):
    """
    Convierte rutas web (/media/... y /static/...) en rutas físicas del disco
    para que xhtml2pdf pueda incrustar imágenes y recursos locales en el PDF.
    """
    if settings.MEDIA_URL and uri.startswith(settings.MEDIA_URL):
        ruta_relativa = uri.replace(settings.MEDIA_URL, "", 1).lstrip("/")
        ruta_absoluta = os.path.join(settings.MEDIA_ROOT, ruta_relativa)
        if os.path.isfile(ruta_absoluta):
            return ruta_absoluta

    if settings.STATIC_URL and uri.startswith(settings.STATIC_URL):
        ruta_relativa = uri.replace(settings.STATIC_URL, "", 1).lstrip("/")
        if getattr(settings, "STATIC_ROOT", None):
            ruta_absoluta = os.path.join(settings.STATIC_ROOT, ruta_relativa)
            if os.path.isfile(ruta_absoluta):
                return ruta_absoluta
        for static_dir in getattr(settings, "STATICFILES_DIRS", []):
            ruta_absoluta = os.path.join(static_dir, ruta_relativa)
            if os.path.isfile(ruta_absoluta):
                return ruta_absoluta

    return uri


def render_pdf(template, contexto, nombre_archivo, descargar=False):
    """
    Renderiza un template HTML a PDF con xhtml2pdf.
    - descargar=False -> Content-Disposition: inline (se abre en el navegador).
    - descargar=True  -> Content-Disposition: attachment (descarga directa).
    """
    html = render_to_string(template, contexto)
    buffer = BytesIO()

    pdf = pisa.CreatePDF(
        src=BytesIO(html.encode("UTF-8")),
        dest=buffer,
        encoding="UTF-8",
        link_callback=link_callback,
    )

    if pdf.err:
        return HttpResponse(f"Error al generar el PDF: {pdf.err}", status=500)

    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    disposicion = "attachment" if descargar else "inline"
    response["Content-Disposition"] = f'{disposicion}; filename="{nombre_archivo}.pdf"'
    return response