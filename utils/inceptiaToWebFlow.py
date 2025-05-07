import pandas as pd

def exportar_eventos(df):
    columnas_requeridas = ['Fecha', 'Hora', 'Codigo', 'Estado', 'Telefono']
    for col in columnas_requeridas:
        if col not in df.columns:
            raise ValueError(f"Falta la columna requerida: {col}")

    # Diccionario de mapeo según imagen
    mapeo_eventos = {
        "Correo de Voz": "NOCONTESTA",
        "Cortó Bot": "AVITITUL",
        "Cortó Llamada": "AVITITUL",
        "Equivocado": "NOCONTESTA",
        "Falleció": "AVITITUL",
        "Interesado - Transferir": "AVITITUL",
        "No Interesado": "AVITITUL",
        "No Titular": "NOCONTESTA",
        "Ocupado": "NOCONTESTA",
        "Titular Cortó": "AVITITUL",
        "Transferir": "AVITITUL"
    }

    df_export = pd.DataFrame()
    df_export['FECHA'] = df['Fecha']
    df_export['HORA'] = df['Hora']
    df_export['OPERADOR'] = 'IArtificial'
    df_export['CARPETA'] = df['Codigo']

    # Aplicar mapeo a la columna Estado para definir EVENTO
    df_export['EVENTO'] = df['Estado'].map(mapeo_eventos).fillna("DESCONOCIDO")

    # Comentario con resultado original
    df_export['COMENTARIOS'] = df['Telefono'].astype(str) + \
        ' SE CONTACTA POR IA. RESULTADO: ' + df['Estado'].astype(str)

    return df_export
