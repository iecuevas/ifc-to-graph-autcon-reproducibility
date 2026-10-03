# IFC-to-Graph AUTCON reproducibility package

> **Private-repository staging package.** This repository supports the major revision of manuscript **AUTCON-D-26-04369**, *Optimized IFC-to-Graph Conversion: Reducing the Performance Barrier to Graph-Based BIM Data Representation*. The package is ready to be uploaded to the private GitHub repository `iecuevas/ifc-to-graph-autcon-reproducibility`. Keep the repository Private until the remaining publication-rights, license,
and archival-release items in PREPUBLICATION_CHECKLIST.md are resolved.

## Scope

This repository contains a minimal, paper-focused reproducibility package for the IFC-to-Graph conversion and persistence implementation evaluated in the manuscript. It intentionally excludes unrelated multi-agent, API, deployment, document-RAG, and project-management components from the larger institutional repository.

Four implementation files are preserved **byte-for-byte** from the audited source snapshot:

- `src/ingest/ifc_graph/graph_builder.py`
- `src/core/neo4j_driver.py`
- `src/core/logger.py`
- `src/core/timer.py`

The source Python-version metadata file `.python-version` is also preserved from the supplied snapshot. Provenance and SHA-256 hashes are recorded in `SOURCE_MANIFEST.csv` and `docs/provenance.md`.

Files under `scripts/`, most files under `docs/`, package `__init__.py` files, `.env.example`, and the CSV summaries were added during the major-revision reproducibility work. They are support material and were **not** part of the preserved experimental implementation.

## Repository provenance

- Source project: institutional GitLab project `arencox-ia`
- Audited source snapshot / ZIP comment: `b7c821ec50f8be67e3cd82ca08dd67c707701e55`
- Target GitHub repository: `https://github.com/iecuevas/ifc-to-graph-autcon-reproducibility`

The commit above is the exact snapshot audited during revision. The supplied archive does not independently establish that this was the historical commit used for every original benchmark run, so the release describes it as the **audited revision snapshot**.

## What is included

- audited IFC-to-Graph graph-builder and Neo4j persistence code;
- source Python-version metadata (`3.12`);
- minimal Python dependency list;
- a revision-added CLI helper for running a conversion;
- a revision-added database reset helper;
- parser-behavior documentation based on direct source inspection;
- experimental environment and protocol documentation reconciled to the available evidence;
- benchmark manifest for the eight models used in the study;
- reported timing statistics and graph-count comparison.

## What is intentionally not included

- the full institutional repository;
- agent/LLM code, APIs, deployment scripts, cloud configuration, private project notes, or unrelated experiments;
- `.env` files, credentials, API keys, passwords, tokens, or service configuration;
- raw IFC benchmark files, pending verification of redistribution rights;
- fabricated per-run timing data. The supplied source snapshot did not contain the 40 individual run records (8 models x 5 runs), so only the reported aggregate statistics are included.

## Software environment

The source snapshot consistently identifies **Python 3.12** (`.python-version = 3.12`; original project configuration requires Python `>=3.12`). The revised manuscript has been reconciled to report Python 3.12 rather than the previously stated 3.14.

Minimal Python dependencies used by the preserved conversion code are:

```text
ifcopenshell==0.8.0
neo4j==5.28.1
```

The preserved graph builder also requires an operational Neo4j database with APOC available because it calls APOC procedures for dynamic labels, batching, and relationship creation. The reported study environment additionally records Neo4j Desktop 2.0.5 and APOC 2025.10.1-core. The separate underlying Neo4j DBMS/server version is not recoverable from the supplied materials and is therefore not invented in this package.

See `docs/environment.md` for the complete recorded configuration.

## Quick start

The helper below was added for the reproducibility release; it is **not** represented as original experimental code.

1. Use Python 3.12 and create/activate an isolated environment.
2. Install the minimal dependencies:

```bash
pip install -r requirements.txt
```

3. Start Neo4j and ensure APOC is installed/enabled.
4. Copy `.env.example` values into your local environment and set your own Neo4j password. Do not commit real credentials.
5. Run a conversion:

