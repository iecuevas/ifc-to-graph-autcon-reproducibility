# Pre-publication checklist

The package is ready to be uploaded to the **private** GitHub repository. Resolve every unchecked item below before changing repository visibility from **Private** to **Public**.

## Evidence reconciliation completed

- [x] **Python version reconciled.** Source metadata supports Python 3.12; the manuscript/package were corrected from 3.14 to 3.12.
- [x] **Database-reset wording reconciled.** The manuscript/package no longer claim that indexes and constraints were purged between runs. The preserved source supports graph-data deletion/query-cache clearing and timed `CREATE ... IF NOT EXISTS` schema preparation.
- [x] Preserved source files verified byte-for-byte against the audited snapshot using `scripts/verify_source_integrity.py`.
- [x] Package-level secret scan completed with no obvious committed secrets/credentials detected.
- [x] No synthetic 40-run timing dataset was created; only reported aggregate statistics are included.

## Blocking items before public release

- [ ] Confirm with the project PI/team that the preserved institutional source files may be published from the personal GitHub repository `iecuevas/ifc-to-graph-autcon-reproducibility`.
- [ ] Confirm the software author/contributor list for `CITATION.cff`.
- [ ] Approve a software license. The institutional snapshot contains no `LICENSE` file, so no license has been inferred or invented.
- [ ] Verify redistribution rights for every benchmark IFC file before adding any model binary. Until then, keep benchmark files out of the repository.
- [ ] Replace `CITATION.cff.template` with a final `CITATION.cff` after attribution is approved.
- [ ] Add the approved `LICENSE` file.
- [ ] Decide whether to leave the Neo4j DBMS/server engine version unreported (current evidence-bounded choice) or add it only if recoverable from an authoritative experiment record.
- [ ] If the original 40 per-run timing records are ever recovered, add them as raw data and verify their recomputed mean/SD/CV; do not reconstruct missing raw runs.
- [ ] Run one final secret/provenance scan immediately before switching the repository to Public.
- [ ] Create the versioned release (planned: `v1.0-autcon-revision`).
- [ ] Archive the exact release in Zenodo and insert the final repository URL, release tag, and DOI into the manuscript and Response to Reviewers.

## Upload-now instruction

It is safe to populate the repository while it remains **Private**. Upload the contents of this package root, not the original institutional ZIP.
