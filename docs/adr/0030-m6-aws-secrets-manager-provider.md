# ADR-0030: M6 optional AWS Secrets Manager secret resolution

Date: 2026-11-05
Status: PROPOSED / INDEPENDENT REVIEW REQUIRED

## Problem and trust boundary

M6's opaque `SecretRef` and scoped consumer allow different providers,
but the current synthetic memory resolver does not demonstrate use of a
real cloud secret manager. A provider-specific adapter must never let a
caller-supplied JWT, username or credential selector choose a secret ARN,
version, account or AWS region.

## Candidate decision

Use Ports & Adapters: `AwsSecretsManagerResolver` implements the existing
async `SecretResolver` interface. The host provides an already-configured
AWS SDK client and an explicit immutable dictionary of
`SecretRef -> ApprovedAwsSecret(full ARN)`. The adapter admits only exact
provider `aws-secrets-manager`, `verify` purpose, valid fixed VersionId
and one AWS region/account/partition per adapter. A shared ARN+VersionId
cannot alias different tenant references.

On each call use `GetSecretValue(SecretId=full_arn,
VersionId=ref.version, VersionStage="AWSCURRENT")`, then require the
response ARN, VersionId and AWSCURRENT stage to match. Read binary material
only, cap its size, refuse ambiguous text/empty/mismatched responses, and
redact all provider failure messages. M4 enforces its own 32-byte HMAC key
contract. There is no plaintext persistence, no cache and no fallback.

The AWS SDK is an optional dependency and is constructed by the trusted host,
not imported or auto-configured by PyAuthKit at package import time.

## Known limitations

- The pinned IAM policy, KMS rights, SDK client region, endpoint/TLS setup,
  network egress, CloudTrail validation and real throttling/cancellation
  behavior need independent deployment verification.
- AWS GetSecretValue has required IAM permissions and may require
  `kms:Decrypt` for customer-managed KMS keys.
- Because the boto3 API is synchronous, the async adapter uses a worker
  thread. Coroutine cancellation or asyncio timeout cannot terminate the
  underlying request. Host-owned retry/time/concurrency budgets remain
  mandatory. No external key rotation/promotion is performed by this adapter.
- A privileged host with access to SDK client internals could subvert the
  in-process adapter. Python bytes are not guaranteed zeroizable.
- Requiring AWSCURRENT is a deliberate operational policy, not a guarantee
  that all stale credentials are instantly revoked across deployments.

## Tests and evidence

`tests/security/test_m6_aws_secrets.py`,
`tests/integration/test_m6_aws_sdk_stubber.py` and
`test_m6_aws_*m4*` in M6 M4 integration tests exercise exact contracts,
error sanitization, stage/version mismatch and post-bootstrap denial.
Stubber does not make a live AWS request and cannot prove production IAM,
KMS, TLS or region-to-account isolation.

AWS SDK API: https://docs.aws.amazon.com/boto3/latest/reference/services/secretsmanager/client/get_secret_value.html

GATE27-07 remains NO-GO until independent security qualification.
