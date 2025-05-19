import pandas as pd
from utils.script_gender import detectar_genero

def reducir_columnas(df):
    columnas_deseadas = [
        "DNI",
        "Apellido y Nombre",
        "Clave Banco de la cuenta",
        "Subsegmento",
        "deuda total del cliente",
        "Localidad",
        "Provincia",
        "grupo del producto",
        "días de mora Total Cliente"
    ]

    columnas_existentes = [col for col in columnas_deseadas if col in df.columns]
    columnas_faltantes = [col for col in columnas_deseadas if col not in df.columns]

    if columnas_faltantes:
        raise ValueError(f"Faltan columnas requeridas: {', '.join(columnas_faltantes)}")

    df = df[columnas_deseadas].copy()

    # deuda / 100
    df["deuda total del cliente"] = df["deuda total del cliente"] / 100

    # Eliminar duplicados por DNI y días de mora
    df = df.drop_duplicates(subset=["DNI", "días de mora Total Cliente"])

    # Tramo de mora
    def clasificar_tramo(dias):
        if dias <= 120:
            return "0 - 120"
        elif dias <= 180:
            return "121 - 180"
        elif dias <= 360:
            return "181 - 360"
        elif dias <= 720:
            return "361 - 720"
        elif dias <= 1080:
            return "721 - 1080"
        elif dias <= 1440:
            return "1081 - 1440"
        elif dias <= 1800:
            return "1441 - 1800"
        else:
            return "Mas 1800"
    
    df["Tramo de Mora"] = df["días de mora Total Cliente"].apply(clasificar_tramo)

    # Rango Etario
    def clasificar_rango_etario(dni):
        try:
            if dni < 19000000:
                return "Mas 60"
            elif 19000000 <= dni < 26000000:
                return "50-60"
            elif 26000000 <= dni < 32000000:
                return "40-50"
            elif 32000000 <= dni < 38000000:
                return "30-40"
            elif 38000000 <= dni < 53000000:
                return "18-30"
            else:
                return "Extranjero"
        except:
            return "Extranjero"

    df["Rango Etario"] = df["DNI"].apply(clasificar_rango_etario)

    # Renombrar y aplicar género
    df = df.rename(columns={"Apellido y Nombre": "Nombre"})
    df = detectar_genero(df)

    return df
