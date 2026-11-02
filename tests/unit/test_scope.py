from dataclasses import FrozenInstanceError

import pytest

from pyauthkit.domain.scope import TrustedScopeRef


def test_scope_reference_accepts_safe_identifier() -> None:
    scope = TrustedScopeRef("tenant-a:production")
    assert scope.value == "tenant-a:production"


@pytest.mark.parametrize("value", ["", " ", "tenant/a", "tenant\nA", "\x00"])
def test_scope_reference_rejects_invalid_strings(value: str) -> None:
    with pytest.raises(ValueError, match="invalid scope reference"):
        TrustedScopeRef(value)


def test_scope_reference_is_immutable() -> None:
    scope = TrustedScopeRef("tenant-a")
    with pytest.raises(FrozenInstanceError):
        scope.value = "tenant-b"  # type: ignore[misc]
