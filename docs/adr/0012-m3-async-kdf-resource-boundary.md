# ADR-0012: Async native KDF capacity and cancellation

- Date: 2026-11-02
- Status: PROPOSED
- Scope: M3 / PR-06B / WP27-022

## Threat
A CPU/memory-hard KDF can starve an asyncio event loop or consume unlimited memory under attack. Cancelling an asyncio task does not terminate native C work running in a thread.

## Decision
Use a dedicated bounded `ThreadPoolExecutor` and non-blocking bounded semaphore. At bootstrap validate `max_workers * max_KDF_memory <= memory_budget`. Enforce finite in-flight plus queued slots. A permit is released by the `concurrent.futures.Future` callback ONLY after native computation completes. Use `asyncio.shield` to avoid cancellation of the underlying job. The host rate limit remains mandatory for a network-facing service.

## Limits
Budgets are per process; multiple instances need host-wide capacity/abuse controls. Python threads and process memory have additional overhead. Engine timeouts do not preempt Argon2. Operators must benchmark and provide worker lifecycle shutdown. No local implementation guarantees distributed rate limiting or constant-time network responses.

## Tests
Resource-budget validation, saturation and cancellation held slot, event loop responsiveness and post-timeout allocation discipline.
