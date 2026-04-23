from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import AtencionUrgencia
from services.data_processor import procesar_reporte_urgencia

router = APIRouter(prefix="/api/urgencias", tags=["Urgencias"])

@router.post("/upload")
async def upload_urgencias(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="El archivo debe ser un Excel (.xlsx o .xls)")
    
    contents = await file.read()
    try:
        resultado = procesar_reporte_urgencia(db, contents, file.filename)
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("/registros")
def get_urgencias(db: Session = Depends(get_db)):
    registros = db.query(AtencionUrgencia).all()
    return {"data": registros}

@router.delete("/eliminar/{archivo_origen}")
def delete_urgencias(archivo_origen: str, db: Session = Depends(get_db)):
    db.query(AtencionUrgencia).filter(AtencionUrgencia.archivo_origen == archivo_origen).delete()
    db.commit()
    return {"mensaje": f"Registros del archivo {archivo_origen} eliminados correctamente"}