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
st.set_page_config(
    page_title="Calculador Cashea",
    layout="wide",
    page_icon="💰"
)

# --- ESTILO Y LOGO ---
st.markdown(
    f"""
    <style>
        .stApp {{
            background-color: white;
        }}
        .logo-container {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }}
        .logo {{
            height: 80px;
        }}
        .title {{
            text-align: center;
            color: #333;
        }}
        .highlight {{
            background-color: #fdfa3d;
            padding: 0.5rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }}
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    f"""
    <div class="logo-container">
        <img src="https://via.placeholder.com/200x80?text=Logo+1" class="logo">
        <h1 class="title">💰 Calculador Cashea</h1>
        <img src="https://via.placeholder.com/200x80?text=Logo+2" class="logo">
    </div>
    """,
    unsafe_allow_html=True
)

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
                # --- PROCESAMIENTO DE FECHAS ---
                col_fecha = 'Fecha_Pago'
                res['Vencimiento'] = pd.to_datetime(
                    res[col_fecha].astype(str).str.split(' ').str[0],
                    format='%Y-%m-%d',
                    errors='coerce'
                )

                # Hoy: 07/04/2026
                hoy = pd.Timestamp.now().normalize()

                col_monto_act = 'Monto_por_cobrar_actual'
                col_monto_orig = 'Monto_por_cobrar' if 'Monto_por_cobrar' in res.columns else 'Monto'

                # --- LÓGICA DE MORA (EXCLUYE PAGADO/CANCELADA) ---
                def calcular_mora(vto, monto_pendiente, tramo_actual):
                    if pd.isnull(vto) or monto_pendiente <= 0 or tramo_actual in ['Pagado', 'Cancelada']:
                        return 0
                    vto_puro = vto.normalize()
                    if vto_puro < hoy:
                        return (hoy - vto_puro).days
                    return 0

                res['Dias_Mora'] = res.apply(
                    lambda x: calcular_mora(x['Vencimiento'], x[col_monto_act], x['Tramo_actual']),
                    axis=1
                )

                # --- 1. TOTALIZADOS (FORMATO USD) ---
                st.markdown("### 📊 Resumen de Deuda", unsafe_allow_html=True)
                t1, t2, t3 = st.columns(3)
                with t1:
                    max_mora = int(res['Dias_Mora'].max())
                    st.metric("Días de Mora (Máx)", f"{max_mora} días")
                with t2:
                    total_orig = res[col_monto_orig].sum()
                    st.metric("Suma Monto Original", f"USD {total_orig:,.2f}")
                with t3:
                    total_actual = res[col_monto_act].sum()
                    st.metric("Total Pendiente Actual", f"USD {total_actual:,.2f}")

                st.divider()

                # --- 2. DETALLE (TODAS LAS CUOTAS, INCLUYENDO PAGADAS/CANCELADAS) ---
                st.markdown("### 💳 Detalle de Cuotas", unsafe_allow_html=True)
                columnas_posibles = ['ID_cuota', 'Dias_Mora', 'Vencimiento', col_monto_orig, 'ID_orden', 'Tramo_actual', 'Tramo_inicial_Usuario', col_monto_act]
                cols_presentes = [c for c in columnas_posibles if c in res.columns or c in ['Vencimiento', 'Dias_Mora']]

                res_display = res[cols_presentes].copy()
                res_display['Vencimiento'] = res_display['Vencimiento'].dt.strftime('%d/%m/%Y')
                res_display[col_monto_orig] = res_display[col_monto_orig].apply(lambda x: f"USD {x:,.2f}")
                res_display[col_monto_act] = res_display[col_monto_act].apply(lambda x: f"USD {x:,.2f}")

                st.dataframe(res_display.sort_values('Dias_Mora', ascending=False), use_container_width=True, hide_index=True)

                # --- 3. CONTACTO ---
                with st.expander("📞 Ver Datos de Contacto", expanded=True):
                    c1, c2, c3 = st.columns(3)
                    with c1: st.write(f"**Nombre:** {res['Nombre_usuario'].iloc[0]}")
                    with c2: st.write(f"**Email:** {res['Email_usuario'].iloc[0]}")
                    with c3: st.write(f"**Teléfono:** {res['Telefono'].iloc[0]}")
            else:
                st.warning("DNI no encontrado.")
    else:
        st.error(nombre_archivo)
except Exception as e:
    st.error(f"Error: {e}")