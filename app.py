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

@st.cache_data(ttl=600)
def load_data_from_subfolder(root_id):
    service = get_drive_service()
    ahora = datetime.now()
    
    meses = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio", 
             7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}
    
    # 1. Buscar carpeta del mes (ej: "Abril 2026")
    q_folder = f"'{root_id}' in parents and name contains '{meses[ahora.month]}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    res_folder = service.files().list(q=q_folder).execute()
    folders = res_folder.get('files', [])
    
    if not folders:
        return None, f"No se encontró carpeta para {meses[ahora.month]}"
    
    folder_id = folders[0]['id']
    
    # 2. Buscar el archivo que diga "Stock" dentro de esa carpeta
    q_csv = f"'{folder_id}' in parents and name contains 'Stock' and trashed = false"
    res_csv = service.files().list(q=q_csv).execute()
    csv_files = res_csv.get('files', [])
    
    if not csv_files:
        return None, "No se encontró el archivo de Stock (.csv)"
    
    file_id = csv_files[0]['id']
    file_name = csv_files[0]['name']
    
    # 3. Descarga
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    
    fh.seek(0)
    
    # 4. Lectura Robusta con detección de separador y encoding
    try:
        # engine='python' + sep=None hace que pandas adivine si es , o ;
        df = pd.read_csv(fh, sep=None, engine='python', encoding='utf-8')
    except:
        fh.seek(0)
        df = pd.read_csv(fh, sep=None, engine='python', encoding='latin-1')
        
    # LIMPIEZA INMEDIATA DE COLUMNAS
    df.columns = [c.strip().replace('#', '').replace(' ', '_') for c in df.columns]
    return df, file_name

# --- INTERFAZ ---
st.set_page_config(page_title="Mora Transvalores", layout="wide")
st.title("🔎 Consulta de Mora")

try:
    df, nombre_archivo = load_data_from_subfolder(ID_CARPETA_RAIZ)
    
    if df is not None:
        st.success(f"Archivo cargado: {nombre_archivo}")
        
        cedula_input = st.text_input("Ingrese Cédula / DNI:")
        
        if cedula_input:
            # Buscamos la columna de cédula (ahora se llama 'Cedula' sin el # por la limpieza)
            col_id = 'Cedula' if 'Cedula' in df.columns else df.columns[0]
            
            df[col_id] = df[col_id].astype(str).str.strip()
            res = df[df[col_id] == str(cedula_input).strip()].copy()
            
            if not res.empty:
                # Mostrar Info
                nombre = res['Nombre_usuario'].iloc[0] if 'Nombre_usuario' in res.columns else "Cliente"
                st.subheader(f"Cliente: {nombre}")
                
                # Procesar Fechas y Mora
                # Buscamos la columna de fecha (que ahora se llama Fecha_Pago por la limpieza)
                col_fecha = 'Fecha_Pago' if 'Fecha_Pago' in res.columns else 'Fecha'
                res['Fecha_vto'] = pd.to_datetime(res[col_fecha], dayfirst=True, errors='coerce')
                
                hoy = datetime.now()
                # Columna de monto (Monto_por_cobrar_actual)
                col_monto = 'Monto_por_cobrar_actual'
                
                res['Dias_Mora'] = res.apply(
                    lambda x: (hoy - x['Fecha_vto']).days if pd.notnull(x['Fecha_vto']) and x[col_monto] > 0 and x['Fecha_vto'] < hoy else 0, 
                    axis=1
                )
                
                # Mostrar Tabla
                st.dataframe(res.sort_values('Fecha_vto'), use_container_width=True)
            else:
                st.warning("DNI no encontrado.")
                # Debug por si acaso:
                with st.expander("Ver columnas detectadas"):
                    st.write(list(df.columns))
    else:
        st.error(nombre_archivo)

except Exception as e:
    st.error(f"Error: {e}")