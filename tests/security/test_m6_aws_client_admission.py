"""M6 security checks for an explicit host-created, no-network botocore client."""

from collections.abc import Mapping

import pytest
from botocore.config import Config
from botocore.session import get_session

from pyauthkit.adapters.aws_client_admission import (
    AwsClientAdmissionRejected,
    admit_aws_client_profile,
    build_admitted_aws_resolver,
)
from pyauthkit.adapters.secrets_aws import ApprovedAwsSecret
from pyauthkit.domain.secret import SecretRef

REGION = "eu-west-1"
ACCOUNT = "123456789012"
ARN = "arn:aws:secretsmanager:eu-west-1:123456789012:secret:tenant-a/hmac-QWERTY"
REF = SecretRef("aws-secrets-manager", "tenant-a", "hmac", bytes(range(16)).hex(), "verify")


def sdk(
    *,
    service: str = "secretsmanager",
    region: str = REGION,
    endpoint: str | None = None,
    connect_timeout: float = 1.0,
    read_timeout: float = 1.0,
    total_max_attempts: int = 2,
    signature_version: str = "v4",
):
    session = get_session()
    session.set_credentials("synthetic", "synthetic")
    return session.create_client(
        service,
        region_name=region,
        endpoint_url=endpoint,
        config=Config(
            connect_timeout=connect_timeout,
            read_timeout=read_timeout,
            retries={"mode": "standard", "total_max_attempts": total_max_attempts},
            parameter_validation=True,
            signature_version=signature_version,
        ),
    )


def test_m6_aws_real_client_exact_profile_is_admitted_without_network() -> None:
    client = sdk()
    try:
        admit_aws_client_profile(client, region=REGION)
        resolver = build_admitted_aws_resolver(
            client=client,
            bindings={REF: ApprovedAwsSecret(ARN)},
            account_id=ACCOUNT,
            region=REGION,
        )
        assert "redacted" in repr(resolver)
    finally:
        client.close()


@pytest.mark.parametrize(
    "changes",
    [
        {"service": "ssm"},
        {"region": "us-east-1"},
        {"endpoint": "http://secretsmanager.eu-west-1.amazonaws.com"},
        {"endpoint": "https://secretsmanager.eu-west-1.amazonaws.com.attacker.invalid"},
        {"endpoint": "https://example.invalid"},
        {"connect_timeout": 60.0},
        {"read_timeout": 3.0},
        {"total_max_attempts": 5},
        {"signature_version": "unsigned"},
    ],
)
def test_m6_aws_unsafe_sdk_profiles_rejected_without_request(changes: dict[str, object]) -> None:
    client = sdk(**changes)
    try:
        with pytest.raises(AwsClientAdmissionRejected, match="not approved"):
            build_admitted_aws_resolver(
                client=client,
                bindings={REF: ApprovedAwsSecret(ARN)},
                account_id=ACCOUNT,
                region=REGION,
            )
    finally:
        client.close()


def test_m6_aws_client_admission_denies_missing_sdk_metadata() -> None:
    class FakeClient:
        def get_secret_value(self, **_kw: str) -> Mapping[str, object]:
            return {}

    with pytest.raises(AwsClientAdmissionRejected):
        admit_aws_client_profile(FakeClient(), region=REGION)


def test_m6_aws_client_admission_denies_wrong_region_policy() -> None:
    client = sdk()
    try:
        with pytest.raises(AwsClientAdmissionRejected):
            admit_aws_client_profile(client, region="not-an-aws-region")
        with pytest.raises(AwsClientAdmissionRejected):
            admit_aws_client_profile(client, region=REGION, partition="aws-cn")
    finally:
        client.close()


def test_m6_aws_rejected_client_does_not_expose_endpoint_or_credentials() -> None:
    client = sdk(endpoint="https://example.invalid")
    try:
        with pytest.raises(AwsClientAdmissionRejected) as caught:
            admit_aws_client_profile(client, region=REGION)
        assert "example.invalid" not in str(caught.value)
        assert "synthetic" not in str(caught.value)
    finally:
        client.close()
