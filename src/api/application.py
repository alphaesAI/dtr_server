import importlib
import inspect
import pkgutil
from contextlib import asynccontextmanager
from fastapi import APIRouter, FastAPI
from src.api import routers

def get_routers() -> dict[str, APIRouter]:
    """Dynamically imports and inspects all routers in the routers package."""
    available = {}
    
    # 1. Force-load all modules inside the routers package dynamically
    for _, module_name, _ in pkgutil.iter_modules(routers.__path__):
        importlib.import_module(f"src.api.routers.{module_name}")
        
    # 2. Inspect the loaded modules package just like txtai
    for name, module in inspect.getmembers(routers, inspect.ismodule):
        if hasattr(module, "router") and isinstance(module.router, APIRouter):
            available[name.lower()] = module.router
            
    return available

@asynccontextmanager
async def lifespan(app: FastAPI):
        
    # Automatically register all discovered routers under /fhir
    for name, router in get_routers().items():
        app.include_router(router, prefix="/fhir")
    yield

def create() -> FastAPI:
    app = FastAPI(
        lifespan=lifespan
    )
        
    return app

app = create()