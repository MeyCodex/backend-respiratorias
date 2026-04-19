import pandas as pd
import io
from datetime import datetime
from sqlalchemy.orm import Session
from models import OcupacionCamas

def procesar_reporte_camas(db: Session, contents: bytes, filename: str):
    #Validación de archivo único
    archivo_existente = db.query(OcupacionCamas).filter(OcupacionCamas.archivo_origen == filename).first()
    if archivo_existente:
        raise ValueError(f"ERROR: El archivo '{filename}' ya fue procesado anteriormente. Cámbiale el nombre si es un archivo nuevo.")
    
    #Leer el archivo excel
    file_stream = io.BytesIO(contents)
    df = None
    try:
        df = pd.read_excel(file_stream, engine='openpyxl')
    except Exception:
        try:
            file_stream.seek(0)
            df = pd.read_excel(file_stream, engine='xlrd')
        except Exception as e:
            raise ValueError(f"No se pudo leer el archivo Excel. Verifica que el formato sea correcto. Detalle: {str(e)}")

    if df is None or df.empty:
        raise ValueError("El archivo está vacío o no contiene datos válidos.")

    #Estandarizar nombres de columnas
    df.columns = df.columns.astype(str).str.strip()

    #Mapeo de columnas
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
                
    #Validar columnas
    if 'FechaFoto' not in col_map or 'Unidad funcional' not in col_map:
        raise ValueError("El Excel debe contener obligatoriamente las columnas 'FechaFoto' y 'Unidad funcional'.")

    col_fecha = col_map['FechaFoto']
    col_unidad = col_map['Unidad funcional']

    #Limpieza de datos
    df = df.dropna(subset=[col_fecha, col_unidad])

    #Helpers para extraer datos seguros
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

    #Iterar y procesar cada fila
    for index, row in df.iterrows():
        #Procesar fecha
        fecha_raw = row[col_fecha]
        fecha_foto = None
        
        if isinstance(fecha_raw, datetime):
            fecha_foto = fecha_raw.date()
        else:
            try:
                fecha_foto = pd.to_datetime(fecha_raw, dayfirst=True).date()
            except Exception:
                continue

        #Extraer métricas
        dotacion = get_int_val(row, 'Dotación')
        ocupadas = get_int_val(row, 'Ocupadas')
        fuera_servicio = get_int_val(row, 'Fuera de servicio')
        disponibles_calculadas = dotacion - (ocupadas + fuera_servicio)

        #Crear registro para la DB
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

    #Guardado masivo
    if registros_nuevos:
        db.bulk_save_objects(registros_nuevos)
        db.commit()

    return {
        "mensaje": "Reporte de Ocupación de Camas procesado exitosamente",
        "filas_ingresadas": len(registros_nuevos)
    }