"""AWS adapter trust boundary using deterministic, network-free SDK-shaped fakes."""

import asyncio
from collections.abc import Mapping

import pytest

from pyauthkit.adapters.secrets_aws import ApprovedAwsSecret, AwsSecretsManagerResolver
from pyauthkit.configuration.secrets import SecretResolutionUnavailable
from pyauthkit.domain.secret import SecretRef

VERSION = "0123456789abcdef0123456789abcdef"
OTHER_VERSION = "fedcba9876543210fedcba9876543210"
ARN = "arn:aws:secretsmanager:eu-west-1:123456789012:secret:tenant-a/hmac-QWERTY"
RAW = bytes(range(32))
REF = SecretRef("aws-secrets-manager", "tenant-a", "hmac", VERSION, "verify")
OTHER_REF = SecretRef("aws-secrets-manager", "tenant-b", "hmac", VERSION, "verify")
CANARY = "AWS_PROVIDER_RESPONSE_SECRET_M6_CANARY"


class FakeAwsClient:
    def __init__(self, payload: Mapping[str, object] | None = None) -> None:
        self.calls: list[dict[str, str]] = []
        self.payload = (
            {"ARN": ARN, "VersionId": VERSION, "VersionStages": ["AWSCURRENT"], "SecretBinary": RAW}
            if payload is None
            else payload
        )
        self.unavailable = False

    def get_secret_value(self, **kwargs: str) -> Mapping[str, object]:
        self.calls.append(kwargs)
        if self.unavailable:
            raise RuntimeError(CANARY)
        return self.payload


def make(client: FakeAwsClient, *, bindings=None) -> AwsSecretsManagerResolver:
    return AwsSecretsManagerResolver(
        client=client,
        bindings={REF: ApprovedAwsSecret(ARN)} if bindings is None else bindings,
        account_id="123456789012",
        region="eu-west-1",
    )


def resolve(adapter: AwsSecretsManagerResolver, ref: SecretRef = REF) -> bytes:
    return asyncio.run(adapter.resolve(ref=ref, purpose="verify"))


def test_m6_aws_exact_version_and_stage_are_required_on_request() -> None:
    client = FakeAwsClient()
    result = resolve(make(client))
    assert result == RAW
    assert client.calls == [{"SecretId": ARN, "VersionId": VERSION, "VersionStage": "AWSCURRENT"}]


def test_m6_aws_cross_tenant_and_unknown_version_fail_before_sdk_call() -> None:
    client = FakeAwsClient()
    adapter = make(client)
    for ref in (
        OTHER_REF,
        SecretRef(REF.provider, REF.namespace, REF.key_id, OTHER_VERSION, "verify"),
    ):
        with pytest.raises(SecretResolutionUnavailable, match="denied"):
            resolve(adapter, ref)
    assert client.calls == []


def test_m6_aws_wrong_purpose_fails_before_sdk_call() -> None:
    client = FakeAwsClient()
    adapter = make(client)
    with pytest.raises(SecretResolutionUnavailable):
        asyncio.run(adapter.resolve(ref=REF, purpose="pepper"))
    assert client.calls == []


@pytest.mark.parametrize(
    "response",
    [
        {
            "ARN": ARN,
            "VersionId": OTHER_VERSION,
            "VersionStages": ["AWSCURRENT"],
            "SecretBinary": RAW,
        },
        {"ARN": ARN, "VersionId": VERSION, "VersionStages": ["AWSPREVIOUS"], "SecretBinary": RAW},
        {"ARN": ARN, "VersionId": VERSION, "VersionStages": [], "SecretBinary": RAW},
        {"ARN": ARN, "VersionId": VERSION, "VersionStages": ["AWSCURRENT"], "SecretString": CANARY},
        {"ARN": ARN, "VersionId": VERSION, "VersionStages": ["AWSCURRENT"], "SecretBinary": CANARY},
        {"ARN": ARN, "VersionId": VERSION, "VersionStages": ["AWSCURRENT"], "SecretBinary": b""},
        {
            "ARN": ARN,
            "VersionId": VERSION,
            "VersionStages": ["AWSCURRENT"],
            "SecretBinary": b"x" * 65537,
        },
        {
            "ARN": ARN + "-other",
            "VersionId": VERSION,
            "VersionStages": ["AWSCURRENT"],
            "SecretBinary": RAW,
        },
    ],
)
def test_m6_aws_wrong_version_stage_identity_or_material_fails_closed(
    response: dict[str, object],
) -> None:
    with pytest.raises(SecretResolutionUnavailable, match="secret unavailable"):
        resolve(make(FakeAwsClient(response)))


