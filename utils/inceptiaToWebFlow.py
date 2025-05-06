import pandas as pd

def exportar_eventos(df):
    columnas_requeridas = ['Fecha', 'Hora', 'Codigo', 'Estado', 'Telefono']
    for col in columnas_requeridas:
        if col not in df.columns:
            raise ValueError(f"Falta la columna requerida: {col}")

    df_export = pd.DataFrame()
    df_export['FECHA'] = df['Fecha']
    df_export['HORA'] = df['Hora']
    df_export['OPERADOR'] = 'IArtificial'
    df_export['CARPETA'] = df['Codigo']
    df_export['EVENTO'] = df['Estado']
    df_export['COMENTARIOS'] = df['Telefono'].astype(str) + ' SE CONTACTA POR IA. RESULTADO: ' + df['Estado'].astype(str)

    return df_export