```bash
python scripts/run_conversion.py path/to/model.ifc --clear-ifc --json-out conversion_result.json
```

For destructive database-reset options intended for future reproduction attempts, see:

```bash
python scripts/reset_database.py --help
```

## Timing boundary implemented in the preserved code

`IfcGraphBuilder.build_graph()` returns a `total_time` equal to the sum of the measured durations for:

1. index/constraint preparation (`CREATE ... IF NOT EXISTS`);
2. IFC file opening;
3. schema / project / IFC-file node creation;
4. entity processing and node persistence;
5. relationship processing and persistence.

Pre-run graph-data clearing, operating-system cache clearing, and machine restart are outside this returned timing value. The preserved code supports deleting an existing IFC graph namespace before conversion and contains a database-clearing method that deletes graph data and clears the Neo4j query cache. The supplied snapshot does **not** establish that indexes and constraints were dropped between benchmark runs; accordingly, the revised manuscript no longer makes that claim. See `docs/experimental_protocol.md`.

## Results supplied

`results/timings_summary.csv` contains the mean, standard deviation, coefficient of variation, published baseline time, and descriptive baseline/proposed-time ratio reported in the revised manuscript. `results/graph_counts.csv` contains the published and proposed node/relationship counts.

The baseline values originate from Zhu, Wu, and Lei (2023), *IFC-graph for facilitating building information access and query*, Automation in Construction 148, 104778, DOI `10.1016/j.autcon.2023.104778`.

## Benchmark files and raw timing records

The eight benchmark IFC binaries are not redistributed in this staging package because redistribution rights have not yet been verified. `benchmarks/model_manifest.csv` provides the paper identifiers and known metadata without claiming file redistribution rights.

The supplied source snapshot contains no recoverable file with the 40 individual timing observations implied by 8 models x 5 runs. Raw observations are therefore not reconstructed. Only the reported aggregate statistics are provided.

## Authorship and source attribution

This repository accompanies the manuscript:

**“Optimized IFC-to-Graph Conversion: Reducing the Performance Barrier to Graph-Based BIM Data Representation”**

The authors of the associated manuscript and reproducibility package are:

- Ignacio Cuevas, Pontifical Catholic University of Chile
- Sebastián Lobo, Pontifical Catholic University of Chile
- Andrés Neyem, Pontifical Catholic University of Chile
- Claudio Mourgues, Pontifical Catholic University of Chile

Ignacio Cuevas is the corresponding author of the associated manuscript.

### Source-code attribution

The original IFC-to-Graph implementation preserved in this repository was developed by **Sebastián Lobo** within the institutional `arencox-ia` project.

The following core implementation files are preserved from the audited source snapshot:

- `src/ingest/ifc_graph/graph_builder.py`
- `src/core/neo4j_driver.py`
- `src/core/logger.py`
- `src/core/timer.py`

The remaining documentation, provenance records, benchmark metadata, results summaries, packaging files, and reproducibility helper scripts were assembled or added for the major-revision reproducibility package associated with AUTCON-D-26-04369.

This repository is intentionally limited to the code and supporting material required to document and reproduce the IFC-to-Graph workflow evaluated in the article.

## Citation and license

Citation metadata for this reproducibility package are provided in `CITATION.cff`.

The associated manuscript and reproducibility package are authored by Ignacio Cuevas, Sebastián Lobo, Andrés Neyem, and Claudio Mourgues. The original IFC-to-Graph implementation preserved in this repository was developed by Sebastián Lobo, as stated in the source-code attribution section above.

A software license has not yet been assigned. The preserved implementation originates from an institutional project, and public-release authorization and licensing must be confirmed before the repository is made Public.

Until that authorization is resolved, this repository must remain **Private**.

After public-release authorization is confirmed, the repository will be finalized by:
1. assigning the approved software license, if applicable;
2. removing private staging and prepublication-control files;
3. creating the journal-revision release;
4. archiving that release with a persistent identifier; and
5. inserting the final repository URL, release tag, and archival DOI into the manuscript and Response to Reviewers.
