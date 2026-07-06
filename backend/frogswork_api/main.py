"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from frogswork_api.archetypes.router import permissions_router, router as archetypes_router
from frogswork_api.auth.router import router as auth_router
from frogswork_api.config import get_jwt_secret
from frogswork_api.db import connect, init_db, is_setup_complete
from frogswork_api.folders.router import router as folders_router
from frogswork_api.helper.router import router as helper_router
from frogswork_api.integrations.linux_users import ensure_superuser_group
from frogswork_api.paths import read_version
from frogswork_api.services.folders import sync_all_folders
from frogswork_api.services.system import ensure_ssh_setting_migrated
from frogswork_api.public.router import router as public_router
from frogswork_api.setup.router import router as setup_router
from frogswork_api.snapshots.router import router as snapshots_router
from frogswork_api.storage.router import router as storage_router
from frogswork_api.system.router import router as system_router
from frogswork_api.users.router import router as users_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    get_jwt_secret()
    try:
        ensure_superuser_group()
    except Exception:
        pass  # group may already exist; sudoers applied on appliance
    try:
        with connect() as conn:
            if is_setup_complete(conn):
                from frogswork_api.services import elevations as elevation_service

                elevation_service.expire_stale_elevations(conn)
                sync_all_folders()
                ensure_ssh_setting_migrated()
    except Exception:
        pass  # first boot or missing sudoers during dev
    yield


app = FastAPI(
    title="FrogsWork File Storage API",
    version=read_version(),
    description="Control plane for the FrogsWork SMB appliance.",
    lifespan=lifespan,
)

app.include_router(setup_router)
app.include_router(public_router)
app.include_router(helper_router)
app.include_router(auth_router)
app.include_router(archetypes_router)
app.include_router(permissions_router)
app.include_router(users_router)
app.include_router(folders_router)
app.include_router(storage_router)
app.include_router(snapshots_router)
app.include_router(system_router)


@app.get("/api/health")
def health():
    return {"status": "ok", "version": read_version()}
