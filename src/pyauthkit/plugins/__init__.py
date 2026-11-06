"""M7 explicit metadata discovery and host-authorized plugin admission."""

from .admission import PluginGrant, load_approved_authenticators
from .discovery import (
    ENTRY_POINT_GROUP,
    SPI_MAJOR,
    PluginAdmissionRejected,
    PluginCandidate,
    discover_authenticator_plugins,
)
from .lifecycle import activate_approved_authenticators

__all__ = [
    "ENTRY_POINT_GROUP",
    "SPI_MAJOR",
    "PluginAdmissionRejected",
    "PluginCandidate",
    "PluginGrant",
    "discover_authenticator_plugins",
    "load_approved_authenticators",
    "activate_approved_authenticators",
]
