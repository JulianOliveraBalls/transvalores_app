import pandas as pd

# Leer el archivo (ajustá el nombre y ruta si es necesario)
df = pd.read_excel('pagos.xlsx')

# Asegurarse de que la columna de fecha esté en formato de fecha
df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True)

# Reemplazar comas por puntos y convertir a numérico (en caso de que haya valores como "35764,08")
df['$ Recaudado Transvalores'] = df['$ Recaudado Transvalores'].astype(str).str.replace(',', '.')
df['$ Recaudado Transvalores'] = pd.to_numeric(df['$ Recaudado Transvalores'], errors='coerce')

# Agrupar por fecha y sumar los montos
df_grouped = df.groupby('Fecha', as_index=False)['$ Recaudado Transvalores'].sum()

# Guardar el resultado en un nuevo archivo
df_grouped.to_excel('pagos_consolidados.xlsx', index=False)

print("Consolidación completada. Archivo generado: pagos_consolidados.xlsx")
