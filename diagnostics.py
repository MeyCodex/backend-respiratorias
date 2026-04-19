#DIAGNOSTICOS FIJOS 

MACRO_GRUPOS = [
    "Infecciones Respiratorias Superiores",
    "Infecciones Respiratorias Inferiores",
]

FILAS_FIJAS_DIAGNOSTICOS = [
    "Amigdalitis ",
    "Faringitis",
    "Asma",
    "SBO",
    "BOR",
    "Bronquitis",
    "Bronquiolitis",
    "COVID-19",
    "EPOC",
    "Influenza",
    "IRA Alta",
    "Laringitis",
    "Neumonía",
    "Bronconeumonía",
    "Otitis",
    "Rinitis ALERGICA",
    "Alergias",
    "Rinofaringitis (Resfrío)",
    "Sinusitis / Pansinusitis",
    "Tuberculosis",
    "Otras Causas Respiratorias"
]

#MACRO GRUPO
ATENCIONES_RESPIRATORIAS = set(FILAS_FIJAS_DIAGNOSTICOS)

#DICCIONARIO MAPEO 
MAPEO_PALABRAS_CLAVE = {
    #Asma, SBO y BOR (Síndrome Bronquial Obstructivo Recurrente)
    "asma": "Asma / SBO / BOR",
    "sbo": "Asma / SBO / BOR",
    "bor": "Asma / SBO / BOR",
    "obstructivo": "Asma / SBO / BOR",
    "obstructiva bronquial": "Asma / SBO / BOR",

    #EPOC
    "epoc": "EPOC",
    "obstructiva cronica": "EPOC",
    "obstructiva crónica": "EPOC",

    #Neumonías y Bronconeumonías
    "bronconeumonia": "Neumonía / Bronconeumonía",
    "bronconeumonía": "Neumonía / Bronconeumonía",
    "neumonia": "Neumonía / Bronconeumonía",
    "neumonía": "Neumonía / Bronconeumonía",
    "neumonitis": "Neumonía / Bronconeumonía",

    #Bronquitis y Bronquiolitis
    "bronquiolitis": "Bronquitis / Bronquiolitis",
    "bronquitis": "Bronquitis / Bronquiolitis",

    #COVID-19
    "covid": "COVID-19",

    #Influenza
    "influenza": "Influenza",

    #IRA Alta / Vías Superiores
    "ira alta": "IRA Alta / Infecciones Respiratorias Superiores",
    "vias respiratorias superiores": "IRA Alta / Infecciones Respiratorias Superiores",
    "vías respiratorias superiores": "IRA Alta / Infecciones Respiratorias Superiores",
    "respiratorias altas": "IRA Alta / Infecciones Respiratorias Superiores",

    #Amigdalitis y Faringitis
    "amigdalitis": "Amigdalitis / Faringitis",
    "faringitis": "Amigdalitis / Faringitis",

    #Laringitis
    "laringitis": "Laringitis",

    #Rinofaringitis
    "rinofaringitis": "Rinofaringitis (Resfrío)",
    "resfrio": "Rinofaringitis (Resfrío)",
    "resfrío": "Rinofaringitis (Resfrío)",

    #Sinusitis y Pansinusitis
    "sinusitis": "Sinusitis / Pansinusitis",
    "pansinusitis": "Sinusitis / Pansinusitis",

    #Otitis
    "otitis": "Otitis",

    #Rinitis, Pólipos y Adenoides
    "rinitis": "Rinitis / Alergias",
    "adenoides": "Rinitis / Alergias",
    "polipo": "Rinitis / Alergias",
    "pólipo": "Rinitis / Alergias",

    #Tuberculosis
    "tuberculosis": "Tuberculosis",

    #Otras Causas Respiratorias
    "disnea": "Otras Causas Respiratorias",
    "hipoxia": "Otras Causas Respiratorias",
    "edema pulmonar": "Otras Causas Respiratorias",
    "embolia pulmonar": "Otras Causas Respiratorias",
    "intersticial": "Otras Causas Respiratorias",
    "fibrosis": "Otras Causas Respiratorias",
    "hemoptisis": "Otras Causas Respiratorias",
    "insuficiencia respiratoria": "Otras Causas Respiratorias",
    "insuciencia respiratoria": "Otras Causas Respiratorias", 
    "neumoconiosis": "Otras Causas Respiratorias",
    "tumor maligno": "Otras Causas Respiratorias",
    "bronquiectasia": "Otras Causas Respiratorias",
    "glandula lagrimal": "Otras Causas Respiratorias",
    "glándula lagrimal": "Otras Causas Respiratorias",
    "otras causas respiratorias": "Otras Causas Respiratorias"
}

PALABRAS_EXCLUSION = [
    "cateterizacion", "cateterismo", "sondaje", "procedimiento", 
    "curacion", "retiro de puntos", "administracion de", "instalacion de",
    "por otra persona", "inflingido", "golpe", "patada", "riña",
    "artritis", "calculo", "litiasis"
]

def clasificar_diagnostico_crudo(diagnostico_crudo: str) -> str:
    if not isinstance(diagnostico_crudo, str):
        return "Otras atenciones"
        
    texto_evaluar = diagnostico_crudo.lower()

    for exclusion in PALABRAS_EXCLUSION:
        if exclusion in texto_evaluar:
            return "Otras atenciones"

    texto_con_espacios = f" {texto_evaluar} "

    for palabra_clave, categoria_fija in MAPEO_PALABRAS_CLAVE.items():
        if len(palabra_clave) <= 3:
            if f" {palabra_clave} " in texto_con_espacios:
                return categoria_fija
        else:
            if palabra_clave in texto_evaluar:
                return categoria_fija
            
    return "Otras atenciones"

def obtener_macro_grupo(categoria_fija: str) -> str:
    if categoria_fija in ATENCIONES_RESPIRATORIAS:
        return "Respiratorias"
    else:
        return "Otras atenciones"