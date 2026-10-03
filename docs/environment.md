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
