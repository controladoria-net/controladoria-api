import uvicorn
from dotenv import load_dotenv


from src.domain.core.logger import get_logger
from src.infra.http.fastapi.app import create_app

load_dotenv()

logger = get_logger(__name__)
app = create_app()

if __name__ == "__main__":
    logger.info("Iniciando a aplicação ControladorIA API...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
