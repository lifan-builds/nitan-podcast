# Bug Analysis: X collection failed only in scheduled runs

## 1. Root Cause Category

- **Category**: B/E — Cross-layer contract and implicit assumption
- **Specific cause**: The X CLI can extract browser cookies when launched interactively, but the background self-hosted Actions service cannot rely on the interactive browser/Keychain boundary. The workflow passed no `TWITTER_AUTH_TOKEN` or `TWITTER_CT0`, so every approved-account read exited before returning JSON even though the same executable and working tree succeeded interactively.

## 2. Why Fixes Failed

1. Treating the August 17 failure as a transient upstream outage did not explain why 19/19 accounts failed in two consecutive workflow runs while an immediate local read succeeded.
2. Adding one collector retry improved transient handling but repeated the same unavailable authentication path, so it could not repair the runner boundary.
3. The decisive evidence was environment-specific: the CLI existed on the runner `PATH`, the identical checkout succeeded interactively after the job, and the CLI implementation documented environment-cookie support for non-interactive execution.

## 3. Prevention Mechanisms

| Priority | Mechanism | Specific action | Status |
| --- | --- | --- | --- |
| P0 | Architecture | Pass X session fields to only the read-only review step through GitHub Actions secrets. | DONE |
| P0 | Runtime | Require 80% account success plus one in-window post before emitting a top ten. | DONE |
| P1 | Test coverage | Assert workflow secret wiring, X retry/health, and unhealthy-X omission of review artifacts. | DONE |
| P1 | Documentation | Distinguish optional X for podcast publication from required X for community-first review-only runs. | DONE |

## 4. Systematic Expansion

- **Similar issues**: Any self-hosted workflow that depends on browser cookies or macOS Keychain access can pass local tests and still fail as a background service.
- **Design improvement**: Authenticated read clients should receive narrowly scoped secret environment variables at the step boundary; collectors should emit only controlled health metadata.
- **Process improvement**: Validate authenticated integrations from the actual scheduled runner, not only from an interactive shell.

## 5. Knowledge Capture

- [x] Updated the review-only pipeline code-spec with the X health and fail-closed contract.
- [x] Added workflow and integration regressions.
- [x] Verified a manual scheduled run with 19/19 accounts and 163 in-window posts.
