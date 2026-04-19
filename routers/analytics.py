import unicodedata
import pandas as pd
import numpy as np
from datetime import date
from typing import List
from models import OcupacionCamas

def limpiar_servicio_backend(nombre: str) -> str:
    if not isinstance(nombre, str):
        return "Otros"

    n = unicodedata.normalize('NFKD', nombre).encode('ASCII', 'ignore').decode('utf-8').lower()
    
    if "pediatr" in n or "infantil" in n: return "Pediatría"
    if "obstetri" in n or "maternidad" in n or "mujer" in n: return "Obstetricia"
    if "socio" in n: return "Sociosanitarias"
    if "medicina" in n or "adulto" in n: return "Medicina"
    return "Otros"

def generar_historico_bi(registros: List[OcupacionCamas], year: int, agrupacion: str):
    if not registros:
        return {"current_year": [], "previous_year": []}
    
    data = []
    for r in registros:
        data.append({
            "fecha": pd.to_datetime(r.fecha_foto),
            "anio": r.fecha_foto.year,
            "servicio": limpiar_servicio_backend(r.unidad_funcional),
            "ocupadas": r.ocupadas
        })
    
    df = pd.DataFrame(data)
    df_diario = df.groupby(['fecha', 'anio', 'servicio'])['ocupadas'].max().reset_index()

    def procesar_por_anio(df_year, anio_objetivo):
        if df_year.empty:
            return []
            
        df_pivot = df_year.pivot_table(index='fecha', columns='servicio', values='ocupadas', aggfunc='max').fillna(0)
        
        if agrupacion == "diario":
            df_agrupado = df_pivot
            df_agrupado.index = df_agrupado.index.strftime('%d/%m')
            
        elif agrupacion == "semanal":
            df_agrupado = df_pivot.resample('W').max().dropna(how='all')
            meses_cortos = {1:"Ene", 2:"Feb", 3:"Mar", 4:"Abr", 5:"May", 6:"Jun", 7:"Jul", 8:"Ago", 9:"Sep", 10:"Oct", 11:"Nov", 12:"Dic"}
            df_agrupado.index = "S" + df_agrupado.index.isocalendar().week.astype(str) + " (" + df_agrupado.index.month.map(meses_cortos) + ")"
            
        elif agrupacion == "quincenal":
            df_pivot['quincena'] = np.where(df_pivot.index.day <= 15, '1ª', '2ª')
            df_pivot['mes'] = df_pivot.index.month
            df_agrupado = df_pivot.groupby(['mes', 'quincena']).max()
            meses_cortos = {1:"Ene", 2:"Feb", 3:"Mar", 4:"Abr", 5:"May", 6:"Jun", 7:"Jul", 8:"Ago", 9:"Sep", 10:"Oct", 11:"Nov", 12:"Dic"}
            nuevos_indices = []
            for mes, quincena in df_agrupado.index:
                nuevos_indices.append(f"{quincena} {meses_cortos[mes]}")
            df_agrupado.index = nuevos_indices
            
        elif agrupacion == "mensual":
            df_agrupado = df_pivot.resample('ME').max().dropna(how='all')
            meses_cortos = {1:"Ene", 2:"Feb", 3:"Mar", 4:"Abr", 5:"May", 6:"Jun", 7:"Jul", 8:"Ago", 9:"Sep", 10:"Oct", 11:"Nov", 12:"Dic"}
            df_agrupado.index = df_agrupado.index.month.map(meses_cortos)
            
        elif agrupacion == "bimestral":
            df_agrupado = df_pivot.resample('2ME').max().dropna(how='all')
            bimestres = np.ceil(df_agrupado.index.month / 2.0).astype(int)
            df_agrupado.index = "Bim " + bimestres.astype(str)
            
        elif agrupacion == "trimestral":
            df_agrupado = df_pivot.resample('3ME').max().dropna(how='all')
            trimestres = np.ceil(df_agrupado.index.month / 3.0).astype(int)
            df_agrupado.index = "Trim " + trimestres.astype(str)
            
        else:
            df_agrupado = df_pivot

        resultado = []
        for index, row in df_agrupado.iterrows():
            entry = {"name": index}
            for col in df_agrupado.columns:
                if pd.notnull(row[col]):
                    entry[col] = int(row[col])
                else:
                    entry[col] = 0
            resultado.append(entry)
            
        return resultado

    df_current = df_diario[df_diario['anio'] == year].copy()
    df_previous = df_diario[df_diario['anio'] == (year - 1)].copy()

    return {
        "current_year": procesar_por_anio(df_current, year),
        "previous_year": procesar_por_anio(df_previous, year - 1)
    }