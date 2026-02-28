from io import BytesIO
from datetime import date
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

app = FastAPI()

# -------------------------
# MODELOS (esto permite POST con JSON)
# -------------------------

class Item(BaseModel):
    code: str
    description: str
    qty: float
    unit_price: float

class Client(BaseModel):
    name: str
    id: str | None = None
    address: str | None = None
    email: str | None = None

class QuoteRequest(BaseModel):
    number: str
    date: str
    iva_rate: float
    client: Client
    items: List[Item]
    terms: List[str] | None = []

# -------------------------
# RUTA PRINCIPAL
# -------------------------

@app.get("/")
def home():
    return {"message": "API de Cotizaciones funcionando correctamente"}

# -------------------------
# PDF (AHORA ES POST)
# -------------------------

@app.post("/cotizacion/pdf")
def generar_pdf(payload: QuoteRequest):

    iva_rate = payload.iva_rate
    items = payload.items

    # Cálculos
    subtotal = 0
    for it in items:
        subtotal_linea = it.qty * it.unit_price
        subtotal += subtotal_linea

    subtotal = round(subtotal, 2)
    iva_total = round(subtotal * iva_rate, 2)
    total = round(subtotal + iva_total, 2)

    # Crear PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"<b>COTIZACIÓN {payload.number}</b>", styles["Title"]))
    elements.append(Paragraph(f"Fecha: {payload.date}", styles["Normal"]))
    elements.append(Paragraph(f"Cliente: {payload.client.name}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    data = [["Código", "Descripción", "Cant.", "P.Unit", "Total Línea"]]

    for it in items:
        total_linea = round(it.qty * it.unit_price * (1 + iva_rate), 2)
        data.append([
            it.code,
            it.description,
            str(it.qty),
            f"${it.unit_price:.2f}",
            f"${total_linea:.2f}",
        ])

    table = Table(data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("ALIGN", (2, 1), (-1, -1), "CENTER"),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"Subtotal: ${subtotal:.2f}", styles["Normal"]))
    elements.append(Paragraph(f"IVA: ${iva_total:.2f}", styles["Normal"]))
    elements.append(Paragraph(f"<b>TOTAL: ${total:.2f}</b>", styles["Normal"]))

    if payload.terms:
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("<b>Condiciones:</b>", styles["Normal"]))
        for t in payload.terms:
            elements.append(Paragraph(f"- {t}", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={payload.number}.pdf"}
    )
