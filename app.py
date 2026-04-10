import streamlit as st
import pandas as pd
import io
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Calculador Cashea",
    layout="wide",
    page_icon="💰"
)

# --- CONFIGURACIÓN DRIVE ---
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
    
    nombre_mes_buscado = meses[ahora.month].lower() # Ejemplo: "abril"

    try:
        # --- PASO 1: Listar carpetas en la Raíz ---
        q_folders = f"'{root_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        res_folder = service.files().list(q=q_folders, fields="files(id, name)").execute()
        all_folders = res_folder.get('files', [])
        
        # Log de carpetas encontradas para depurar
        nombres_carpetas = [f['name'] for f in all_folders]
        
        # Buscar la carpeta que contenga el mes (insensible a mayúsculas)
        target_folder = next((f for f in all_folders if nombre_mes_buscado in f['name'].lower()), None)
        
        if not target_folder:
            error_msg = f"❌ No se encontró carpeta para '{meses[ahora.month]}'. "
            error_msg += f"En la raíz ({root_id}) solo veo estas carpetas: {', '.join(nombres_carpetas) if nombres_carpetas else 'NINGUNA'}. "
            error_msg += "Revisa si el Service Account tiene permisos en la carpeta raíz."
            return None, error_msg

        # --- PASO 2: Listar archivos dentro de la carpeta encontrada ---
        folder_id = target_folder['id']
        q_files = f"'{folder_id}' in parents and trashed = false"
        res_files = service.files().list(q=q_files, fields="files(id, name, mimeType)").execute()
        all_files = res_files.get('files', [])
        
        nombres_archivos = [f"{f['name']} ({f['mimeType']})" for f in all_files]
        
        # Buscar el archivo de Stock
        target_file = next((f for f in all_files if "stock" in f['name'].lower()), None)

        if not target_file:
            error_msg = f"📂 Carpeta '{target_folder['name']}' encontrada, pero no hay archivos de 'Stock'. "
            error_msg += f"Contenido actual: {', '.join(nombres_archivos) if nombres_archivos else 'VACÍA'}."
            return None, error_msg

        # --- PASO 3: Descarga y validación de formato ---
        # Si el archivo es un Google Sheet (nativo), lanzamos un aviso específico
        if target_file['mimeType'] == 'application/vnd.google-apps.spreadsheet':
            return None, f"⚠️ El archivo '{target_file['name']}' es un Google Sheet nativo. Debe ser un .csv para que este código funcione."

        file_id = target_file['id']
        file_name = target_file['name']
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
        return None, f"🔥 Error crítico de API o Conexión: {str(e)}"

# --- ESTILO CSS PERSONALIZADO ---
st.markdown(
    """
    <style>
        .stApp {
            background-color: white;
        }
        /* Contenedor Principal del Header */
        .header-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 20px;
            margin-bottom: 25px;
            border-bottom: 1px solid #f0f2f6;
        }
        /* Logo Izquierdo (Cashea) */
        .logo-left {
            height: 40px;
            object-fit: contain;
        }
        /* Título Centralizado */
        .title-center {
            flex-grow: 1;
            text-align: center;
            font-size: 26px !important;
            font-weight: 800;
            color: #1A1C1E;
            margin: 0;
        }
        /* Logo Derecho (Personalizado) */
        .logo-right {
            height: 55px;
            object-fit: contain;
        }
        /* Ajuste para dispositivos móviles */
        @media (max-width: 768px) {
            .header-container {
                flex-direction: column;
                text-align: center;
                gap: 10px;
            }
            .logo-left, .logo-right { height: 40px; }
        }
    </style>
    """,
    unsafe_allow_html=True
)

# --- RENDERIZADO DEL HEADER ---
st.markdown(
    f"""
    <div class="header-container">
        <img src="https://cdn.prod.website-files.com/632db6924fcc7661685adfa8/649e418aa37a8933337ef18d_cashea-v3.png" class="logo-left">
        <h1 class="title-center">💰 Calculador Cashea</h1>
        <img src="https://app.mailzilla.com.ar/frontend/assets/files/customer/yf195vfqvc266/Gemini_Generated_Image_avzdunavzdunavzd__1_-removebg-preview.png" class="logo-right">
    </div>
    """,
    unsafe_allow_html=True
)

# --- LÓGICA DE DATOS ---
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

                # Hoy (ajustado a la fecha del sistema)
                hoy = pd.Timestamp.now().normalize()

                col_monto_act = 'Monto_por_cobrar_actual'
                col_monto_orig = 'Monto_por_cobrar' if 'Monto_por_cobrar' in res.columns else 'Monto'

                # --- LÓGICA DE MORA ---
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

                # --- 1. TOTALIZADOS ---
                st.markdown("### 📊 Resumen de Deuda")
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

                # --- 2. DETALLE DE CUOTAS ---
                st.markdown("### 💳 Detalle de Cuotas")
                columnas_posibles = ['ID_cuota', 'Dias_Mora', 'Vencimiento', col_monto_orig, 'ID_orden', 'Tramo_actual', col_monto_act]
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
    st.error(f"Error de ejecución: {e}")