# Provenance

## Source snapshot

The publication package was assembled from the supplied archive `arencox-ia-master.zip`.

- ZIP-embedded source commit: `b7c821ec50f8be67e3cd82ca08dd67c707701e55`
- ZIP SHA-256: `06552f39640806afc1d88651252454fd84eb1665a45b005a2dcf8ba98ab93bab`
- Source project name: `arencox-ia`

The four files classified as `preserved_source` in `SOURCE_MANIFEST.csv` were copied byte-for-byte. The source `.python-version` metadata file was also copied without modification. The publication packaging process did not reformat, translate, or modify those preserved items.

## Scope of the GitHub package

The institutional project is broader than the paper. It contains multi-agent, API, document ingestion/RAG, deployment, CI, experiment, and project-management material that is not necessary to expose the IFC-to-Graph conversion implementation evaluated in the article. Those components were intentionally excluded.

## Revision-added material

The following material was created specifically for the major-revision reproducibility package and should not be represented as original experimental code:

- package `__init__.py` files;
- `.env.example`;
- `scripts/run_conversion.py`;
- `scripts/reset_database.py`;
- `scripts/verify_source_integrity.py`;
- documentation under `docs/`;
- benchmark/result CSVs;
- repository README, minimal requirements file, citation template, and pre-publication checklist.

## Evidence reconciliation performed during revision

Two earlier manuscript details were narrowed after auditing the source snapshot:

1. **Python version:** the manuscript was corrected from Python 3.14 to Python 3.12 because the source archive consistently records 3.12 / `>=3.12` and provides no evidence for 3.14.
2. **Pre-run schema reset:** the manuscript no longer states that indexes and constraints were dropped before every run. The preserved clearing methods delete graph data (and, in `clear_database()`, clear the query cache), while `build_graph()` ensures the required schema objects exist with `CREATE ... IF NOT EXISTS` at the beginning of the timed routine.

These corrections are documentation/reproducibility reconciliations; the preserved implementation files themselves remain byte-for-byte unchanged.

## Important historical limitation

The commit above is the exact source snapshot audited during revision. The supplied archive by itself does not establish the historical commit at which every benchmark run was originally executed. The release therefore describes this commit as the **audited revision snapshot** unless an authoritative experiment record establishes otherwise.
