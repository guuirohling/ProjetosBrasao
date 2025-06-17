from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import cm

def format_brl(value):
    # Se for string num formato estranho, tenta transformar em float
    if isinstance(value, str):
        try:
            val = float(value.replace("R$", "").replace(".", "").replace(",", "."))
        except Exception:
            return value
    else:
        val = value
    return f"R$ {val:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

def export_to_pdf(df, file_path):
    df = df.copy()
    col_titles = []
    col_widths = []
    for col in df.columns:
        if col == "date":
            col_titles.append("Data")
            col_widths.append(3.5*cm)
        elif col == "amount":
            col_titles.append("Valor")
            col_widths.append(3.2*cm)
        elif col.lower() == "classification":
            col_titles.append("Classificação")
            col_widths.append(6*cm)
        elif col.lower() == "conta":
            col_titles.append("Conta")
            col_widths.append(3.2*cm)
        else:
            col_titles.append(col.capitalize())
            col_widths.append(4*cm)
    row_height = 17
    margin = 2*cm

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4
    x = margin
    y = height - margin

    # Cabeçalho (alinha "Valor" à direita)
    c.setFont("Helvetica-Bold", 10)
    for i, title in enumerate(col_titles):
        if title == "Valor":
            c.drawRightString(x + sum(col_widths[:i+1]) - 6, y, title)
        else:
            c.drawString(x + sum(col_widths[:i]), y, title)
    y -= row_height

    # Dados
    c.setFont("Helvetica", 10)
    for idx, row in df.iterrows():
        if idx % 2 == 0:
            c.setFillColorRGB(0.96,0.96,0.96)
            c.rect(x - 2, y - 4, sum(col_widths)+4, row_height, fill=True, stroke=False)
        c.setFillColor(colors.black)

        for i, col in enumerate(df.columns):
            val = row[col]
            if col == "date" and hasattr(val, "strftime"):
                val = val.strftime("%d/%m/%Y")
            if col == "amount":
                val = format_brl(val)
                c.drawRightString(x + sum(col_widths[:i+1]) - 6, y, val)
            else:
                c.drawString(x + sum(col_widths[:i]), y, str(val))
        y -= row_height
        if y < margin + row_height:
            c.showPage()
            c.setFont("Helvetica", 10)
            y = height - margin

    c.save()
