from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import services.data_processor as processor

router = APIRouter(
    prefix="/api/sync",
    tags=["Sincronización Centralizada"]
)

@router.post("/upload")
async def sincronizar_archivo(file: UploadFile = File(...), db: Session = Depends(get_db)):
    filename = file.filename.upper()
    contents = await file.read()

    try:
        if "CAMA" in filename or "OCUPACION" in filename:
            resultado = processor.procesar_reporte_camas(db, contents, file.filename)
        
        elif "URGENCIA" in filename or "DX" in filename:
            resultado = processor.procesar_reporte_urgencia(db, contents, file.filename)
            
        elif any(k in filename for k in ["MONITOREO", "DIARIA", "AGENDA"]):
            raise HTTPException(status_code=501, detail="Procesador de APS aún no implementado.")
            
        else:
            raise ValueError(f"No se reconoce el tipo de archivo: {file.filename}. Debe incluir 'CAMAS' o 'URGENCIA' en el nombre.")

        return {"status": "success", "data": resultado}

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error crítico en el despacho: {str(e)}")