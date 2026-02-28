from io import BytesIO
from datetime import date
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

app = FastAPI()

@app.get("/")
def home():
    return {"message": "API de Cotizaciones funcionando correctamente"}

@app.get("/cotizacion/pdf")
def generar_pdf():

    iva_rate = 0.12

    items = [
        {"code": "CUP-001", "description": "Luminaria CÚPULA", "qty": 1, "unit_price": 36.00},
        {"code": "IRM-002", "description": "Luminaria IRON MAN", "qty": 1, "unit_price": 29.75},
    ]

    for it in items:
        subtotal_linea = it["qty"] * it["unit_price"]
        it["iva_amount"] = round(subtotal_linea * iva_rate, 2)
        it["line_total"] = round(subtotal_linea + it["iva_amount"], 2)

    subtotal = round(sum(it["qty"] * it["unit_price"] for it in items), 2)
    iva_total = round(subtotal * iva_rate, 2)
    total = round(subtotal + iva_total, 2)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b>COTIZACIÓN COT-2026-001</b>", styles["Title"]))
    elements.append(Paragraph(f"Fecha: {date.today().strftime('%d/%m/%Y')}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    data = [["Código", "Descripción", "Cant.", "P.Unit", "IVA", "Total"]]

    for it in items:
        data.append([
            it["code"],
            it["description"],
            str(it["qty"]),
            f"${it['unit_price']:.2f}",
            f"${it['iva_amount']:.2f}",
            f"${it['line_total']:.2f}",
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
    elements.append(Paragraph(f"IVA 12%: ${iva_total:.2f}", styles["Normal"]))
    elements.append(Paragraph(f"<b>TOTAL: ${total:.2f}</b>", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=COT-2026-001.pdf"}
    )
