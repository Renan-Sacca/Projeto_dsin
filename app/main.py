import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.database.base import Base
from app.database.connection import engine, SessionLocal
from app.database.seed import seed_database

from app.models import User, Client, Service, Appointment, AppointmentService, SystemConfig

from app.routers import auth, clients, services, appointments, system_config, pages


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("cabeleleila")

settings = get_settings()



@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info(f"  {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info("=" * 60)

    Base.metadata.create_all(bind=engine)
    logger.info("Tabelas do banco de dados criadas/verificadas.")

    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()

    logger.info("Aplicação iniciada com sucesso!")
    logger.info(f"Acesse: http://localhost:8000")
    logger.info("=" * 60)

    yield

    logger.info("Aplicação finalizada.")



app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Sistema de agendamento para o salão Cabeleleila Leila",
    lifespan=lifespan,
    docs_url="/swagger",
    redoc_url=None,
    openapi_url="/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


app.include_router(pages.router)
app.include_router(auth.router)
from app.routers import google_auth
app.include_router(google_auth.router)
app.include_router(clients.router)
app.include_router(services.router)
app.include_router(appointments.router)
app.include_router(system_config.router)



@app.get("/api/health", tags=["Health"])
def health_check():
    """Verifica se a API está funcionando."""
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}
