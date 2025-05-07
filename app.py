import streamlit as st
import pandas as pd
from io import BytesIO
from PIL import Image
from utils.script_gender import detectar_genero
from utils.inceptiaToWebFlow import exportar_eventos

# Configurar la página
st.set_page_config(page_title="Transvalores App", layout="centered")

# Mostrar el logo y el título
logo = Image.open("logo.png")
st.image(logo, width=150)
st.title("📊 Herramienta de procesamiento Excel / CSV / TXT")

# Selector de opción
opcion = st.selectbox("Seleccioná qué querés hacer:", [
    "Detectar género",
    "Exportar eventos IA"
])

# Ejemplos de estructura por cada opción
ejemplos = {
    "Detectar género": pd.DataFrame({
        "Nombre": ["Juan Pérez", "María Gómez", "A. Sosa"]
    }),
    "Exportar eventos IA": pd.DataFrame({
        "Fecha": ["2024-05-01", "2024-05-02"],
        "Hora": ["10:30", "14:15"],
        "Codigo": [1234, 5678],
        "Estado": ["Correo de Voz", "Cortó Llamada"],
        "Telefono": ["1134567890", "1198765432"]
    })
}

# Mostrar preview del formato esperado
st.markdown("📌 *Formato esperado para esta opción:*")
st.dataframe(ejemplos[opcion])

# Subida del archivo
archivo = st.file_uploader("📂 Subí un archivo Excel o CSV", type=["xlsx", "csv"])

# Procesamiento del archivo
if archivo:
    try:
        # Detectar tipo de archivo y leerlo
        if archivo.name.endswith(".csv"):
            df = pd.read_csv(archivo)
        else:
            df = pd.read_excel(archivo)

        st.write("📋 Vista previa del archivo cargado:")
        st.dataframe(df.head())

        # Procesamiento según opción
        if opcion == "Detectar género":
            df = detectar_genero(df)
        elif opcion == "Exportar eventos IA":
            df = exportar_eventos(df)

        # Mostrar resultado
        st.success("✅ Procesamiento completo")
        st.dataframe(df.head())

        # Exportar a Excel en memoria
        output_excel = BytesIO()
        with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        output_excel.seek(0)

        # Exportar a TXT en memoria (separado por espacios)
        output_txt = BytesIO()
        df.to_csv(output_txt, index=False, sep=' ', lineterminator='\n')
        output_txt.seek(0)

        # Mostrar los botones de descarga
        st.download_button(
            label="📥 Descargar resultado en Excel (.xlsx)",
            data=output_excel,
            file_name="resultado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.download_button(
            label="📥 Descargar resultado en Texto (.txt separado por espacios)",
            data=output_txt,
            file_name="resultado.txt",
            mime="text/plain"
        )

    except Exception as e:
        st.error(f"❌ Error: {e}")
