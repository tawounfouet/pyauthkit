"""M6 AWS Secrets Manager SDK contract, using botocore Stubber (no network).

This exercises actual botocore request validation, exact VersionId, stage
selection and provider exception handling. An AWS account / IAM / KMS / TLS
integration test remains a separate deployment qualification.
"""

import asyncio

from botocore.session import get_session
from botocore.stub import Stubber

from pyauthkit.adapters.secrets_aws import ApprovedAwsSecret, AwsSecretsManagerResolver
from pyauthkit.configuration.secrets import SecretResolutionUnavailable
from pyauthkit.domain.secret import SecretRef

VERSION = "0123456789abcdef0123456789abcdef"
ARN = "arn:aws:secretsmanager:eu-west-1:123456789012:secret:tenant-a/hmac-QWERTY"
REF = SecretRef("aws-secrets-manager", "tenant-a", "hmac", VERSION, "verify")
REQUEST = {"SecretId": ARN, "VersionId": VERSION, "VersionStage": "AWSCURRENT"}


def client():
    # All calls are intercepted by Stubber; synthetic credentials are test-only.
    return get_session().create_client(
        "secretsmanager",
        region_name="eu-west-1",
        aws_access_key_id="synthetic",
        aws_secret_access_key="synthetic",
    )


def adapter(sdk_client):
    return AwsSecretsManagerResolver(
        client=sdk_client,
        bindings={REF: ApprovedAwsSecret(ARN)},
        account_id="123456789012",
        region="eu-west-1",
    )


def test_m6_aws_botocore_real_request_is_exact_version_and_stage() -> None:
    sdk = client()
    try:
        with Stubber(sdk) as stubber:
            payload = bytes(range(32))
            stubber.add_response(
                "get_secret_value",
                {
                    "ARN": ARN,
                    "Name": "tenant-a/hmac",
                    "VersionId": VERSION,
                    "VersionStages": ["AWSCURRENT"],
                    "SecretBinary": payload,
                },
                REQUEST,
            )
            assert asyncio.run(adapter(sdk).resolve(ref=REF, purpose="verify")) == payload
            stubber.assert_no_pending_responses()
    finally:
        sdk.close()


def test_m6_aws_botocore_resource_not_found_is_sanitized() -> None:
    sdk = client()
    try:
        with Stubber(sdk) as stubber:
            stubber.add_client_error(
                "get_secret_value",
                service_error_code="ResourceNotFoundException",
                service_message="raw provider diagnostic should not escape",
                expected_params=REQUEST,
            )
            from pytest import raises

            with raises(SecretResolutionUnavailable) as caught:
                asyncio.run(adapter(sdk).resolve(ref=REF, purpose="verify"))
            assert "raw provider diagnostic" not in str(caught.value)
            stubber.assert_no_pending_responses()
    finally:
        sdk.close()
