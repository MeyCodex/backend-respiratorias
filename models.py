from sqlalchemy import Boolean, Column, Integer, String, Date
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

class AtencionUrgencia(Base):
    __tablename__ = "atenciones_urgencia"
    
    id = Column(Integer, primary_key=True, index=True)
    n_episodio = Column(String, index=True)   
    fecha_admision = Column(Date)
    hora_admision = Column(String)
    paciente = Column(String)
    documento = Column(String)
    tipo_documento = Column(String, nullable=True) 
    edad_raw = Column(String) 
    edad_anos = Column(Integer)
    sexo = Column(String)
    diagnostico = Column(String)
    cod_diag = Column(String)
    destino = Column(String)
    visitado = Column(String)
    traslado_establecimiento = Column(String)
    grupo_bi = Column(String) 
    es_respiratorio = Column(Boolean, default=False)
    es_hospitalizado = Column(Boolean, default=False) 
    archivo_origen = Column(String)