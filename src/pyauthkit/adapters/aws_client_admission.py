"""Strict, explicit AWS SDK client profile admission for M6 secret reads.

[SECURITY: Transport boundary] A correctly pinned SecretRef does not itself
attest the endpoint, retry policy or timeouts of a host-created boto3 client.
This helper checks a botocore client profile before the low-level resolver is
constructed. It does NOT attest IAM identity, real TLS network routing, KMS
permissions, proxy environment, VPC endpoint rules or the remote AWS account.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from typing import Protocol

from pyauthkit.domain.secret import SecretRef

from .secrets_aws import ApprovedAwsSecret, AwsSecretsManagerResolver, SecretsManagerClient

_REGION = re.compile(r"[a-z]{2}(?:-[a-z]+)+-[1-9][0-9]?\Z")


class AwsClientAdmissionRejected(ValueError):
    """Sanitized refusal of an unexpected SDK client profile."""


class AwsClientProfile(Protocol):
    """Minimal host-side client metadata contract, without importing boto3."""

    @property
    def meta(self) -> object: ...


def _bounded_timeout(value: object) -> bool:
    return (
        type(value) in (int, float)
        and math.isfinite(value)
        and 0 < value <= 2
    )


def admit_aws_client_profile(
    client: object,
    *,
    region: str,
    partition: str = "aws",
) -> None:
    """Reject an SDK client that could contact an unapproved AWS endpoint.

    The host must also enforce trusted credentials, IAM least privilege, KMS,
    DNS/TLS, VPC endpoint policies and worker concurrency. The SDK's proxy
    environment and future mutable client internals are not attested here.
    """
    if (
        type(region) is not str
        or _REGION.fullmatch(region) is None
        or partition not in ("aws", "aws-us-gov", "aws-cn")
    ):
        raise AwsClientAdmissionRejected("invalid AWS client region policy")
    suffix = "amazonaws.com.cn" if partition == "aws-cn" else "amazonaws.com"
    expected_url = f"https://secretsmanager.{region}.{suffix}"
    meta = getattr(client, "meta", None)
    service_model = getattr(meta, "service_model", None)
    config = getattr(meta, "config", None)
    retries = getattr(config, "retries", None)
    if (
        getattr(service_model, "service_name", None) != "secretsmanager"
        or getattr(meta, "region_name", None) != region
        or getattr(meta, "endpoint_url", None) != expected_url
        or getattr(config, "signature_version", None) != "v4"
        or not _bounded_timeout(getattr(config, "connect_timeout", None))
        or not _bounded_timeout(getattr(config, "read_timeout", None))
        or getattr(config, "parameter_validation", None) is not True
        or getattr(config, "proxies", None) not in (None, {})
        or not isinstance(retries, Mapping)
        or retries.get("mode") != "standard"
        or type(retries.get("total_max_attempts")) is not int
        or not 1 <= retries["total_max_attempts"] <= 2
    ):
        raise AwsClientAdmissionRejected("AWS SDK client profile not approved")


def build_admitted_aws_resolver(
    *,
    client: SecretsManagerClient,
    bindings: Mapping[SecretRef, ApprovedAwsSecret],
    account_id: str,
    region: str,
    partition: str = "aws",
) -> AwsSecretsManagerResolver:
    """Preferred production composition route, with explicit client checks.

    Offline fake clients may still use the lower-level resolver for isolated
    tests. This function never constructs credentials, a network client or a
    source of authority from an untrusted incoming authentication request.
    """
    admit_aws_client_profile(client, region=region, partition=partition)
    return AwsSecretsManagerResolver(
        client=client,
        bindings=bindings,
        account_id=account_id,
        region=region,
        partition=partition,
    )
