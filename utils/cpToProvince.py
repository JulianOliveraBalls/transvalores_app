import pandas as pd
import requests
from bs4 import BeautifulSoup

def obtener_provincia(cp):
    url = f"https://codigo-postal.co/argentina/cp/{cp}/"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None
        soup = BeautifulSoup(response.text, 'html.parser')

        # Opción 1: buscar en tabla
        tabla = soup.find('table')
        if tabla:
            primer_td = tabla.find('td')
            if primer_td:
                return primer_td.text.strip()

        # Opción 2: buscar en <h3> dentro de div.question
        h3 = soup.find('div', class_='question')
        if h3:
            h3_tag = h3.find('h3')
            if h3_tag and " en " in h3_tag.text.lower():
                texto = h3_tag.text
                provincia = texto.split(" en ")[-1].strip()
                return provincia

        # Opción 3: buscar segundo <em> dentro del <p> del div principal
        p_tag = soup.find('div', class_='breadcrumbs_div').find_next_sibling('p')
        if p_tag:
            em_tags = p_tag.find_all('em')
            if len(em_tags) >= 2:
                return em_tags[1].text.strip()

    except Exception as e:
        print(f"Error en CP {cp}: {e}")
        return None

def procesar_excel(ruta_archivo):
    df = pd.read_excel(ruta_archivo)
    if 'cp' not in df.columns:
        raise ValueError("El archivo debe contener una columna llamada 'cp'")
    
    df['provincia'] = df['cp'].astype(str).apply(lambda cp: obtener_provincia(cp))
    
    return df

# Ruta al archivo Excel de entrada
archivo_entrada = "codigos_postales.xlsx"
archivo_salida = "codigos_postales_con_provincia.xlsx"

# Procesar y guardar
df_resultado = procesar_excel(archivo_entrada)
df_resultado.to_excel(archivo_salida, index=False)
print(f"Archivo guardado en: {archivo_salida}")
