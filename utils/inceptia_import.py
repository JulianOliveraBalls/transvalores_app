import pandas as pd

# Leer archivo con el nuevo formato
df = pd.read_excel("inputInceptia.xlsx")  # Cambiar si el nombre del archivo es diferente

# Filtrar teléfonos válidos
df = df[df['Numero'].notna()]

# Eliminar duplicados por Documento + Numero
df = df.drop_duplicates(subset=['Documento', 'Numero'])

# Indexar los teléfonos por cada Documento
df['telefono_index'] = df.groupby('Documento').cumcount() + 1

# Pivotear los teléfonos
telefonos = df.pivot(index='Documento', columns='telefono_index', values='Numero')
telefonos.columns = [f'TELEFONO{i}' for i in telefonos.columns]

# Crear columnas de tipo (CELULAR)
tipos_tel = telefonos.notna().replace({True: 'CELULAR', False: None})
tipos_tel.columns = [f'TIPO_TEL{i}' for i in range(1, len(tipos_tel.columns) + 1)]

# Obtener el apellido único por Documento
datos_unicos = df.drop_duplicates('Documento')[['Documento', 'Apellido']].set_index('Documento')

# Combinar todos los datos
df_final = pd.concat([datos_unicos, telefonos, tipos_tel], axis=1)

# Armar las columnas intercaladas TELEFONOn - TIPO_TELn
max_tel = telefonos.shape[1]
columnas_intercaladas = []
for i in range(1, max_tel + 1):
    columnas_intercaladas.append(f'TELEFONO{i}')
    columnas_intercaladas.append(f'TIPO_TEL{i}')

# Reorden final
columnas_finales = ['Documento', 'Apellido'] + columnas_intercaladas
df_final = df_final.reset_index()[columnas_finales]

# Guardar el resultado
df_final.to_excel("telefonos_sin_duplicados.xlsx", index=False)

print("Archivo generado: telefonos_sin_duplicados.xlsx")
