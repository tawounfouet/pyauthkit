"""Deliberate M7 public consumer surface.

The host owns trust configuration and route resolution. This module adds no
authentication decision path and imports no optional framework/provider.
"""

from pyauthkit.application.engine import AuthenticationEngine
from pyauthkit.application.host_context import (
    HostBinding,
    HostRouteNotConfigured,
    HostTrustCatalog,
    TrustedEntryContext,
)
from pyauthkit.composition.registry import (
    AuthenticatorNotConfigured,
    AuthenticatorRegistry,
    AuthenticatorRegistryBuilder,
)
from pyauthkit.configuration.bootstrap import M6Runtime, compose_authentication_engine
from pyauthkit.configuration.models import (
    AuditDeliveryPolicy,
    ConfigurationGeneration,
    ConfigurationRejected,
    ConfigurationSnapshot,
    SourceProvenance,
)
from pyauthkit.domain.evidence import EvidenceMethod, PresentedEvidence
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.result import (
    Authenticated,
    AuthenticationResult,
    AuthError,
    ChallengeRequired,
    Rejected,
)
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.temporal import CorrelationId
from pyauthkit.domain.trust import TrustProfileRef

__all__ = [
    "AuditDeliveryPolicy",
    "Authenticated",
    "AuthenticationEngine",
    "AuthenticationRequest",
    "AuthenticationResult",
    "AuthenticatorNotConfigured",
    "AuthenticatorRegistry",
    "AuthenticatorRegistryBuilder",
    "AuthError",
    "ChallengeRequired",
    "ConfigurationGeneration",
    "ConfigurationRejected",
    "ConfigurationSnapshot",
    "CorrelationId",
    "EvidenceMethod",
    "HostBinding",
    "HostRouteNotConfigured",
    "HostTrustCatalog",
    "M6Runtime",
    "PresentedEvidence",
    "Rejected",
    "SourceProvenance",
    "TrustedEntryContext",
    "TrustedScopeRef",
    "TrustProfileRef",
    "compose_authentication_engine",
]
