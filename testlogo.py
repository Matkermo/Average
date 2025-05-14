from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Image
from reportlab.lib.utils import ImageReader
from io import BytesIO
import requests

logo_url = "https://raw.githubusercontent.com/Matkermo/Average/main/pngegg.png"
response = requests.get(logo_url, timeout=10)
image_data = BytesIO(response.content)
try:
    image_reader = ImageReader(image_data)
    logo = Image(image_reader, width=80, height=45)

    doc = SimpleDocTemplate("LOGO_TEST.pdf", pagesize=letter)
    doc.build([logo])
    print("PDF généré : regarde le fichier LOGO_TEST.pdf")
except Exception as ex:
    print("Erreur lors de la création de l'image : ", ex)