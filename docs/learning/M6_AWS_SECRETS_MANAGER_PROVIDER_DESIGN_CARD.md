# M6 Design Learning Card - Host-pinned AWS secrets

Date: 2026-11-05
Status: IMPLEMENTATION CANDIDATE / NOT PRODUCTION QUALIFIED

## Problem

A normal cloud SDK can fetch arbitrary secrets if the process's permissions
are overly broad. Merely passing a provider string through configuration
does not prove the requested secret is scoped to the active trusted host
profile, nor does a secret version alias prove the intended key identity.

## SOLID / DDD / Hexagonal applied

- [DDD Value Object] `SecretRef` represents a logical provider/namespace/
  key/version/purpose without plaintext. `ApprovedAwsSecret` is an immutable
  host-owned complete ARN reference.
- [DIP / Ports & Adapters] AWS is injected behind `SecretResolver`, while
  M4 still calls `ApiKeyProtectionKeySource`. The M2 authentication engine
  and final policy remain unchanged.
- [Explicit Fail Closed] Unknown logical reference, cross-tenant alias,
  changed version/stage/ARN, unexpected return type or provider errors never
  switch to another AWS secret or local fallback.
- [Separation of Concerns] IAM, KMS, region/endpoint, transport retries,
  CloudTrail and host deployment are infrastructure responsibilities, not
  equivalent to validating Python configuration values.

## Alternatives rejected

Calling boto3 directly from a JWT authenticator, selecting the secret name
from an untrusted request, defaulting to AWSCURRENT without VersionId,
falling back to AWSPREVIOUS after rotation, logging SDK exception strings,
or persisting HMAC key bytes in ConfigurationSnapshot.

## Falsification and security limits

Offline botocore Stubber and security tests cover provider request shape,
identity checks, post-bootstrap failure, no leaked SDK exception content and
true M4 HMAC use. Actual AWS account integration, IAM/KMS least privilege and
provider outage behavior remain separate qualification gates.

Also: asyncio.to_thread cannot cancel an already executing blocking SDK
network call. The host needs a concurrency budget and finite SDK retries and
read/connect timeouts; asyncio's own timeout is not a transport kill switch.
