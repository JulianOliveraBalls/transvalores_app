import streamlit as st
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# --- CONFIGURACIÓN ---
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
ID_CARPETA = "1UU3CQl7GY1qnZ3QByuLnxNcT2XfWtaUL"

def get_drive_service():
    # 1. Obtenemos el diccionario de secrets
    # Es vital convertirlo a dict para poder manipular la private_key
    info = dict(st.secrets["gcp_service_account"])
    
    # 2. Limpieza CRÍTICA de la llave
    # Reemplazamos la cadena literal '\n' por saltos de línea reales
    info["private_key"] = info["private_key"].replace("\\n", "\n")
    
    # 3. Crear credenciales
    creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

st.title("🚀 Verificación de Carpeta Drive")

if st.button("Listar Archivos"):
    try:
        service = get_drive_service()
        
        # Consultar archivos en la carpeta
        query = f"'{ID_CARPETA}' in parents and trashed = false"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        items = results.get('files', [])

        if not items:
            st.warning("La carpeta está vacía.")
        else:
            st.success(f"✅ ¡Conexión exitosa! Encontrados {len(items)} archivos:")
            for item in items:
                st.write(f"📄 **Nombre:** {item['name']} (ID: {item['id']})")
                
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        st.info("Si el error persiste, probá dándole a 'Reboot app' en el panel de Streamlit.")