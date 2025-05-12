import pandas as pd
import gender_guesser.detector as gender

d = gender.Detector(case_sensitive=False)

def predecir_genero(nombre_completo):
    if pd.isnull(nombre_completo):
        return "desconocido"
    
    try:
        partes = nombre_completo.split()
        if len(partes) < 1:
            return "desconocido"
        
        # Intentar con el primer nombre
        genero = d.get_gender(partes[0])
        if genero in ["male", "mostly_male"]:
            return "masculino"
        elif genero in ["female", "mostly_female"]:
            return "femenino"
        
        # Si no es concluyente, intentar con el segundo (si hay)
        if len(partes) > 1:
            genero2 = d.get_gender(partes[1])
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

