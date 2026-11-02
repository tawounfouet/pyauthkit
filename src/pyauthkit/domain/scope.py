"""Syntactic scope references, not proof of trusted provenance."""

import re
from dataclasses import dataclass

_SCOPE_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")


@dataclass(frozen=True, slots=True, repr=False)
class TrustedScopeRef:
    """Well-formed reference only. An authorized host must establish trust."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not _SCOPE_PATTERN.fullmatch(self.value):
            raise ValueError("invalid scope reference")

    def __repr__(self) -> str:
        return "TrustedScopeRef(<unapproved reference>)"
