"""M7 explicit metadata discovery and host-authorized plugin admission."""

from .admission import PluginGrant, load_approved_authenticators
from .discovery import (
    ENTRY_POINT_GROUP,
    ENTRY_POINT_GROUP_V2,
    SPI_MAJOR,
    SPI_MAJOR_V2,
    PluginAdmissionRejected,
    PluginCandidate,
    discover_authenticator_plugins,
)
from .lifecycle import activate_approved_authenticators
from .services import PluginHostServices

__all__ = [
    "ENTRY_POINT_GROUP",
    "ENTRY_POINT_GROUP_V2",
    "SPI_MAJOR",
    "SPI_MAJOR_V2",
    "PluginAdmissionRejected",
    "PluginCandidate",
    "PluginGrant",
    "PluginHostServices",
    "discover_authenticator_plugins",
    "load_approved_authenticators",
    "activate_approved_authenticators",
]
