import logging

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.artifact_routes import router as artifact_router
from src.api.routes import router
from src.api.youtube_routes import router as youtube_router
from src.config import get_allowed_origins, validate_environment


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    validate_environment()

    app = FastAPI(title="ClipContext API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_allowed_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)
    app.include_router(youtube_router)
    app.include_router(artifact_router)

    return app


app = create_app()
