import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# --- CONFIGURACIÓN ---
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
ID_CARPETA = "10ZvtViZ0RrPatahlFpWxFr-zwa-AoRXC"

def get_drive_service():
    info = dict(st.secrets["gcp_service_account"])
    info["private_key"] = info["private_key"].replace("\\n", "\n")
    creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

st.title("DEBUG: Listado de archivos en Carpeta")

try:
    service = get_drive_service()
    
    # Listamos TODO lo que haya en la carpeta sin filtros de nombre o tipo
    query = f"'{ID_CARPETA}' in parents and trashed = false"
    results = service.files().list(
        q=query, 
        fields="files(id, name, mimeType, modifiedTime)"
    ).execute()
    
    items = results.get('files', [])

    if not items:
        st.warning("La carpeta está totalmente vacía en Google Drive.")
    else:
        st.write(f"Se encontraron {len(items)} elementos:")
        for item in items:
            # Usamos columnas para que sea fácil de leer
            col1, col2, col3 = st.columns([2, 2, 1])
            col1.write(f"📄 **Nombre:** {item['name']}")
            col2.write(f"🔑 **Tipo:** `{item['mimeType']}`")
            col3.write(f"📅 **Modificado:** {item['modifiedTime'][:10]}")
            st.divider()

except Exception as e:
    st.error(f"Error al listar: {e}")