def test_m6_aws_post_bootstrap_revocation_fails_closed() -> None:
    client = FakeAwsClient()
    adapter = make(client)
    assert resolve(adapter) == RAW
    client.payload = {
        "ARN": ARN,
        "VersionId": VERSION,
        "VersionStages": ["AWSPREVIOUS"],
        "SecretBinary": RAW,
    }
    with pytest.raises(SecretResolutionUnavailable):
        resolve(adapter)


def test_m6_aws_provider_errors_are_sanitized() -> None:
    client = FakeAwsClient()
    client.unavailable = True
    with pytest.raises(SecretResolutionUnavailable) as ex:
        resolve(make(client))
    assert CANARY not in str(ex.value)
    assert ex.value.__cause__ is None


@pytest.mark.parametrize(
    "bad_arn",
    [
        "tenant-a/hmac",
        "arn:aws:secretsmanager:eu-west-1:000000000000:secret:",
        "arn:aws:secretsmanager:eu-west-1:123456789012:secret:name?x=1",
        "arn:aws:secretsmanager:eu-west-1:123456789012:secret:name#fragment",
    ],
)
def test_m6_aws_invalid_or_partial_arn_is_denied(bad_arn: str) -> None:
    with pytest.raises(ValueError):
        ApprovedAwsSecret(bad_arn)


def test_m6_aws_account_region_and_partition_are_host_pinned() -> None:
    client = FakeAwsClient()
    for region, account, partition in (
        ("us-east-1", "123456789012", "aws"),
        ("eu-west-1", "987654321098", "aws"),
        ("eu-west-1", "123456789012", "aws-cn"),
    ):
        with pytest.raises(ValueError):
            AwsSecretsManagerResolver(
                client=client,
                bindings={REF: ApprovedAwsSecret(ARN)},
                account_id=account,
                region=region,
                partition=partition,
            )
    assert client.calls == []


def test_m6_aws_same_arn_version_cannot_alias_two_scopes() -> None:
    with pytest.raises(ValueError, match="cross-scope"):
        make(
            FakeAwsClient(),
            bindings={REF: ApprovedAwsSecret(ARN), OTHER_REF: ApprovedAwsSecret(ARN)},
        )


def test_m6_aws_rejects_logical_unsupported_version() -> None:
    ref = SecretRef("aws-secrets-manager", "tenant-a", "hmac", "v1", "verify")
    with pytest.raises(ValueError):
        make(FakeAwsClient(), bindings={ref: ApprovedAwsSecret(ARN)})


def test_m6_aws_mapping_mutation_and_repr_cannot_disclose_arn_or_material() -> None:
    client = FakeAwsClient()
    grants = {REF: ApprovedAwsSecret(ARN)}
    adapter = make(client, bindings=grants)
    grants.clear()
    assert resolve(adapter) == RAW
    assert ARN not in repr(adapter)
    assert CANARY not in repr(adapter)
    assert ARN not in repr(ApprovedAwsSecret(ARN))
    with pytest.raises(AttributeError):
        adapter._bindings = {}  # type: ignore[assignment]


def test_m6_aws_cancellation_propagates() -> None:
    class Cancellable:
        def get_secret_value(self, **_kwargs: str) -> Mapping[str, object]:
            raise asyncio.CancelledError

    # asyncio.to_thread propagates CancelledError thrown in the worker.
    adapter = make(Cancellable())  # type: ignore[arg-type]
    with pytest.raises(asyncio.CancelledError):
        resolve(adapter)
