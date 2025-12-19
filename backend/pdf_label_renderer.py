# backend/pdf_label_renderer.py
# ======================================================
# PDF Label Renderer (Layout-Agnostic)
#
# - Reuses canonical QR label image (PNG)
# - PDF is only a transport container
# - No label design logic here
# ======================================================

import os
from PySide6.QtGui import QPdfWriter, QPainter, QPixmap, QPageSize, QPageLayout
from PySide6.QtCore import QSizeF, QMarginsF


def render_label_pdf(
    output_path: str,
    label_image_path: str,
    label_size_mm=(50.8, 25.4),
    dpi=203,
):
    """
    Render an existing label image into a PDF.

    :param output_path: PDF file path
    :param label_image_path: Absolute path to label PNG
    :param label_size_mm: Physical label size (mm)
    :param dpi: Printer DPI
    """

    if not os.path.exists(label_image_path):
        raise FileNotFoundError(f"Label image not found: {label_image_path}")

    pdf = QPdfWriter(output_path)
    pdf.setResolution(dpi)

    page_size = QPageSize(
        QSizeF(label_size_mm[0], label_size_mm[1]),
        QPageSize.Millimeter
    )

    layout = QPageLayout(
        page_size,
        QPageLayout.Portrait,
        QMarginsF(0, 0, 0, 0),
    )
    pdf.setPageLayout(layout)

    painter = QPainter(pdf)

    pixmap = QPixmap(label_image_path)
    if pixmap.isNull():
        painter.end()
        raise RuntimeError("Failed to load label image")

    page_rect = painter.viewport()
    painter.drawPixmap(page_rect, pixmap)

    painter.end()
