# M6 AWS Secrets Manager - manual test-account qualification

Status: CANDIDATE HARNESS ONLY. No live run has been executed here.
Do not invoke this against production AWS accounts, roles, secrets or KMS keys.

## Prerequisites (human approval and test account only)

The operator must first approve an isolated AWS test account, a disposable
32-byte binary secret, a concrete version ID and an STS assumed-role principal.
Credential ownership stays with the approved AWS execution environment, not
with PyAuthKit or this repository. No access key, session token or secret
material should be committed or placed in command line arguments.

- A dedicated, isolated AWS account and short-lived read-only role.
- IAM: allow `secretsmanager:GetSecretValue` only on the exact full secret ARN,
  and `sts:GetCallerIdentity` for identity checking. Deny secret write,
  rotation, deletion and enumeration. For a customer-managed KMS key, allow
  `kms:Decrypt` only as needed, ideally with `kms:ViaService` and encryption
  context constraints. Review both IAM and key policy.
- Enforce AWS endpoint, HTTPS/TLS and network egress at the deployment layer,
  preferably by restrictive VPC endpoint policy. The Python code does not
  attest AWS KMS permissions, VPC policies, DNS or peer certificate state.
- The host provisions a test-only `SecretBinary` with exactly 32 bytes and
  records its full ARN and concrete `VersionId`. `AWSCURRENT` must refer to
  that version. The value must NOT be printed, logged or stored in this repo.
- The host sets explicit SDK credentials through an approved AWS role or
  workload identity mechanism. Never reuse personal or production credentials.

## Explicit opt-in

From an approved, isolated runtime, supply the following eight metadata
variables and the explicit approval marker through the host environment:

```text
PYA_M6_LIVE_APPROVAL=APPROVE_READ_ONLY_TEST
PYA_M6_LIVE_ACCOUNT=<test AWS account ID>
PYA_M6_LIVE_REGION=<test region>
PYA_M6_LIVE_PARTITION=aws
PYA_M6_LIVE_RESOURCE_ARN=<full test secret ARN>
PYA_M6_LIVE_VERSION=<specific current VersionId>
PYA_M6_LIVE_NAMESPACE=<test tenant namespace>
PYA_M6_LIVE_KEY_ID=<logical key ID>
PYA_M6_LIVE_EXPECTED_PRINCIPAL=<exact sts:GetCallerIdentity Arn>
```

Run explicitly in the approved environment with the AWS optional dependency:

```bash
python -m pip install ".[aws]"
python -m qualification.m6_aws_live.run_live
```

Ordinary PR CI never runs this executable; missing approval fails before boto3
is imported and before any network call. The only output is PASS or REJECTED.
No secret bytes, ARN or role identity are printed. This proof alone does not
sign off IAM, egress, KMS or failure behaviors.

## Manual negative drill matrix (requires separately authorized fixtures)

1. Wrong IAM principal or AWS account: refuse before requesting material.
2. Wrong region or endpoint: refuse before requesting material.
3. Wrong VersionId or AWSPREVIOUS instead of AWSCURRENT: refuse the read.
4. Denied `secretsmanager:GetSecretValue` or KMS decrypt: fail closed.
5. Resource not found or revoked staging label: fail closed.
6. Throttling, TLS failure, DNS error or SDK timeout: fail closed.
7. Concurrent G1/G2 rotation: evaluate provider stage promotion together with
   application restart and host generation-fencing behavior.
8. Check provider audit trails, access logs and application logs for no leaked
   material; verify the strict IAM and KMS policies were actually applied.

Record only synthetic test IDs, approved exact git SHA, job/run identifier,
time, signed reviewer decisions and redacted failure codes, never raw
response bodies or secret contents.

## Limits and sign-off

- A successful GetSecretValue with exact identity, ARN, version and stage is
  merely a *positive read smoke test*. It does not cover all failure drills.
- The synchronous boto3 request runs in a worker thread and cannot be
  cancelled in-flight simply by cancelling the coroutine.
- The in-memory `bytes` payload cannot be guaranteed to be zeroized.
- `GATE27-07` remains NO-GO until this harness and the negative drills are
  executed in the approved AWS environment, reviewed independently and
  correlated to security acceptance records.

Official documentation:
- https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
- https://docs.aws.amazon.com/secretsmanager/latest/userguide/security-encryption.html
- https://docs.aws.amazon.com/secretsmanager/latest/userguide/vpc-endpoint-overview.html
- https://docs.aws.amazon.com/botocore/latest/reference/config.html
