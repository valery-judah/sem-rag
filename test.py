from reportlab.pdfgen import canvas

c = canvas.Canvas("data/dummy.pdf")
c.drawString(100, 750, "Welcome to Reportlab!")
c.save()
