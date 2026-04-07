import streamlit as st
import pandas as pd
import io
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from datetime import datetime

# --- CONFIGURACIÓN ---
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
ID_CARPETA = "10ZvtViZ0RrPatahlFpWxFr-zwa-AoRXC"

def get_drive_service():
    info = dict(st.secrets["gcp_service_account"])
    info["private_key"] = info["private_key"].replace("\\n", "\n")
    creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

@st.cache_data(ttl=3600)
def load_specific_csv(folder_id):
    service = get_drive_service()
    
    # Generamos el nombre esperado según el mes actual: Transvalores_2026-04.csv
    ahora = datetime.now()
    nombre_esperado = f"Transvalores_{ahora.strftime('%Y-%m')}.csv"
    
    # Buscamos el archivo por nombre exacto dentro de la carpeta
    query = f"'{folder_id}' in parents and name = '{nombre_esperado}' and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])
    
    if not files:
        return None, f"No se encontró el archivo del mes: {nombre_esperado}"
    
    file_id = files[0]['id']
    file_name = files[0]['name']
    
    # Descarga
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    
    fh.seek(0)
    
    # IMPORTANTE: Cambiado a read_csv. 
    # Agregué encoding='latin-1' o 'utf-8' por si el CSV tiene caracteres especiales
    try:
        df = pd.read_csv(fh, encoding='utf-8')
    except UnicodeDecodeError:
        fh.seek(0)
        df = pd.read_csv(fh, encoding='latin-1')
        
    return df, file_name

# --- INTERFAZ ---
st.set_page_config(page_title="Gestión de Mora - Transvalores", layout="wide")
st.title("🔎 Consulta de Cuotas y Días de Mora")

try:
    df, nombre_archivo = load_specific_csv(ID_CARPETA)
    
    if df is not None:
        st.caption(f"📂 Datos cargados de: **{nombre_archivo}**")
        
        cedula_input = st.text_input("Ingrese Cédula / DNI del cliente:", placeholder="Ej: 12345678")
        
        if cedula_input:
            # Aseguramos que la columna sea string y quitamos espacios
            df['#Cedula'] = df['#Cedula'].astype(str).str.strip()
            res = df[df['#Cedula'] == str(cedula_input)].copy()
            
            if not res.empty:
                st.subheader(f"Cliente: {res['Nombre usuario'].iloc[0]}")
                
                # --- PROCESAMIENTO DE MORA ---
                # Ajustamos el formato de fecha si es necesario (ej: 2026-04-10)
                res['Fecha Pago'] = pd.to_datetime(res['Fecha Pago'], errors='coerce')
                hoy = datetime.now()
                
                def calcular_mora(fila):
                    if pd.notnull(fila['Fecha Pago']) and fila['Monto por cobrar actual'] > 0:
                        if fila['Fecha Pago'] < hoy:
                            return (hoy - fila['Fecha Pago']).days
                    return 0

                res['Días de Mora'] = res.apply(calcular_mora, axis=1)
                
                # --- MOSTRAR RESULTADOS ---
                columnas_mostrar = [
                    'ID cuota', '#Cuota', 'Fecha Pago', 
                    'Monto por cobrar actual', 'Días de Mora', 'Tramo actual'
                ]
                
                res_display = res[columnas_mostrar].rename(columns={'Fecha Pago': 'Vencimiento'})
                
                col1, col2 = st.columns(2)
                with col1:
                    total_deuda = res_display['Monto por cobrar actual'].sum()
                    st.metric("Deuda Total Pendiente", f"${total_deuda:,.2f}")
                with col2:
                    max_mora = res_display['Días de Mora'].max()
                    st.metric("Máximo de Días de Mora", f"{max_mora} días")

                st.dataframe(res_display.sort_values('Vencimiento'), use_container_width=True)
            else:
                st.warning(f"No se encontraron registros para el DNI {cedula_input}.")
    else:
        # Aquí mostramos el error de que no se encontró el archivo del mes
        st.error(nombre_archivo)

except Exception as e:
    st.error(f"Ocurrió un error al procesar los datos: {e}")