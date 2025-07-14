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

    empresa = re.search(r'MARC GIOVANNI ADDIS HERNANDEZ', text, re.IGNORECASE)
    data = re.search(r'Data[:\s]*(\d{2}/\d{2}/\d{4})', text)

    línies = text.splitlines()
    import_final = None

    for i, línia in enumerate(línies):
        if "TOTAL" in línia.upper():
            match_inline = re.findall(r'(\d+[.,]\d{2})', línia)
            if match_inline:
                import_final = match_inline[-1].replace('.', ',')  # Agafa l'últim número
                break
            if i > 0:
                línia_previa = línies[i - 1]
                match_sobre = re.findall(r'(\d+[.,]\d{2})', línia_previa)
                if match_sobre:
                    import_final = match_sobre[-1].replace('.', ',')
                    break
            if i + 1 < len(línies):
                línia_sota = línies[i + 1]
                match_dessota = re.findall(r'(\d+[.,]\d{2})', línia_sota)
                if match_dessota:
                    import_final = match_dessota[-1].replace('.', ',')
                    break

    return {
        "Empresa": empresa.group(0).strip() if empresa else "Desconeguda",
        "Data": data.group(1) if data else "",
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
            if "ParsedResults" in result and result["ParsedResults"]:
                parsed = result["ParsedResults"][0]["ParsedText"]
                st.subheader("📝 Text extret (OCR):")
                st.code(parsed)
                dades = extreu_dades(parsed)
                st.success("✅ Dades extretes correctament:")
                st.json(dades)

                df = pd.DataFrame([dades])
                buf = BytesIO()
                df.to_excel(buf, index=False, engine='openpyxl')
                buf.seek(0)
                st.download_button("📥 Descarrega Excel", buf, file_name="dades_tiquet.xlsx")
            else:
                st.error("❌ No s'han pogut extreure dades del tiquet. Torna-ho a provar amb una imatge més clara.")

