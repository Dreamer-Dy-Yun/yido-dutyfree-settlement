# PROCESSOR_MATCHING

This folder owns receipt-passport matching contracts, concrete matching rules, matcher registry, and the Redis-backed match worker.

## Files

| Path | Responsibility |
| --- | --- |
| `matcher.py` | Abstract matching workflow and `MatchResult` contract. Hardened candidate. |
| `matcher_registry.py` | Registry mapping matcher keys to concrete matcher classes. |
| `run_match_worker.py` | Redis worker that consumes match jobs and calls the internal tenant match API. |

## Subfolders

| Path | Responsibility |
| --- | --- |
| `matchers/` | Concrete vendor matching strategies. |
| `tests/` | End-to-end matching tests. |

## Boundary Notes

- Matching rules should live in concrete matcher classes, not routers.
- Worker code should call internal APIs and not duplicate matching persistence logic.
- The matcher registry is the extension point for adding new vendor matchers.
