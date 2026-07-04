"""FastAPI application entrypoint. Routes and business logic land in M2+."""

from fastapi import FastAPI

from frogswork_api.paths import read_version

app = FastAPI(
    title="FrogsWork File Storage API",
    version=read_version(),
    description="Control plane for the FrogsWork SMB appliance.",
)


@app.get("/api/health")
def health():
    return {"status": "ok", "version": read_version()}
