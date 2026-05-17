"""Dependency injection module.

Exports all service, use case, and auth dependencies for convenient importing.
"""

# Events
from app.deps.events import get_event_bus

# Services
from app.deps.services import (
    get_user_service,
    get_storage_service,
    get_address_service,
    get_company_service,
    get_location_service,
    get_attribute_service,
    get_token_service,
    get_email_service,
)

# Use Cases
from app.deps.use_cases import (
    get_create_user_use_case,
   
)

# Auth
from app.deps.auth import get_current_user

__all__ = [
    # Events
    "get_event_bus",
    # Services
    "get_user_service",
    "get_storage_service",
    "get_address_service",
    "get_company_service",
    "get_location_service",
    "get_attribute_service",
    "get_token_service",
    "get_email_service",
    # Use Cases
    "get_create_user_use_case",
    
    # Auth
    "get_current_user",
]
