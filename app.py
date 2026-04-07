import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Configuración básica
st.set_page_config(page_title="Consulta de Mora Transvalores", layout="wide")

def get_data():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    try:
        # 1. Intentar cargar credenciales desde st.secrets
        if "gcp_service_account" not in st.secrets:
            st.error("❌ El bloque [gcp_service_account] no se encuentra en los Secrets de Streamlit.")
            return pd.DataFrame()
            
        creds_dict = dict(st.secrets["gcp_service_account"])
        # Aseguramos que la private_key no tenga problemas de escapes
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # 2. Intentar abrir el archivo
        # REEMPLAZA ESTO por el nombre exacto de tu archivo
        nombre_sheet = "TU_NOMBRE_DE_ARCHIVO_AQUI" 
        sheet = client.open(nombre_sheet).sheet1 
        
        # 3. Traer datos
        data = sheet.get_all_records()
        return pd.DataFrame(data)

    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"❌ No se encontró el archivo: '{nombre_sheet}'. Revisá el nombre o compartilo con el email de la cuenta de servicio.")
    except Exception as e:
        st.error(f"⚠️ Error detallado: {e}")
    return pd.DataFrame()

try:
    df = get_data()

    if not df.empty:
        # Input del usuario
        cedula = st.text_input("Ingrese número de Cédula / DNI:", placeholder="Ej: 12345678")

        if cedula:
            # Limpieza y filtrado
            df['#Cedula'] = df['#Cedula'].astype(str).str.strip()
            res = df[df['#Cedula'] == str(cedula)].copy()

            if not res.empty:
                st.info(f"Cliente: **{res['Nombre usuario'].iloc[0]}**")
                
                # --- PROCESAMIENTO DE FECHAS Y MORA ---
                # Convertimos 'Fecha Pago' (Vencimiento) a fecha
                res['Fecha Pago'] = pd.to_datetime(res['Fecha Pago'], dayfirst=True, errors='coerce')
                hoy = datetime.now()

                # Calculamos mora solo si tiene deuda y la fecha ya pasó
                def calcular_dias(fila):
                    if fila['Monto por cobrar actual'] > 0 and pd.notnull(fila['Fecha Pago']):
                        if fila['Fecha Pago'] < hoy:
                            return (hoy - fila['Fecha Pago']).days
                    return 0

                res['Días de Mora'] = res.apply(calcular_dias, axis=1)

                # --- MOSTRAR RESULTADOS ---
                # Seleccionamos las columnas que pidió el usuario
                columnas_ver = [
                    'ID cuota', '#Cuota', 'Fecha Pago', 
                    'Monto por cobrar actual', 'Días de Mora', 'Tramo actual'
                ]
                
                # Formatear la tabla para que se vea limpia
                tabla_final = res[columnas_ver].rename(columns={'Fecha Pago': 'Vto'})
                
                # Mostrar métrica de deuda total
                deuda_total = tabla_final['Monto por cobrar actual'].sum()
                st.metric("Deuda Total Pendiente", f"${deuda_total:,.2f}")

                # Tabla interactiva
                st.dataframe(tabla_final.sort_values('Vto'), use_container_width=True)
            else:
                st.warning("No se encontró deuda pendiente para esa cédula.")
    
except Exception as e:
    st.error(f"Error: {e}")