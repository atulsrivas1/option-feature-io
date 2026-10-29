# HANDOFF

State (2026-10-29): option-feature-io moved to 0.2.0a1 with exact pins option-feature-contracts==0.2.0a1, following the library P1 compatibility manifest (option-features docs/p1/COMPATIBILITY.json, library commit 62a178c).

- Pins: packages/*/pyproject.toml; tests/fixtures.py embeds the result version strings.
- Version records: docs/VERSIONING.md (P1 paragraph).
- History, not edited: docs/R25_*, docs/SESSION_HANDOFF.md, docs/OPEN_CONTRACTS.json (R25 pointers), variants1 reference cohort strings.
- Not qualified: no wheels built, nothing published; the manifest marks 0.2.0a1 qualified=false.
- Open for PO: see the pull request body.
