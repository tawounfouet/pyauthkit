"""Host-authoritative, explicit M6 bootstrap. No environment auto-discovery."""

from .api_key_bootstrap import compose_secret_backed_api_key_runtime
from .bootstrap import M6Runtime, compose_authentication_engine
from .jwt_bootstrap import compose_trusted_jwt_runtime
from .models import (
    AuditDeliveryPolicy,
    ConfigurationGeneration,
    ConfigurationSnapshot,
    SourcePolicy,
    SourceProvenance,
)
from .sources import load_approved_configuration

__all__ = [
    "AuditDeliveryPolicy",
    "ConfigurationGeneration",
    "ConfigurationSnapshot",
    "M6Runtime",
    "SourcePolicy",
    "SourceProvenance",
    "compose_authentication_engine",
    "compose_trusted_jwt_runtime",
    "compose_secret_backed_api_key_runtime",
    "load_approved_configuration",
]
