"""PR-06A contract: two adapters obey the same scoped-read contract."""

import asyncio

import pytest

from pyauthkit.adapters.password.callback import CallbackPasswordCredentialResolver
from pyauthkit.adapters.password.memory import InMemoryPasswordCredentialResolver
from pyauthkit.domain.identity import ScopedSubjectRef
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.password.records import (
    PasswordRecordAmbiguous,
    PasswordRecordFound,
    PasswordRecordMissing,
    PasswordRecordStatus,
    PasswordRecordUnavailable,
    PasswordVerifierRecord,
)


def record(scope: TrustedScopeRef) -> PasswordVerifierRecord:
    return PasswordVerifierRecord(
        scope_ref=scope,
        subject_ref=ScopedSubjectRef("subject-1", "local-auth", scope),
        encoded_hash="$argon2id$v=19$m=19456,t=2,p=1$synthetic$synthetic",
        status=PasswordRecordStatus.ACTIVE,
        version=1,
    )


@pytest.mark.parametrize("use_callback", [False, True])
def test_m3_scoped_lookup_missing_found_ambiguous_and_no_global_fallback(
    use_callback: bool,
) -> None:
    tenant_a = TrustedScopeRef("tenant-a")
    tenant_b = TrustedScopeRef("tenant-b")
    stored = record(tenant_a)
    inner = InMemoryPasswordCredentialResolver(
        {("tenant-a", "username", "same"): (stored,)}
    )
    if use_callback:
        resolver = CallbackPasswordCredentialResolver(
            resolve_callback=lambda scope, kind, value: inner.resolve(
                scope_ref=scope, identifier_kind=kind, identifier_value=value
            ),
            current_callback=lambda found: inner.is_current(record=found),
        )
    else:
        resolver = inner

    async def check() -> None:
        a = await resolver.resolve(
            scope_ref=tenant_a, identifier_kind="username", identifier_value="same"
        )
        b = await resolver.resolve(
            scope_ref=tenant_b, identifier_kind="username", identifier_value="same"
        )
        assert isinstance(a, PasswordRecordFound) and a.record is stored
        assert isinstance(b, PasswordRecordMissing)
        assert await resolver.is_current(record=stored) is True

    asyncio.run(check())


def test_m3_ambiguous_and_foreign_scope_never_return_verified_record() -> None:
    a, b = TrustedScopeRef("a"), TrustedScopeRef("b")
    normal = record(a)
    collision = InMemoryPasswordCredentialResolver(
        {("a", "username", "x"): (normal, normal)}
    )
    broken = InMemoryPasswordCredentialResolver(
        {("a", "username", "x"): (record(b),)}
    )

    async def check() -> None:
        one = await collision.resolve(scope_ref=a, identifier_kind="username", identifier_value="x")
        two = await broken.resolve(scope_ref=a, identifier_kind="username", identifier_value="x")
        assert isinstance(one, PasswordRecordAmbiguous)
        assert isinstance(two, PasswordRecordUnavailable)

    asyncio.run(check())


def test_m3_verifier_projection_redacts_sensitive_material() -> None:
    scope = TrustedScopeRef("test")
    secret = "private-hash-not-for-logs"
    item = PasswordVerifierRecord(
        scope_ref=scope,
        subject_ref=ScopedSubjectRef("private-id", "private-issuer", scope),
        encoded_hash=secret,
        status=PasswordRecordStatus.ACTIVE,
        version=1,
    )
    assert secret not in repr(item)
    assert "private-id" not in repr(PasswordRecordFound(item))
    with pytest.raises(TypeError):
        from dataclasses import asdict

        asdict(item)  # type: ignore[arg-type]
    with pytest.raises(AttributeError):
        item.encoded_hash = "changed"  # type: ignore[misc]
