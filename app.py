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
    
    try:
        q_folder = f"'{root_id}' in parents and name contains '{meses[ahora.month]}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        res_folder = service.files().list(q=q_folder).execute()
        folders = res_folder.get('files', [])
        if not folders: return None, f"No se encontró carpeta para {meses[ahora.month]}"
        
        folder_id = folders[0]['id']
        q_csv = f"'{folder_id}' in parents and name contains 'Stock' and trashed = false"
        res_csv = service.files().list(q=q_csv).execute()
        csv_files = res_csv.get('files', [])
        if not csv_files: return None, "No se encontró el archivo de Stock (.csv)"
        
        file_id = csv_files[0]['id']
        file_name = csv_files[0]['name']
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        
        fh.seek(0)
        try:
            df = pd.read_csv(fh, sep=None, engine='python', encoding='utf-8')
        except:
            fh.seek(0)
            df = pd.read_csv(fh, sep=None, engine='python', encoding='latin-1')
            
        df.columns = [c.strip().replace('#', '').replace(' ', '_') for c in df.columns]
        return df, file_name
    except Exception as e:
        return None, f"Error al cargar Drive: {e}"

# --- INTERFAZ ---
st.set_page_config(page_title="Mora Transvalores", layout="wide")
st.title("🔎 Consulta de Cuotas y Días de Mora")

# 🔥 Toggle de debug
debug = st.checkbox("🛠️ Modo debug")

try:
    df, nombre_archivo = load_data_from_subfolder(ID_CARPETA_RAIZ)
    
    if df is not None:
        st.success(f"Archivo cargado: {nombre_archivo}")

        if debug:
            st.subheader("📄 Preview CSV original")
            st.write(df.head(10))
            st.write("Columnas:", df.columns.tolist())

        cedula_input = st.text_input("Ingrese Cédula / DNI del cliente:")
        
        if cedula_input:
            col_id = 'Cedula' if 'Cedula' in df.columns else df.columns[0]
            df[col_id] = df[col_id].astype(str).str.strip()
            res = df[df[col_id] == str(cedula_input).strip()].copy()
            
            if not res.empty:

                col_fecha = 'Fecha_Pago' if 'Fecha_Pago' in res.columns else 'Fecha'
                col_monto_act = 'Monto_por_cobrar_actual'
                col_monto_orig = 'Monto' if 'Monto' in res.columns else 'Monto_por_cobrar'

                if debug:
                    st.subheader("📅 Datos crudos de fecha")
                    st.write(res[col_fecha].head(10))

                # --- PARSEO SIMPLE Y ROBUSTO ---
                res['Vencimiento'] = pd.to_datetime(
                    res[col_fecha].astype(str).str.strip(),
                    dayfirst=True,
                    errors='coerce'
                )

                # --- Montos ---
                res[col_monto_act] = pd.to_numeric(res[col_monto_act], errors='coerce')
                res[col_monto_orig] = pd.to_numeric(res[col_monto_orig], errors='coerce')

                hoy = pd.Timestamp.now().normalize()

                # --- Cálculo mora ---
                res['Dias_Mora'] = (hoy - res['Vencimiento']).dt.days

                res['Dias_Mora'] = res['Dias_Mora'].fillna(0)
                res.loc[res['Dias_Mora'] < 0, 'Dias_Mora'] = 0
                res.loc[res[col_monto_act] <= 0, 'Dias_Mora'] = 0
                res['Dias_Mora'] = res['Dias_Mora'].astype(int)

                # 🔍 DEBUG CLAVE
                if debug:
                    st.subheader("🧠 Resultado parseo fechas")
                    st.write(res[[col_fecha, 'Vencimiento']].head(10))

                    st.write("NaT en fechas:", res['Vencimiento'].isna().sum())

                    st.subheader("💰 Montos")
                    st.write(res[[col_monto_act, col_monto_orig]].head(10))

                    st.subheader("📊 Mora calculada")
                    st.write(res[['Vencimiento', 'Dias_Mora']].head(10))

                # --- RESUMEN ---
                st.markdown("### 📊 Resumen de Deuda")
                t1, t2, t3 = st.columns(3)
                with t1:
                    st.metric("Días de Mora (Máx)", f"{int(res['Dias_Mora'].max())} días")
                with t2:
                    st.metric("Suma Monto Original", f"${res[col_monto_orig].sum():,.2f}")
                with t3:
                    st.metric("Total Pendiente Actual", f"${res[col_monto_act].sum():,.2f}")

                st.divider()

                # --- DETALLE ---
                st.markdown("### 💳 Detalle de Cuotas")
                res_display = res[['Dias_Mora', 'Vencimiento', col_monto_orig, col_monto_act]].copy()
                res_display = res_display.sort_values('Vencimiento')
                res_display['Vencimiento'] = res_display['Vencimiento'].dt.strftime('%d/%m/%Y')

                st.dataframe(res_display, use_container_width=True, hide_index=True)

            else:
                st.warning("DNI no encontrado.")
    else:
        st.error(nombre_archivo)

except Exception as e:
    st.error(f"Error: {e}")