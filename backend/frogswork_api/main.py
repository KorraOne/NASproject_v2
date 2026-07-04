"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from frogswork_api.auth.router import router as auth_router
from frogswork_api.config import get_jwt_secret
from frogswork_api.db import init_db
from frogswork_api.paths import read_version
from frogswork_api.setup.router import router as setup_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    get_jwt_secret()
    yield


app = FastAPI(
    title="FrogsWork File Storage API",
    version=read_version(),
    description="Control plane for the FrogsWork SMB appliance.",
    lifespan=lifespan,
)

app.include_router(setup_router)
app.include_router(auth_router)


@app.get("/api/health")
def health():
    return {"status": "ok", "version": read_version()}
