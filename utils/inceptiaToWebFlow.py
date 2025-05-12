import pandas as pd

def exportar_eventos(df):
    columnas_requeridas = ['Fecha', 'Hora', 'Codigo', 'Estado', 'Telefono']
    for col in columnas_requeridas:
        if col not in df.columns:
            raise ValueError(f"Falta la columna requerida: {col}")

    prioridad_estado = {
        "Interesado - Transferir": 1,
        "Transferir": 2,
        "Titular Cortó": 3,
        "Cortó Bot": 4,
        "Cortó Llamada": 5,
        "Falleció": 6,
        "No Interesado": 7
    }

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
        "Indefinido": "NOCONTESTA",
        "Titular Cortó": "AVITITUL",
        "Transferir": "AVITITUL"
    }

    # Reformat fecha
    df['Fecha'] = pd.to_datetime(df['Fecha']).dt.strftime('%d/%m/%Y')

    # Aplicar mapeo y prioridad
    df['EVENTO'] = df['Estado'].map(mapeo_eventos).fillna("DESCONOCIDO")
    df['PRIORIDAD'] = df['Estado'].map(prioridad_estado)
    df['OPERADOR'] = 'IArtificial'
    df.rename(columns={'Fecha': 'FECHA', 'Hora': 'HORA', 'Codigo': 'CARPETA'}, inplace=True)

    df['COMENTARIOS'] = df['Telefono'].astype(str) + ' SE CONTACTA POR IA. RESULTADO: ' + df['Estado'].astype(str)

    def consolidar(grupo):
        if all(grupo['EVENTO'] == "NOCONTESTA"):
            unicos = grupo[['Telefono', 'Estado']].drop_duplicates()
            telefonos = unicos['Telefono'].astype(str).tolist()
            estados = unicos['Estado'].astype(str).tolist()
            comentarios = " - ".join(telefonos) + " NO SE CONTACTA POR IA. RESULTADO: " + " - ".join(estados)
            return pd.Series({
                'FECHA': grupo.iloc[0]['FECHA'],
                'HORA': grupo.iloc[0]['HORA'],
                'OPERADOR': 'IArtificial',
                'CARPETA': grupo.iloc[0]['CARPETA'],
                'EVENTO': 'NOCONTESTA',
                'COMENTARIOS': comentarios
            })
        else:
            grupo_avititul = grupo[grupo['EVENTO'] == 'AVITITUL'].copy()
            if grupo_avititul.empty:
                fila = grupo.iloc[0]
            else:
                grupo_avititul = grupo_avititul.sort_values(by='PRIORIDAD', na_position='last')
                fila = grupo_avititul.iloc[0]

            return pd.Series({
                'FECHA': fila['FECHA'],
                'HORA': fila['HORA'],
                'OPERADOR': 'IArtificial',
                'CARPETA': fila['CARPETA'],
                'EVENTO': fila['EVENTO'],
                'COMENTARIOS': fila['COMENTARIOS']
            })

    df_export = df.groupby('CARPETA', as_index=False).apply(consolidar).reset_index(drop=True)

    # (Opcional) Filtrar filas con evento desconocido
    df_export = df_export[df_export['EVENTO'] != "DESCONOCIDO"]

    return df_export

