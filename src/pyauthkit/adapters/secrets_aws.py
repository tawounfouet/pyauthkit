"""Optional AWS Secrets Manager adapter for the M6 SecretResolver port.

[ARCH: Ports & Adapters] [SECURITY: pinned secret identity + version]
The host constructs the AWS SDK client and provides an allowlist of complete
resource ARNs. No SDK session, environment credentials, endpoint or default
secret is created/discovered by PyAuthKit.

This is not a production AWS/IAM qualification: deployment egress, IAM, KMS,
TLS and retry policy remain the responsibility of the host. The boto3 client
is synchronous and executed in a worker thread: cancelling the async caller
cannot cancel an already running AWS SDK request. Bound transport retries,
connect/read timeouts and concurrency in the host. Never log SDK exceptions.
"""

from __future__ import annotations

import asyncio
import re
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Never, Protocol

from pyauthkit.configuration.secrets import SecretResolutionUnavailable
from pyauthkit.domain.secret import SecretRef

# Require a complete ARN. Partial ARNs, names and endpoints are never accepted.
_ARN = re.compile(
    r"arn:(aws|aws-us-gov|aws-cn):secretsmanager:([a-z0-9-]+):(\d{12}):"
    r"secret:([A-Za-z0-9/_+=.@-]+)\Z"
)
_VERSION = re.compile(r"[A-Za-z0-9-]{32,64}\Z")
_PROVIDER = "aws-secrets-manager"
_MAX_MATERIAL_BYTES = 65536


class SecretsManagerClient(Protocol):
    """Structural interface of a host-created boto3 Secrets Manager client."""

    def get_secret_value(
        self, *, SecretId: str, VersionId: str, VersionStage: str
    ) -> Mapping[str, object]: ...


@dataclass(frozen=True, slots=True, repr=False)
class ApprovedAwsSecret:
    """Host-owned exact ARN, never assembled from a client request or JWT."""

    arn: str

    def __post_init__(self) -> None:
        if type(self.arn) is not str or len(self.arn) > 2048 or _ARN.fullmatch(self.arn) is None:
            raise ValueError("invalid approved AWS secret ARN")

    def __repr__(self) -> str:
        return "ApprovedAwsSecret(<redacted host-owned ARN>)"


class AwsSecretsManagerResolver:
    """Uncached, version-pinned AWS SecretBinary reader for approved references.

    The binding is a copied immutable mapping. AWS access must additionally
    be constrained through a host-owned IAM and KMS policy.
    """

    __slots__ = ("_client", "_bindings")

    _client: SecretsManagerClient
    _bindings: Mapping[SecretRef, ApprovedAwsSecret]

    def __init__(
        self,
        *,
        client: SecretsManagerClient,
        bindings: Mapping[SecretRef, ApprovedAwsSecret],
        account_id: str,
        region: str,
        partition: str = "aws",
    ) -> None:
        if (
            not callable(getattr(client, "get_secret_value", None))
            or not isinstance(bindings, Mapping)
            or not 1 <= len(bindings) <= 128
            or type(account_id) is not str
            or not re.fullmatch(r"\d{12}", account_id)
            or type(region) is not str
            or not re.fullmatch(r"[a-z0-9-]{4,32}", region)
            or partition not in ("aws", "aws-us-gov", "aws-cn")
        ):
            raise ValueError("invalid AWS secret adapter admission")
        checked: dict[SecretRef, ApprovedAwsSecret] = {}
        used: set[tuple[str, str]] = set()
        for ref, location in bindings.items():
            if (
                not isinstance(ref, SecretRef)
                or ref.provider != _PROVIDER
                or ref.purpose != "verify"
                or _VERSION.fullmatch(ref.version) is None
                or not isinstance(location, ApprovedAwsSecret)
            ):
                raise ValueError("unapproved AWS secret reference")
            match = _ARN.fullmatch(location.arn)
            if match is None or match.groups()[:3] != (partition, region, account_id):
                raise ValueError("AWS secret account or region mismatch")
            unique = (location.arn, ref.version)
            if unique in used:
                raise ValueError("cross-scope AWS secret alias is not admitted")
            used.add(unique)
            checked[ref] = location
        # Only explicitly mapped logical references can reach this client.
        object.__setattr__(self, "_client", client)
        object.__setattr__(self, "_bindings", MappingProxyType(checked))

    def __setattr__(self, _name: str, _value: object) -> Never:
        raise AttributeError("approved AWS secret bindings are immutable")

    def __repr__(self) -> str:
        return "AwsSecretsManagerResolver(<approved, uncached, redacted>)"

    async def resolve(self, *, ref: SecretRef, purpose: str) -> bytes:
        """Never fall back to AWSCURRENT alone or a previous key version."""
        if (
            not isinstance(ref, SecretRef)
            or ref.purpose != purpose
            or purpose != "verify"
            or ref not in self._bindings
        ):
            raise SecretResolutionUnavailable("secret access denied")
        arn = self._bindings[ref].arn
        try:
            response = await asyncio.to_thread(
                self._client.get_secret_value,
                SecretId=arn,
                VersionId=ref.version,
                VersionStage="AWSCURRENT",
            )
            if not isinstance(response, Mapping):
                raise SecretResolutionUnavailable("secret unavailable")
            stages = response.get("VersionStages")
            material = response.get("SecretBinary")
            if (
                response.get("ARN") != arn
                or response.get("VersionId") != ref.version
                or type(stages) is not list
                or "AWSCURRENT" not in stages
                or "SecretString" in response
                or type(material) is not bytes
                or not 1 <= len(material) <= _MAX_MATERIAL_BYTES
            ):
                raise SecretResolutionUnavailable("secret unavailable")
            return material
        except asyncio.CancelledError:
            raise
        except Exception:
            # AWS errors might include resource metadata or request arguments.
            raise SecretResolutionUnavailable("secret unavailable") from None
