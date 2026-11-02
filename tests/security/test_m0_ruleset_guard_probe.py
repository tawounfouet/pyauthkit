"""Intentionally failing security-gate proof.

DISPOSABLE TEST PR ONLY. Never merge this file into main.
The expected pytest failure demonstrates the required CI check cannot pass.
"""


def test_m0_ruleset_rejects_failing_required_check() -> None:
    """This assertion must fail, to exercise protection of the default branch."""
    assert False, "INTENTIONAL_FAILURE_M0_RULESET_PROBE"
