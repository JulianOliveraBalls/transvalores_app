import pandas as pd
import gender_guesser.detector as gender

d = gender.Detector(case_sensitive=False)

def predecir_genero(nombre_completo):
    if pd.isnull(nombre_completo):
        return "desconocido"
    
    try:
        partes = nombre_completo.split()
        if len(partes) < 2:
            return "desconocido"
        
        posible_nombre = partes[1]
        genero = d.get_gender(posible_nombre)

        if genero in ["male", "mostly_male"]:
            return "masculino"
        elif genero in ["female", "mostly_female"]:
            return "femenino"
        else:
            genero2 = d.get_gender(partes[0])
            if genero2 in ["male", "mostly_male"]:
                return "masculino"
            elif genero2 in ["female", "mostly_female"]:
                return "femenino"

        return "desconocido"

    except Exception:
        return "desconocido"

def detectar_genero(df):
    if "Nombre" not in df.columns:
        raise ValueError("La columna 'Nombre' no está presente en el archivo.")
    
    df["Género"] = df["Nombre"].apply(predecir_genero)
    return df
