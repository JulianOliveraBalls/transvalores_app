import pandas as pd
import requests
import streamlit as st

# Función personalizada para aplanar diccionarios anidados
def flatten_dict(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

# Función para consultar la API por cada CUIL
def consultar_api_certero(cuil, token):
    url = f"https://certero.info/API/V1/Sumario?cuitcuil={cuil}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            st.warning(f"⚠️ Error en consulta para {cuil}: {response.status_code}")
            return None
    except Exception as e:
        st.warning(f"⚠️ Error consultando API para {cuil}: {e}")
        return None

# Función principal que procesa el archivo subido y consulta la API
def procesar_archivo_con_api(df, token, columna_cuil):
    resultados = []

    for _, row in df.iterrows():
        cuil = str(row[columna_cuil])
        data = consultar_api_certero(cuil, token)
        if data:
            flat_data = {"cuil_consultado": cuil}

            for key, value in data.items():
                # Si es un diccionario plano, aplanarlo directamente
                if isinstance(value, dict):
                    flat_data.update(flatten_dict({key: value}))
                # Si es una lista, tratar según el tipo
                elif isinstance(value, list):
                    if key == "celulares":
                        for i, cel in enumerate(value):
                            for k, v in cel.items():
                                flat_data[f"celular_{i}_{k}"] = ", ".join(v) if isinstance(v, list) else v
                    elif key == "telefonosFijos":
                        for i, tel in enumerate(value):
                            for k, v in tel.items():
                                flat_data[f"telefono_{i}_{k}"] = ", ".join(v) if isinstance(v, list) else v
                    elif key == "emails":
                        for i, email in enumerate(value):
                            for k, v in email.items():
                                flat_data[f"email_{i}_{k}"] = ", ".join(v) if isinstance(v, list) else v
                    elif key == "relaciones":
                        flat_data["relaciones_cantidad"] = len(value)
                    elif key == "bcraDeudas":
                        for i, item in enumerate(value):
                            flat_data.update(flatten_dict({f"bcraDeuda_{i}": item}))
                    elif key == "vehiculos":
                        for i, item in enumerate(value):
                            flat_data.update(flatten_dict({f"vehiculo_{i}": item}))
                    elif key == "asignacionesAnses":
                        for i, item in enumerate(value):
                            flat_data.update(flatten_dict({f"asignacion_{i}": item}))
                    elif key == "chequesRechazados":
                        for i, item in enumerate(value):
                            flat_data.update(flatten_dict({f"chequeRechazado_{i}": item}))
                    elif key == "domicilios":
                        if len(value) > 0 and isinstance(value[0], dict):
                            flat_data.update(flatten_dict({"domicilio": value[0]}))
                else:
                    flat_data[key] = value

            resultados.append(flat_data)

    return pd.DataFrame(resultados)
