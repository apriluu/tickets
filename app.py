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
    files = {'file': ('tiquet.jpg', image_bytes, 'image/jpeg')}
    resp = requests.post('https://api.ocr.space/parse/image', files=files, data=payload)
    return resp.json()

def extreu_dades(text):
    import re

    # 🔍 Empresa: agafem el nom en majúscules abans de "Nif:"
    empresa_match = re.search(r'([A-ZÀ-Ú\s]{5,})\s*\nNif:', text)
    empresa = empresa_match.group(1).strip() if empresa_match else "Desconeguda"

    # 🔍 Data
    data_match = re.search(r'Data[:\s]*(\d{2}/\d{2}/\d{4})', text)
    data = data_match.group(1) if data_match else ""

    # 🔍 Preu total: busquem línia amb "TOTAL" i agafem número anterior si cal
    linies = text.splitlines()
    import_final = None
    for i, linia in enumerate(linies):
        if "TOTAL" in linia.upper():
            # Comprova si el número està abans
            if i >= 1:
                num_match = re.search(r'(\d+[.,]\d{2})', linies[i - 1])
                if num_match:
                    import_final = num_match.group(1).replace('.', ',')
                    break
            # O a la mateixa línia (per si canvia en altres tiquets)
            num_match = re.search(r'(\d+[.,]\d{2})', linia)
            if num_match:
                import_final = num_match.group(1).replace('.', ',')
                break

    return {
        "Empresa": empresa,
        "Data": data,
        "Import": import_final if import_final else "0,00"
    }


st.title("🧾 Lectura de tiquets")
upload = st.file_uploader("Puja una imatge (.jpg, .png)", type=['jpg', 'jpeg', 'png'])

if upload:
    img = Image.open(upload)
    st.image(img, caption="Tiquet", use_container_width=True)

    if st.button("Processa i genera Excel"):
        # 🔽 Converteix i comprimeix la imatge
        img = img.convert("RGB")
        compressed = BytesIO()
        img.save(compressed, format="JPEG", optimize=True, quality=50)
        compressed.seek(0)

        result = ocr_space_file(compressed)

        if not result or "ParsedResults" not in result:
            st.error("❌ Error en la resposta de l'OCR.")
            st.write(result)  # Mostra la resposta completa per depurar

        else:
            parsed = result["ParsedResults"][0]["ParsedText"]
            st.subheader("📝 Text extret (OCR):")
            st.code(parsed)
            dades = extreu_dades(parsed)
            st.success("✅ Dades extretes:")
            st.json(dades)

            df = pd.DataFrame([dades])
            buf = BytesIO()
            df.to_excel(buf, index=False, engine='openpyxl')
            buf.seek(0)
            st.download_button("📥 Descarrega Excel", buf, file_name="dades_tiquet.xlsx")

