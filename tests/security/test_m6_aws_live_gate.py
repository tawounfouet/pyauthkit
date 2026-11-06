"""Offline checks for manual AWS live qualification guard. No network calls."""

import pytest

from qualification.m6_aws_live.run_live import LiveSettings, read_live_settings

PREFIX = "PYA_M6_LIVE_"


def valid_settings() -> dict[str, str]:
    return {
        PREFIX + "APPROVAL": "APPROVE_READ_ONLY_TEST",
        PREFIX + "ACCOUNT": "123456789012",
        PREFIX + "REGION": "eu-west-1",
        PREFIX + "PARTITION": "aws",
        PREFIX + "RESOURCE_ARN": (
            "arn:aws:secretsmanager:eu-west-1:123456789012:secret:tenant-a/hmac-QWERTY"
        ),
        PREFIX + "VERSION": bytes(range(16)).hex(),
        PREFIX + "NAMESPACE": "tenant-a",
        PREFIX + "KEY_ID": "hmac",
        PREFIX + "EXPECTED_PRINCIPAL": (
            "arn:aws:sts::123456789012:assumed-role/m6-read-only/ci-test"
        ),
    }


def test_manual_aws_live_run_requires_explicit_opt_in() -> None:
    with pytest.raises(ValueError, match="not been approved"):
        read_live_settings({})
    env = valid_settings()
    del env[PREFIX + "APPROVAL"]
    with pytest.raises(ValueError, match="not been approved"):
        read_live_settings(env)


def test_manual_aws_live_settings_are_metadata_only_and_redacted() -> None:
    env = valid_settings()
    settings = read_live_settings(env)
    assert isinstance(settings, LiveSettings)
    assert settings.namespace == "tenant-a"
    assert settings.version == bytes(range(16)).hex()
    assert "123456789012" not in repr(settings)
    assert "QWERTY" not in repr(settings)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("ACCOUNT", "999"),
        ("REGION", "us-east-1"),
        ("PARTITION", "aws-cn"),
        ("VERSION", "not-a-concrete-version"),
        ("NAMESPACE", "../escape"),
        ("EXPECTED_PRINCIPAL", "arn:aws:iam::123456789012:root"),
        ("RESOURCE_ARN", "https://attacker.invalid"),
    ],
)
def test_manual_aws_live_settings_reject_mismatched_identity(field: str, value: str) -> None:
    env = valid_settings()
    env[PREFIX + field] = value
    with pytest.raises(ValueError):
        read_live_settings(env)


def test_manual_aws_live_rejects_missing_fields_without_io() -> None:
    env = valid_settings()
    del env[PREFIX + "RESOURCE_ARN"]
    with pytest.raises(ValueError, match="incomplete"):
        read_live_settings(env)
