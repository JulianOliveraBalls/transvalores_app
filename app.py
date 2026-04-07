import streamlit as st
import pandas as pd
import io
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from datetime import datetime

# --- CONFIGURACIÓN ---
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
ID_CARPETA_RAIZ = "10ZvtViZ0RrPatahlFpWxFr-zwa-AoRXC"

def get_drive_service():
    info = dict(st.secrets["gcp_service_account"])
    info["private_key"] = info["private_key"].replace("\\n", "\n")
    creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

@st.cache_data(ttl=3600)
def load_data_from_subfolder(root_id):
    service = get_drive_service()
    ahora = datetime.now()
    
    # 1. Mapeo de meses para buscar la carpeta (ej: "Abril 2026")
    meses = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto", 
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    nombre_carpeta_mes = f"{meses[ahora.month]} {ahora.year}"
    
    # 2. Buscar la carpeta del mes
    q_folder = f"'{root_id}' in parents and name contains '{meses[ahora.month]}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    res_folder = service.files().list(q=q_folder, fields="files(id, name)").execute()
    folders = res_folder.get('files', [])
    
    if not folders:
        return None, f"No se encontró la carpeta del mes: {nombre_carpeta_mes}"
    
    folder_id = folders[0]['id']
    
    # 3. Buscar el CSV dentro de esa carpeta
    q_csv = f"'{folder_id}' in parents and mimeType = 'text/csv' and trashed = false"
    res_csv = service.files().list(q=q_csv, fields="files(id, name)").execute()
    csv_files = res_csv.get('files', [])
    
    if not csv_files:
        return None, f"No se encontró ningún archivo CSV dentro de la carpeta {nombre_carpeta_mes}"
    
    # Tomamos el primero que encuentre
    file_id = csv_files[0]['id']
    file_name = csv_files[0]['name']
    
    # 4. Descarga y lectura
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    
    fh.seek(0)
    try:
        df = pd.read_csv(fh, encoding='utf-8', sep=None, engine='python')
    except:
        fh.seek(0)
        df = pd.read_csv(fh, encoding='latin-1', sep=None, engine='python')
        
    return df, file_name

# --- INTERFAZ ---
st.set_page_config(page_title="Gestión de Mora - Transvalores", layout="wide")
st.title("🔎 Consulta de Cuotas y Días de Mora")

try:
    df, nombre_archivo = load_data_from_subfolder(ID_CARPETA_RAIZ)
    
    if df is not None:
        st.success(f"Conectado: {nombre_archivo}")
        
        cedula_input = st.text_input("Ingrese Cédula / DNI:", placeholder="Ej: 12345678")
        
        if cedula_input:
            df['#Cedula'] = df['#Cedula'].astype(str).str.strip()
            res = df[df['#Cedula'] == str(cedula_input)].copy()
            
            if not res.empty:
                st.subheader(f"Cliente: {res['Nombre usuario'].iloc[0]}")
                
                # Cálculo de Mora
                res['Fecha Pago'] = pd.to_datetime(res['Fecha Pago'], errors='coerce')
                hoy = datetime.now()
                
                def calcular_mora(fila):
                    if pd.notnull(fila['Fecha Pago']) and fila['Monto por cobrar actual'] > 0:
                        if fila['Fecha Pago'] < hoy:
                            return (hoy - fila['Fecha Pago']).days
                    return 0

                res['Días de Mora'] = res.apply(calcular_mora, axis=1)
                
                # Mostrar Tabla
                columnas = ['ID cuota', '#Cuota', 'Fecha Pago', 'Monto por cobrar actual', 'Días de Mora', 'Tramo actual']
                st.dataframe(res[columnas].rename(columns={'Fecha Pago': 'Vencimiento'}), use_container_width=True)
            else:
                st.warning("DNI no encontrado.")
    else:
        st.error(df_error := nombre_archivo)

except Exception as e:
    st.error(f"Error general: {e}")