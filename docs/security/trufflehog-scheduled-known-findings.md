# Scheduled TruffleHog known findings

The nightly TruffleHog job scans full history with `--results=verified,unknown`. One already-exposed credential still sits in git history. Its detector drops HTTP 401 and reports other verification responses, including HTTP 429, as unknown. Those unknown results fail the job. HTTP 401 produces no result, so the same history flips between green and red. The credential is treated as publicly compromised. The account is being closed, and the value cannot be rotated.

Pull request and push scans are unchanged. They do not read the baseline and they do not use path excludes.

## Baseline

[`.github/trufflehog-known-findings.json`](../../.github/trufflehog-known-findings.json) lists detector name, file path, commit, and line. Each entry expires on **2026-11-23**. An optional `closed_on` date, when set, replaces `expires` and must be on or before that date. The scheduled job runs TruffleHog JSON into [`.github/scripts/trufflehog_known_findings.py`](../../.github/scripts/trufflehog_known_findings.py).

The job passes only when every finding matches an unexpired entry by detector, path, and commit. It fails when:

- a finding is not in the unexpired baseline
- any result is verified, including a baselined location
- any baseline entry is expired, even when the scan reports nothing

An entry is unexpired only while the UTC date is before its effective expiry. On 2026-11-23 the nightly job fails so the exception is revisited. The matcher prints counts, matched entries, and days to expiry. It does not print secret values. Do not add raw secrets, secret substrings, or hashes of secret values to the baseline.

The example-path exclude file used by the nightly job is unchanged. It is not a detector exclude, and it does not cover this credential.

## After account closure

When account closure is confirmed, convert these entries into revoked-history suppressions: set `closed_on` to the closure date and set `evidence` to an https link that shows the closure. Leave the commits in history.

Rewriting git history is out of scope. It needs separate owner approval.
