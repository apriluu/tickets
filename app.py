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
    línies = text.splitlines()

    empresa = None
    for línia in línies:
            empresa = línia.strip()
            break

    # Data
    data = ""
    match_data = re.search(r'Data[:\s]*(\d{2}/\d{2}/\d{4})', text)
    if match_data:
        data = match_data.group(1)


    # Import final correcte: el número que està just abans de "TOTAL"
    import_final = "0,00"
    for i, línia in enumerate(línies):
        if "TOTAL" in línia.upper():
            # Mira enrere fins a 2 línies abans per trobar el número
            for j in range(i - 1, max(i - 3, -1), -1):
                match = re.search(r'(\d+[.,]\d{2})', línies[j])
                if match:
                    import_final = match.group(1).replace('.', ',')
                    break
            break

    return {
        "Empresa": empresa if empresa else "Desconeguda",
        "Data": data,
        "Import": import_final
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

