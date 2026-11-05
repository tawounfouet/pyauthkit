"""Manual, opt-in M6 AWS qualification reader. NEVER runs in ordinary CI.

Uses a separately approved test AWS account and an IAM read-only identity.
The read material stays in memory and is never logged, printed or persisted.
"""

from __future__ import annotations

import asyncio
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass

from pyauthkit.adapters.aws_client_admission import build_admitted_aws_resolver
from pyauthkit.adapters.secrets_aws import ApprovedAwsSecret
from pyauthkit.domain.secret import SecretRef

_PREFIX = "PYA_M6_LIVE_"
_OPT_IN = "APPROVE_READ_ONLY_TEST"
_VERSION = re.compile(r"[A-Za-z0-9-]{32,64}\Z")
_ACCOUNT = re.compile(r"\d{12}\Z")


@dataclass(frozen=True, slots=True, repr=False)
class LiveSettings:
    """Configuration metadata only. Credentials are supplied to the AWS SDK."""

    account: str
    region: str
    partition: str
    resource_arn: str
    version: str
    namespace: str
    key_id: str
    expected_principal: str

    def __repr__(self) -> str:
        return "LiveSettings(<redacted test-account metadata>)"


def read_live_settings(values: Mapping[str, str]) -> LiveSettings:
    """Fail closed before importing boto3 or invoking ANY network call."""
    if values.get(_PREFIX + "APPROVAL") != _OPT_IN:
        raise ValueError("live AWS read has not been approved")
    required = {
        name: values.get(_PREFIX + name)
        for name in (
            "ACCOUNT", "REGION", "PARTITION", "RESOURCE_ARN",
            "VERSION", "NAMESPACE", "KEY_ID", "EXPECTED_PRINCIPAL",
        )
    }
    if any(not isinstance(value, str) or not value for value in required.values()):
        raise ValueError("incomplete live qualification environment")
    settings = LiveSettings(
        account=required["ACCOUNT"],
        region=required["REGION"],
        partition=required["PARTITION"],
        resource_arn=required["RESOURCE_ARN"],
        version=required["VERSION"],
        namespace=required["NAMESPACE"],
        key_id=required["KEY_ID"],
        expected_principal=required["EXPECTED_PRINCIPAL"],
    )
    if (
        _ACCOUNT.fullmatch(settings.account) is None
        or _VERSION.fullmatch(settings.version) is None
        or settings.partition not in ("aws", "aws-us-gov", "aws-cn")
        or not settings.expected_principal.startswith(
            f"arn:{settings.partition}:sts::{settings.account}:assumed-role/"
        )
    ):
        raise ValueError("unapproved test-account identity")
    approved = ApprovedAwsSecret(settings.resource_arn)
    ref = SecretRef(
        "aws-secrets-manager", settings.namespace, settings.key_id,
        settings.version, "verify",
    )
    if (
        f":secretsmanager:{settings.region}:{settings.account}:" not in approved.arn
        or not approved.arn.startswith(f"arn:{settings.partition}:")
        or ref.version != settings.version
    ):
        raise ValueError("unapproved AWS test resource")
    return settings


async def check_live_aws(settings: LiveSettings) -> None:
    """Fetch only the explicitly approved version; never reveal the bytes.

    Running this requires separately approved AWS credentials, test-only IAM,
    KMS and VPC/egress policy. It is a read-only check, not full G7 signoff.
    """
    import boto3
    from botocore.config import Config

    config = Config(
        region_name=settings.region,
        signature_version="v4",
        connect_timeout=1.0,
        read_timeout=1.0,
        parameter_validation=True,
        retries={"mode": "standard", "total_max_attempts": 2},
        proxies={},
    )
    session = boto3.Session(region_name=settings.region)
    identity = session.client("sts", config=config)
    client = session.client("secretsmanager", config=config)
    try:
        principal = await asyncio.to_thread(identity.get_caller_identity)
        if (
            principal.get("Account") != settings.account
            or principal.get("Arn") != settings.expected_principal
        ):
            raise ValueError("unexpected AWS qualification principal")
        ref = SecretRef(
            "aws-secrets-manager", settings.namespace, settings.key_id,
            settings.version, "verify",
        )
        resolver = build_admitted_aws_resolver(
            client=client,
            bindings={ref: ApprovedAwsSecret(settings.resource_arn)},
            account_id=settings.account,
            region=settings.region,
            partition=settings.partition,
        )
        material = await resolver.resolve(ref=ref, purpose="verify")
        if len(material) != 32:
            raise ValueError("invalid M4 HMAC material length")
        del material  # Python bytes cannot guarantee zeroization.
    finally:
        client.close()
        identity.close()


def main() -> int:
    try:
        settings = read_live_settings(os.environ)
        asyncio.run(check_live_aws(settings))
    except (Exception, KeyboardInterrupt):
        # Never propagate SDK errors (including possible ARN/request metadata)
        # or secret values into CI logs / operator consoles.
        print("M6 AWS read-only qualification: REJECTED (details withheld)")
        return 1
    print("M6 AWS read-only qualification: PASS (content withheld)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
