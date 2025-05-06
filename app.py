import streamlit as st
import pandas as pd
from io import BytesIO
from PIL import Image

from utils.script_gender import detectar_genero
from utils.inceptiaToWebFlow import exportar_eventos

# Configurar la página (esto debe ser lo primero de Streamlit)
st.set_page_config(page_title="Transvalores App", layout="centered")

# Mostrar el logo y el título
logo = Image.open("logo.png")
st.image(logo, width=150)
st.title("📊 Herramienta de procesamiento Excel")

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
        "Estado": ["CONTACTADO", "NO CONTESTA"],
        "Telefono": ["1134567890", "1198765432"]
    })
}

# Mostrar preview del formato esperado
st.markdown("📌 *Formato esperado para esta opción:*")
st.dataframe(ejemplos[opcion])


# Subida del archivo
archivo = st.file_uploader("📂 Subí un archivo Excel", type=["xlsx"])

# Procesamiento del archivo
if archivo:
    try:
        df = pd.read_excel(archivo)
        st.write("📋 Vista previa del archivo cargado:")
        st.dataframe(df.head())

        # Elegir qué hacer
        if opcion == "Detectar género":
            df = detectar_genero(df)
        elif opcion == "Exportar eventos IA":
            df = exportar_eventos(df)

        # Mostrar resultado
        st.success("✅ Procesamiento completo")
        st.dataframe(df.head())

        # Exportar a Excel en memoria
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        output.seek(0)

        # Botón de descarga
        st.download_button(
            label="📥 Descargar resultado",
            data=output,
            file_name="resultado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"❌ Error: {e}")
