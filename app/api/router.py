import pkgutil
import importlib
from fastapi import APIRouter

api_router = APIRouter()


def load_routes():
    import os
    package = "app.api"
    current_dir = os.path.dirname(__file__)

    for _, module_name, _ in pkgutil.iter_modules([current_dir]):
        if module_name.endswith("_route"):
            module = importlib.import_module(f"{package}.{module_name}")
            if hasattr(module, "router"):
                api_router.include_router(module.router)


load_routes()