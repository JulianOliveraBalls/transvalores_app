import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

def get_drive_service():
    # Cargamos desde Secrets
    info = dict(st.secrets["gcp_service_account"])
    
    # IMPORTANTE: Reemplazar el doble escape por salto de línea real
    info["private_key"] = info["private_key"].replace("\\n", "\n")
    
    creds = Credentials.from_service_account_info(info, scopes=['https://www.googleapis.com/auth/drive.readonly'])
    return build('drive', 'v3', credentials=creds)

# Prueba simple de lectura de carpeta
st.title("Test de Carpeta")

try:
    service = get_drive_service()
    ID_CARPETA = "1UU3CQl7GY1qnZ3QByuLnxNcT2XfWtaUL"
    
    query = f"'{ID_CARPETA}' in parents and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    items = results.get('files', [])

    if not items:
        st.write("Conectado, pero la carpeta está vacía.")
    else:
        for item in items:
            st.write(f"✅ Archivo encontrado: {item['name']}")
            
except Exception as e:
    st.error(f"Error: {e}")