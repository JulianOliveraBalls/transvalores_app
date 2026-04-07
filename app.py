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

try:
    df, nombre_archivo = load_data_from_subfolder(ID_CARPETA_RAIZ)
    
    if df is not None:
        st.success(f"Archivo cargado: {nombre_archivo}")
        cedula_input = st.text_input("Ingrese Cédula / DNI del cliente:")
        
        if cedula_input:
            col_id = 'Cedula' if 'Cedula' in df.columns else df.columns[0]
            df[col_id] = df[col_id].astype(str).str.strip()
            res = df[df[col_id] == str(cedula_input).strip()].copy()
            
            if not res.empty:

                col_fecha = 'Fecha_Pago' if 'Fecha_Pago' in res.columns else 'Fecha'
                col_monto_act = 'Monto_por_cobrar_actual'
                col_monto_orig = 'Monto' if 'Monto' in res.columns else 'Monto_por_cobrar'

                # --- 1. Parseo robusto de fechas ---
                res['Vencimiento'] = pd.to_datetime(
                    res[col_fecha],
                    dayfirst=True,
                    errors='coerce'
                )

                # --- 2. Asegurar montos numéricos ---
                res[col_monto_act] = pd.to_numeric(res[col_monto_act], errors='coerce')
                res[col_monto_orig] = pd.to_numeric(res[col_monto_orig], errors='coerce')

                # --- 3. Fecha actual ---
                hoy = pd.Timestamp.now().normalize()

                # --- 4. Calcular días de mora ---
                res['Dias_Mora'] = (hoy - res['Vencimiento']).dt.days

                # --- 5. Reglas de negocio ---
                res['Dias_Mora'] = res['Dias_Mora'].fillna(0)
                res.loc[res['Dias_Mora'] < 0, 'Dias_Mora'] = 0
                res.loc[res[col_monto_act] <= 0, 'Dias_Mora'] = 0
                res['Dias_Mora'] = res['Dias_Mora'].astype(int)

                # --- 1. TOTALIZADOS ---
                st.markdown("### 📊 Resumen de Deuda")
                t1, t2, t3 = st.columns(3)
                with t1:
                    max_mora = int(res['Dias_Mora'].max())
                    st.metric("Días de Mora (Máx)", f"{max_mora} días")
                with t2:
                    total_orig = res[col_monto_orig].sum()
                    st.metric("Suma Monto Original", f"${total_orig:,.2f}")
                with t3:
                    total_actual = res[col_monto_act].sum()
                    st.metric("Total Pendiente Actual", f"${total_actual:,.2f}")

                st.divider()

                # --- 2. DETALLE ---
                st.markdown("### 💳 Detalle de Cuotas")
                columnas_interes = ['ID_cuota', 'Dias_Mora', 'Vencimiento', col_monto_orig, 'ID_orden', 'Tramo_actual', 'Tramo_inicial_Usuario', col_monto_act]
                cols_finales = [c for c in columnas_interes if c in res.columns or c in ['Vencimiento', 'Dias_Mora']]
                
                res_display = res[cols_finales].copy()
                res_display = res_display.sort_values('Vencimiento')
                res_display['Vencimiento'] = res_display['Vencimiento'].dt.strftime('%d/%m/%Y')
                
                st.dataframe(res_display, use_container_width=True, hide_index=True)

                # --- 3. CONTACTO ---
                with st.expander("📞 Ver Datos de Contacto", expanded=True):
                    c1, c2, c3 = st.columns(3)
                    with c1: st.write(f"**Nombre:** {res['Nombre_usuario'].iloc[0] if 'Nombre_usuario' in res.columns else 'N/A'}")
                    with c2: st.write(f"**Email:** {res['Email_usuario'].iloc[0] if 'Email_usuario' in res.columns else 'N/A'}")
                    with c3: st.write(f"**Teléfono:** {res['Telefono'].iloc[0] if 'Telefono' in res.columns else 'N/A'}")
            else:
                st.warning("DNI no encontrado.")
    else:
        st.error(nombre_archivo)
except Exception as e:
    st.error(f"Error: {e}")