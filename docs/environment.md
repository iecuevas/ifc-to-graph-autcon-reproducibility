# Experimental environment

## Configuration supported by the manuscript record and source snapshot

- Operating system: Windows 10 Pro 22H2
- CPU: Intel Core i7-12700
- RAM: 128 GB
- Storage: 2.73 TB (932 GB Crucial SSD + 1.82 TB WDC HDD)
- GPUs: NVIDIA GeForce GTX 1080 Ti (11 GB) and NVIDIA GeForce RTX 2080 (8 GB)
- Neo4j Desktop: 2.0.5
- APOC: 2025.10.1-core
- Neo4j Python Driver: 5.28.1
- Python: **3.12**
- IfcOpenShell: 0.8.0

## Python-version reconciliation

The earlier revision draft stated Python 3.14. The supplied institutional source archive instead provides multiple concordant indicators of the project runtime baseline, including `.python-version = 3.12` and original project configuration requiring Python `>=3.12`. Because no supplied artifact supports Python 3.14 for the audited conversion snapshot, the manuscript and this reproducibility package were reconciled to **Python 3.12**.

The original broad project configuration was not copied into this paper-specific package because it contains many dependencies unrelated to the IFC-to-Graph paper. `requirements.txt` therefore lists only the external Python packages imported by the preserved conversion implementation and pins the Neo4j driver to the version recorded in the manuscript.

## Neo4j DBMS/server version

The manuscript record identifies Neo4j Desktop 2.0.5 but the supplied materials do not establish a separate Neo4j DBMS/server engine version with sufficient confidence. This package therefore reports the Desktop/APOC/driver versions that are documented and does not invent a DBMS engine version.

## APOC note

The preserved implementation uses APOC procedures for dynamic labels, batch execution, and relationship creation. Reproduction therefore requires APOC to be installed and enabled. The reported APOC version is documented as part of the evaluated environment rather than as a general future-version recommendation.

## Current reproduction smoke test

A clean-install smoke test of the preserved IFC-to-Graph workflow was completed using the public reproducibility package. This test does not replace or reinterpret the historical experimental environment reported in the manuscript.

The current reproduction environment was:

- Python 3.12.10
- IfcOpenShell 0.8.1
- Neo4j Python Driver 5.28.1
- Neo4j DBMS 2025.10.1
- APOC 2025.10.1-core
- Neo4j Desktop 2.2.1
- Windows

The recorded historical study environment used IfcOpenShell 0.8.0. During the current clean-install test, that version was not resolvable through the tested Python 3.12 / pip installation path, so IfcOpenShell 0.8.1 was used for the reproduction smoke test. No preserved IFC-to-Graph implementation source code was modified.

The smoke test successfully opened and converted an IFC2X3 model and persisted the resulting graph to Neo4j without an exception. The instrumented conversion reported:

- 557,189 processed nodes
- 954,667 processed relationships
- total conversion time of approximately 89.99 s

The physical Neo4j database contained 557,192 nodes and 954,668 relationships. The difference corresponds to the contextual Project, IfcFile, and IfcSchema nodes created during initialization and the HAS_IFC relationship between the project and IFC-file context.

These smoke-test values are provided only to document successful execution of the public reproducibility package. They are not part of the historical benchmark dataset and are not used as performance results in the manuscript.
