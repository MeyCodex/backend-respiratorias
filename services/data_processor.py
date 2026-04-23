import pandas as pd
import io
import re
import unicodedata
from datetime import datetime
from sqlalchemy.orm import Session
from models import OcupacionCamas, AtencionUrgencia
from constants import DIAGNOSTICOS_RESPIRATORIOS

def normalizar_texto(texto):
    if not texto or not isinstance(texto, str):
        return ""
    return ''.join(
        c for c in unicodedata.normalize('NFKD', texto)
        if unicodedata.category(c) != 'Mn'
    ).lower().strip()

def extraer_edad_anos(edad_str):
    if not edad_str or not isinstance(edad_str, str):
        return 0
    match = re.search(r'(\d+)\s*año', str(edad_str), re.IGNORECASE)
    if match:
        return int(match.group(1))
    match_num = re.search(r'(\d+)', str(edad_str))
    return int(match_num.group(1)) if match_num else 0

def procesar_reporte_camas(db: Session, contents: bytes, filename: str):
    archivo_existente = db.query(OcupacionCamas).filter(OcupacionCamas.archivo_origen == filename).first()
    if archivo_existente:
        raise ValueError(f"ERROR: El archivo '{filename}' ya fue procesado anteriormente.")
    
    file_stream = io.BytesIO(contents)
    df = None
    try:
        df = pd.read_excel(file_stream, engine='openpyxl')
    except Exception:
        try:
            file_stream.seek(0)
            df = pd.read_excel(file_stream, engine='xlrd')
        except Exception as e:
            raise ValueError(f"No se pudo leer el archivo Excel. Detalle: {str(e)}")

    if df is None or df.empty:
        raise ValueError("El archivo está vacío.")

    df.columns = df.columns.astype(str).str.strip()
    columnas_esperadas = [
        'FechaFoto', 'Nivel de cuidado', 'Tipo de paciente', 'Unidad funcional',
        'Dotación', 'Ocupadas', 'Fuera de servicio', 'Disponibles',
        'Complejizadas', 'Adic. complej.', 'Complejizadas CI', 'Adic. complej. CI',
        'Ultima actualización'
    ]
    
    col_map = {}
    for col_esperada in columnas_esperadas:
        for col_real in df.columns:
            if col_esperada.lower() in col_real.lower():
                col_map[col_esperada] = col_real
                break
                
    if 'FechaFoto' not in col_map or 'Unidad funcional' not in col_map:
        raise ValueError("El Excel debe contener obligatoriamente las columnas 'FechaFoto' y 'Unidad funcional'.")

    col_fecha = col_map['FechaFoto']
    col_unidad = col_map['Unidad funcional']
    df = df.dropna(subset=[col_fecha, col_unidad])

    def get_int_val(row, col_name):
        if col_name in col_map:
            val = row[col_map[col_name]]
            if pd.notnull(val):
                try:
                    return int(float(val))
                except ValueError:
                    return 0
        return 0

    def get_str_val(row, col_name):
        if col_name in col_map:
            val = row[col_map[col_name]]
            if pd.notnull(val):
                return str(val).strip()
        return None

    registros_nuevos = []
    for index, row in df.iterrows():
        fecha_raw = row[col_fecha]
        fecha_foto = None
        if isinstance(fecha_raw, datetime):
            fecha_foto = fecha_raw.date()
        else:
            try:
                fecha_foto = pd.to_datetime(fecha_raw, dayfirst=True).date()
            except:
                continue

        dotacion = get_int_val(row, 'Dotación')
        ocupadas = get_int_val(row, 'Ocupadas')
        fuera_servicio = get_int_val(row, 'Fuera de servicio')
        disponibles_calculadas = dotacion - (ocupadas + fuera_servicio)

        registro = OcupacionCamas(
            fecha_foto=fecha_foto,
            unidad_funcional=get_str_val(row, 'Unidad funcional'),
            nivel_cuidado=get_str_val(row, 'Nivel de cuidado'),
            tipo_paciente=get_str_val(row, 'Tipo de paciente'),
            dotacion=dotacion,
            ocupadas=ocupadas,
            fuera_servicio=fuera_servicio,
            disponibles=disponibles_calculadas,
            complejizadas=get_int_val(row, 'Complejizadas'),
            adic_complej=get_int_val(row, 'Adic. complej.'),
            complejizadas_ci=get_int_val(row, 'Complejizadas CI'),
            adic_complej_ci=get_int_val(row, 'Adic. complej. CI'),
            ultima_actualizacion=get_str_val(row, 'Ultima actualización'),
            archivo_origen=filename
        )
        registros_nuevos.append(registro)

    if registros_nuevos:
        db.bulk_save_objects(registros_nuevos)
        db.commit()

    return {
        "mensaje": "Reporte de Ocupación de Camas procesado exitosamente",
        "filas_ingresadas": len(registros_nuevos)
    }

