from sqlalchemy import Column, Integer, String, Date
from database import Base

class OcupacionCamas(Base):
    __tablename__ = "ocupacion_camas"

    id = Column(Integer, primary_key=True, index=True)    
    fecha_foto = Column(Date, index=True, nullable=False)
    unidad_funcional = Column(String, index=True, nullable=False)
    nivel_cuidado = Column(String, index=True)
    #Detalles de la cama
    tipo_paciente = Column(String)
    #Métricas numéricas base
    dotacion = Column(Integer, default=0)
    ocupadas = Column(Integer, default=0)
    fuera_servicio = Column(Integer, default=0)
    disponibles = Column(Integer, default=0)
    complejizadas = Column(Integer, default=0)
    adic_complej = Column(Integer, default=0)
    complejizadas_ci = Column(Integer, default=0)
    adic_complej_ci = Column(Integer, default=0)
    #Metadatos del registro
    ultima_actualizacion = Column(String) 
    archivo_origen = Column(String, nullable=False)