import streamlit as st
import pandas as pd
from io import BytesIO
from PIL import Image
from utils.script_gender import detectar_genero
from utils.inceptiaToWebFlow import exportar_eventos
from utils.CleanStockSPV import reducir_columnas
from utils.connectCertero import procesar_archivo_con_api

# Configurar la página
st.set_page_config(page_title="Transvalores App", layout="centered")

# Mostrar el logo y el título
logo = Image.open("logo.png")
st.image(logo, width=150)
st.title("📊 Herramienta de procesamiento Excel / CSV / TXT")

# Selector de opción
opcion = st.selectbox("Seleccioná qué querés hacer:", [
    "Detectar género",
    "Exportar eventos IA",
    "Clean Superville Stock",
    "Conectar con Certero API"
])

# Ejemplos de estructura por cada opción
ejemplos = {
    "Detectar género": pd.DataFrame({"Nombre": ["Juan Pérez", "María Gómez", "A. Sosa"]}),
    "Exportar eventos IA": pd.DataFrame({
        "Fecha": ["2024-05-01", "2024-05-02"],
        "Hora": ["10:30", "14:15"],
        "Codigo": [1234, 5678],
        "Estado": ["Correo de Voz", "Cortó Llamada"],
        "Telefono": ["1134567890", "1198765432"]
    }),
    "Clean Superville Stock": pd.DataFrame({
        "DNI": [12345678, 87654321],
        "Apellido y Nombre": ["JUAN PEREZ", "MARÍA GOMEZ"],
        "Clave Banco de la cuenta": [111, 222],
        "Subsegmento": ["ALTO", "BAJO"],
        "deuda total del cliente": [50000, 30000],
        "Localidad": ["CABA", "LA PLATA"],
        "Provincia": ["BUENOS AIRES", "BUENOS AIRES"],
        "grupo del producto": ["TC", "PP"],
        "días de mora Total Cliente": [45, 30]
    }),
    "Conectar con Certero API": pd.DataFrame({
        "CUIL": [20123456789, 20234567891]
    })
}

# Mostrar preview del formato esperado
st.markdown(":pushpin: *Formato esperado para esta opción:*")
st.dataframe(ejemplos[opcion])

# Subida del archivo
archivo = st.file_uploader("📂 Subí un archivo Excel o CSV", type=["xlsx", "csv"])

# Token para Certero API (mostrar si corresponde)
if opcion == "Conectar con Certero API":
    token = st.text_input("Token de autenticación para la API Certero", type="password")

# Procesamiento del archivo
if archivo:
    try:
        # Leer archivo
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
        elif opcion == "Clean Superville Stock":
            df = reducir_columnas(df)
        elif opcion == "Conectar con Certero API":
            if not token:
                st.warning("🔚 Ingresá un token válido para usar la API")
            else:
                columna_cuil = st.selectbox("Seleccioná la columna con CUIL", df.columns)
                df = procesar_archivo_con_api(df, token, columna_cuil)

        # Mostrar resultado y exportaciones
        st.success("✅ Procesamiento completo")
        st.dataframe(df.head())

        output_excel = BytesIO()
        with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        output_excel.seek(0)

        output_txt = BytesIO()
        df.to_csv(output_txt, index=False, sep=' ', lineterminator='\n')
        output_txt.seek(0)

        st.download_button(
            label="📅 Descargar resultado en Excel (.xlsx)",
            data=output_excel,
            file_name="resultado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.download_button(
            label="📅 Descargar resultado en Texto (.txt separado por espacios)",
            data=output_txt,
            file_name="resultado.txt",
            mime="text/plain"
        )

    except Exception as e:
        st.error(f"❌ Error: {e}")