def procesar_reporte_urgencia(db: Session, contents: bytes, filename: str):
    archivo_existente = db.query(AtencionUrgencia).filter(AtencionUrgencia.archivo_origen == filename).first()
    if archivo_existente:
        raise ValueError(f"El archivo '{filename}' ya fue procesado.") 

    file_stream = io.BytesIO(contents)
    try:
        if filename.lower().endswith('.csv'):
            df = pd.read_csv(file_stream, skiprows=8, sep=None, engine='python', encoding='latin1')
        else:
            df = pd.read_excel(file_stream, skiprows=8, engine='openpyxl')
    except Exception as e:
        raise ValueError(f"No se pudo leer el archivo. Detalle: {str(e)}")

    if df is None or df.empty:
        raise ValueError("El archivo no contiene datos válidos después de la fila 8.")

    df.columns = df.columns.astype(str).str.strip()

    columnas_esperadas = [
        'N° Episodio', 'Fecha Admisión', 'Hora Admisión', 'Paciente', 
        'Documento', 'Tipo Documento', 'Edad', 'Sexo', 'Diagnósticos', 
        'Cod. Diag', 'Destino', 'Estado', 'Traslado a otro Establecimiento'
    ]
    
    col_map = {}
    for col_esp in columnas_esperadas:
        esp_norm = normalizar_texto(col_esp).replace("n°", "n").replace(" ", "")
        for col_real in df.columns:
            real_norm = normalizar_texto(col_real).replace("n°", "n").replace(" ", "")
            if esp_norm == real_norm:
                col_map[col_esp] = col_real
                break
                
    if 'Fecha Admisión' not in col_map:
        raise ValueError(f"No se encontró la columna de Fecha. Columnas detectadas: {list(df.columns[:5])}")

    def get_val(r, col_name, default=''):
        real_col = col_map.get(col_name)
        if real_col and real_col in r:
            val = r[real_col]
            return val if pd.notnull(val) else default
        return default

    registros_nuevos = []
    errores_fila = []

    for index, row in df.iterrows():
        try:
            fecha_raw = get_val(row, 'Fecha Admisión', None)
            
            if fecha_raw is None or str(fecha_raw).strip() == '':
                continue

            str_fecha_clean = str(fecha_raw).strip().replace(".", "").replace(",", "")
            if str_fecha_clean.isdigit():
                continue

            if isinstance(fecha_raw, datetime):
                fecha_adm = fecha_raw.date()
            else:
                fecha_str = str(fecha_raw).strip()[:10]
                try:
                    fecha_adm = pd.to_datetime(fecha_str, dayfirst=True).date()
                except:
                    fecha_adm = pd.to_datetime(fecha_str, format="%d/%m/%Y").date()

            diag_original = str(get_val(row, 'Diagnósticos', '')).strip()
            diag_norm = normalizar_texto(diag_original)
            
            grupo_bi = "NO RESPIRATORIO"
            es_resp = False
            
            for grupo, palabras in DIAGNOSTICOS_RESPIRATORIOS.items():
                for palabra in palabras:
                    if palabra in diag_norm:
                        grupo_bi = grupo
                        es_resp = True
                        break

            destino = str(get_val(row, 'Destino', '')).strip().upper()
            traslado = str(get_val(row, 'Traslado a otro Establecimiento', '')).strip()
            es_hosp = "HOSPITALIZA" in destino            
            valor_estado = str(get_val(row, 'Estado', '')).strip().upper()
            edad_str = str(get_val(row, 'Edad', '0'))

            registro = AtencionUrgencia(
                n_episodio=str(get_val(row, 'N° Episodio', f'URG-{index}')),
                fecha_admision=fecha_adm,
                hora_admision=str(get_val(row, 'Hora Admisión', '')),
                paciente=str(get_val(row, 'Paciente', '')),
                documento=str(get_val(row, 'Documento', '')),
                tipo_documento=str(get_val(row, 'Tipo Documento', '')),
                edad_raw=edad_str,
                edad_anos=extraer_edad_anos(edad_str),
                sexo=str(get_val(row, 'Sexo', '')),
                diagnostico=diag_original,
                cod_diag=str(get_val(row, 'Cod. Diag', '')),
                destino=destino,
                visitado=valor_estado,
                traslado_establecimiento=traslado,
                grupo_bi=grupo_bi,
                es_respiratorio=es_resp,
                es_hospitalizado=es_hosp,
                archivo_origen=filename
            )
            registros_nuevos.append(registro)
        except Exception as e:
            errores_fila.append(f"Fila {index}: {str(e)}")
            continue

    if not registros_nuevos:
        motivo = errores_fila[0] if errores_fila else "Las celdas de fecha están vacías o el archivo solo contenía datos no válidos."
        raise ValueError(f"Ninguna fila pudo procesarse. Motivo exacto del rechazo: {motivo}")
    
    if errores_fila:
        print(f"ATENCIÓN ARQUITECTA: Se ignoraron {len(errores_fila)} filas por errores de formato:")
        for error in errores_fila[:20]:
            print(error)

    db.bulk_save_objects(registros_nuevos)
    db.commit()

    return {
        "status": "success",
        "mensaje": f"Reporte procesado: {len(registros_nuevos)} registros.",
        "respiratorios": len([r for r in registros_nuevos if r.es_respiratorio])
    }