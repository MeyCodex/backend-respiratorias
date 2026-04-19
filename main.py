import sys
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.requests import Request
from database import engine, Base, BASE_PATH
from routers import camas, sync

if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")


Base.metadata.create_all(bind=engine)

uploads_dir = os.path.join(BASE_PATH, "uploads")
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir, exist_ok=True)
    print(f"Carpeta creada: {uploads_dir}")

app = FastAPI(
    title="API SALA IRA",
    description="Backend analítico para procesamiento de atenciones y reportes ENO (DAU/APS)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

app.include_router(sync.router) 
app.include_router(camas.router)

def obtener_ruta_frontend():
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, "dist")

    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")

ruta_dist = obtener_ruta_frontend()

if os.path.exists(ruta_dist):
    @app.middleware("http")
    async def spa_middleware(request: Request, call_next):
        response = await call_next(request)
        
        if response.status_code == 404:
            rutas_api = ["/api", "/docs", "/openapi.json"]
            es_ruta_api = any(request.url.path.startswith(ruta) for ruta in rutas_api)
            if not es_ruta_api:
                return FileResponse(os.path.join(ruta_dist, "index.html"))
        
        return response
    
    app.mount("/", StaticFiles(directory=ruta_dist, html=True), name="spa")
else:
    @app.get("/")
    def root():
        return {
            "status": "online",
            "mensaje": "¡El motor analítico está funcionando, pero falta compilar el frontend!"
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9090)