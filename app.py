import streamlit as st
import requests
import pandas as pd
from io import BytesIO
from PIL import Image

# 📌 Personalitza aquí la clau API d'OCR.space
OCR_SPACE_API_KEY = st.secrets["ocr_space_api"]

def ocr_space_file(image_bytes):
    payload = {
        'apikey': OCR_SPACE_API_KEY,
        'language': 'spa',
        'OCREngine': 2,
        'isTable': False,
        'detectOrientation': True
    }
    files = {'file': image_bytes}
    resp = requests.post('https://api.ocr.space/parse/image', files=files, data=payload)
    return resp.json()

def extreu_dades(text):
    import re
    empresa = re.search(r'([A-ZÀ-Ú\s]{5,}SL)', text)
    data_hora = re.search(r'(\d{2}/\d{2}/\d{4}).*?(\d{2}:\d{2})', text)
    import_final = re.search(r'(?:TOTAL|Import).*?(\d+[,\.]\d{2})', text, re.IGNORECASE)
    return {
        "Empresa": empresa.group(1).strip() if empresa else "Desconeguda",
        "Import": import_final.group(1).replace('.', ',') if import_final else "0,00"
    }

st.title("🧾 Lectura de tiquets via OCR.space")
upload = st.file_uploader("Puja una imatge (.jpg, .png)", type=['jpg', 'jpeg', 'png'])

if upload:
    img = Image.open(upload)
    st.image(img, caption="Tiquet", use_container_width=True)
    if st.button("Processa i genera Excel"):
        result = ocr_space_file(upload.getvalue())

        if not result or "ParsedResults" not in result:
            st.error("❌ No s'ha pogut llegir el tiquet. Revisa la clau API o torna-ho a intentar.")
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

