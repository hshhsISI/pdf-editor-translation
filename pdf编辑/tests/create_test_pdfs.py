from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PIL import Image, ImageDraw, ImageFont

# Create text-only PDF a.pdf
c = canvas.Canvas('a.pdf', pagesize=letter)
c.setFont('Helvetica', 14)
c.drawString(100, 700, 'This is PDF A - page 1')
c.showPage()
c.drawString(100, 700, 'This is PDF A - page 2')
c.save()

# Create an image and embed into b.pdf
img = Image.new('RGB', (400, 200), color='lightblue')
d = ImageDraw.Draw(img)
d.text((10, 10), 'Sample Image', fill='black')
img.save('sample.png')

c = canvas.Canvas('b.pdf', pagesize=letter)
c.drawString(100, 700, 'This is PDF B - contains an image')
c.drawImage('sample.png', 100, 400, width=200, height=100)
c.showPage()
c.save()
print('Created a.pdf, b.pdf, sample.png')