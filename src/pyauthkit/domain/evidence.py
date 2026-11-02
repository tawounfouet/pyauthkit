"""Bounded untrusted authentication evidence, without implicit verification."""

from enum import StrEnum, auto
from typing import Never


class EvidenceMethod(StrEnum):
    """MVP evidence kinds; unknown methods must be rejected, not downgraded."""

    PASSWORD = auto()
    API_KEY = auto()
    JWT = auto()


MAX_EVIDENCE_BYTES = 65536


class PresentedEvidence:
    """Sensitive, untrusted evidence bytes.

    Avoid dataclasses.asdict and default serializer traversal by deliberately
    using a plain slotted class. Expose only explicitly sanitized summaries.
    Neither the type nor the input parser performs credential verification.
    The Python runtime does not guarantee byte-array zeroization.
    """

    __slots__ = ("method", "_opaque_payload")

    method: EvidenceMethod
    _opaque_payload: bytes

    def __init__(self, method: EvidenceMethod, opaque_payload: bytes) -> None:
        if not isinstance(method, EvidenceMethod):
            raise ValueError("unsupported evidence method")
        if type(opaque_payload) is not bytes or not 1 <= len(opaque_payload) <= MAX_EVIDENCE_BYTES:
            raise ValueError("invalid evidence payload")
        object.__setattr__(self, "method", method)
        object.__setattr__(self, "_opaque_payload", opaque_payload)

    @property
    def opaque_payload(self) -> bytes:
        """Raw evidence for a future approved verifier. Never log or serialize."""
        return self._opaque_payload

    def __setattr__(self, _name: str, _value: object) -> None:
        raise AttributeError("evidence is immutable")

    def __deepcopy__(self, _memo: dict[int, object]) -> Never:
        raise TypeError("sensitive evidence cannot be copied by a generic serializer")

    def __repr__(self) -> str:
        return f"PresentedEvidence(method={self.method.value!r}, payload=<redacted>)"
