import streamlit as st
import pandas as pd
from io import BytesIO
from PIL import Image

from utils.script_gender import detectar_genero
from utils.inceptiaToWebFlow import exportar_eventos

# Configurar la página (esto debe ser lo primero de Streamlit)
st.set_page_config(page_title="Transvalores App", layout="centered")

# Estilos personalizados
st.markdown(
    """
    <style>
    .main {
        background-color: #f4f6f9;
    }

    img {
        display: block;
        margin-left: auto;
        margin-right: auto;
    }

    h1 {
        color: #124e8b;
        text-align: center;
        font-size: 36px;
    }

    .stButton>button {
        background-color: #124e8b;
        color: white;
        border: none;
        padding: 0.5em 1em;
        font-weight: bold;
        border-radius: 5px;
        transition: 0.3s;
    }

    .stButton>button:hover {
        background-color: #0d3a66;
    }

    .stAlert, .stSuccess, .stError {
        border-left: 5px solid #124e8b;
    }

    .stSelectbox>div {
        background-color: white;
        color: #124e8b;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Mostrar el logo y el título
logo = Image.open("logo.png")
st.image(logo, width=150)
st.title("📊 Herramienta de procesamiento Excel")

# Selector de opción
opcion = st.selectbox("Seleccioná qué querés hacer:", [
    "Detectar género",
    "Exportar eventos IA"
])

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
