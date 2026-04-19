from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from services.data_processor import procesar_reporte_camas
from models import OcupacionCamas

router = APIRouter(
    prefix="/api/camas",
    tags=["Módulo 1: Ocupación de camas"]
)

@router.post("/upload")
async def upload_reporte_camas(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(('.xls', '.xlsx')):
        raise HTTPException(status_code=400, detail="Formato inválido. Solo se admiten archivos Excel (.xls o .xlsx)")

    try:
        contents = await file.read()
        resultado = procesar_reporte_camas(db, contents, file.filename)
        return {"status": "success", "data": resultado}
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno al procesar el archivo: {str(e)}")

@router.get("/registros")
def obtener_registros_camas(
    unidad_funcional: Optional[str] = Query(None, description="Filtrar por unidad (Ej: Medicina, Pediatría)"),
    db: Session = Depends(get_db)
):
    try:
        query = db.query(OcupacionCamas)
        
        if unidad_funcional:
            query = query.filter(OcupacionCamas.unidad_funcional == unidad_funcional)
            
        registros = query.order_by(OcupacionCamas.fecha_foto.asc()).all()
        
        return {"status": "success", "data": registros}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/eliminar/{archivo_origen}")
def eliminar_reporte_camas(archivo_origen: str, db: Session = Depends(get_db)):
    try:
        registros = db.query(OcupacionCamas).filter(OcupacionCamas.archivo_origen == archivo_origen).all()
        
        if not registros:
            raise HTTPException(status_code=404, detail="No se encontraron registros para este archivo.")
            
        for r in registros:
            db.delete(r)
            
        db.commit()
        return {"status": "success", "mensaje": f"Se han eliminado todos los registros del archivo '{archivo_origen}'."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))