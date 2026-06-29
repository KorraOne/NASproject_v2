"""FastAPI application entrypoint. Routes and business logic land in M2+."""

from fastapi import FastAPI

app = FastAPI(
    title="FrogsWork File Storage API",
    version="0.0.0-dev",
    description="Control plane for the FrogsWork SMB appliance.",
)
