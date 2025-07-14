import streamlit as st
import requests
import pandas as pd
from io import BytesIO
from PIL import Image

# 📌 Personalitza aquí la clau API d'OCR.space
OCR_SPACE_API_KEY = st.secrets["ocr_space_api"]

# 👇 Afegeix això just abans de cridar a ocr_space_file()
from PIL import ImageOps

# Redueix mida a JPEG de baixa qualitat
img = Image.open(upload)
img = img.convert("RGB")
compressed = BytesIO()
img.save(compressed, format="JPEG", optimize=True, quality=50)
compressed.seek(0)

# Envia aquesta imatge comprimida
result = ocr_space_file(compressed)



def ocr_space_file(image_bytes):
    payload = {
        'apikey': OCR_SPACE_API_KEY,
        'language': 'spa',
        'OCREngine': 2,
        'isTable': False,
        'detectOrientation': True
    }
    files = {'file': ('tiquet.jpg', image_bytes, 'image/jpeg')}
    resp = requests.post('https://api.ocr.space/parse/image', files=files, data=payload)
    return resp.json()

def extreu_dades(text):
    import re
    empresa = re.search(r'([A-ZÀ-Ú\s]{5,}SL)', text)
    import_final = re.search(r'(?:TOTAL|Import).*?(\d+[,\.]\d{2})', text, re.IGNORECASE)
    return {
        "Empresa": empresa.group(1).strip() if empresa else "Desconeguda",
        "Import": import_final.group(1).replace('.', ',') if import_final else "0,00"
    }

st.title("🧾 Lectura de tiquets via OCR.space")
upload = st.file_uploader("Puja una imatge (.jpg, .png)", type=['jpg', 'jpeg', 'png'])

if upload:
    if upload:
        img = Image.open(upload)
        st.image(img, caption="Tiquet", use_container_width=True)

        if st.button("Processa i genera Excel"):
            # 🔽 Converteix i comprimeix la imatge
            img = img.convert("RGB")
            compressed = BytesIO()
            img.save(compressed, format="JPEG", optimize=True, quality=50)
            compressed.seek(0)

            # 📤 Envia la imatge comprimida a l'OCR
            result = ocr_space_file(compressed)

        if not result or "ParsedResults" not in result:
            st.error("❌ Error en la resposta de l'OCR.")
            st.write(result)  # Mostra la resposta completa per depurar

        else:
            parsed = result["ParsedResults"][0]["ParsedText"]
            dades = extreu_dades(parsed)
            st.success("✅ Dades extretes:")
            st.json(dades)

            df = pd.DataFrame([dades])
            buf = BytesIO()
            df.to_excel(buf, index=False, engine='openpyxl')
            buf.seek(0)
            st.download_button("📥 Descarrega Excel", buf, file_name="dades_tiquet.xlsx")

